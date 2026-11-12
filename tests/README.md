# Tests de validation

Tests YAML au format OpenFisca, exécutables avec le moteur OpenFisca-Tunisia.

## Lancer les tests

Depuis un environnement où `openfisca-tunisia` est installé :

```bash
openfisca test tests/paie/ -c openfisca_tunisia
```

## Organisation

- `paie/rsna_2024.yaml` — fiche de paie RSNA, revenus 2024 (CNSS 9,18 %).
- `paie/rsna_2025.yaml` — fiche de paie RSNA, revenus 2025 (CNSS 9,68 %,
  barème LF2025).

Les valeurs attendues sont celles du moteur OpenFisca-Tunisia, cohérentes avec
le droit de l'année testée. Les cas sont comparés — hors dépôt — à des
simulateurs de paie en ligne (correspondance dans `sources_locales/`, non
publiée). Les décisions tranchant les divergences sont dans
[`../docs/notes/desaccords.md`](../docs/notes/desaccords.md).

## Convention de millésime (retenue à la source)

Pour une paie de l'année N : cotisations au taux du mois de paie, barème IRPP
des revenus N. OpenFisca applique les deux au millésime du mois de paie.
