# AGENTS.md

Instructions et profils d'agents pour ce dépôt, lisibles par n'importe quel
opérateur d'agent (Claude Code, opencode, Cursor, pi…).

## Le projet

Simulateurs de **fiche de paie**, d'**impôt** et de **retraite** pour la Tunisie,
construits sur le moteur [OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia)
et une interface [Shiny for Python](https://shiny.posit.co/py/). Premier livré :
fiche de paie du salarié du privé (régime CNSS non agricole « RSNA »).

**L'application ne calcule rien elle-même** : elle poste la situation d'un
salarié à l'API web d'OpenFisca-Tunisia et affiche le bulletin. OpenFisca est le
moteur unique.

## Règles de travail

- **Le droit fait référence** (lois de finances, Code IRPP/IS, textes CNSS). Les
  simulateurs de paie en ligne sont des points de comparaison, pas la vérité.
- Chaque divergence est **identifiée, documentée et tranchée par le texte** dans
  `docs/notes/desaccords.md`. Un simulateur peut n'être exact que pour certaines
  années : le cas de test est alors calé sur l'année où sa règle est valide.
- **Convention de millésime (retenue à la source)** : pour une paie de l'année N,
  cotisations au taux du mois de paie, barème IRPP des revenus N.
- **Confidentialité des sources** : les noms des simulateurs testés ne figurent
  pas dans le dépôt public. La correspondance « cas ↔ source » est tenue dans
  `sources_locales/` (gitignoré).
- Les tests YAML (`tests/paie/`) sont exécutés par le moteur :
  `openfisca test tests/paie/ -c openfisca_tunisia`.

## Profils d'agents disponibles

**Source unique** : `.pi/agents/*.md` (frontmatter name/description/tools/model).
Les autres formats sont **générés** par `scripts/deploy_agents.sh` :

```bash
scripts/deploy_agents.sh           # régénère .claude/agents/ et .opencode/agent/ (projet)
scripts/deploy_agents.sh --global  # + déploie en user : ~/.pi/agent/agents, ~/.claude/agents, ~/.config/opencode/agent
scripts/deploy_agents.sh --check   # vérifie la synchro (CI), sans écrire
```

N'éditez que `.pi/agents/*.md`, puis relancez le script. `--global` rend les
agents disponibles depuis n'importe quel répertoire de travail. Tout opérateur
qui ne lit aucun de ces dossiers peut reproduire les profils à partir des
descriptions ci-dessous.

### `analyste-openfisca` — analyse du modèle (lecture seule, économe)

- **But** : répondre à des questions précises sur le code et les paramètres
  d'OpenFisca-Tunisia (`/home/benjello/projets/openfisca-tunisia`) — variables,
  taux par branche et par année, enchaînement du calcul de paie.
- **Outils** : lecture seule (read, grep, find, ls, bash en lecture).
  Ne modifie aucun fichier.
- **Modèle conseillé** : petit/rapide (p. ex. Haiku) — tâche mécanique.
- **Exigence clé** : **vérifier les chiffres par le calcul** via le venv
  `openfisca-tunisia/.venv` (SimulationBuilder sur CountryTaxBenefitSystem),
  et **sourcer** chaque taux (fichier YAML + date d'effet). Signaler les
  reports/lacunes.

### `juriste-fiscal-tn` — droit fiscal tunisien de la paie

- **But** : établir ce que dit la loi (IRPP, CNSS, CSS) pour trancher les écarts
  de calcul, en partant des textes primaires (LF, Code IRPP/IS art. 26/40/44/53,
  textes CNSS).
- **Outils** : lecture seule + recherche web (web_search, web_fetch).
- **Modèle conseillé** : intermédiaire (p. ex. Sonnet) — interprétation.
- **Exigence clé** : distinguer année des revenus et année de la loi de finances ;
  citer article + date d'effet ; ne jamais inventer un chiffre ; fournir un bloc
  « à documenter dans desaccords.md » prêt à coller.

## Entités et variables OpenFisca (mémo)

- Individu dans `individus`. Foyer `foyers_fiscaux` (rôle `declarants`,
  variables annuelles `chef_de_famille`, `nb_enf`, `nb_enf_sup`, `nb_infirme`).
  Ménage `menages` (rôle `personne_de_reference`).
- Variables de paie : `cotisations_salarie`, `cotisations_employeur`,
  `salaire_imposable`, `irpp_salarie_preleve_a_la_source`,
  `contribution_sociale_solidarite_prelevee_a_la_source`, `salaire_net_a_payer`,
  `salaire_super_brut`.
- Régime par défaut : `regime_securite_sociale_cotisant = rsna`.
