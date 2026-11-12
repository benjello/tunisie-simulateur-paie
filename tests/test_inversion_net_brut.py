"""Test de l'inversion net -> brut (côté client, via l'API OpenFisca).

Vérifie l'aller-retour : partant d'un brut, on calcule le net (API brut->net),
puis on redemande le brut depuis ce net (dichotomie) et on doit retrouver le
brut de départ à ~1 millime près.

Nécessite l'API OpenFisca lancée (openfisca serve -c openfisca_tunisia -p 5000).
Le test est ignoré si l'API n'est pas joignable.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from openfisca_client import (  # noqa: E402
    api_disponible,
    brut_depuis_net,
    calculer_bulletin,
    construire_situation,
)

pytestmark = pytest.mark.skipif(
    not api_disponible(), reason="API OpenFisca injoignable (lancer openfisca serve)"
)

CAS = [
    (2025, 1500, "rsna"),
    (2025, 3000, "rsna"),
    (2025, 5000, "rsna"),
    (2024, 1000, "rsna"),
    (2025, 2000, "rsa"),
    (2025, 2000, "rsaa"),
    (2025, 2000, "salarie_cnrps"),
]


@pytest.mark.parametrize("annee,brut,regime", CAS)
def test_aller_retour_brut_net_brut(annee, brut, regime):
    bulletin = calculer_bulletin(
        construire_situation(salaire_de_base=brut, annee=annee, regime=regime),
        annee=annee,
    )
    net = bulletin["salaire_net_a_payer"]

    inverse = brut_depuis_net(net, annee=annee, regime=regime)
    brut_trouve = inverse["salaire_brut"]

    # Tolérance : 0,05 DT (la dichotomie converge au millime sur le net).
    assert abs(brut_trouve - brut) < 0.05, (
        f"{annee} {regime} brut={brut} net={net:.3f} -> brut_inv={brut_trouve:.3f}"
    )


# Inversion avec primes CONNUES fixes : l'inconnue est le salaire de base.
CAS_PRIMES = [
    (2025, 1200, 300, "rsna"),
    (2025, 2000, 0, "rsna"),
    (2025, 800, 700, "rsna"),
    (2025, 1500, 1500, "rsna"),
]


@pytest.mark.parametrize("annee,base,prime,regime", CAS_PRIMES)
def test_inversion_avec_primes(annee, base, prime, regime):
    bulletin = calculer_bulletin(
        construire_situation(
            salaire_de_base=base, annee=annee, regime=regime, primes=prime
        ),
        annee=annee,
    )
    net = bulletin["salaire_net_a_payer"]

    inverse = brut_depuis_net(net, annee=annee, regime=regime, primes=prime)
    # salaire_brut inclut les primes ; on isole le salaire de base retrouvé.
    base_trouve = inverse["salaire_brut"] - prime

    assert abs(base_trouve - base) < 0.05, (
        f"{annee} {regime} base={base} prime={prime} net={net:.3f} "
        f"-> base_inv={base_trouve:.3f}"
    )
