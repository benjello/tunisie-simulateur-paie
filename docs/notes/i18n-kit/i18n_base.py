"""Socle i18n réutilisable (FR/AR) — à adapter par chaque simulateur.

Copie ce fichier en `app/i18n.py` et REMPLACE le dictionnaire TRADUCTIONS par
les libellés propres à ton simulateur (pension, amen-social…). La mécanique
`t(cle, lang)`, le sélecteur de langue et le RTL sont génériques.

Voir i18n-cablage.md pour le câblage dans app.py (sélecteur + RTL + update_*).
"""

from __future__ import annotations

LANGUES = {"fr": "Français", "ar": "العربية"}

# ⚠️ À REMPLACER par les libellés de TON simulateur. Exemples génériques :
TRADUCTIONS: dict[str, dict[str, str]] = {
    "langue": {"fr": "Langue", "ar": "اللغة"},
    # ... ajoute ici toutes tes clés : titres, champs, sorties, messages ...
    # Astuce : garde les mêmes clés que les libellés en dur de ton app.py
    # actuel, puis remplace chaque chaîne par t("cle", lang).
}


def t(cle: str, lang: str = "fr") -> str:
    """Renvoie la traduction de `cle` pour `lang` (repli fr, puis la clé)."""
    entree = TRADUCTIONS.get(cle)
    if entree is None:
        return cle
    return entree.get(lang) or entree.get("fr") or cle
