# Backlog durable

Reports et pistes à suivre, versés ici pour ne pas vivre uniquement dans une
conversation.

## Améliorations identifiées (à implémenter une à une)

Hiérarchisées par ratio valeur/effort. Cochées au fur et à mesure.

### Fiabilité / confiance
- [x] **A1 — Validation croisée réelle** : barème IRPP et CSS alignés au centime
  avec les simulateurs ; seul écart = CNSS déjà tranché. Mapping étendu dans
  `sources_locales/`.
- [x] **A2 — Validation des entrées** (garde-fous + messages).
- [x] **A3 — Détail CNSS par branche** (repli dans le bulletin).

### Expérience utilisateur
- [x] **A4 — Export du bulletin** PDF (via matplotlib).
- [x] **A5 — Taux effectif + graphique** net = f(brut).
- [x] **A6 — Comparateur** multi-années / multi-régimes (onglet dédié).
- [x] **A7 — Bilingue FR/AR** : module `app/i18n.py`, sélecteur de langue,
  direction **RTL** pour l'arabe, labels du panneau latéral, **toutes les
  sorties** ET **titres de section + notes des 3 onglets** traduits.
  *Limites résiduelles* : (1) les **libellés d'onglets** (barre de navigation)
  restent dans la langue de définition — Shiny ne permet pas de les renommer
  après création ; (2) le **PDF** est produit en français quelle que soit la
  langue (matplotlib ne rend pas l'arabe RTL sans `arabic-reshaper` +
  `python-bidi`). À traiter si besoin dans une itération dédiée.

### Couverture fonctionnelle
- [x] **A8 — Onglet annuel enrichi** (effet des déductions sur l'IRPP).
- [x] **A9 — CIVP/stage et export** : approximation « néant » signalée en UI.
- [x] **A10 — Heures suppl. fines** (régimes 40h/48h, art. 90).

### Robustesse technique
- [x] **A11 — CI GitHub Actions** (openfisca test + pytest + check agents).
- [x] **A12 — Cache** dans la dichotomie net→brut.
- [x] **A13 — Gestion d'erreur** fine (timeout/connexion).
- [x] **A14 — Déploiement** : HF Spaces écarté (Docker devenu payant, seul
  « Static » gratuit). **Déployé sur shinyapps.io** (compte benjello, plan
  gratuit, mode moteur-en-direct). Voir `deploy/shinyapps/`. **App en ligne.**
  Limite : 25 h actives/mois sur le plan gratuit.

## État du chantier (ce dépôt = FICHE DE PAIE)

**Fait** : repo public, modèle openfisca validé (10 tests YAML paie, suite
complète openfisca 8137 OK), désaccords tranchés (CNSS 9,68 % LF2025, perte
d'emploi déductible, millésime RAS, CSS 2026 prolongée), app Shiny via API
openfisca avec sélecteur de régime (rsna/rsa/rsaa/cnrps/exonéré), agents
portables (AGENTS.md + .pi/.claude/.opencode). App en local : :8100 (app) / :5000
(API).

**Fait (suite)** : net→brut dans l'app (inversion dichotomique côté client, sans
scipy) ; tests régimes 2025 (RSA/RSAA/CNRPS) + test pytest d'inversion (20 tests
au total) ; options avancées (retraite complémentaire RSNA, heures suppl.
valorisées côté app) ; préparation déploiement (`deploy/` : Dockerfile.api +
procédure + piste MCP).

**Décisions prises pendant le développement** :
- **Heures supplémentaires** : non modélisées par openfisca côté bulletin (taux
  de droit du travail présents en paramètres mais aucune variable ne les
  consomme). Valorisées dans l'app (nb × taux × majoration) et ajoutées aux
  `primes`.
- **Déductions IRPP** (assurance-vie, crédit logement, CEA/CEI, dons, prêts
  universitaires) : elles **n'affectent PAS la retenue à la source mensuelle**
  (seulement l'IRPP annuel `irpp`). Les exposer dans le bulletin mensuel serait
  trompeur → réservées à un futur **onglet « simulation annuelle »** (backlog).

**À faire (todos actives)** :
- **#16 Hébergement API** : préparé (`deploy/`), mais le déploiement effectif
  (HF Spaces / VPS) requiert des identifiants — action À FAIRE côté utilisateur.
- **Onglet simulation annuelle IRPP** (pour exposer les déductions ci-dessus).
- **Piste MCP** (après hébergement API).

**Chantier pension** : délégué à une session dédiée. Tout le contexte capturé
(modèle `openfisca_tunisia_pension`, simulateurs, cas chiffrés, désaccords) est
dans `docs/notes/relais-pension.md` — à recopier dans le futur dépôt
`tunisie-simulateur-pension`.

## Architecture / déploiement

- **API OpenFisca en local uniquement** pour l'instant. L'app Shiny appelle
  `http://localhost:5000`. À héberger pour un déploiement réel.
- **GitHub Pages / WebAssembly écarté** : OpenFisca-core importe au chargement
  des extensions compilées absentes de Pyodide — `pendulum` (Rust, structurant
  dans `periods/`), `numexpr` (C, un usage dans `apply_thresholds`), `psutil`
  (C, un usage mémoire dans `holders/holder.py`). Un déploiement 100 % navigateur
  exigerait des shims pour ces trois modules → fragile. Décision : mode
  client/serveur.
- **Piste MCP** : à terme, exposer OpenFisca-Tunisia via un serveur **MCP**
  (outils `calculer_paie`, `brut_vers_net`, …), consommable à la fois par l'app
  et par des agents. Le passage actuel par la web-api est une étape naturelle
  vers ça (même encapsulation du moteur).
- Options d'hébergement de l'API à trancher : Hugging Face Spaces, VPS,
  Shinyapps.io (pour une version serveur de l'app), etc.

## Fonctionnalités paie (élargissement)

- **Sens net → brut** (inversion), proposé par la plupart des simulateurs.
- **Autres régimes CNSS** : RSAA (agricole amélioré), CIVP/stage, entreprise
  totalement exportatrice, CNRPS (public). Le modèle OpenFisca les porte déjà ;
  à exposer dans l'UI et à tester.
- **Heures supplémentaires** : régimes 40 h et 48 h/semaine (majorations
  25 / 50 / 75 %). Vérifier la couverture dans OpenFisca.
- **Autres déductions IRPP** : intérêts crédit logement, assurance-vie,
  épargne (CEA/CEI), prêts universitaires, dons — déjà modélisées dans
  OpenFisca, à exposer.
- **Export** du bulletin (PDF / PNG), comme les générateurs en ligne.

## Tests

- Étendre les cas YAML : net → brut, autres régimes, primes, heures supp.
- Caler chaque cas emprunté à un simulateur sur l'année où sa règle est valide
  (voir `sources_locales/`, local).
- **CSS 2026** : tracer sa suppression annoncée (LF2026) et vérifier le barème
  IRPP 2026 dans OpenFisca.
### Suite de tests OpenFisca-Tunisia (exécutée le 2026-11-12)

- `openfisca test --country-package openfisca_tunisia tests` :
  **8137 passés / 0 échec / 0 skip / 0 warning** (~4 min). Config pytest
  stricte (`filterwarnings = error`). Moteur sain, rien de cassé.
- Système des pensions testé à part (`make test-pension`, package
  `openfisca_tunisia_pension`) — non lancé, pertinent pour le futur simulateur
  retraite.

### Ressources existantes réutilisables (trouvées dans openfisca-tunisia)

- **Fiches de paie complètes** : `tests/fiches_de_paie/{salarie_fictif,
  enseignant,ouvriere_2016_02}.yaml` → cas de référence à rejouer / comparer.
- **net → brut** déjà outillé via réformes :
  `tests/reforms/de_net_a_salaire_de_base/*` et `de_net_a_imposable/basic.yaml`
  → base pour la fonctionnalité net→brut de l'app.
- **CRES / net** : `tests/cres/{excel,spec_calcul_net}.yaml`.

### Lacune confirmée (ce que nos tests apportent)

- `salaire_net_a_payer`, `irpp_salarie_preleve_a_la_source`,
  `cotisations_salarie`/`cotisations_employeur` ne sont **pas testés
  isolément** dans openfisca-tunisia (seulement indirectement via les fiches
  complètes). Nos `tests/paie/rsna_*.yaml` comblent ce trou — à étendre.

## Résultats des pistes explorées (2026-11-12)

### net → brut (faisable via réforme openfisca)

- Réforme `openfisca_tunisia.reforms.de_net_a_salaire_de_base.de_net_a_salaire_de_base` :
  prend `salaire_net_a_payer` en entrée, renvoie `salaire_de_base` (vrai brut)
  par inversion numérique (`scipy.optimize.fsolve`). Traverse toute la chaîne
  (CNSS + IRPP + CSS, CSS incluse depuis 2018).
- Activation API : `openfisca serve -c openfisca_tunisia -r openfisca_tunisia.reforms.de_net_a_salaire_de_base.de_net_a_salaire_de_base -p 5000`.
  Payload : `salaire_net_a_payer` renseigné, `salaire_de_base` à `null`.
- **À valider avant intégration** : `scipy` doit être installé ; `fsolve` fait des
  `print()` de debug et clone la simulation à chaque itération (latence) ; tests
  existants seulement en 2016 — tester sur 2025. Repli possible : inversion
  dichotomique côté client sur l'API brut→net standard.

### Régimes CNSS salariés (valeurs `regime_securite_sociale_cotisant`)

| Régime | Valeur JSON | Salarié 2025 | Patronal 2025 |
|---|---|---|---|
| Privé non agricole | `rsna` | 9,68 %* | 17,07 %* |
| Salarié agricole | `rsa` | 4,5725 % | 7,7175 % |
| Agricole amélioré | `rsaa` | 6,99 % | 12,48 % |
| Public (CNRPS) | `salarie_cnrps` | 12,95 % (+0,30 % UGTT) | 18,50 % |

*RSNA : 9,68 %/17,07 % à 1000 TND. La **retraite complémentaire** (3 %/6 %) n'est
due que sur la fraction d'assiette > 6×SMIG **et** si
`adhesion_cnss_regime_complementaire = True` — l'app doit décider de l'exposer,
sinon elle sous-estime les hauts salaires. CNRPS : l'agrégat inclut 3 TND de
cotisation syndicale UGTT (0,30 %).

**Non modelés (lacune)** : **CIVP/stage** et **entreprise totalement
exportatrice** n'ont ni régime ni paramètre dédié dans openfisca-tunisia.
Fallback côté app : `neant` (0 cotisation) en signalant que l'exonération n'est
pas paramétrée. Régime `re` (stagiaires) : dossiers cotisations incomplets.

### Cas de référence openfisca réutilisables

- `tests/fiches_de_paie/ouvriere_2016_02.yaml` : **RSNA**, net complet —
  réutilisable (année 2016, paramètres historiques requis).
- `tests/fiches_de_paie/{salarie_fictif,enseignant}.yaml` : **CNRPS public**,
  chaîne brut→net complète (2018 / 2016).
- `tests/cres/spec_calcul_net.yaml` : taux `cotisations_salarie` par régime en
  2023 (rsna 9,18 %, rsa, rsaa, rtns, rtte, rtfr, raci) — bon pour la ligne
  cotisations, pas le net.
- **Lacune** : aucun cas RSNA **récent (2023+) couvrant le net complet** — à
  créer. `cres/excel.yaml` quasi vide (net/irpp commientés). `cotisations_employeur`
  absent de tous ces fichiers.

### Droit 2026 (CSS non supprimée)

- La CSS **n'est pas supprimée** en 2026 : l'art. 87 LF2026 (loi n° 2025-17)
  prolonge le régime exceptionnel à 0,5 %. OpenFisca reconduit le droit 2025 en
  2026 (barème IRPP, CNSS 9,68 %, CSS 0,5 %) — écart nul, conforme.
- Vigilance : ajouter dans openfisca une référence datée 2026-01-01 (même taux,
  réf. art. 87 LF2026) pour tracer la prolongation.

## Désaccords à surveiller

- Simulateurs restés à CNSS 9,18 % en 2025 : corrects seulement pour revenus
  ≤ 2024 (voir `docs/notes/desaccords.md`, D1/D2).
