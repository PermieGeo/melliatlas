"""Static backend import policy derived from the active module dependency plan."""

import ast
from collections import defaultdict
from pathlib import Path

# These dependencies are direct imports, not transitive permission to reach an implementation.
ALLOWED_DEPENDENCIES: dict[str, frozenset[str]] = {
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

DATABASE_IMPORTS = frozenset(
    {"sqlalchemy", "psycopg", "psycopg2", "psycopg_pool", "asyncpg", "sqlite3", "geoalchemy2"}
)
FRAMEWORK_IMPORTS = frozenset({"fastapi", "starlette", "pydantic"})
NETWORK_IMPORTS = frozenset(
    {"httpx", "requests", "aiohttp", "urllib3", "urllib.request", "http.client", "socket"}
)


def _python_module(source_root: Path, path: Path) -> tuple[str, tuple[str, ...]]:
    parts = path.relative_to(source_root).with_suffix("").parts
    module = ".".join(parts)
    package = parts[:-1]
    if parts[-1] == "__init__":
        module = ".".join(parts[:-1])
    return module, package


def _resolve_relative(package: tuple[str, ...], level: int, module: str | None) -> str | None:
    if level > len(package):
        return None
    prefix = package[: len(package) - level + 1]
    suffix = module.split(".") if module else []
    return ".".join((*prefix, *suffix))


def _facade_exports(source_root: Path, capability: str) -> frozenset[str]:
    """Only literal __all__ exports authorize peer imports through a package facade."""
    path = source_root / "melliatlas" / capability / "__init__.py"
    if not path.is_file():
        return frozenset()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
            return frozenset()
        exports: set[str] = set()
        for item in node.value.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                return frozenset()
            exports.add(item.value)
        return frozenset(exports)
    return frozenset()


def _external_category(module: str) -> str | None:
    if module.split(".")[0] in DATABASE_IMPORTS:
        return "database"
    if module.split(".")[0] in FRAMEWORK_IMPORTS:
        return "framework"
    if module.split(".")[0] in NETWORK_IMPORTS:
        return "network"
    if module in {"urllib.request", "http.client"} or module.startswith(
        ("urllib.request.", "http.client.")
    ):
        return "network"
    return None


def find_violations(source_root: Path) -> list[str]:
    dependencies: dict[str, set[str]] = defaultdict(set)
    violations: list[str] = []
    facade_exports = {name: _facade_exports(source_root, name) for name in ALLOWED_DEPENDENCIES}

    for path in sorted(source_root.rglob("*.py")):
        source_module, package = _python_module(source_root, path)
        parts = source_module.split(".")
        if len(parts) < 2 or parts[0] != "melliatlas":
            continue
        owner = parts[1]
        if owner not in ALLOWED_DEPENDENCIES:
            continue
        dependencies.setdefault(owner, set())
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        def check_import(imported: str, line: int, member: str | None = None) -> None:
            # `from melliatlas import engine` names a capability through its imported member.
            if imported == "melliatlas" and member in ALLOWED_DEPENDENCIES:
                imported = f"melliatlas.{member}"
                member = None
            # From-imports can name a module, e.g. `from urllib import request`.
            external = _external_category(imported)
            if member is not None and external is None:
                external = _external_category(f"{imported}.{member}")
            if external == "database" and owner != "persistence":
                violations.append(f"{path}:{line}: {owner} imports database {imported}")
            elif external == "framework" and owner != "api":
                violations.append(f"{path}:{line}: {owner} imports framework {imported}")
            elif external == "network":
                violations.append(f"{path}:{line}: {owner} imports network client {imported}")

            imported_parts = imported.split(".")
            if len(imported_parts) < 2 or imported_parts[0] != "melliatlas":
                return
            target = imported_parts[1]
            if target not in ALLOWED_DEPENDENCIES or target == owner:
                return
            dependencies[owner].add(target)
            if target not in ALLOWED_DEPENDENCIES[owner]:
                violations.append(f"{path}:{line}: forbidden dependency {owner} -> {target}")
            if len(imported_parts) > 2 and (imported_parts[2] != "api" or len(imported_parts) > 3):
                violations.append(f"{path}:{line}: imports private module {imported}")
            elif len(imported_parts) == 2 and (
                (member is None and not facade_exports[target])
                or (member is not None and member not in facade_exports[target] and member != "api")
            ):
                detail = f".{member}" if member else " (no explicit facade)"
                violations.append(f"{path}:{line}: imports private module {imported}{detail}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    check_import(alias.name, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                imported = (
                    _resolve_relative(package, node.level, node.module)
                    if node.level
                    else node.module
                )
                if imported is None:
                    violations.append(f"{path}:{node.lineno}: relative import escapes package")
                    continue
                for alias in node.names:
                    if alias.name == "*" and imported.startswith("melliatlas."):
                        violations.append(
                            f"{path}:{node.lineno}: wildcard capability import {imported}"
                        )
                    check_import(imported, node.lineno, alias.name)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(capability: str) -> None:
        if capability in visiting:
            violations.append(f"dependency cycle detected at {capability}")
            return
        if capability in visited:
            return
        visiting.add(capability)
        for target in sorted(dependencies[capability]):
            visit(target)
        visiting.remove(capability)
        visited.add(capability)

    for capability in sorted(dependencies):
        visit(capability)
    return violations
