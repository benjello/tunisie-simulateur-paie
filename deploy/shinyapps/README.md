# Déploiement sur shinyapps.io

Hébergement gratuit de l'app Shiny (compte shinyapps.io, sans carte bancaire ;
plan gratuit = 25 h actives/mois, 1 Go RAM). L'app calcule OpenFisca **en
direct** dans le process (`OPENFISCA_MODE=local`) : pas d'API HTTP séparée.

## Prérequis (une seule fois)

1. **Compte** sur https://www.shinyapps.io (Google/GitHub, sans carte).
2. **rsconnect-python** : déjà installé dans le venv du projet (`uv sync --group dev`).
3. **Autoriser le compte** — contient ton SECRET, à lancer dans TON terminal
   (depuis Account → Tokens sur shinyapps.io, bouton « Copy to clipboard ») :

   ```bash
   .venv/bin/rsconnect add --account <compte> --name <compte> \
     --token <TOKEN> --secret <SECRET>
   ```

   > Le token/secret donnent accès à ton compte : ne les commite jamais. Tu peux
   > les révoquer/régénérer à tout moment depuis la page Tokens.

## Déployer

```bash
deploy/shinyapps/push.sh <compte> [nom-app]
# ex :
deploy/shinyapps/push.sh benjello simulateur-paie-tunisie
```

Le script assemble un bundle propre (point d'entrée `app.py` qui force le mode
local + `app_main.py` + `openfisca_client.py` + `i18n.py` + `requirements.txt`)
et lance `rsconnect deploy shiny`. L'URL publique s'affiche à la fin.

## Fichiers

- `app.py` — point d'entrée déploiement (force `OPENFISCA_MODE=local`).
- `requirements.txt` — dépendances (shiny, openfisca-tunisia, matplotlib, httpx).
- `push.sh` — assemble le bundle et déploie.

## Déploiement automatique (GitHub Actions)

Le workflow `.github/workflows/deploy.yml` déploie l'app à chaque push sur
`main` touchant `app/` ou `deploy/shinyapps/` (et manuellement via
*Actions → Deploy to shinyapps.io → Run workflow*).

**Configuration unique — définir 3 secrets GitHub** (Settings → Secrets and
variables → Actions → New repository secret) :

| Secret | Valeur |
|--------|--------|
| `SHINYAPPS_ACCOUNT` | ton compte, ex. `benjello` |
| `SHINYAPPS_TOKEN`   | le token (Account → Tokens sur shinyapps.io) |
| `SHINYAPPS_SECRET`  | le secret associé |
| `SHINYAPPS_APP_ID`  | **(important)** l'ID de l'app déjà déployée, pour la METTRE À JOUR au lieu d'en créer une nouvelle |

### ⚠️ Limite 5 apps (plan gratuit) — ne pas recréer à chaque déploiement

Sans `SHINYAPPS_APP_ID`, chaque `rsconnect deploy` **crée une nouvelle app** et
sature vite le quota de 5 apps du plan gratuit (erreur *« maximum number of
applications »*). Pour l'éviter :

1. Sur https://www.shinyapps.io/admin/#/applications, **supprime les apps en
   double** ; garde `simulateur-paie-tunisie` et note son **app ID**.
2. Ajoute le secret GitHub `SHINYAPPS_APP_ID` avec cette valeur.
3. Décommente le bloc `push:` dans `.github/workflows/deploy.yml` pour
   réactiver le déploiement automatique (il est en manuel seul par défaut).

Le workflow passe `--app-id` quand ce secret existe → il met à jour l'app au
lieu d'en créer une.

Ces valeurs sont chiffrées par GitHub et ne sont jamais exposées dans les logs.
Tant qu'elles ne sont pas définies, le job échoue proprement (rien n'est
déployé). Pour les changer : régénère le token sur shinyapps.io et mets à jour
le secret.

### Propager les secrets à d'autres repos (pension, impôt…)

Les secrets GitHub ne se copient pas d'un repo à l'autre automatiquement. Pour
éviter de les ressaisir dans l'interface, utilise
`scripts/set_shinyapps_secrets.sh` (lit les valeurs depuis l'environnement, les
pousse via `gh`) :

```bash
SHINYAPPS_ACCOUNT=benjello \
SHINYAPPS_TOKEN=<token> \
SHINYAPPS_SECRET=<secret> \
scripts/set_shinyapps_secrets.sh benjello/tunisie-simulateur-pension
```

(Préfixe la commande d'un espace pour ne pas la garder dans l'historique si
`HISTCONTROL=ignorespace`.) Le repo cible doit avoir le workflow `deploy.yml`
(adapté à son app) pour que les secrets servent.

> **Alternative pour beaucoup de repos** : les déplacer dans une **organisation
> GitHub** et définir les secrets `SHINYAPPS_*` **une seule fois** au niveau de
> l'org (accessibles à tous ses repos). Surdimensionné pour 2-3 repos.

Ce script est générique : il peut être copié dans chaque simulateur (comme les
agents, via un kit) ou lancé depuis le dépôt paie en ciblant un autre repo.

Procédure complète côté repo pension : voir
`docs/notes/relais-pension.md` (chantier pension) — copier `deploy/shinyapps/`,
adapter `app.py`/`requirements.txt`, ajouter `deploy.yml`, puis pousser les
secrets avec ce script.

## Limite du plan gratuit

## Limite du plan gratuit

25 h actives/mois. Au-delà, l'app est suspendue jusqu'au mois suivant. Pour un
usage soutenu : plan payant shinyapps.io, ou un VPS (voir `../README.md`).
