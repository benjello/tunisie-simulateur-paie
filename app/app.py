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
    DEDUCTIONS_ANNUELLES,
    api_disponible,
    brut_depuis_net,
    calculer_bulletin,
    calculer_irpp_annuel,
    construire_situation,
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
            ui.input_numeric("taux_horaire", "Taux horaire normal (DT/h)", 0, min=0, step=0.5),
            ui.input_select(
                "majoration_hs",
                "Majoration heures supp.",
                {"1.25": "25 %", "1.50": "50 %", "1.75": "75 %"},
                selected="1.25",
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
            try:
                return ("ok", brut_depuis_net(
                    float(input.net_cible() or 0), annee=annee, regime=regime,
                    primes=float(input.primes_net() or 0),
                    adhesion_complementaire=adhesion, **fam,
                ))
            except httpx.HTTPError as erreur:
                return ("erreur", str(erreur))
        # Heures supplémentaires : non modélisées par OpenFisca côté bulletin.
        # On les valorise ici (taux horaire × majoration) et on les ajoute aux
        # primes, qui entrent dans l'assiette de cotisations et l'imposable.
        valeur_hs = (
            float(input.heures_sup() or 0)
            * float(input.taux_horaire() or 0)
            * float(input.majoration_hs())
        )
        situation = construire_situation(
            salaire_de_base=float(input.salaire_de_base() or 0),
            annee=annee,
            primes=float(input.primes() or 0) + valeur_hs,
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
                ui.card(ui.card_header("Côté salarié"), salarie),
                ui.card(ui.card_header("Côté employeur"), employeur),
                col_widths=(7, 5),
            ),
        )

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
