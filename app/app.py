"""Simulateur de fiche de paie (Tunisie, régime CNSS non agricole RSNA).

Interface Shiny for Python. Aucun calcul n'est fait ici : la situation est
envoyée à l'API OpenFisca-Tunisia, qui renvoie le bulletin.

Lancer l'API puis l'app, en local :
    openfisca serve -c openfisca_tunisia -p 5000
    shiny run app/app.py
"""

from __future__ import annotations

import httpx
from shiny import App, reactive, render, ui

from openfisca_client import (
    BRANCHES_CNSS_SALARIE,
    DEDUCTIONS_ANNUELLES,
    api_disponible,
    brut_depuis_net,
    calculer_bulletin,
    calculer_irpp_annuel,
    construire_situation,
    valoriser_heures_supp,
)
from i18n import LANGUES, t

# Clés i18n des branches CNSS et déductions (mêmes ordres que dans le client).
CLE_BRANCHE = {
    "retraite_salarie": "br_retraite",
    "retraite_complementaire_salarie": "br_retraite_compl",
    "maladie_salarie": "br_maladie",
    "maternite_salarie": "br_maternite",
    "deces_salarie": "br_deces",
    "famille_salarie": "br_famille",
    "accident_du_travail_salarie": "br_accident",
    "perte_d_emploi_salarie": "br_perte_emploi",
    "protection_sociale_travailleurs_salarie": "br_protection",
    "soin_salarie": "br_soins",
}
CLE_REGIME = {
    "rsna": "reg_rsna", "rsa": "reg_rsa", "rsaa": "reg_rsaa",
    "salarie_cnrps": "reg_cnrps", "neant": "reg_neant",
}
CLE_DEDUCTION = {
    "prime_assurance_vie": "ded_assurance_vie",
    "interets_acquisition_logement": "ded_logement",
    "compte_epargne_en_actions": "ded_cea",
    "compte_epargne_investissement": "ded_cei",
    "pret_universitaire": "ded_pret_univ",
    "dons": "ded_dons",
}

ANNEES = [str(a) for a in range(2020, 2027)]

# Régimes de sécurité sociale pour salariés (valeur openfisca -> libellé UI).
# CIVP/stage et entreprise totalement exportatrice ne sont pas modelés dans
# openfisca-tunisia : on les traite en "neant" (exonération, 0 cotisation).
REGIMES = {
    "rsna": "Privé non agricole (RSNA)",
    "rsa": "Salarié agricole (RSA)",
    "rsaa": "Agricole amélioré (RSAA)",
    "salarie_cnrps": "Secteur public (CNRPS)",
    "neant": "Exonéré / CIVP / export (0 cotisation)",
}

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("lang", "Langue / اللغة", LANGUES, selected="fr"),
        ui.input_select("annee", "Année de paie", ANNEES, selected="2025"),
        ui.input_select("regime", "Régime de sécurité sociale", REGIMES, selected="rsna"),
        ui.input_radio_buttons(
            "sens",
            "Sens du calcul",
            {"brut_net": "Brut → Net", "net_brut": "Net → Brut"},
            selected="brut_net",
            inline=True,
        ),
        ui.panel_conditional(
            "input.sens === 'brut_net'",
            ui.input_numeric("salaire_de_base", "Salaire de base (DT/mois)", 1500, min=0, step=50),
            ui.input_numeric("primes", "Primes et indemnités (DT/mois)", 0, min=0, step=50),
            ui.input_numeric("heures_sup", "Heures supplémentaires (nb/mois)", 0, min=0, step=1),
            ui.input_select(
                "regime_horaire",
                "Régime hebdomadaire",
                {"48h": "48 h/semaine (+75 %)", "40h": "40 h/semaine (+25/50 %)"},
                selected="48h",
            ),
        ),
        ui.panel_conditional(
            "input.sens === 'net_brut'",
            ui.input_numeric("net_cible", "Net à payer souhaité (DT/mois)", 1200, min=0, step=50),
            ui.input_numeric("primes_net", "Primes connues (DT/mois)", 0, min=0, step=50),
        ),
        ui.hr(),
        ui.h6("Situation familiale (IRPP)"),
        ui.input_checkbox("chef_de_famille", "Chef de famille", False),
        ui.input_numeric("nb_enf", "Enfants à charge (≤ 4)", 0, min=0, max=10, step=1),
        ui.input_numeric("nb_enf_sup", "Étudiants sans bourse", 0, min=0, max=10, step=1),
        ui.input_numeric("nb_infirme", "Enfants handicapés", 0, min=0, max=10, step=1),
        ui.hr(),
        ui.input_checkbox(
            "adhesion_complementaire",
            "Retraite complémentaire CNSS (RSNA, > 6×SMIG)",
            False,
        ),
        ui.input_action_button("calculer", "Calculer le bulletin", class_="btn-primary"),
        width=320,
    ),
    ui.output_ui("statut_api"),
    ui.navset_tab(
        ui.nav_panel(
            "Bulletin mensuel",
            ui.output_ui("titre_bulletin_ui"),
            ui.output_ui("bulletin"),
            ui.download_button("export_pdf", "PDF"),
            ui.output_plot("courbe_net", height="320px"),
            ui.output_ui("note_bulletin_ui"),
            value="tab_bulletin",
        ),
        ui.nav_panel(
            "Comparateur",
            ui.output_ui("titre_comparateur_ui"),
            ui.output_ui("note_comparateur_ui"),
            ui.output_ui("comparateur"),
            value="tab_comparateur",
        ),
        ui.nav_panel(
            "Simulation annuelle (IRPP)",
            ui.output_ui("titre_annuel_ui"),
            ui.output_ui("note_annuel_ui"),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.output_ui("titre_deductions_ui"),
                    *[
                        ui.input_numeric(f"ded_{var}", var, 0, min=0, step=100)
                        for var in DEDUCTIONS_ANNUELLES
                    ],
                    width=330,
                ),
                ui.output_ui("annuel"),
            ),
            value="tab_annuel",
        ),
        id="onglets",
    ),
    title="Simulateur de paie Tunisie",
)


def _message_erreur(erreur: Exception) -> str:
    """Message clair selon le type d'erreur (mode API)."""
    if isinstance(erreur, httpx.TimeoutException):
        return (
            "Le calcul a expiré (API trop lente ou injoignable). "
            "Réessayez ; si le problème persiste, vérifiez que l'API tourne."
        )
    if isinstance(erreur, httpx.ConnectError):
        return (
            "Impossible de joindre le moteur de calcul (API injoignable). "
            "Démarrez l'API ou utilisez le mode local (OPENFISCA_MODE=local)."
        )
    return f"Erreur de calcul : {erreur}"


def _ligne(libelle: str, montant, *, fort: bool = False) -> ui.Tag:
    valeur = "—" if montant is None else f"{montant:,.3f} DT".replace(",", " ")
    style = "font-weight:700;" if fort else ""
    return ui.tags.tr(
        ui.tags.td(libelle, style=style),
        ui.tags.td(valeur, style=f"text-align:right;{style}"),
    )


def server(input, output, session):
    @reactive.effect
    def _appliquer_langue():
        lang = str(input.lang())
        # Direction du document : RTL pour l'arabe.
        direction = "rtl" if lang == "ar" else "ltr"
        ui.insert_ui(
            ui.tags.script(
                f"document.documentElement.setAttribute('dir', '{direction}');"
                f"document.documentElement.setAttribute('lang', '{lang}');"
            ),
            selector="body",
            where="beforeEnd",
            immediate=True,
        )
        # Labels des champs du panneau latéral.
        ui.update_select("annee", label=t("annee", lang))
        ui.update_select(
            "regime", label=t("regime", lang),
            choices={k: t(CLE_REGIME[k], lang) for k in REGIMES},
            selected=str(input.regime()),
        )
        ui.update_radio_buttons(
            "sens", label=t("sens", lang),
            choices={"brut_net": t("brut_net", lang), "net_brut": t("net_brut", lang)},
            selected=str(input.sens()),
        )
        ui.update_numeric("salaire_de_base", label=t("salaire_base", lang))
        ui.update_numeric("primes", label=t("primes", lang))
        ui.update_numeric("heures_sup", label=t("heures_sup", lang))
        ui.update_select(
            "regime_horaire", label=t("regime_horaire", lang),
            choices={"48h": t("reg_48h", lang), "40h": t("reg_40h", lang)},
            selected=str(input.regime_horaire()),
        )
        ui.update_numeric("net_cible", label=t("net_cible", lang))
        ui.update_numeric("primes_net", label=t("primes_net", lang))
        ui.update_checkbox("chef_de_famille", label=t("chef_famille", lang))
        ui.update_numeric("nb_enf", label=t("nb_enf", lang))
        ui.update_numeric("nb_enf_sup", label=t("nb_enf_sup", lang))
        ui.update_numeric("nb_infirme", label=t("nb_infirme", lang))
        ui.update_checkbox("adhesion_complementaire", label=t("adhesion_compl", lang))
        ui.update_action_button("calculer", label=t("calculer", lang))
        for var in DEDUCTIONS_ANNUELLES:
            ui.update_numeric(f"ded_{var}", label=t(CLE_DEDUCTION[var], lang))
        # NB : Shiny ne permet pas de renommer un onglet après création ; les
        # libellés d'onglets restent dans la langue de définition. Tout le
        # CONTENU (titres de section, notes, tableaux, champs) est traduit.

    # Titres et notes des onglets (sorties réactives traduites).
    @render.ui
    def titre_bulletin_ui():
        return ui.h4(t("titre_bulletin", str(input.lang())))

    @render.ui
    def note_bulletin_ui():
        return ui.markdown(t("note_moteur", str(input.lang())))

    @render.ui
    def titre_comparateur_ui():
        return ui.h4(t("titre_comparateur", str(input.lang())))

    @render.ui
    def note_comparateur_ui():
        return ui.markdown(t("note_comparateur", str(input.lang())))

    @render.ui
    def titre_annuel_ui():
        return ui.h4(t("titre_annuel", str(input.lang())))

    @render.ui
    def note_annuel_ui():
        return ui.markdown(t("note_annuel", str(input.lang())))

    @render.ui
    def titre_deductions_ui():
        return ui.h6(t("deductions_annuelles", str(input.lang())))

    @render.ui
    def statut_api():
        if api_disponible():
            return ui.TagList()
        return ui.div(
            ui.markdown(
                "⚠️ **API OpenFisca injoignable.** Démarrez-la en local :\n\n"
                "```\nopenfisca serve -c openfisca_tunisia -p 5000\n```"
            ),
            class_="alert alert-warning",
        )

    @reactive.calc
    @reactive.event(input.calculer, ignore_none=False)
    def resultat():
        annee = int(input.annee())
        regime = str(input.regime())
        adhesion = bool(input.adhesion_complementaire())
        fam = dict(
            chef_de_famille=bool(input.chef_de_famille()),
            nb_enf=int(input.nb_enf() or 0),
            nb_enf_sup=int(input.nb_enf_sup() or 0),
            nb_infirme=int(input.nb_infirme() or 0),
        )
        if str(input.sens()) == "net_brut":
            net_cible = float(input.net_cible() or 0)
            primes_net = float(input.primes_net() or 0)
            if net_cible <= 0:
                return ("invalide", "err_net_positif")
            if primes_net < 0:
                return ("invalide", "err_primes_neg")
            try:
                return ("ok", brut_depuis_net(
                    net_cible, annee=annee, regime=regime,
                    primes=primes_net,
                    adhesion_complementaire=adhesion, **fam,
                ))
            except httpx.HTTPError as erreur:
                return ("erreur", _message_erreur(erreur))
        salaire_base = float(input.salaire_de_base() or 0)
        primes_val = float(input.primes() or 0)
        if salaire_base < 0 or primes_val < 0:
            return ("invalide", "err_salaire_neg")
        if float(input.heures_sup() or 0) < 0:
            return ("invalide", "err_heures_neg")
        # Heures supplémentaires : non modélisées par OpenFisca côté bulletin.
        # On les valorise selon le régime horaire légal (art. 90 code du travail)
        # à partir du salaire de base, et on les ajoute aux primes.
        valeur_hs = valoriser_heures_supp(
            salaire_base,
            float(input.heures_sup() or 0),
            str(input.regime_horaire()),
        )
        situation = construire_situation(
            salaire_de_base=salaire_base,
            annee=annee,
            primes=primes_val + valeur_hs,
            regime=regime,
            adhesion_complementaire=adhesion,
            **fam,
        )
        try:
            return ("ok", calculer_bulletin(situation, annee=annee))
        except httpx.HTTPError as erreur:
            return ("erreur", _message_erreur(erreur))

    @render.ui
    def bulletin():
        lang = str(input.lang())
        statut, contenu = resultat()
        if statut == "invalide":
            return ui.div(ui.markdown(f"⚠️ {t(contenu, lang)}"), class_="alert alert-warning")
        if statut == "erreur":
            return ui.div(
                ui.markdown(f"**{contenu}**"),
                class_="alert alert-danger",
            )

        b = contenu
        brut = b["salaire_brut"]

        avertissement = ui.TagList()
        if str(input.regime()) == "neant":
            avertissement = ui.div(
                ui.markdown("ℹ️ " + t("avert_exonere", lang)),
                class_="alert alert-info",
            )
        css = b["contribution_sociale_solidarite_prelevee_a_la_source"] or 0.0

        # Détail des branches CNSS non nulles (repli dans un <details>).
        lignes_branches = [
            _ligne(f" {t(CLE_BRANCHE[var], lang)}", -(b[var] or 0.0))
            for var in BRANCHES_CNSS_SALARIE
            if (b.get(var) or 0.0) > 0
        ]
        detail_cnss = ui.tags.details(
            ui.tags.summary(t("detail_cnss", lang)),
            ui.tags.table(ui.tags.tbody(*lignes_branches), class_="table table-sm"),
        )

        salarie = ui.tags.table(
            ui.tags.tbody(
                _ligne(t("salaire_brut", lang), brut, fort=True),
                _ligne(t("cnss_salariale", lang), -(b["cotisations_salarie"] or 0.0)),
                _ligne(t("salaire_imposable", lang), b["salaire_imposable"]),
                _ligne(t("irpp_ras", lang), -(b["irpp_salarie_preleve_a_la_source"] or 0.0)),
                _ligne(t("css", lang), -css),
                _ligne(t("net_a_payer", lang), b["salaire_net_a_payer"], fort=True),
            ),
            class_="table table-sm",
        )

        net = b["salaire_net_a_payer"] or 0.0
        taux_preleve = (1 - net / brut) * 100 if brut > 0 else 0.0
        taux_txt = ui.tags.p(
            ui.tags.small(
                f"{t('taux_preleve', lang)} : {taux_preleve:.1f} %"
                if brut > 0 else ""
            )
        )

        employeur = ui.tags.table(
            ui.tags.tbody(
                _ligne(t("cnss_patronale", lang), b["cotisations_employeur"]),
                _ligne(t("cout_employeur", lang), b["salaire_super_brut"], fort=True),
            ),
            class_="table table-sm",
        )

        return ui.TagList(
            avertissement,
            ui.layout_columns(
                ui.card(ui.card_header(t("cote_salarie", lang)), salarie, taux_txt, detail_cnss),
                ui.card(ui.card_header(t("cote_employeur", lang)), employeur),
                col_widths=(7, 5),
            ),
        )

    @render.download(filename="bulletin_paie.pdf")
    def export_pdf():
        import io

        import matplotlib.pyplot as plt

        statut, contenu = resultat()
        # matplotlib ne rend pas correctement l'arabe RTL (réserveré à une
        # itération ultérieure avec arabic-reshaper + python-bidi) : le PDF est
        # produit en français quelle que soit la langue de l'UI.
        lang_pdf = "fr"
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.axis("off")
        if statut != "ok":
            ax.text(0.5, 0.5, "Aucun bulletin calculé.", ha="center")
        else:
            b = contenu
            css = b["contribution_sociale_solidarite_prelevee_a_la_source"] or 0.0
            lignes = [
                (t("salaire_brut", lang_pdf), b["salaire_brut"]),
                (t("cnss_salariale", lang_pdf), -(b["cotisations_salarie"] or 0.0)),
                (t("salaire_imposable", lang_pdf), b["salaire_imposable"]),
                (t("irpp_ras", lang_pdf), -(b["irpp_salarie_preleve_a_la_source"] or 0.0)),
                (t("css", lang_pdf), -css),
                (t("net_a_payer", lang_pdf), b["salaire_net_a_payer"]),
                ("", None),
                (t("cnss_patronale", lang_pdf), b["cotisations_employeur"]),
                (t("cout_employeur", lang_pdf), b["salaire_super_brut"]),
            ]
            ax.set_title(
                f"{t('titre_bulletin', lang_pdf)} — {str(input.regime()).upper()} {int(input.annee())}",
                fontsize=14, fontweight="bold",
            )
            y = 0.9
            for libelle, montant in lignes:
                if libelle:
                    val = "" if montant is None else f"{montant:,.3f} DT".replace(",", " ")
                    gras = libelle in (t("net_a_payer", lang_pdf), t("cout_employeur", lang_pdf))
                    ax.text(0.05, y, libelle, fontsize=11,
                            fontweight="bold" if gras else "normal")
                    ax.text(0.95, y, val, fontsize=11, ha="right",
                            fontweight="bold" if gras else "normal")
                y -= 0.08
            ax.text(0.05, 0.02, "Calculé par OpenFisca-Tunisia — estimation indicative.",
                    fontsize=8, style="italic", color="#666")

        buf = io.BytesIO()
        fig.savefig(buf, format="pdf")
        plt.close(fig)
        yield buf.getvalue()

    @render.plot(alt="Courbe du net en fonction du brut")
    @reactive.event(input.calculer, ignore_none=False)
    def courbe_net():
        import matplotlib.pyplot as plt

        annee = int(input.annee())
        regime = str(input.regime())
        bruts = list(range(500, 6001, 250))
        nets = []
        for montant in bruts:
            situation = construire_situation(
                salaire_de_base=montant, annee=annee, regime=regime
            )
            b = calculer_bulletin(situation, annee=annee)
            nets.append(b["salaire_net_a_payer"] or 0.0)

        fig, ax = plt.subplots()
        ax.plot(bruts, nets, color="#2a7", label="Net à payer")
        ax.plot(bruts, bruts, color="#ccc", linestyle="--", label="Brut (référence)")
        ax.set_xlabel("Salaire brut (DT/mois)")
        ax.set_ylabel("Net à payer (DT/mois)")
        ax.set_title(f"Net selon le brut — {regime.upper()} {annee}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        return fig

    @render.ui
    @reactive.event(input.calculer, ignore_none=False)
    def comparateur():
        lang = str(input.lang())
        salaire_base = float(input.salaire_de_base() or 0)
        if salaire_base <= 0:
            return ui.div(
                ui.markdown("⚠️ " + t("err_salaire_neg", lang)),
                class_="alert alert-warning",
            )
        fam = dict(
            chef_de_famille=bool(input.chef_de_famille()),
            nb_enf=int(input.nb_enf() or 0),
            nb_enf_sup=int(input.nb_enf_sup() or 0),
            nb_infirme=int(input.nb_infirme() or 0),
        )
        regime_courant = str(input.regime())
        annee_courante = int(input.annee())

        def net(annee, regime):
            b = calculer_bulletin(
                construire_situation(
                    salaire_de_base=salaire_base, annee=annee, regime=regime, **fam
                ),
                annee=annee,
            )
            return b["salaire_net_a_payer"] or 0.0, b["cotisations_salarie"] or 0.0

        try:
            lignes_annees = []
            for a in range(2020, 2027):
                n, c = net(a, regime_courant)
                lignes_annees.append(
                    ui.tags.tr(
                        ui.tags.td(str(a)),
                        ui.tags.td(f"{c:.3f}", style="text-align:right"),
                        ui.tags.td(f"{n:.3f}", style="text-align:right"),
                    )
                )
            lignes_regimes = []
            for code in REGIMES:
                n, c = net(annee_courante, code)
                lignes_regimes.append(
                    ui.tags.tr(
                        ui.tags.td(t(CLE_REGIME[code], lang)),
                        ui.tags.td(f"{c:.3f}", style="text-align:right"),
                        ui.tags.td(f"{n:.3f}", style="text-align:right"),
                    )
                )
        except httpx.HTTPError as erreur:
            return ui.div(
                ui.markdown(f"**{_message_erreur(erreur)}**"), class_="alert alert-danger"
            )

        entete = ui.tags.thead(
            ui.tags.tr(
                ui.tags.th(""),
                ui.tags.th(t("col_cnss", lang), style="text-align:right"),
                ui.tags.th(t("col_net", lang), style="text-align:right"),
            )
        )
        return ui.layout_columns(
            ui.card(
                ui.card_header(f"{t('par_annee', lang)} — {regime_courant.upper()}"),
                ui.tags.table(entete, ui.tags.tbody(*lignes_annees), class_="table table-sm"),
            ),
            ui.card(
                ui.card_header(f"{t('par_regime', lang)} — {annee_courante}"),
                ui.tags.table(entete, ui.tags.tbody(*lignes_regimes), class_="table table-sm"),
            ),
            col_widths=(6, 6),
        )

    @render.ui
    @reactive.event(input.calculer, ignore_none=False)
    def annuel():
        lang = str(input.lang())
        annee = int(input.annee())
        salaire_mensuel = float(input.salaire_de_base() or 0)
        deductions = {
            var: float(input[f"ded_{var}"]() or 0)
            for var in DEDUCTIONS_ANNUELLES
            if float(input[f"ded_{var}"]() or 0) > 0
        }
        try:
            res = calculer_irpp_annuel(
                salaire_annuel=salaire_mensuel * 12,
                annee=annee,
                regime=str(input.regime()),
                chef_de_famille=bool(input.chef_de_famille()),
                nb_enf=int(input.nb_enf() or 0),
                nb_enf_sup=int(input.nb_enf_sup() or 0),
                nb_infirme=int(input.nb_infirme() or 0),
                deductions=deductions,
            )
        except httpx.HTTPError as erreur:
            return ui.div(
                ui.markdown(f"**{_message_erreur(erreur)}**"),
                class_="alert alert-danger",
            )

        irpp = res["irpp"] or 0.0
        ras = res["ras_annuelle"] or 0.0
        solde = res["irpp_net_a_payer"] or 0.0
        libelle_solde = (
            t("solde_payer", lang) if solde >= 0 else t("trop_percu", lang)
        )

        table = ui.tags.table(
            ui.tags.tbody(
                _ligne(t("salaire_annuel", lang), salaire_mensuel * 12),
                _ligne(t("irpp_annuel_du", lang), irpp, fort=True),
                _ligne(t("ras_prelevee", lang), -ras),
                _ligne(libelle_solde, abs(solde), fort=True),
            ),
            class_="table table-sm",
        )

        # Effet des déductions : IRPP sans déduction vs avec.
        effet = ui.TagList()
        if deductions:
            try:
                ref = calculer_irpp_annuel(
                    salaire_annuel=salaire_mensuel * 12,
                    annee=annee,
                    regime=str(input.regime()),
                    chef_de_famille=bool(input.chef_de_famille()),
                    nb_enf=int(input.nb_enf() or 0),
                    nb_enf_sup=int(input.nb_enf_sup() or 0),
                    nb_infirme=int(input.nb_infirme() or 0),
                    deductions={},
                )
                irpp_sans = ref["irpp"] or 0.0
                economie = irpp_sans - irpp
                lignes_ded = [
                    _ligne(f" {t(CLE_DEDUCTION[v], lang)}", -montant)
                    for v, montant in deductions.items()
                ]
                effet = ui.card(
                    ui.card_header(t("effet_deductions", lang)),
                    ui.tags.table(
                        ui.tags.tbody(
                            _ligne(t("irpp_sans", lang), irpp_sans),
                            *lignes_ded,
                            _ligne(t("irpp_avec", lang), irpp),
                            _ligne(t("economie", lang), economie, fort=True),
                        ),
                        class_="table table-sm",
                    ),
                )
            except httpx.HTTPError:
                effet = ui.TagList()

        return ui.TagList(ui.card(ui.card_header(t("irpp_annuel_du", lang)), table), effet)


app = App(app_ui, server)
