"""Safety checks for the opt-in, write-capable PostGIS verification command."""

import os
import subprocess
import sys
from pathlib import Path


def test_real_postgis_verifier_requires_explicit_connection_string() -> None:
    backend = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    environment.pop("MELLIATLAS_TEST_POSTGIS_DSN", None)
    environment["PYTHONPATH"] = str(backend / "src")

    completed = subprocess.run(
        [sys.executable, "-B", str(backend / "scripts" / "verify_postgis_investigations.py")],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert completed.returncode != 0
    assert "MELLIATLAS_TEST_POSTGIS_DSN is required" in completed.stderr
