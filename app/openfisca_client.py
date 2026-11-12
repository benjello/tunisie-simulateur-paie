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
    adhesion_complementaire: bool = False,
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
        "adhesion_cnss_regime_complementaire": {mois: adhesion_complementaire},
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


def brut_depuis_net(
    net_cible: float,
    *,
    annee: int,
    regime: str = "rsna",
    adhesion_complementaire: bool = False,
    chef_de_famille: bool = False,
    nb_enf: int = 0,
    nb_enf_sup: int = 0,
    nb_infirme: int = 0,
    tolerance: float = 0.01,
    max_iter: int = 60,
) -> dict:
    """Inverse net -> brut par dichotomie sur l'API brut -> net.

    Le net est strictement croissant avec le brut, donc la dichotomie converge
    toujours. On ne dépend ni de scipy ni d'une réforme côté serveur : on appelle
    l'API brut -> net standard. Renvoie le bulletin complet (comme calculer_bulletin)
    avec le brut trouvé.
    """
    if net_cible <= 0:
        situation = construire_situation(
            salaire_de_base=0.0, annee=annee, regime=regime,
            adhesion_complementaire=adhesion_complementaire,
            chef_de_famille=chef_de_famille, nb_enf=nb_enf,
            nb_enf_sup=nb_enf_sup, nb_infirme=nb_infirme,
        )
        return calculer_bulletin(situation, annee=annee)

    def net_pour(brut: float) -> dict:
        situation = construire_situation(
            salaire_de_base=brut, annee=annee, regime=regime,
            adhesion_complementaire=adhesion_complementaire,
            chef_de_famille=chef_de_famille, nb_enf=nb_enf,
            nb_enf_sup=nb_enf_sup, nb_infirme=nb_infirme,
        )
        return calculer_bulletin(situation, annee=annee)

    # Borne haute : le brut est forcément > net. On double jusqu'à dépasser la cible.
    bas, haut = net_cible, net_cible * 2.0
    bulletin_haut = net_pour(haut)
    gardes = 0
    while (bulletin_haut["salaire_net_a_payer"] or 0.0) < net_cible and gardes < 40:
        haut *= 1.5
        bulletin_haut = net_pour(haut)
        gardes += 1

    dernier = bulletin_haut
    for _ in range(max_iter):
        milieu = (bas + haut) / 2.0
        dernier = net_pour(milieu)
        net_milieu = dernier["salaire_net_a_payer"] or 0.0
        if abs(net_milieu - net_cible) <= tolerance:
            break
        if net_milieu < net_cible:
            bas = milieu
        else:
            haut = milieu
    return dernier


# Déductions IRPP annuelles (variable openfisca -> libellé). Elles n'entrent que
# dans l'IRPP annuel, pas dans la retenue à la source mensuelle.
DEDUCTIONS_ANNUELLES = {
    "prime_assurance_vie": "Primes d'assurance-vie",
    "interets_acquisition_logement": "Intérêts crédit logement (habitation principale)",
    "compte_epargne_en_actions": "Compte épargne en actions (CEA)",
    "compte_epargne_investissement": "Compte épargne investissement (CEI)",
    "pret_universitaire": "Remboursement prêts universitaires",
    "dons": "Dons",
}


def calculer_irpp_annuel(
    *,
    salaire_annuel: float,
    annee: int,
    regime: str = "rsna",
    chef_de_famille: bool = False,
    nb_enf: int = 0,
    nb_enf_sup: int = 0,
    nb_infirme: int = 0,
    deductions: dict | None = None,
    timeout: float = 30.0,
) -> dict:
    """Calcule l'IRPP annuel (variable `irpp`) et le solde de régularisation.

    Les déductions (assurance-vie, logement, CEA/CEI, dons, prêts) sont des
    variables annuelles qui n'affectent que l'IRPP annuel, pas la retenue à la
    source. Renvoie irpp, irpp_net_a_payer (solde après RAS), ras_annuelle.
    """
    an = str(annee)
    deductions = deductions or {}

    regimes_mensuels = {f"{annee}-{m:02d}": regime for m in range(1, 13)}
    individu: dict = {
        "salaire_de_base": {an: salaire_annuel},
        "regime_securite_sociale_cotisant": regimes_mensuels,
    }
    for variable, montant in deductions.items():
        individu[variable] = {an: montant}

    foyer: dict = {
        "declarants": ["ind0"],
        "chef_de_famille": {an: chef_de_famille},
        "nb_enf": {an: nb_enf},
        "nb_enf_sup": {an: nb_enf_sup},
        "nb_infirme": {an: nb_infirme},
        "irpp": {an: None},
        "irpp_net_a_payer": {an: None},
    }

    situation = {
        "individus": {"ind0": individu},
        "menages": {"m0": {"personne_de_reference": ["ind0"]}},
        "foyers_fiscaux": {"f0": foyer},
    }

    reponse = httpx.post(f"{API_URL}/calculate", json=situation, timeout=timeout)
    reponse.raise_for_status()
    foyer_res = reponse.json()["foyers_fiscaux"]["f0"]
    irpp = foyer_res.get("irpp", {}).get(an)
    irpp_net = foyer_res.get("irpp_net_a_payer", {}).get(an)
    # RAS annuelle estimée = irpp - irpp_net (ce qui a déjà été prélevé à la source).
    ras = None if (irpp is None or irpp_net is None) else irpp - irpp_net
    return {"irpp": irpp, "irpp_net_a_payer": irpp_net, "ras_annuelle": ras}


def api_disponible(timeout: float = 3.0) -> bool:
    """Teste si l'API OpenFisca répond (pour un message clair dans l'UI)."""
    try:
        reponse = httpx.get(f"{API_URL}/spec", timeout=timeout)
        return reponse.status_code == 200
    except httpx.HTTPError:
        return False
