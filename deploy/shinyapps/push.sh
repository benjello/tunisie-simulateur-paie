#!/usr/bin/env bash
#
# Déploie l'app Shiny sur shinyapps.io (compte déjà autorisé via `rsconnect add`).
#
# Prérequis (une seule fois) :
#   1. pip/uv : rsconnect-python installé (fait : .venv du projet)
#   2. Autoriser le compte (contient TON secret, à lancer toi-même) :
#        rsconnect add --account <compte> --name <compte> --token <TOKEN> --secret <SECRET>
#
# Usage :
#   deploy/shinyapps/push.sh <compte> [nom-app]
#   ex : deploy/shinyapps/push.sh benjello simulateur-paie-tunisie
#
set -euo pipefail

# <compte> doit correspondre au nom du credential enregistré via `rsconnect add
# --name <compte>` (ici : benjello). On utilise --name (pas --account) pour que
# rsconnect réutilise le token/secret déjà stockés, sans les redemander.
COMPTE="${1:?Usage: push.sh <compte> [nom-app]}"
APPNAME="${2:-simulateur-paie-tunisie}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUNDLE="$(mktemp -d)"

# Charge le .env du projet s'il existe (pour SHINYAPPS_APP_ID notamment).
if [[ -f "$ROOT/.env" ]]; then
  set -a; # shellcheck disable=SC1091
  source "$ROOT/.env"; set +a
fi

echo "Assemblage du bundle dans $BUNDLE"

# Le point d'entrée shinyapps (force le mode local) devient app.py.
cp "$ROOT/deploy/shinyapps/app.py" "$BUNDLE/app.py"
# Le vrai code de l'app : app/app.py -> app_main.py (importé par app.py).
cp "$ROOT/app/app.py" "$BUNDLE/app_main.py"
# Modules de l'app.
cp "$ROOT/app/openfisca_client.py" "$BUNDLE/openfisca_client.py"
cp "$ROOT/app/i18n.py" "$BUNDLE/i18n.py"
# Dépendances.
cp "$ROOT/deploy/shinyapps/requirements.txt" "$BUNDLE/requirements.txt"
# Contrainte de version Python (évite le warning et fige la cible).
echo "3.12" > "$BUNDLE/.python-version"

echo "Contenu du bundle :"
ls -1 "$BUNDLE"

# rsconnect depuis le venv du projet. --app-id si défini (met à jour l'app
# existante au lieu d'en créer une ; évite la limite de 5 apps du plan gratuit).
APPID_ARGS=()
if [[ -n "${SHINYAPPS_APP_ID:-}" ]]; then
  APPID_ARGS=(--app-id "$SHINYAPPS_APP_ID")
fi
"$ROOT/.venv/bin/rsconnect" deploy shiny "$BUNDLE" \
  --name "$COMPTE" \
  --title "$APPNAME" \
  "${APPID_ARGS[@]}" \
  --entrypoint app:app

echo "Déploiement lancé. Suivez l'URL affichée ci-dessus."
rm -rf "$BUNDLE"
