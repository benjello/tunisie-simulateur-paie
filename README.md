# tunisie-simulateur-paie

Simulateurs de **fiche de paie**, d'**impôt** et de **retraite** pour la Tunisie,
construits sur le moteur de micro-simulation [OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia),
avec une interface [Shiny for Python](https://shiny.posit.co/py/).

Premier simulateur livré : **fiche de paie** (salariés du privé, régime CNSS
non agricole « RSNA » ; les autres régimes seront ajoutés ensuite).

## Périmètre de la v1 (fiche de paie RSNA)

Union des éléments repérés dans les simulateurs de paie tunisiens existants :

- **Entrées** : salaire (brut ou net), année de paie, chef de famille, conjoint
  à charge, enfants (≤ 4), étudiants sans bourse, enfants handicapés, autres
  déductions, primes/indemnités, heures supplémentaires.
- **Sorties** : bulletin côté salarié (brut → CNSS → base imposable → abattement
  → IRPP → CSS → net) et côté employeur (CNSS patronale, TFP, FOPROLOS, accident
  du travail, coût total).
- **Deux sens** : brut → net et net → brut.

## Principe de validation

Le **droit fait référence** (loi de finances, Code de l'IRPP et de l'IS, textes
CNSS). Les simulateurs de paie en ligne servent de **points de comparaison** :
chaque cas chiffré devient un test YAML OpenFisca.

Chaque divergence entre simulateurs — ou entre un simulateur et la loi — est
identifiée, documentée dans [`docs/notes/desaccords.md`](docs/notes/desaccords.md)
et tranchée par le texte légal. Un simulateur peut n'être exact que pour
certaines années ; le cas de test est alors calé sur l'année où sa règle est
valide.

> Les noms des simulateurs testés ne figurent pas dans le dépôt public. La
> correspondance « cas de test ↔ source » est tenue localement dans
> `sources_locales/` (dossier gitignoré).

## Convention de millésime (prélèvement à la source)

Pour une paie de l'année N :

- les **cotisations** sont prises au taux en vigueur le mois de la paie ;
- le **barème IRPP** appliqué à la retenue à la source est celui des **revenus
  de l'année N** (fixé par la loi de finances correspondante).

## Structure

```
tests/paie/        Tests YAML OpenFisca (anonymisés, publics)
sources_locales/   Correspondance cas ↔ simulateur (GITIGNORÉ)
docs/notes/        Registre des désaccords et décisions
app/               Application Shiny (à venir)
```
