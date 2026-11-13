# Plan d'améliorations avancées — simulateurs socio-fiscaux Tunisie

Document stratégique. S'appuie sur (1) l'inventaire comparatif des 4 simulateurs
maison (paie, pension, impôt, amen-social) et (2) un benchmark des références
mondiales (LexImpact, PolicyEngine, EUROMOD, OECD TaxBEN, Mes droits sociaux,
Turn2us). Objectif : prioriser des fonctionnalités avancées *utiles*, pas du
gadget.

---

## 0. État des lieux (novembre 2026)

**Les 4 simulateurs existent, fonctionnent, sont scaffoldés sur le modèle paie**
(client OpenFisca bi-mode api/local, uv, agents portables, CI/CD shinyapps.io).

Matrice de parité — `paie` est le plus mûr (625 lignes, 8 tests) :

| Fonction | paie | pension | impôt | amen |
|---|---|---|---|---|
| net→brut (inverse) | ✅ | ❌ | ❌ | ❌ |
| graphique | ✅ | ❌ | ❌ | ❌ |
| export PDF | ✅ | ❌ | ❌ | ❌ |
| comparateur | ✅ | ❌ | ❌ | ❌ |
| bilingue FR/AR | ✅ | ❌ | ✅ | ❌ |
| déployé en ligne | ✅ | ✅ | ✅ | ❌ (bloqué) |

**Manques transversaux** (les 4) : pas d'URL partageable, pas de sauvegarde de
scénario, export limité à paie, pas d'accessibilité testée, pension & amen non
bilingues (alors que l'infra i18n existe), amen non déployé.

---

## 1. Principe directeur (tiré du benchmark)

> **La force d'OpenFisca : un seul moteur sert le cas-type citoyen, l'API,
> et la microsimulation agrégée. Ne pas construire ces fonctions séparément.**

Et pour la Tunisie, l'enjeu social n°1 est le **non-recours aux droits** : la
pédagogie et le parcours « tous droits » priment sur la sophistication experte.
Les prestations sociales (amen) sont le meilleur point d'entrée (fort impact,
moindre aversion que l'impôt).

---

## 2. Chantiers priorisés

### Vague A — Homogénéiser et consolider (socle, effort faible, valeur sûre)

- **A-1. Parité des 4 simulateurs** : porter net→brut (le cas échéant), graphique,
  export, comparateur, **bilingue FR/AR** à pension et amen. L'infra i18n et les
  patterns existent dans paie/impôt → transmission, pas réinvention. *Faible.*
- **A-2. Déployer amen-social** (CD bloqué) et stabiliser les 4 en ligne avec
  `--app-id` (éviter la limite 5 apps). *Faible.*
- **A-3. URL partageable** : encoder la situation dans l'URL (query params) →
  bookmark, partage, reproductibilité. Quasi gratuit, très utile en conseil.
  *Faible-moyenne.* Décliner sur les 4.
- **A-4. Export CSV/PDF** généralisé aux 4 (aujourd'hui paie seul). *Faible.*

### Vague B — Pédagogie & explicabilité (cœur anti-non-recours)

- **B-1. Décomposition « pourquoi ce montant »** : OpenFisca expose l'arbre de
  calcul (`trace`). Afficher la cascade (brut → cotisations par branche →
  imposable → barème → net) avec les montants intermédiaires. paie le fait
  partiellement (branches CNSS) ; généraliser et expliciter. *Moyenne.*
- **B-2. Liens vers les textes de loi / barèmes sources** : les paramètres
  OpenFisca-Tunisia sont déjà sourcés (JORT, articles). Exposer la référence
  légale sous chaque ligne. *Faible-moyenne.*
- **B-3. Barème explorable** : page listant tous les paramètres de la législation
  (taux CNSS par année, barème IRPP, plafonds, SMIG…), navigable. L'API
  OpenFisca le fournit déjà (`/parameters`). *Faible.*

### Vague C — What-if & effets de seuil (valeur sociale très élevée)

- **C-1. Taux marginal effectif de prélèvement (METR) & trappes** : courbe
  « revenu disponible = f(salaire brut) » montrant les paliers où gagner plus
  rapporte peu/rien. Crucial pour amen (benefit cliffs) et paie (tranches IRPP).
  Inspiration : PolicyEngine **CliffWatch**, OECD TaxBEN. *Moyenne.*
- **C-2. What-if « +X % de salaire »** : effet marginal d'une augmentation sur le
  net/l'impôt/les droits. *Faible.*
- **C-3. Comparateur généralisé** (déjà dans paie) : porter aux autres
  (ex. impôt : effet du barème 2024 vs 2025 ; pension : effet d'un départ à
  60 vs 62 ans). *Faible-moyenne.*

### Vague D — Parcours « tous droits » (le grand saut, fort impact)

- **D-1. Simulateur unifié** : un ménage saisit sa situation **une seule fois**
  (composition, revenus, logement…) et voit d'un coup paie + IRPP + pension
  (projetée) + éligibilité amen. C'est le modèle « Mes droits sociaux » /
  « Les Meves Ajudes » (Barcelone, 43 prestations). Même moteur OpenFisca
  derrière. *Élevée* (orchestration + UX), mais c'est le vrai différenciateur
  social. Mobile-first, FR/AR. *Priorité stratégique.*

### Vague E — Simulateur de réforme (façon LexImpact)

- **E-1. Modifier un paramètre législatif** (barème IRPP, taux CNSS, seuil amen)
  et voir l'impact sur des **cas-types**. OpenFisca gère les réformes nativement.
  Utile pour débat public, journalistes, administration. *Moyenne-élevée.*
- **E-2. Impact population** (microsimulation agrégée) : effet d'une réforme sur
  la pauvreté/les inégalités/le budget. Nécessite une **enquête ménages
  tunisienne** calable (INS ?) — **à investiguer, dépendance externe**. *Élevée.*

### Vague F — Spécificités Tunisie / pays en développement

- **F-1. Mobile-first & faible bande passante** : UI légère, test réseau lent.
  Le mode local (openfisca in-process) aide (pas d'aller-retour API). *Moyenne.*
- **F-2. Travailleurs informels / indépendants** : parcours avec revenu
  déclaratif, hypothèses adaptées (une large part des revenus échappe à la paie
  formelle). *Moyenne.*
- **F-3. Arabe partout + RTL soigné** : généraliser l'i18n (pension, amen),
  traiter les limites connues (onglets non renommables en Shiny → envisager un
  autre composant ; PDF arabe → arabic-reshaper + python-bidi). *Moyenne.*

### Vague G — Ouverture & transparence (quasi gratuit avec OpenFisca)

- **G-1. API publique documentée** du moteur tunisien (socle déjà là). *Faible.*
- **G-2. Traçabilité versionnée** : afficher la version du modèle
  OpenFisca-Tunisia et la date des barèmes utilisés dans chaque résultat
  (reproductibilité, à la PolicyEngine). *Faible.*

---

## 3. Dépendances techniques transverses

- **Factoriser le socle commun** : client OpenFisca, i18n, kit déploiement,
  agents, composants UI (lignes de bulletin, cartes) se dupliquent dans les 4
  repos → risque de divergence. Envisager un **package partagé**
  (`tunisie-simulateurs-commons`) ou un **template repo**. *Moyenne, mais
  rentable dès 4 simulateurs.*
- **Mode local par défaut** pour le déploiement (amen le fait déjà) : évite de
  dépendre d'une API hébergée séparément.

---

## 4. Recommandation de séquençage

1. **Vague A** (parité + déploiement + URL partageable) — rend les 4 cohérents
   et présentables. Rapide, haute valeur/effort.
2. **Vague B** (pédagogie/explicabilité) + **G** (traçabilité, API, barèmes) —
   quasi gratuits avec OpenFisca, renforcent la confiance.
3. **Vague C** (trappes/METR) — fort signal social, complexité modérée.
4. **Vague D** (parcours tous droits) — le différenciateur stratégique, à
   lancer une fois le socle factorisé.
5. **Vague E** (réforme + microsimulation) — pour l'impact « décideur », dépend
   de E-2 (microdonnées, à investiguer).
6. **Vague F** (mobile, informel, arabe) — transversale, à intégrer tôt dans
   l'UX plutôt qu'après coup.

---

## 5. Reports / à investiguer (dépendances externes)

- **Enquête ménages tunisienne** calable pour la microsimulation population
  (INS, Banque mondiale ?) — condition de la vague E-2.
- **Composant d'onglets renommables** en Shiny for Python (limite i18n actuelle).
- **Rendu arabe RTL dans les PDF** (arabic-reshaper + python-bidi) — à tester.
- Pas de simulateur socio-fiscal grand public tunisien/maghrébin existant trouvé
  à benchmarker directement (hors OpenFisca-Tunisia) — notre créneau est ouvert.
