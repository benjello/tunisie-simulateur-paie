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
            ui.h4("Fiche de paie — salarié (Tunisie)"),
            ui.output_ui("bulletin"),
            ui.output_plot("courbe_net", height="320px"),
            ui.markdown(
                "Calculé par le moteur **OpenFisca-Tunisia** (via son API). "
                "Convention : cotisations au taux du mois de paie, barème IRPP "
                "des revenus de l'année de paie (retenue à la source)."
            ),
        ),
        ui.nav_panel(
            "Simulation annuelle (IRPP)",
            ui.h4("IRPP annuel et déductions"),
            ui.markdown(
                "Les déductions ci-dessous (assurance-vie, crédit logement, "
                "épargne, dons…) **ne réduisent pas la retenue à la source "
                "mensuelle** : elles ne jouent qu'au niveau de l'**IRPP annuel**, "
                "en régularisation lors de la déclaration. Salaire annuel = "
                "12 × salaire de base mensuel saisi."
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h6("Déductions annuelles (DT/an)"),
                    *[
                        ui.input_numeric(f"ded_{var}", libelle, 0, min=0, step=100)
                        for var, libelle in DEDUCTIONS_ANNUELLES.items()
                    ],
                    width=330,
                ),
                ui.output_ui("annuel"),
            ),
        ),
    ),
    title="Simulateur de paie Tunisie",
)


def _ligne(libelle: str, montant, *, fort: bool = False) -> ui.Tag:
    valeur = "—" if montant is None else f"{montant:,.3f} DT".replace(",", " ")
    style = "font-weight:700;" if fort else ""
    return ui.tags.tr(
        ui.tags.td(libelle, style=style),
        ui.tags.td(valeur, style=f"text-align:right;{style}"),
    )


def server(input, output, session):
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
                return ("invalide", "Saisissez un net à payer strictement positif.")
            if primes_net < 0:
                return ("invalide", "Les primes ne peuvent pas être négatives.")
            try:
                return ("ok", brut_depuis_net(
                    net_cible, annee=annee, regime=regime,
                    primes=primes_net,
                    adhesion_complementaire=adhesion, **fam,
                ))
            except httpx.HTTPError as erreur:
                return ("erreur", str(erreur))
        salaire_base = float(input.salaire_de_base() or 0)
        primes_val = float(input.primes() or 0)
        if salaire_base < 0 or primes_val < 0:
            return ("invalide", "Le salaire et les primes ne peuvent pas être négatifs.")
        if float(input.heures_sup() or 0) < 0:
            return ("invalide", "Le nombre d'heures supplémentaires ne peut pas être négatif.")
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
            return ("erreur", str(erreur))

    @render.ui
    def bulletin():
        statut, contenu = resultat()
        if statut == "invalide":
            return ui.div(ui.markdown(f"⚠️ {contenu}"), class_="alert alert-warning")
        if statut == "erreur":
            return ui.div(
                ui.markdown(f"**Erreur de calcul :** {contenu}"),
                class_="alert alert-danger",
            )

        b = contenu
        brut = b["salaire_brut"]

        avertissement = ui.TagList()
        if str(input.regime()) == "neant":
            avertissement = ui.div(
                ui.markdown(
                    "ℹ️ Régime **exonéré** sélectionné : aucune cotisation sociale. "
                    "CIVP/stage et entreprise totalement exportatrice ne sont pas "
                    "paramétrés finement dans le modèle ; le résultat suppose une "
                    "exonération totale."
                ),
                class_="alert alert-info",
            )
        css = b["contribution_sociale_solidarite_prelevee_a_la_source"] or 0.0

        # Détail des branches CNSS non nulles (repli dans un <details>).
        lignes_branches = [
            _ligne(f" {libelle}", -(b[var] or 0.0))
            for var, libelle in BRANCHES_CNSS_SALARIE.items()
            if (b.get(var) or 0.0) > 0
        ]
        detail_cnss = ui.tags.details(
            ui.tags.summary("Détail des branches CNSS"),
            ui.tags.table(ui.tags.tbody(*lignes_branches), class_="table table-sm"),
        )

        salarie = ui.tags.table(
            ui.tags.tbody(
                _ligne("Salaire brut", brut, fort=True),
                _ligne("CNSS salariale", -(b["cotisations_salarie"] or 0.0)),
                _ligne("Salaire imposable", b["salaire_imposable"]),
                _ligne("IRPP (retenue à la source)", -(b["irpp_salarie_preleve_a_la_source"] or 0.0)),
                _ligne("CSS (contribution solidarité)", -css),
                _ligne("Net à payer", b["salaire_net_a_payer"], fort=True),
            ),
            class_="table table-sm",
        )

        net = b["salaire_net_a_payer"] or 0.0
        taux_preleve = (1 - net / brut) * 100 if brut > 0 else 0.0
        taux_txt = ui.tags.p(
            ui.tags.small(
                f"Taux de prélèvement global : {taux_preleve:.1f} % "
                f"(net = {net / brut * 100:.1f} % du brut)"
                if brut > 0 else ""
            )
        )

        employeur = ui.tags.table(
            ui.tags.tbody(
                _ligne("CNSS patronale", b["cotisations_employeur"]),
                _ligne("Coût total employeur (super-brut)", b["salaire_super_brut"], fort=True),
            ),
            class_="table table-sm",
        )

        return ui.TagList(
            avertissement,
            ui.layout_columns(
                ui.card(ui.card_header("Côté salarié"), salarie, taux_txt, detail_cnss),
                ui.card(ui.card_header("Côté employeur"), employeur),
                col_widths=(7, 5),
            ),
        )

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
    def annuel():
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
                ui.markdown(f"**Erreur de calcul :** {erreur}"),
                class_="alert alert-danger",
            )

        irpp = res["irpp"] or 0.0
        ras = res["ras_annuelle"] or 0.0
        solde = res["irpp_net_a_payer"] or 0.0
        libelle_solde = (
            "Solde à payer (régularisation)" if solde >= 0
            else "Trop-perçu (restitution)"
        )

        table = ui.tags.table(
            ui.tags.tbody(
                _ligne("Salaire annuel (12 mois)", salaire_mensuel * 12),
                _ligne("IRPP annuel dû", irpp, fort=True),
                _ligne("Retenue à la source déjà prélevée", -ras),
                _ligne(libelle_solde, abs(solde), fort=True),
            ),
            class_="table table-sm",
        )
        return ui.card(ui.card_header("IRPP annuel"), table)


app = App(app_ui, server)
