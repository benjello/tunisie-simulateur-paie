# tunisie-simulateur-paie

Simulateurs de **fiche de paie**, d'**impôt** et de **retraite** pour la Tunisie,
construits sur le moteur de micro-simulation [OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia),
avec une interface [Shiny for Python](https://shiny.posit.co/py/).

**🚀 Application en ligne : https://benjello.shinyapps.io/simulateur-paie-tunisie/**

Premier simulateur livré : **fiche de paie** (salarié du privé et public).
Fonctions : brut↔net, régimes CNSS (RSNA/RSA/RSAA/CNRPS), heures supplémentaires,
détail CNSS par branche, graphique, export PDF, comparateur multi-années/régimes,
simulation annuelle IRPP, interface bilingue FR/AR.

## Architecture

L'application **ne calcule rien elle-même** : elle envoie la situation du
salarié à l'**API web d'OpenFisca-Tunisia** et affiche le bulletin renvoyé.
OpenFisca reste le moteur unique ; l'app est une couche de présentation.

```
Shiny (app/)  ──HTTP──▶  API OpenFisca-Tunisia  ──▶  moteur de calcul
```

En local, deux processus (voir [`app/README.md`](app/README.md)) :

```bash
uv run openfisca serve -c openfisca_tunisia -p 5000   # l'API
uv run shiny run app/app.py --port 8100               # l'app
```

> Déploiement statique GitHub Pages non retenu : OpenFisca importe des
> extensions compilées (pendulum, numexpr, psutil) absentes de Pyodide. Voir
> [`docs/notes/backlog.md`](docs/notes/backlog.md) (hébergement de l'API, piste
> MCP).

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
