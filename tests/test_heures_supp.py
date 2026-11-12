"""Test de la valorisation des heures supplémentaires (art. 90 code du travail).

Pur calcul côté app, sans dépendance à OpenFisca ni à l'API.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from openfisca_client import valoriser_heures_supp  # noqa: E402


def test_regime_40h_exemple_reference():
    # 1500 DT/mois, 10 h supp, régime 40h : 8h à +25%, 2h à +50%.
    # taux horaire = 1500 / 173,333 = 8,654 ; 8×8,654×1,25 + 2×8,654×1,50 = 112,50.
    assert valoriser_heures_supp(1500, 10, "40h") == 112.5


def test_regime_48h():
    # 1500 DT/mois, 10 h supp, régime 48h : +75%. 1500/208 = 7,2115 ; ×10×1,75.
    assert abs(valoriser_heures_supp(1500, 10, "48h") - 126.202) < 0.01


def test_zero_heure():
    assert valoriser_heures_supp(1500, 0, "40h") == 0.0
    assert valoriser_heures_supp(0, 10, "48h") == 0.0


def test_40h_sous_8_heures_tout_a_25pct():
    # 5 h supp (< 8) : tout à +25%.
    taux = 1500 / (40 * 52 / 12)
    assert abs(valoriser_heures_supp(1500, 5, "40h") - 5 * taux * 1.25) < 0.01
