---
title: Simulateur de paie Tunisie
emoji: 🧾
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: agpl-3.0
---

# Simulateur de fiche de paie — Tunisie

Simulateur de fiche de paie (salarié du privé et public), calculé par le moteur
[OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia), interface
[Shiny for Python](https://shiny.posit.co/py/).

Le moteur OpenFisca tourne **en direct dans le même process** (variable
`OPENFISCA_MODE=local`) : pas d'API HTTP séparée, adapté à un déploiement
mono-service.

## Déploiement sur Hugging Face Spaces

1. Créer un Space **Docker** sur https://huggingface.co/new-space (CPU Basic,
   gratuit).
2. Copier dans le Space les fichiers du dépôt nécessaires au build :
   - ce `README.md` (avec le front-matter YAML ci-dessus) à la **racine** du
     Space ;
   - le `Dockerfile` (`deploy/hf-space/Dockerfile`) à la racine ;
   - le dossier `app/` et le `pyproject.toml` du dépôt.

   Le plus simple : pousser le dépôt vers le remote du Space, en plaçant ce
   README et ce Dockerfile à la racine. Exemple :

   ```bash
   # depuis une copie du dépôt
   cp deploy/hf-space/Dockerfile ./Dockerfile
   cp deploy/hf-space/README.md ./README.md   # écrase le README racine pour le Space
   git add Dockerfile README.md
   git commit -m "Build HF Space"
   git remote add space https://huggingface.co/spaces/<user>/<space>
   git push space main
   ```

   (Ou garder une branche dédiée au Space pour ne pas écraser le README du
   dépôt GitHub.)

3. HF build l'image et lance l'app sur le port 7860.

## Local

Pour tester le mode déploiement en local (moteur en direct, sans API) :

```bash
OPENFISCA_MODE=local uv run shiny run app/app.py --port 8100
```
