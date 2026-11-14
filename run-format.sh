#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
export PYTHONDONTWRITEBYTECODE=1

if [[ -f backend/pyproject.toml ]]; then
    printf '%s\n' '==> Format Python backend'
    python3 -m ruff check --fix --no-cache backend
    python3 -m ruff format backend
fi
