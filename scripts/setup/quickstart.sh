#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if command -v python3 >/dev/null 2>&1; then
  python3 "$REPO_ROOT/scripts/setup/quickstart.py" --run "$@"
elif command -v python >/dev/null 2>&1; then
  python "$REPO_ROOT/scripts/setup/quickstart.py" --run "$@"
else
  echo "Python 3.10+ was not found in PATH." >&2
  exit 1
fi
