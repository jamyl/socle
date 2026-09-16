#!/usr/bin/env bash
#
# socle — adopter la méthode dans un projet qui existe déjà.
#
# Ce script ne rédige RIEN et n'écrase JAMAIS un fichier existant. Il copie les
# assets de méthode dans un dépôt en cours, signale tout ce qu'il a sauté, et
# installe le skill /adopter-socle qui fera la rédaction en lisant ton code.
#
# Le pendant de bootstrap.sh, qui lui suppose un dépôt neuf issu du template.
#
# Usage, depuis une copie du template :
#   git clone --depth 1 https://github.com/jamyl/socle /tmp/socle
#   cd ~/mon-projet-existant
#   /tmp/socle/scripts/adopt.sh [--stack <module>]
#
#   --stack <module>   reprend AUSSI les sous-agents et les règles de ce module
#                      (ex. stack-laravel), et rien d'autre : ni docker-compose,
#                      ni CI, ni docs. L'infrastructure d'un projet existant ne
#                      se remplace pas par celle d'un template.

set -euo pipefail

SOURCE="$(cd "$(dirname "$0")/.." && pwd)"
CIBLE="$(pwd)"
MODULE=""

usage() {
  sed -n '3,22p' "$0" | sed 's/^# \{0,1\}//' >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --stack) [ $# -ge 2 ] || usage; MODULE="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "✗ argument inconnu : « $1 »" >&2; usage ;;
  esac
done

# --- Gardes. Rien n'est copié avant que tout soit validé.

[ "$SOURCE" != "$CIBLE" ] || {
  echo "✗ Lance ce script DEPUIS ton projet, pas depuis le template." >&2
  echo "  cd ~/mon-projet && $SOURCE/scripts/adopt.sh" >&2
  exit 2; }

[ -f "$SOURCE/.claude/skills/deliver-story/SKILL.md" ] || {
  echo "✗ $SOURCE ne ressemble pas au template socle." >&2; exit 1; }

git -C "$CIBLE" rev-parse --git-dir >/dev/null 2>&1 || {
  echo "✗ $CIBLE n'est pas un dépôt git. La méthode s'appuie sur git : commence par un commit." >&2
  exit 1; }

[ -z "$(git -C "$CIBLE" status --porcelain)" ] || {
  echo "✗ Ton arbre de travail n'est pas propre." >&2
  echo "  Commite ou remise tes changements : le diff de l'adoption doit être lisible seul." >&2
  exit 1; }

[ ! -d "$CIBLE/.claude/skills/deliver-story" ] || {
  echo "✗ Ce projet a déjà /deliver-story : la méthode est en place. Rien à faire." >&2
  exit 1; }

if [ -n "$MODULE" ]; then
  [ -d "$SOURCE/modules/$MODULE/.claude" ] || {
    echo "✗ modules/$MODULE/.claude absent du template." >&2
    echo "  Modules qui fournissent des assets .claude/ : $(cd "$SOURCE/modules" && ls -d */.claude 2>/dev/null | cut -d/ -f1 | tr '\n' ' ')" >&2
    exit 2; }
fi

echo "→ source : $SOURCE"
echo "→ cible  : $CIBLE"
echo "→ module : ${MODULE:-aucun (agents génériques)}"
echo

BRANCHE="adopter-socle"
if git -C "$CIBLE" show-ref --verify --quiet "refs/heads/$BRANCHE"; then
  echo "→ branche $BRANCHE existe déjà, on s'y place"
  git -C "$CIBLE" checkout -q "$BRANCHE"
else
  git -C "$CIBLE" checkout -q -b "$BRANCHE"
  echo "→ branche $BRANCHE créée"
fi

# --- 1. Copie, sans jamais écraser.
# Le tableau des sautés est la sortie la plus importante du script : c'est la
# liste de ce que tu devras rapprocher à la main.

SAUTES=""
copies=0

copier() {   # copier <relatif depuis SOURCE> <relatif dans CIBLE>
  local src="$SOURCE/$1" dst="$CIBLE/$2"
  if [ -e "$dst" ]; then
    SAUTES="$SAUTES  $2"$'\n'
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  cp -p "$src" "$dst"
  copies=$((copies + 1))
}

# Tout `.claude/**` sauf le skill d'amorçage (sans objet ici) et settings.json
# (une liste de permissions se fusionne à la main, jamais par un script).
while IFS= read -r rel; do
  case "$rel" in
    .claude/skills/bootstrap-project/*) continue ;;
    .claude/settings.json) continue ;;
  esac
  copier "$rel" "$rel"
done < <(cd "$SOURCE" && find .claude -type f | sort)

# Les squelettes de documentation.
while IFS= read -r rel; do
  copier "$rel" "$rel"
done < <(cd "$SOURCE" && find docs -type f | sort)

# Les deux fichiers qui portent du contexte projet : jamais écrasés, déposés à
# côté sous `.socle.md` pour que le skill propose la fusion.
for f in CLAUDE.md CONTRIBUTING.md; do
  if [ -e "$CIBLE/$f" ]; then
    cp -p "$SOURCE/$f" "$CIBLE/${f%.md}.socle.md"
    echo "→ $f existe : la version du socle est déposée en ${f%.md}.socle.md"
    copies=$((copies + 1))
  else
    copier "$f" "$f"
  fi
done

# Les agents du module demandé remplacent les gabarits génériques.
if [ -n "$MODULE" ]; then
  while IFS= read -r rel; do
    copier "modules/$MODULE/$rel" "$rel"
  done < <(cd "$SOURCE/modules/$MODULE" && find .claude -type f | sort)
  rm -f "$CIBLE"/.claude/templates/agent-stack-*.md
  echo "→ agents et règles de $MODULE repris ; gabarits génériques retirés"
else
  # Même mécanique que bootstrap.sh : les gabarits deviennent des squelettes
  # dans .claude/agents/, que /adopter-socle spécialise avec la stack observée.
  for gabarit in "$CIBLE"/.claude/templates/agent-stack-*.md; do
    [ -e "$gabarit" ] || continue
    nom="${gabarit##*/agent-stack-}"
    if [ -e "$CIBLE/.claude/agents/$nom" ]; then
      SAUTES="$SAUTES  .claude/agents/$nom (gabarit non installé)"$'\n'
      rm -f "$gabarit"
    else
      mv "$gabarit" "$CIBLE/.claude/agents/$nom"
    fi
  done
fi

# --- 2. .gitignore : ajouter les lignes manquantes, ne rien réécrire.
AJOUTS=""
while IFS= read -r ligne; do
  case "$ligne" in ''|'#'*) continue ;; esac
  grep -qxF "$ligne" "$CIBLE/.gitignore" 2>/dev/null || AJOUTS="$AJOUTS$ligne"$'\n'
done < <(grep -E '^(\.claude/|\*\.bak|__pycache__/|\*\.pyc)' "$SOURCE/.gitignore")

if [ -n "$AJOUTS" ]; then
  { echo ""; echo "# --- socle : état local de session et artefacts d'outillage ---"; printf '%s' "$AJOUTS"; } >> "$CIBLE/.gitignore"
  echo "→ .gitignore : $(printf '%s' "$AJOUTS" | grep -c .) ligne(s) ajoutée(s) à la fin"
fi

# --- 3. Rapport.
echo
echo "✓ $copies fichier(s) copié(s)."

if [ -n "$SAUTES" ]; then
  echo
  echo "⚠️  Sautés parce qu'ils existaient déjà — À RAPPROCHER À LA MAIN :"
  printf '%s' "$SAUTES"
  echo "    Compare-les avec $SOURCE/<même chemin> et reprends ce qui manque."
fi

echo
echo "Jamais touchés, par principe : README.md, LICENSE, .claude/settings.json."
echo "  Les permissions se relisent à la main : voir docs/engineering/config-locale.md"
echo
echo "Suite :"
echo "  1. git -C \"$CIBLE\" diff --stat HEAD     # relis ce qui a atterri"
echo "  2. claude"
echo "  3. /adopter-socle                        # lit ton code, rédige, se supprime"
