#!/bin/sh
# Canonical non-formatting check entry point for apatch CHK and local development.
set -eu
cd "$(dirname "$0")"

# Keep Python validation read-only, including transitive imports.
export PYTHONDONTWRITEBYTECODE=1

