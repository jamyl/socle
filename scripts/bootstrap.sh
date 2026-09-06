#!/usr/bin/env bash
#
# socle — amorçage mécanique d'un nouveau projet.
#
# Ce script ne rédige RIEN. Il substitue les placeholders, copie les modules
# choisis à la racine, puis se supprime avec le skill de bootstrap.
# La rédaction (vision, stack, règles, backlog) est le travail de Claude Code
# via /bootstrap-project — c'est lui qui appelle ce script, pas l'inverse.
#
# Usage : ./scripts/bootstrap.sh <slug> [stack-laravel] [mobile-flutter]

set -euo pipefail

MODULES_DISPONIBLES="stack-laravel mobile-flutter"

usage() {
  cat >&2 <<EOF
Usage : ./scripts/bootstrap.sh <slug> [module...]

  <slug>    kebab-case ; sert au nom de projet Compose, à la base de données
            et aux ports. Ex. : ma-boutique
  module    parmi : ${MODULES_DISPONIBLES}

Exemples :
  ./scripts/bootstrap.sh ma-boutique stack-laravel
  ./scripts/bootstrap.sh ma-boutique stack-laravel mobile-flutter
  ./scripts/bootstrap.sh mon-outil
EOF
  exit 2
}

# --- Gardes. Aucune substitution avant que TOUT soit validé : un script qui
# --- s'arrête au milieu laisse un repo à moitié amorcé, pire qu'un refus net.

[ $# -ge 1 ] || usage

SLUG="$1"; shift

if ! printf '%s' "$SLUG" | grep -qE '^[a-z][a-z0-9-]{1,38}[a-z0-9]$'; then
  echo "✗ slug invalide : « $SLUG »" >&2
  echo "  attendu : minuscules, chiffres et tirets, 3 à 40 caractères, commence par une lettre." >&2
  exit 2
fi

cd "$(dirname "$0")/.."
RACINE="$(pwd)"

[ -d modules ] || { echo "✗ modules/ absent : ce repo est déjà amorcé. Rien à faire." >&2; exit 1; }

for m in "$@"; do
  case " $MODULES_DISPONIBLES " in
    *" $m "*) [ -d "modules/$m" ] || { echo "✗ modules/$m absent du dépôt." >&2; exit 1; } ;;
    *) echo "✗ module inconnu : « $m ». Disponibles : $MODULES_DISPONIBLES" >&2; exit 2 ;;
  esac
done

echo "→ projet   : $SLUG"
echo "→ modules  : ${*:-aucun (cœur seul)}"

# --- 1. Copie des modules choisis.
# `cp -R module/. racine/` fusionne sans écraser les dossiers existants, et
# recouvre volontairement les fichiers de même nom : un module qui fournit un
# stack.md rempli DOIT remplacer le squelette du cœur.
for m in "$@"; do
  echo "→ copie de modules/$m"
  cp -R "modules/$m/." "$RACINE/"
done

# --- 2. Substitution des placeholders.
# On ne touche ni .git, ni modules/ (supprimé juste après), ni les binaires.
# `{{PROJET}}` et `{{BUT}}` ne sont PAS substitués ici : ce sont des trous de
# rédaction que Claude Code remplit avec du texte, pas avec un slug.
NOM_AFFICHE="$(printf '%s' "$SLUG" | tr '-' ' ')"

# 🔑 Identifiant SQL distinct du slug : PostgreSQL exige des guillemets autour
# d'un identifiant portant un tiret. `createdb ma-boutique` passe, mais le
# premier `CREATE SCHEMA ma-boutique` ou le premier outil qui interpole le nom
# sans quoter casse — et le message d'erreur ne pointe pas vers le nom.
# Les tirets deviennent des underscores pour la base, l'utilisateur et le rôle.
SLUG_SQL="$(printf '%s' "$SLUG" | tr '-' '_')"

fichiers_texte() {
  find "$RACINE" -type f \
    -not -path "$RACINE/.git/*" \
    -not -path "$RACINE/modules/*" \
    -not -path "$RACINE/scripts/*" \
    -not -name '*.png' -not -name '*.jpg' -not -name '*.pdf' -not -name '*.ico'
}

n=0
while IFS= read -r f; do
  if grep -q '{{SLUG}}\|{{SLUG_SQL}}\|{{NOM_AFFICHE}}' "$f" 2>/dev/null; then
    # `-i.bak` est la seule forme de remplacement en place acceptée à la fois
    # par le sed BSD (macOS) et le sed GNU (Linux, CI) : `-i ''` casse sur GNU,
    # `-i` seul casse sur BSD. On édite en place plutôt que d'écrire un fichier
    # temporaire, sinon le bit d'exécution de scan-secrets.sh est perdu.
    # {{SLUG_SQL}} d'ABORD : sinon `{{SLUG}}` matcherait son préfixe et
    # laisserait un `ma-boutique_SQL}}` derrière lui.
    sed -i.bak \
      -e "s/{{SLUG_SQL}}/$SLUG_SQL/g" \
      -e "s/{{SLUG}}/$SLUG/g" \
      -e "s/{{NOM_AFFICHE}}/$NOM_AFFICHE/g" "$f"
    rm -f "$f.bak"
    n=$((n + 1))
  fi
done < <(fichiers_texte)
echo "→ $n fichier(s) substitué(s)"

# --- 3. Auto-suppression.
# Le template ne doit pas survivre dans le projet : modules/ non choisis,
# skill de bootstrap, et ce script lui-même. Un amorçage ne se rejoue pas.
rm -rf "$RACINE/modules"
rm -rf "$RACINE/.claude/skills/bootstrap-project"
rm -f "$RACINE/GETTING-STARTED.md"
rm -f "$0"
rmdir "$RACINE/scripts" 2>/dev/null || true

git -C "$RACINE" add -A >/dev/null 2>&1 || true

echo
echo "✓ mécanique terminée. Il reste les placeholders de RÉDACTION :"
grep -rlo '{{[A-Z_]*}}' "$RACINE" --exclude-dir=.git 2>/dev/null | sort -u | sed 's/^/    /' || echo "    (aucun)"
echo
echo "  C'est le travail de /bootstrap-project : vision, stack, règles, E01."
