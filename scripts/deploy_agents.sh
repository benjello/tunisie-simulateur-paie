#!/usr/bin/env bash
#
# Déploie / synchronise les agents depuis une SOURCE UNIQUE vers les formats
# attendus par chaque harnais (Claude Code, opencode) et, en option, vers
# l'emplacement global de pi.
#
#   Source de vérité : .pi/agents/*.md  (frontmatter name/description/tools/model)
#
# Générés à partir de la source :
#   - .claude/agents/*.md      (format Claude Code — identique à pi)
#   - .opencode/agent/*.md     (format opencode — ajoute "mode: subagent")
#
# Déploiement global optionnel (--global) :
#   - ~/.pi/agent/agents/*.md        (pi, tous projets)
#   - ~/.claude/agents/*.md          (Claude Code, tous projets)
#   - ~/.config/opencode/agent/*.md  (opencode, tous projets)
#
# Usage :
#   scripts/deploy_agents.sh            # régénère les dossiers projet
#   scripts/deploy_agents.sh --global   # + déploie aussi en global (user)
#   scripts/deploy_agents.sh --check     # vérifie que tout est à jour (CI), sans écrire
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/.pi/agents"

GLOBAL=0
CHECK=0
for arg in "$@"; do
  case "$arg" in
    --global) GLOBAL=1 ;;
    --check)  CHECK=1 ;;
    *) echo "Argument inconnu : $arg" >&2; exit 2 ;;
  esac
done

if [[ ! -d "$SRC" ]]; then
  echo "Source introuvable : $SRC" >&2
  exit 1
fi

# Transforme un fichier source pi en format opencode (insère "mode: subagent"
# juste après la première ligne '---' du frontmatter).
to_opencode() {
  awk 'NR==1 && $0=="---"{print; print "mode: subagent"; next} {print}' "$1"
}

tmp_diff=0

sync_file() {
  # sync_file <contenu-attendu-fichier-tmp> <destination>
  local expected="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -f "$dest" ]] && diff -q "$expected" "$dest" >/dev/null 2>&1; then
    return 0
  fi
  if [[ "$CHECK" -eq 1 ]]; then
    echo "DIFFÈRE : $dest"
    tmp_diff=1
  else
    cp "$expected" "$dest"
    echo "écrit : $dest"
  fi
}

for f in "$SRC"/*.md; do
  [[ -e "$f" ]] || { echo "Aucun agent dans $SRC" >&2; exit 1; }
  name="$(basename "$f")"

  # Claude Code (projet) : copie identique.
  sync_file "$f" "$ROOT/.claude/agents/$name"

  # opencode (projet) : ajoute mode: subagent.
  oc_tmp="$(mktemp)"; to_opencode "$f" > "$oc_tmp"
  sync_file "$oc_tmp" "$ROOT/.opencode/agent/$name"
  rm -f "$oc_tmp"

  if [[ "$GLOBAL" -eq 1 ]]; then
    sync_file "$f" "$HOME/.pi/agent/agents/$name"
    sync_file "$f" "$HOME/.claude/agents/$name"
    oc_tmp="$(mktemp)"; to_opencode "$f" > "$oc_tmp"
    sync_file "$oc_tmp" "$HOME/.config/opencode/agent/$name"
    rm -f "$oc_tmp"
  fi
done

if [[ "$CHECK" -eq 1 && "$tmp_diff" -eq 1 ]]; then
  echo "Des cibles sont désynchronisées. Lancer : scripts/deploy_agents.sh" >&2
  exit 1
fi

echo "OK."
