# Application — fiche de paie (local)

Interface [Shiny for Python](https://shiny.posit.co/py/) pour le simulateur de
fiche de paie. **Tout le calcul est fait par OpenFisca-Tunisia**, via son API
web : l'app construit une situation (ménage d'un salarié), la poste à l'API, et
affiche le bulletin.

## Lancer en local

Deux processus. Dans un premier terminal, l'API OpenFisca :

```bash
uv run openfisca serve -c openfisca_tunisia -p 5000
```

Dans un second, l'app Shiny :

```bash
uv run shiny run app/app.py --port 8100
```

Puis ouvrir http://localhost:8100.

Pour pointer vers une API hébergée ailleurs, définir `OPENFISCA_API_URL` :

```bash
OPENFISCA_API_URL=https://mon-api-openfisca.example uv run shiny run app/app.py
```

## Fichiers

- `openfisca_client.py` — construction de la situation et appels `/calculate`.
- `app.py` — interface Shiny (entrées : salaire, année, régime, situation
  familiale, primes ; sorties : bulletin salarié + coût employeur).

## Périmètre actuel

Régime **RSNA** (salariés du privé non agricoles), sens **brut → net**. Le
net → brut, les autres régimes (RSAA, CIVP, export, CNRPS) et les heures
supplémentaires sont au backlog.

## Déploiement

Le déploiement statique GitHub Pages n'est pas possible tel quel : OpenFisca
importe des extensions compilées (pendulum, numexpr, psutil) absentes de
Pyodide. L'app vit donc en mode client/serveur. L'étape suivante envisagée est
d'héberger l'API (ou de l'exposer via un serveur **MCP**) puis d'y connecter le
front. Voir `docs/notes/backlog.md`.
