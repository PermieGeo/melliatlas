"""Detect drift between approved HTTP operations and implemented public routes."""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/specs/active/subspecs/subspec-01-backend-planning.md"
ROUTES = ROOT / "backend/src/melliatlas/api/routes_territories.py"
APPLICATION = ROOT / "backend/src/melliatlas/api/app.py"


def territory_route_errors(spec: str, routes: str) -> list[str]:
    """Compare implemented territory paths with the normative contract subset."""
    errors: list[str] = []
    tree = ast.parse(routes)
    prefixes = [
        keyword.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "APIRouter"
        for keyword in node.keywords
        if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant)
        and isinstance(keyword.value.value, str)
    ]
    if len(prefixes) != 1:
        return ["Expected exactly one territory router prefix"]
    routes_by_path: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "get"
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "router"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                path = prefixes[0] + decorator.args[0].value
                routes_by_path[path] = {arg.arg for arg in node.args.args}
    for identifier in range(1, 5):
        reference = f"BE-API-{identifier:02d}"
        match = re.search(
            rf"(?m)^\| `{reference}` \| `GET ([^`]+)` \|", spec
        )
        if match is None:
            errors.append(f"{reference}: normative path missing")
            continue
        route_with_query = match.group(1).replace("\\|", "|")
        path, _, query = route_with_query.partition("?")
        if path not in routes_by_path:
            errors.append(f"{reference}: route {path} not implemented")
            continue
        if query:
            parameter = query.split("=", 1)[0]
            if parameter not in routes_by_path[path]:
                errors.append(f"{reference}: query parameter {parameter} missing")
    return errors


class ContractConsistencyTests(unittest.TestCase):
    def test_normative_territory_paths_match_implemented_routes(self) -> None:
        self.assertEqual(
            [],
            territory_route_errors(
                SPEC.read_text(encoding="utf-8"), ROUTES.read_text(encoding="utf-8")
            ),
        )

    def test_obsolete_district_path_is_detected(self) -> None:
        spec = SPEC.read_text(encoding="utf-8").replace(
            "/territories/districts?region_id=...", "/territories/{region_id}/districts", 1
        )
        self.assertTrue(any("BE-API-03" in issue for issue in territory_route_errors(
            spec, ROUTES.read_text(encoding="utf-8")
        )))

    def test_existing_application_factory_remains_backward_compatible(self) -> None:
        tree = ast.parse(APPLICATION.read_text(encoding="utf-8"))
        factory = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "create_app"
        )
        self.assertEqual(["settings", "territories"], [arg.arg for arg in factory.args.kwonlyargs])
        self.assertEqual(2, len(factory.args.kw_defaults))
        self.assertTrue(all(isinstance(default, ast.Constant) and default.value is None
                            for default in factory.args.kw_defaults))
        self.assertEqual([], factory.args.args)


if __name__ == "__main__":
    unittest.main()
