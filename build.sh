#!/bin/sh
set -eu

cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1

if [ -f backend/pyproject.toml ]; then
    printf '%s\n' '==> Python backend static checks'
    python3 -m ruff check --no-cache backend/src backend/scripts
    python3 -m ruff format --check backend/src backend/scripts
    python3 -m pyright --project backend backend/src

    printf '%s\n' '==> Python syntax and offline application startup'
    python3 -B -c '
from pathlib import Path

for directory in (Path("backend/src"), Path("backend/scripts")):
    for path in directory.rglob("*.py"):
        compile(path.read_bytes(), str(path), "exec")
'
    (
        unset MELLIATLAS_DATABASE_URL MELLIATLAS_REFERENCE_SNAPSHOT MELLIATLAS_REFERENCE_INVENTORY
        export MELLIATLAS_SOURCE_PROVIDER=disabled
        export MELLIATLAS_SATURN_LIVE_ENABLED=false
        export MELLIATLAS_WEATHER_LIVE_ENABLED=false
        PYTHONPATH=backend/src python3 -B -c '
import asyncio
from melliatlas.main import app

async def check_startup() -> None:
    async with app.router.lifespan_context(app):
        if not any(getattr(route, "path", None) == "/health" for route in app.routes):
            raise RuntimeError("Application health route is unavailable")

asyncio.run(check_startup())
'
    )
else
    printf '%s\n' '==> Python backend: manifest not yet present'
fi

if [ -f web/package.json ]; then
    printf '%s\n' '==> React frontend static checks and production build'
    (
        cd web
        ./node_modules/.bin/prettier --check src index.html package.json tsconfig.json vite.config.ts
        ./node_modules/.bin/eslint src
        ./node_modules/.bin/tsc -p ../tsconfig.build.json --noEmit
        ./node_modules/.bin/vite build
    )
else
    printf '%s\n' '==> React frontend: manifest not yet present'
fi
