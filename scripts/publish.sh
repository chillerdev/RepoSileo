#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${1:-}"
MESSAGE="${2:-Update Sileo repository}"
"$ROOT/scripts/update-repo.sh"
cd "$ROOT"
test -d .git || git init -b main
if [[ -n "$REMOTE" ]]; then
  git remote get-url origin >/dev/null 2>&1 && git remote set-url origin "$REMOTE" || git remote add origin "$REMOTE"
fi
git remote get-url origin >/dev/null 2>&1 || { echo "Thieu remote GitHub."; exit 1; }
git add --all
git diff --cached --quiet || git commit -m "$MESSAGE"
git push -u origin main
