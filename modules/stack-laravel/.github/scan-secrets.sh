#!/usr/bin/env bash
# {{NOM_AFFICHE}} — refuse tout secret commité.
#
# Scanne les fichiers SUIVIS par git uniquement. `.env` n'est pas suivi, donc
# jamais scanné : c'est bien un secret *commité* que l'on cherche, pas un secret
# local.
set -uo pipefail

# Motifs de clés. Chaque entrée : "libellé:::regex"
PATTERNS=(
  "Clé privée PEM:::-----BEGIN [A-Z ]*PRIVATE KEY-----"
  "Clé AWS:::AKIA[0-9A-Z]{16}"
  "Token GitHub:::gh[pousr]_[A-Za-z0-9]{36,}"
  # 🔑 LES DEUX ORDRES DE PRÉFIXE. Stripe écrit `sk_live_`, d'autres passerelles
  # écrivent `live_sk_`. Ne couvrir qu'un ordre laisse la moitié du couple
  # invisible — défaut réel trouvé par `/security-review` sur le projet
  # d'origine, alors que l'autre moitié venait justement d'être ajoutée.
  "Clé de paiement live:::(sk|pk)_live_[A-Za-z0-9]{16,}"
  "Clé de paiement live (ordre inverse):::live_(sk|pk)_[A-Za-z0-9]{16,}"
  # 🔑 LES CLÉS DE BAC À SABLE AUSSI. Elles ne donnent accès à aucun argent
  # réel, mais elles se promènent bien plus facilement — dans un ticket, un
  # chat, un README — et une clé de test commitée est une clé de production
  # commitée dans six mois, quand quelqu'un remplacera la valeur sans déplacer
  # la ligne.
  "Clé de paiement de test:::(sk|pk)_test_[A-Za-z0-9]{16,}"
  "Clé de paiement de test (ordre inverse):::test_(sk|pk)_[A-Za-z0-9]{16,}"
  "Clé Google/Firebase:::AIza[0-9A-Za-z_-]{35}"
  "Clé applicative Laravel:::APP_KEY=base64:[A-Za-z0-9+/=]{40,}"
  # `[[:space:]]` et non `\s` : le grep BSD (macOS) ne connaît pas `\s`, et ce
  # script doit tourner à l'identique en local et en CI.
  # `[=,]` couvre aussi bien `API_KEY = '…'` que `define('API_KEY', '…')`.
  "Secret assigné en dur:::(SECRET|PASSWORD|API_KEY|TOKEN)[A-Z_]*['\"]?[[:space:]]*[=,][[:space:]]*['\"][^'\"[:space:]]{16,}['\"]"
)

# Fichiers exclus : le scanner lui-même (il contient les motifs) et les binaires.
EXCLUDE_RE='^(\.github/scan-secrets\.sh|.*\.(pdf|docx|pptx|png|jpg|jpeg|gif|ico|lock))$'

# Lignes exclues : `env('X', 'défaut')` et `config('x.y')` LISENT une valeur, ils
# ne la codent pas en dur. C'est le motif normal des fichiers `config/` Laravel.
LINE_ALLOW_RE="(env\(|config\()"

# `mapfile` n'existe qu'en bash 4+ : un poste macOS livre bash 3.2, et le script
# doit se lancer exactement comme en CI.
FILES=()
while IFS= read -r f; do FILES+=("$f"); done < <(git ls-files | grep -Ev "$EXCLUDE_RE")
[ ${#FILES[@]} -eq 0 ] && { echo "Aucun fichier à scanner."; exit 0; }

found=0
for entry in "${PATTERNS[@]}"; do
  label="${entry%%:::*}"
  regex="${entry##*:::}"
  # `-e` est indispensable : le motif PEM commence par des tirets et serait
  # sinon interprété comme des options de grep.
  hits=$(grep -EnI -e "$regex" -- "${FILES[@]}" 2>/dev/null | grep -Ev "$LINE_ALLOW_RE")
  if [ -n "$hits" ]; then
    echo "::error::Secret potentiel détecté — $label"
    echo "$hits" | sed 's/^/    /'
    found=1
  fi
done

if [ "$found" -eq 1 ]; then
  echo
  echo "Un secret ne se retire pas par un simple commit correctif :"
  echo "  1. RÉVOQUER la clé chez le fournisseur (l'historique git la garde)."
  echo "  2. La remplacer, puis retirer la valeur du code."
  exit 1
fi

echo "✅ Aucun secret détecté dans ${#FILES[@]} fichiers suivis."

# ⚠️ Ce scanner se teste DANS LES DEUX SENS, sinon il n'est qu'un décor : 0 faux
# positif sur le dépôt réel, ET détection d'un faux secret de chaque motif qu'on
# y glisse temporairement. Le second test est le seul qui prouve qu'il marche.
