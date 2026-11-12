"""Client de l'API web OpenFisca-Tunisia.

L'app Shiny ne calcule rien elle-même : elle construit une situation (ménage
d'un salarié), la poste à l'API OpenFisca-Tunisia, et lit le bulletin dans la
réponse. OpenFisca reste le seul moteur de calcul.

En local, lancer l'API avec :
    openfisca serve -c openfisca_tunisia -p 5000
"""

from __future__ import annotations

import os

import httpx

# URL de l'API OpenFisca. Surchargée par la variable d'environnement
# OPENFISCA_API_URL (utile pour pointer, plus tard, vers une API hébergée).
API_URL = os.environ.get("OPENFISCA_API_URL", "http://localhost:5000")

# Variables du bulletin de paie demandées au moteur (côté salarié + employeur).
VARIABLES_PAIE = [
    "cotisations_salarie",
    "salaire_imposable",
    "irpp_salarie_preleve_a_la_source",
    "contribution_sociale_solidarite_prelevee_a_la_source",
    "salaire_net_a_payer",
    "cotisations_employeur",
    "salaire_super_brut",
]


def construire_situation(
    *,
    salaire_de_base: float,
    annee: int,
    primes: float = 0.0,
    regime: str = "rsna",
    chef_de_famille: bool = False,
    nb_enf: int = 0,
    nb_enf_sup: int = 0,
    nb_infirme: int = 0,
) -> dict:
    """Construit la situation JSON OpenFisca pour un salarié sur janvier de `annee`.

    Les cotisations et le salaire sont mensuels (janvier) ; les charges de
    famille sont annuelles.
    """
    mois = f"{annee}-01"
    an = str(annee)

    individu: dict = {
        "salaire_de_base": {mois: salaire_de_base},
        "primes": {mois: primes},
        "regime_securite_sociale_cotisant": {mois: regime},
    }
    for variable in VARIABLES_PAIE:
        individu[variable] = {mois: None}

    foyer: dict = {
        "declarants": ["ind0"],
        "chef_de_famille": {an: chef_de_famille},
        "nb_enf": {an: nb_enf},
        "nb_enf_sup": {an: nb_enf_sup},
        "nb_infirme": {an: nb_infirme},
    }

    return {
        "individus": {"ind0": individu},
        "menages": {"m0": {"personne_de_reference": ["ind0"]}},
        "foyers_fiscaux": {"f0": foyer},
    }


def calculer_bulletin(situation: dict, *, annee: int, timeout: float = 30.0) -> dict:
    """Poste la situation à l'API et renvoie le bulletin mensuel (dict plat).

    Lève httpx.HTTPError si l'API ne répond pas ou renvoie une erreur.
    """
    mois = f"{annee}-01"
    reponse = httpx.post(
        f"{API_URL}/calculate",
        json=situation,
        timeout=timeout,
    )
    reponse.raise_for_status()
    data = reponse.json()

    individu = data["individus"]["ind0"]
    bulletin = {}
    for variable in VARIABLES_PAIE:
        bulletin[variable] = individu.get(variable, {}).get(mois)
    # Brut utile à l'affichage.
    brut = individu.get("salaire_de_base", {}).get(mois, 0.0) or 0.0
    brut += individu.get("primes", {}).get(mois, 0.0) or 0.0
    bulletin["salaire_brut"] = brut
    return bulletin


def api_disponible(timeout: float = 3.0) -> bool:
    """Teste si l'API OpenFisca répond (pour un message clair dans l'UI)."""
    try:
        reponse = httpx.get(f"{API_URL}/spec", timeout=timeout)
        return reponse.status_code == 200
    except httpx.HTTPError:
        return False
