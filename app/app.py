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
    api_disponible,
    calculer_bulletin,
    construire_situation,
)

ANNEES = [str(a) for a in range(2020, 2027)]

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("annee", "Année de paie", ANNEES, selected="2025"),
        ui.input_numeric("salaire_de_base", "Salaire de base (DT/mois)", 1500, min=0, step=50),
        ui.input_numeric("primes", "Primes et indemnités (DT/mois)", 0, min=0, step=50),
        ui.hr(),
        ui.h6("Situation familiale (IRPP)"),
        ui.input_checkbox("chef_de_famille", "Chef de famille", False),
        ui.input_numeric("nb_enf", "Enfants à charge (≤ 4)", 0, min=0, max=10, step=1),
        ui.input_numeric("nb_enf_sup", "Étudiants sans bourse", 0, min=0, max=10, step=1),
        ui.input_numeric("nb_infirme", "Enfants handicapés", 0, min=0, max=10, step=1),
        ui.hr(),
        ui.input_action_button("calculer", "Calculer le bulletin", class_="btn-primary"),
        width=320,
    ),
    ui.h3("Fiche de paie — salarié du privé (CNSS, régime RSNA)"),
    ui.output_ui("statut_api"),
    ui.output_ui("bulletin"),
    ui.markdown(
        "Calculé par le moteur **OpenFisca-Tunisia** (via son API). "
        "Convention : cotisations au taux du mois de paie, barème IRPP des "
        "revenus de l'année de paie (retenue à la source)."
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
        situation = construire_situation(
            salaire_de_base=float(input.salaire_de_base() or 0),
            annee=annee,
            primes=float(input.primes() or 0),
            regime="rsna",
            chef_de_famille=bool(input.chef_de_famille()),
            nb_enf=int(input.nb_enf() or 0),
            nb_enf_sup=int(input.nb_enf_sup() or 0),
            nb_infirme=int(input.nb_infirme() or 0),
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

        return ui.layout_columns(
            ui.card(ui.card_header("Côté salarié"), salarie),
            ui.card(ui.card_header("Côté employeur"), employeur),
            col_widths=(7, 5),
        )


app = App(app_ui, server)
