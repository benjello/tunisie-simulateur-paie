#!/usr/bin/env bash
#
# Pousse les 3 secrets shinyapps.io vers un repo GitHub, pour activer le
# déploiement automatique (.github/workflows/deploy.yml) sur ce repo.
#
# À réutiliser pour chaque simulateur (pension, impôt, …) afin de ne pas
# ressaisir les secrets à la main dans l'interface GitHub.
#
# Les valeurs sont lues depuis l'ENVIRONNEMENT — jamais écrites dans un fichier,
# jamais commitées. Elles ne transitent que par la CLI gh (chiffrées côté GitHub).
#
# Usage :
#   SHINYAPPS_ACCOUNT=benjello \
#   SHINYAPPS_TOKEN=xxxxxxxx \
#   SHINYAPPS_SECRET=yyyyyyyy \
#   scripts/set_shinyapps_secrets.sh benjello/tunisie-simulateur-pension
#
# Astuce pour éviter que le secret reste dans l'historique du shell : préfixe la
# commande d'un espace (si HISTCONTROL=ignorespace), ou exporte les variables
# dans un sous-shell que tu fermes ensuite.
set -euo pipefail

REPO="${1:?Usage: set_shinyapps_secrets.sh <owner/repo>}"

# Charge un .env à la racine du projet s'il existe (gitignoré). Évite d'avoir à
# exporter les variables à la main à chaque fois.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a  # exporte automatiquement les variables définies
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

: "${SHINYAPPS_ACCOUNT:?Définis la variable SHINYAPPS_ACCOUNT}"
: "${SHINYAPPS_TOKEN:?Définis la variable SHINYAPPS_TOKEN}"
: "${SHINYAPPS_SECRET:?Définis la variable SHINYAPPS_SECRET}"

echo "Pose des secrets shinyapps.io sur $REPO…"
gh secret set SHINYAPPS_ACCOUNT --repo "$REPO" --body "$SHINYAPPS_ACCOUNT"
gh secret set SHINYAPPS_TOKEN   --repo "$REPO" --body "$SHINYAPPS_TOKEN"
gh secret set SHINYAPPS_SECRET  --repo "$REPO" --body "$SHINYAPPS_SECRET"

echo "OK. Secrets définis sur $REPO :"
gh secret list --repo "$REPO"
