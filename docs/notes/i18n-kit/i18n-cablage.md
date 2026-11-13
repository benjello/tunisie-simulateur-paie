# Câblage i18n FR/AR dans une app Shiny (pattern éprouvé sur paie)

Transmis par la session paie. Permet d'ajouter l'arabe + RTL à pension et
amen-social (aujourd'hui 100 % FR). Le module `app/i18n.py` (voir `i18n_base.py`)
porte les traductions ; voici comment le brancher dans `app.py`.

## 1. Module de traductions

Copier `i18n_base.py` en `app/i18n.py`, puis remplir `TRADUCTIONS` avec les
libellés de ton simulateur (une clé par libellé, valeurs `fr`/`ar`).

## 2. Import dans app.py

```python
from i18n import LANGUES, t
```

## 3. Sélecteur de langue (en tête du panneau latéral)

```python
ui.input_select("lang", "Langue / اللغة", LANGUES, selected="fr"),
```

## 4. Effet : RTL + mise à jour des labels (dans le server)

```python
@reactive.effect
def _appliquer_langue():
    lang = str(input.lang())
    direction = "rtl" if lang == "ar" else "ltr"
    ui.insert_ui(
        ui.tags.script(
            f"document.documentElement.setAttribute('dir','{direction}');"
            f"document.documentElement.setAttribute('lang','{lang}');"
        ),
        selector="body", where="beforeEnd", immediate=True,
    )
    # Mettre à jour le label de CHAQUE input statique :
    ui.update_select("mon_champ", label=t("ma_cle", lang))
    ui.update_numeric("autre_champ", label=t("autre_cle", lang))
    # Pour un select dont les CHOIX doivent aussi être traduits :
    ui.update_select("regime", label=t("regime", lang),
                     choices={k: t(cle_par_code[k], lang) for k in CODES},
                     selected=str(input.regime()))
    # ... checkbox: ui.update_checkbox / radio: ui.update_radio_buttons / bouton: ui.update_action_button
```

## 5. Sorties traduites

Dans chaque `@render.ui`, lire la langue et utiliser `t()` :

```python
@render.ui
def mon_tableau():
    lang = str(input.lang())
    return _ligne(t("salaire_brut", lang), montant)  # etc.
```

Les **titres de section** et **notes** statiques doivent devenir des
`ui.output_ui(...)` rendus dynamiquement (sinon ils restent figés dans la langue
de définition).

## 6. Limites connues (documentées sur paie)

- **Libellés d'onglets** (`nav_panel("...")`) : Shiny ne permet pas de les
  renommer après création → ils restent dans la langue de définition. Donne-leur
  des libellés courts/neutres, ou des `value=` pour piloter au moins le contenu.
- **Export PDF arabe** : matplotlib ne rend pas le RTL sans `arabic-reshaper`
  + `python-bidi`. Produire le PDF en FR, ou ajouter ces libs.

## 7. Référence

L'implémentation complète et fonctionnelle est dans
`tunisie-simulateur-paie/app/{i18n.py,app.py}` (88 clés AR, RTL, sélecteur,
sorties + titres + notes traduits). S'en inspirer directement.
