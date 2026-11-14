"""Architecture contract tests for API-only peer imports and acyclic dependencies."""

import ast
from collections import defaultdict
from pathlib import Path

CAPABILITIES = frozenset(
    {
        "territories",
        "planning",
        "sources",
        "analyzers",
        "engine",
        "agent",
        "jobs",
        "persistence",
        "api",
    }
)
FRAMEWORKS = frozenset({"fastapi", "pydantic", "sqlalchemy", "psycopg", "psycopg2"})


def find_violations(source_root: Path) -> list[str]:
    dependencies: dict[str, set[str]] = defaultdict(set)
    violations: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        source_module = ".".join(path.relative_to(source_root).with_suffix("").parts)
        parts = source_module.split(".")
        if len(parts) < 2 or parts[0] != "melliatlas":
            continue
        owner = parts[1]
        if owner not in CAPABILITIES:
            continue
        dependencies.setdefault(owner, set())
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.append(node.module)
        for imported in imports:
            first = imported.split(".")[0]
            if owner != "api" and first in FRAMEWORKS:
                violations.append(f"{path}: {owner} imports framework {first}")
            imported_parts = imported.split(".")
            if len(imported_parts) >= 3 and imported_parts[0] == "melliatlas":
                target = imported_parts[1]
                if target in CAPABILITIES and target != owner:
                    if imported_parts[2] not in {"api", "__init__"}:
                        violations.append(f"{path}: imports private module {imported}")
                    dependencies[owner].add(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            violations.append(f"dependency cycle detected at {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for target in sorted(dependencies[node]):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for owner in sorted(dependencies):
        visit(owner)
    return violations


SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src"


def test_module_import_boundaries() -> None:
    assert find_violations(SOURCE_ROOT) == []


def test_rejects_private_cross_module_import(tmp_path: Path) -> None:
    owned = tmp_path / "melliatlas" / "agent"
    owned.mkdir(parents=True)
    (owned / "api.py").write_text("from melliatlas.engine.executor import run\n", encoding="utf-8")
    assert any("private module" in item for item in find_violations(tmp_path))


def test_rejects_framework_in_domain(tmp_path: Path) -> None:
    owned = tmp_path / "melliatlas" / "planning"
    owned.mkdir(parents=True)
    (owned / "api.py").write_text("import fastapi\n", encoding="utf-8")
    assert any("imports framework" in item for item in find_violations(tmp_path))


def test_rejects_capability_cycles(tmp_path: Path) -> None:
    for capability, target in (("agent", "engine"), ("engine", "agent")):
        owned = tmp_path / "melliatlas" / capability
        owned.mkdir(parents=True)
        (owned / "api.py").write_text(
            f"from melliatlas.{target}.api import Value\n", encoding="utf-8"
        )
    assert any("cycle" in item for item in find_violations(tmp_path))
