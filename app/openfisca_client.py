"""Client de calcul OpenFisca-Tunisia pour l'app de paie.

L'app Shiny ne contient aucune logique fiscale : elle construit une situation
(ménage d'un salarié) et demande le bulletin à OpenFisca-Tunisia. OpenFisca
reste le seul moteur de calcul.

Deux modes, selon la variable d'environnement OPENFISCA_MODE :
- "api" (défaut) : poste la situation à l'API web (openfisca serve). Pratique en
  développement local (API séparée sur OPENFISCA_API_URL).
- "local" : calcule en direct, dans le même process, via
  CountryTaxBenefitSystem. Utilisé en déploiement (HF Spaces) où un seul
  service tourne : pas d'API HTTP séparée.

Les deux modes consomment le MÊME format de situation JSON ; SimulationBuilder
sait le lire directement.

En local (mode api), lancer l'API avec :
    openfisca serve -c openfisca_tunisia -p 5000
"""

from __future__ import annotations

import os

import httpx

# URL de l'API OpenFisca (mode "api"). Surchargée par OPENFISCA_API_URL.
API_URL = os.environ.get("OPENFISCA_API_URL", "http://localhost:5000")

# Mode de calcul : "api" (HTTP) ou "local" (moteur in-process).
MODE = os.environ.get("OPENFISCA_MODE", "api").lower()

# TaxBenefitSystem chargé paresseusement en mode local (coûteux à l'import).
_TBS = None


def _get_tbs():
    global _TBS
    if _TBS is None:
        from openfisca_tunisia import CountryTaxBenefitSystem

        _TBS = CountryTaxBenefitSystem()
    return _TBS


def _calculate_local(situation: dict) -> dict:
    """Calcule en direct via SimulationBuilder et renvoie le résultat au format API.

    Toutes les variables à `None` dans la situation sont calculées et remplies,
    pour chaque période demandée ; on imite la structure de réponse de l'API.
    """
    from openfisca_core.simulations import SimulationBuilder

    tbs = _get_tbs()
    builder = SimulationBuilder()
    simulation = builder.build_from_entities(tbs, situation)

    resultat = {k: {} for k in situation}
    for collection, entites in situation.items():
        for ident, variables in entites.items():
            resultat[collection][ident] = {}
            for variable, periodes in variables.items():
                if not isinstance(periodes, dict):
                    # champ non temporel (ex. liste de rôles) : recopié tel quel
                    resultat[collection][ident][variable] = periodes
                    continue
                resultat[collection][ident][variable] = {}
                for periode, valeur in periodes.items():
                    if valeur is None:
                        calcule = simulation.calculate(variable, periode)
                        valeur = float(calcule[0])
                    resultat[collection][ident][variable][periode] = valeur
    return resultat


def _calculate(situation: dict, *, timeout: float = 30.0) -> dict:
    """Route le calcul vers l'API HTTP ou le moteur local selon OPENFISCA_MODE."""
    if MODE == "local":
        return _calculate_local(situation)
    reponse = httpx.post(f"{API_URL}/calculate", json=situation, timeout=timeout)
    reponse.raise_for_status()
    return reponse.json()

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
    data = _calculate(situation, timeout=timeout)

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
    primes: float = 0.0,
    adhesion_complementaire: bool = False,
    chef_de_famille: bool = False,
    nb_enf: int = 0,
    nb_enf_sup: int = 0,
    nb_infirme: int = 0,
    tolerance: float = 0.01,
    max_iter: int = 60,
) -> dict:
    """Inverse net -> salaire de base par dichotomie sur l'API brut -> net.

    Les `primes` sont une donnée CONNUE, maintenue fixe : l'inconnue cherchée est
    le salaire de base tel que net(salaire_de_base + primes) = net_cible. Le net
    croît avec le salaire de base, donc la dichotomie converge toujours. Renvoie
    le bulletin complet (le `salaire_brut` renvoyé inclut les primes).
    """
    cache: dict[float, dict] = {}

    def net_pour(salaire_base: float) -> dict:
        # Clé au millime : la dichotomie réévalue parfois des bornes identiques.
        cle = round(salaire_base, 3)
        if cle in cache:
            return cache[cle]
        situation = construire_situation(
            salaire_de_base=salaire_base, annee=annee, regime=regime, primes=primes,
            adhesion_complementaire=adhesion_complementaire,
            chef_de_famille=chef_de_famille, nb_enf=nb_enf,
            nb_enf_sup=nb_enf_sup, nb_infirme=nb_infirme,
        )
        resultat = calculer_bulletin(situation, annee=annee)
        cache[cle] = resultat
        return resultat

    # Si les primes seules produisent déjà un net >= cible, le salaire de base est 0.
    bulletin_bas = net_pour(0.0)
    if net_cible <= 0 or (bulletin_bas["salaire_net_a_payer"] or 0.0) >= net_cible:
        return bulletin_bas

    # Borne haute : on part du net cible et on augmente jusqu'à dépasser.
    bas, haut = 0.0, max(net_cible, 1.0) * 2.0
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

    data = _calculate(situation, timeout=timeout)
    foyer_res = data["foyers_fiscaux"]["f0"]
    irpp = foyer_res.get("irpp", {}).get(an)
    irpp_net = foyer_res.get("irpp_net_a_payer", {}).get(an)
    # RAS annuelle estimée = irpp - irpp_net (ce qui a déjà été prélevé à la source).
    ras = None if (irpp is None or irpp_net is None) else irpp - irpp_net
    return {"irpp": irpp, "irpp_net_a_payer": irpp_net, "ras_annuelle": ras}


def api_disponible(timeout: float = 3.0) -> bool:
    """Indique si le moteur est prêt (pour un message clair dans l'UI).

    En mode local, le moteur est toujours disponible (calcul in-process). En
    mode api, on teste la joignabilité de l'API.
    """
    if MODE == "local":
        return True
    try:
        reponse = httpx.get(f"{API_URL}/spec", timeout=timeout)
        return reponse.status_code == 200
    except httpx.HTTPError:
        return False
