# Déploiement

L'app Shiny appelle l'API web d'OpenFisca-Tunisia. Pour sortir du « tout en
local », il faut héberger **deux services** : l'API OpenFisca et l'app Shiny.
L'app lit l'URL de l'API dans la variable d'environnement `OPENFISCA_API_URL`.

Rien n'est déployé automatiquement ici (pas d'identifiants dans le dépôt) :
ce dossier fournit la procédure et les fichiers de référence.

## 1. API OpenFisca-Tunisia

Service HTTP sans état, exposant `/calculate`, `/spec`, etc.

```bash
openfisca serve --country-package openfisca_tunisia --bind 0.0.0.0:5000
```

(`--bind host:port` est transmis à gunicorn ; en local, `--port 5000` suffit.)

Voir `Dockerfile.api` pour une image conteneur minimale.

### Pistes d'hébergement

| Cible | Notes |
|---|---|
| **Hugging Face Spaces** (Docker) | gratuit, simple, CORS à autoriser pour le front |
| **VPS** (docker run) | contrôle total, coût fixe |
| **Fly.io / Render** | déploiement Docker direct |

> Rappel : le déploiement 100 % navigateur (GitHub Pages / WebAssembly) reste
> impossible tant qu'OpenFisca importe `pendulum`/`numexpr`/`psutil` (absents de
> Pyodide). D'où le modèle client/serveur.

## 2. App Shiny

```bash
OPENFISCA_API_URL=https://<api-hébergée> shiny run app/app.py --host 0.0.0.0 --port 8100
```

Hébergement : Hugging Face Spaces (Shiny), shinyapps.io, ou le même VPS que
l'API.

## 3. Piste MCP (à terme)

Exposer OpenFisca-Tunisia via un serveur **MCP** (`calculer_paie`,
`brut_vers_net`, `net_vers_brut`) consommable par l'app ET par des agents. La
web-api actuelle est l'étape intermédiaire : même encapsulation du moteur,
protocole différent. À prototyper une fois l'hébergement API en place.
