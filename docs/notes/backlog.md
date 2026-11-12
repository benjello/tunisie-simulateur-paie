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
- [à compléter] Résultat de l'exécution de la suite de tests complète
  OpenFisca-Tunisia (agent lancé le 2026-11-12) : nombre de tests
  passants/échecs, échecs pré-existants éventuels, liste des tests YAML paie
  existants réutilisables.

## Désaccords à surveiller

- Simulateurs restés à CNSS 9,18 % en 2025 : corrects seulement pour revenus
  ≤ 2024 (voir `docs/notes/desaccords.md`, D1/D2).
