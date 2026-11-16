#!/bin/sh
set -eu

cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1

if [ -f backend/pyproject.toml ]; then
    printf '%s\n' '==> Format Python backend'
    python3 -m ruff check --fix --no-cache backend
    python3 -m ruff format backend
fi

if [ -f web/package.json ]; then
    printf '%s\n' '==> Format React Web client'
    (
        cd web
        npm run format
    )
fi
