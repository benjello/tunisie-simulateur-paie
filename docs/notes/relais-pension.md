# Relais de passation — chantier PENSION

Ce fichier transmet le chantier **pension de retraite** à sa session dédiée.
Il a été produit dans la session « fiche de paie », qui se concentre désormais
sur la paie. À lire en premier dans la session pension, puis à recopier dans le
futur dépôt `tunisie-simulateur-pension` (p. ex. `docs/notes/backlog.md`).

## Objectif

Reproduire pour la **pension** le cheminement de la paie :
1. Créer le repo public `benjello/tunisie-simulateur-pension`.
2. Recenser les simulateurs de pension tunisiens (comparaison).
3. Tests YAML validés par openfisca (anonymisés, mapping local gitignoré).
4. App Shiny via l'API openfisca.

## Méthode (identique à la paie)

- **La loi fait référence** ; les simulateurs sont des indices. Désaccords
  documentés et tranchés par le texte (loi 85-12 CNRPS, loi 60-30 / décret
  74-499 CNSS, LF récentes).
- **Confidentialité des sources** : noms des simulateurs hors du dépôt public →
  `sources_locales/` gitignoré, tests à identifiants neutres.
- **Architecture** : l'app ne calcule rien, elle appelle l'API web openfisca.
  GitHub Pages/wasm écarté (pendulum/numexpr/psutil absents de Pyodide).
- **Modèle à copier** : le dépôt `~/projets/tunisie-simulateur-paie/`
  (structure, `.gitignore`, `AGENTS.md` + agents `.pi/.claude/.opencode`,
  `app/openfisca_client.py`, `app/app.py`, `pyproject.toml` uv, format tests).
- **Agents portables réutilisables** : `analyste-openfisca` (Haiku, lecture
  seule), `juriste-fiscal-tn` (Sonnet, web) — à copier.

## MODÈLE openfisca pension (agent `pension-model`, vérifié par calcul)

- Package **séparé** `openfisca_tunisia_pension/` avec son propre
  `TunisiaPensionTaxBenefitSystem` (devise « DT »). **Exige `numba`** :
  `pip install 'openfisca-tunisia[pension]'`.
- Les classes `regimes/*.py` sont transformées en variables préfixées
  (`rsna_*`, `cnrps_*`, `rsa_*`) par AST au chargement
  (`scripts_ast/script_ast.py`). Paramètres lus dans l'arbre commun
  `openfisca_tunisia/parameters/retraite/` (+ `marche_travail`).
- **Chaîne de calcul** (`regimes/regime.py`, `AbstractRegimeEnAnnuites`) :
  - Entrées : `*_salaire_de_base` (MONTH), `*_duree_assurance` (trimestres),
    `age`, `*_liquidation_date`, `regime_securite_sociale`.
  - `*_salaire_de_reference` → `*_taux_de_liquidation` (= `bareme_annuite.calc`)
    → `*_pension_brute` = taux × salaire réf →
    `*_pension = eligible × min(pension_maximale, max(pension_brute, pension_minimale))`
    → `*_pension_servie` (revalorisée depuis la liquidation).
- **Régimes réellement modélisés** : **RSNA** (privé), **CNRPS** (public),
  **RSA** (agricole). Enum `TypesRegimeSecuriteSociale` dans
  `variables/data.py`. Autres (rsaa, rtns, rtte, raci, re, rtfr, pensionne_cnrps)
  = paramètres présents mais **PAS de classe régime** → lacune.
- **API** : `openfisca serve --country-package openfisca_tunisia_pension`
  (country-package distinct d'`openfisca_tunisia`).

### Cas chiffrés openfisca (oracles de test)

- `tests_pension/formulas/rsna/pension.yaml` : 12000 DT/an, 50 trimestres,
  2011 → taux 45 %, `rsna_pension` = **6416,94 DT** (vérifié : sal_ref 14259,86).
- `tests_pension/formulas/cnrps/taux_de_liquidation.yaml` : 20 trim → 0,10 ;
  40 trim → 0,20 ; 84 trim → 0,52.
- `tests_pension/formulas/cnrps/pension.yaml` : 3 ans → 0 (inéligible) ;
  7 ans → 0,5 × 235,04 × 12 ; 17 ans → 0,66666 × 235,04 × 12.

### Reports/lacunes modèle (à mettre au backlog pension)

- Régimes rsaa, rtns, rtte, re, rtfr, raci, pensionne_cnrps non modélisés.
- `pension_brute` de `regime.py` renvoie un tuple `(taux × salaire,)` — vérifier
  (surchargé dans les régimes concrets ?).
- `salaire_de_reference` RSNA 1990-09-23→1994-06-30 : `NotImplementedError`
  volontaire (texte non tranché).
- `duree_assurance` de base : pas de formule active (entrée directe).
- Cohérence `pyproject` numba (0.64–0.66 vs 0.67) à vérifier.

## SIMULATEURS pension en ligne (agent `pension-web`)

Simulateurs : **secu.tn** (CNSS / CNRPS / complémentaire CAVIS — le plus
détaillé), **22.tn** (CNSS+CNRPS, cas chiffrés), **retraite.tn** et
**ihsibly.com** (React, non extractibles en statique). CNSS/CNRPS officiels :
pas de simulateur de pension public. Noms à garder dans `sources_locales/`.

### Méthode (à confronter à la loi)

- **Privé CNSS/RSNA** : salaire de référence = moyenne des **10 dernières
  années actualisées**, plafonnée à 6×SMIG. Taux = 40 % (10 premières années)
  puis +2 %/an (0,5 %/trimestre), **plafond 80 %**. Min 10 ans. Âge 60
  (55 pénibles). Minoration départ anticipé −0,5 %/trimestre. Mini 2/3 SMIG.
- **Public CNRPS** : salaire réf = **dernier salaire** (≥3 ans), sans plafond.
  Taux 2 %/an (10 premières), 3 %/an (10 suivantes), 2 %/an au-delà, **plafond
  90 %**. Min 15 ans. Âge 62.

### Cas chiffrés de référence (anonymiser la source dans le dépôt)

- CNSS 25 ans, moyenne 1305 D → 70 % → brut 913,5 D.
- CNSS 25 ans, moyenne 4480 D plafonnée 2760 D → 70 % → brut 1932 D.
- CNSS dernier salaire 2000 D, 25 ans → 70 % → brut 1400 D.
- CNRPS dernier salaire 2000 D, 30 ans → 70 % → brut 1400 D.
- Taux : CNSS 19 ans = 58 %, 41,25 ans = 80 % ; CNRPS 19 ans = 47 %,
  41,25 ans = 90 %.

### Désaccords à trancher (loi)

1. Salaire de référence CNSS : « 10 dernières années » (secu.tn/22.tn) vs
   « meilleures années » (retraite.tn) — trancher par décret 74-499.
2. retraite.tn omet le palier 40 %/10 ans CNSS — simplification probablement
   fausse.
3. CNRPS : « dernier salaire » vs clause des 3 ans — préciser.
4. Réformes récentes (SMIG 2025, régime exceptionnel CNRPS 57 ans 2022-2028).

### Lacunes recherche

- Coefficients d'actualisation CNSS et barème exact non collectés (page secu.tn
  dédiée à exploiter, ou via navigateur pour les simulateurs React).
