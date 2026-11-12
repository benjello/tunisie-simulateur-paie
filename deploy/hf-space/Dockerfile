# Dockerfile pour Hugging Face Spaces (type Docker).
# Un seul process : l'app Shiny calcule via OpenFisca EN DIRECT (mode local),
# sans API HTTP séparée. HF Spaces expose le port 7860.
FROM python:3.12-slim

WORKDIR /app

# Dépendances : shiny + openfisca-tunisia (le moteur tourne dans le process).
COPY pyproject.toml ./
RUN pip install --no-cache-dir "shiny>=1.0" "openfisca-tunisia>=0.159" "matplotlib>=3.8"

# matplotlib sans display : backend non interactif.
ENV MPLBACKEND=Agg

# Code de l'app.
COPY app/ ./app/

# Mode « moteur en direct » : pas d'API HTTP.
ENV OPENFISCA_MODE=local

# HF Spaces attend le service sur le port 7860.
EXPOSE 7860
CMD ["shiny", "run", "app/app.py", "--host", "0.0.0.0", "--port", "7860"]
