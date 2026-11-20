#!/bin/sh
set -eu

cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1

printf '%s\n' '==> Documentation and specification tests'
python3 -B -m unittest discover -s tests -p 'test_*.py' -v

if [ -f backend/pyproject.toml ]; then
    printf '%s\n' '==> Python backend tests'
    python3 -B -m pytest -p no:cacheprovider backend/tests
else
    printf '%s\n' '==> Python backend: manifest not yet present'
fi

if [ -f web/package.json ]; then
    printf '%s\n' '==> React frontend tests'
    (
        cd web
        npm run test:ci
    )
else
    printf '%s\n' '==> React frontend: manifest not yet present'
fi
