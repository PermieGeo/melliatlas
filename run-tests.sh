#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
export PYTHONDONTWRITEBYTECODE=1

printf '%s\n' '==> Documentation and specification checks'
python3 -B -m unittest discover -s tests -p 'test_*.py' -v

if [[ -f backend/pyproject.toml ]]; then
    printf '%s\n' '==> Python backend checks'
    python3 -B -m pytest -p no:cacheprovider backend/tests
    python3 -m ruff check --no-cache backend
    python3 -m ruff format --check backend
    python3 -m pyright backend
else
    printf '%s\n' '==> Python backend: manifest not yet present'
fi

if [[ -f web/package.json ]]; then
    printf '%s\n' '==> React frontend checks'
    (
        cd web
        npm run lint
        npm run typecheck
        npm run test:ci
    )
else
    printf '%s\n' '==> React frontend: manifest not yet present'
fi
