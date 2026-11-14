"""Architecture regression tests for allowed imports and capability boundaries."""

from pathlib import Path

import pytest

from .import_policy import ALLOWED_DEPENDENCIES, find_violations

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src"


def _violations(tmp_path: Path, owner: str, statement: str) -> list[str]:
    path = tmp_path / "melliatlas" / owner / "api.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(statement + "\n", encoding="utf-8")
    return find_violations(tmp_path)


def test_real_source_respects_module_boundaries() -> None:
    assert find_violations(SOURCE_ROOT) == []


def test_dependency_matrix_matches_current_implementation_plan() -> None:
    # This independently locked policy must change only with an approved dependency review.
    assert ALLOWED_DEPENDENCIES == {
        "territories": frozenset(),
        "planning": frozenset({"territories"}),
        "sources": frozenset({"territories", "planning"}),
        "analyzers": frozenset({"territories", "sources", "planning"}),
        "engine": frozenset({"sources", "analyzers", "planning"}),
        "agent": frozenset({"engine", "planning", "sources"}),
        "jobs": frozenset({"agent", "engine", "planning", "territories"}),
        "persistence": frozenset({"jobs", "territories"}),
        "api": frozenset(
            {
                "territories",
                "planning",
                "sources",
                "analyzers",
                "engine",
                "agent",
                "jobs",
                "persistence",
            }
        ),
    }


@pytest.mark.parametrize(
    ("owner", "statement", "reason"),
    [
        ("agent", "from melliatlas.engine.executor import run", "private module"),
        ("agent", "from melliatlas.engine import executor", "private module"),
        ("agent", "from ..engine.executor import run", "private module"),
        ("agent", "import melliatlas.engine.executor", "private module"),
        ("agent", "from ..engine import executor", "private module"),
        ("agent", "from melliatlas.api.api import create_app", "forbidden dependency"),
        ("agent", "from .. import api", "forbidden dependency"),
        ("agent", "from melliatlas import api", "forbidden dependency"),
        ("api", "import httpx", "network client"),
        ("api", "from melliatlas.territories.api.helpers import x", "private module"),
        ("territories", "from melliatlas.agent.api import Planner", "forbidden dependency"),
        ("engine", "from melliatlas.agent.api import Planner", "forbidden dependency"),
        ("planning", "from melliatlas.persistence.api import Store", "forbidden dependency"),
        (
            "api",
            "from melliatlas.territories.validation import validate_reference",
            "private module",
        ),
        ("api", "from melliatlas.territories import catalog", "private module"),
        ("api", "from melliatlas.territories.api import *", "wildcard capability"),
        ("agent", "import httpx", "network client"),
        ("sources", "from urllib import request", "network client"),
        ("analyzers", "from http import client", "network client"),
        ("territories", "from sqlalchemy import text", "database"),
        ("api", "import psycopg", "database"),
        ("agent", "import fastapi", "framework"),
        ("planning", "from pydantic import BaseModel", "framework"),
    ],
)
def test_forbidden_import_mutations_are_detected(
    tmp_path: Path, owner: str, statement: str, reason: str
) -> None:
    assert any(reason in issue for issue in _violations(tmp_path, owner, statement))


@pytest.mark.parametrize(
    ("owner", "statement"),
    [
        ("agent", "from melliatlas.engine.api import ExecutionResult"),
        ("agent", "from ..engine.api import ExecutionResult"),
        ("api", "from melliatlas.territories.api import CountryCode"),
        ("planning", "from melliatlas.territories.api import Territory"),
        ("planning", "from .api import LocalValue"),
        ("sources", "from urllib.parse import urlsplit"),
        ("persistence", "import psycopg"),
        ("api", "from pydantic import BaseModel"),
    ],
)
def test_permitted_imports_are_not_rejected(tmp_path: Path, owner: str, statement: str) -> None:
    assert _violations(tmp_path, owner, statement) == []


def test_explicit_facade_export_is_permitted(tmp_path: Path) -> None:
    facade = tmp_path / "melliatlas" / "territories" / "__init__.py"
    facade.parent.mkdir(parents=True)
    facade.write_text('__all__ = ["PublicType"]\n', encoding="utf-8")
    assert _violations(tmp_path, "planning", "from melliatlas.territories import PublicType") == []
    assert _violations(tmp_path, "planning", "from melliatlas import territories") == []
    assert _violations(tmp_path, "planning", "import melliatlas.territories") == []
    assert any(
        "private module" in issue
        for issue in _violations(
            tmp_path, "planning", "from melliatlas.territories import internal"
        )
    )


def test_rejects_dependency_cycle(tmp_path: Path) -> None:
    _violations(tmp_path, "agent", "from melliatlas.engine.api import Value")
    issues = _violations(tmp_path, "engine", "from melliatlas.agent.api import Value")
    assert any("dependency cycle" in issue for issue in issues)


def test_rejects_relative_import_outside_package(tmp_path: Path) -> None:
    assert any(
        "relative import escapes package" in issue
        for issue in _violations(tmp_path, "agent", "from ....engine.api import Value")
    )


def test_relative_import_from_package_initializer_is_resolved(tmp_path: Path) -> None:
    path = tmp_path / "melliatlas" / "agent" / "__init__.py"
    path.parent.mkdir(parents=True)
    path.write_text("from ..engine.executor import run\n", encoding="utf-8")
    assert any("private module" in issue for issue in find_violations(tmp_path))
