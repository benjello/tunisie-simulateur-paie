# Backlog durable

Reports et pistes à suivre, versés ici pour ne pas vivre uniquement dans une
conversation.

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

## Désaccords à surveiller

- Simulateurs restés à CNSS 9,18 % en 2025 : corrects seulement pour revenus
  ≤ 2024 (voir `docs/notes/desaccords.md`, D1/D2).
