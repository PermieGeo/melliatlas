"""Validate that feature ownership references real behavior, not scaffolding."""

from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROSS_REF = ROOT / "docs/specs/feature-cross-ref.yaml"
SCHEMA = ROOT / "docs/specs/feature-cross-ref.schema.json"


def parse_feature_entries(source: str) -> list[dict[str, object]]:
    """Parse the repository's deliberately limited cross-reference YAML layout."""
    entries: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    active_list: str | None = None
    for line in source.splitlines():
        if line in {"schema_version: 2", "features:", ""}:
            continue
        if line.startswith("  - feature_id: "):
            current = {"feature_id": line.removeprefix("  - feature_id: ")}
            entries.append(current)
            active_list = None
        elif current is not None and line.startswith("    implementation_status: "):
            current["implementation_status"] = line.removeprefix("    implementation_status: ")
            active_list = None
        elif current is not None and line.startswith("    stages: ["):
            current["stages"] = _inline_list(line)
            active_list = None
        elif current is not None and line.startswith("    spec_paths: ["):
            current["spec_paths"] = _inline_list(line)
            active_list = None
        elif current is not None and line in {"    owners: []", "    test_files: []"}:
            active_list = line.strip().split(":", 1)[0]
            current[active_list] = []
        elif current is not None and line in {"    owners:", "    test_files:"}:
            active_list = line.strip()[:-1]
            current[active_list] = []
        elif current is not None and line.startswith("      - ") and active_list is not None:
            values = current[active_list]
            if not isinstance(values, list):
                raise ValueError("Invalid cross-reference sequence")
            values.append(line.removeprefix("      - "))
        else:
            raise ValueError(f"Unsupported cross-reference layout: {line}")
    return entries


def _inline_list(line: str) -> list[str]:
    value = line.split(": ", 1)[1]
    if not value.startswith("[") or not value.endswith("]"):
        raise ValueError(f"Invalid inline list: {line}")
    return [item.strip() for item in value[1:-1].split(",") if item.strip()]


def traceability_errors(source: str, root: Path) -> list[str]:
    """Detect inaccurate feature maturity, nonexistent symbols, and stale file links."""
    errors: list[str] = []
    try:
        entries = parse_feature_entries(source)
    except ValueError as exc:
        return [str(exc)]
    catalog = (root / "docs/FEATURES.md").read_text(encoding="utf-8")
    known = set(re.findall(r"(?m)^\| `([A-Z0-9_.]+)` \|", catalog))
    seen: set[str] = set()
    for entry in entries:
        feature_id = str(entry.get("feature_id", ""))
        status = entry.get("implementation_status")
        owners = entry.get("owners")
        tests = entry.get("test_files")
        specs = entry.get("spec_paths")
        if feature_id in seen:
            errors.append(f"{feature_id}: duplicate feature ID")
        seen.add(feature_id)
        if feature_id not in known:
            errors.append(f"{feature_id}: not in feature catalog")
        if status not in {"planned", "partial", "verified"}:
            errors.append(f"{feature_id}: invalid or missing implementation_status")
        if not isinstance(owners, list) or not isinstance(tests, list):
            errors.append(f"{feature_id}: owners and test_files must be lists")
            continue
        if status == "planned" and (owners or tests):
            errors.append(f"{feature_id}: planned feature cannot claim implementation owners/tests")
        if status in {"partial", "verified"} and (not owners or not tests):
            errors.append(f"{feature_id}: {status} feature requires code and test owners")
        if not isinstance(specs, list) or not specs:
            errors.append(f"{feature_id}: missing specifications")
            continue
        for link in specs + tests:
            if not isinstance(link, str) or not (root / link).is_file():
                errors.append(f"{feature_id}: missing linked file {link}")
        for owner in owners:
            if not isinstance(owner, str):
                errors.append(f"{feature_id}: invalid owner entry")
                continue
            file_name, sep, symbol = owner.partition("#")
            file_path = root / file_name
            if not file_path.is_file():
                errors.append(f"{feature_id}: missing owner path {file_name}")
                continue
            if sep:
                if file_path.suffix != ".py":
                    errors.append(f"{feature_id}: symbol reference is not Python: {owner}")
                    continue
                module = ast.parse(file_path.read_text(encoding="utf-8"), filename=file_name)
                declared = {
                    node.name
                    for node in module.body
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                }
                if symbol not in declared:
                    errors.append(f"{feature_id}: missing public symbol {owner}")
    return errors


class FeatureTraceabilityTests(unittest.TestCase):
    def test_schema_requires_explicit_implementation_status(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        entry = schema["properties"]["features"]["items"]
        self.assertIn("implementation_status", entry["required"])
        self.assertEqual(
            ["planned", "partial", "verified"],
            entry["properties"]["implementation_status"]["enum"],
        )

    def test_every_record_links_real_owners_and_tests(self) -> None:
        self.assertEqual([], traceability_errors(CROSS_REF.read_text(encoding="utf-8"), ROOT))

    def test_scaffold_is_not_investigation_or_map_implementation(self) -> None:
        records = {
            str(entry["feature_id"]): entry
            for entry in parse_feature_entries(CROSS_REF.read_text(encoding="utf-8"))
        }
        for feature_id in ("WEB.INVESTIGATIONS", "MAP.BASEMAP"):
            with self.subTest(feature_id=feature_id):
                self.assertEqual("planned", records[feature_id]["implementation_status"])
                self.assertEqual([], records[feature_id]["owners"])
        for feature_id in ("GEOGRAPHY.RU_REGIONS", "GEOGRAPHY.BY_REGIONS",
                           "GEOGRAPHY.PILOT_DISTRICTS", "DATA.PROVENANCE"):
            with self.subTest(feature_id=feature_id):
                self.assertEqual("partial", records[feature_id]["implementation_status"])

    def test_false_implementation_owner_is_rejected(self) -> None:
        source = CROSS_REF.read_text(encoding="utf-8").replace(
            "backend/src/melliatlas/territories/api.py#TerritoryCatalog",
            "backend/src/melliatlas/territories/api.py#NonexistentCatalog",
            1,
        )
        self.assertTrue(any("missing public symbol" in error for error in traceability_errors(source, ROOT)))

    def test_premature_implementation_claim_is_rejected(self) -> None:
        source = CROSS_REF.read_text(encoding="utf-8").replace(
            "  - feature_id: WEB.INVESTIGATIONS\n    implementation_status: planned",
            "  - feature_id: WEB.INVESTIGATIONS\n    implementation_status: partial",
            1,
        )
        self.assertTrue(any("partial feature requires" in error for error in traceability_errors(source, ROOT)))

    def test_planned_feature_cannot_claim_health_as_owner(self) -> None:
        source = CROSS_REF.read_text(encoding="utf-8").replace(
            "  - feature_id: WEB.INVESTIGATIONS\n    implementation_status: planned\n    stages: [MVP-01]\n"
            "    spec_paths: [docs/specs/active/subspecs/subspec-01-backend-planning.md]\n"
            "    owners: []\n    test_files: []",
            "  - feature_id: WEB.INVESTIGATIONS\n    implementation_status: planned\n    stages: [MVP-01]\n"
            "    spec_paths: [docs/specs/active/subspecs/subspec-01-backend-planning.md]\n"
            "    owners:\n      - backend/src/melliatlas/api/app.py#create_app\n"
            "    test_files:\n      - backend/tests/contract/test_api_smoke.py",
            1,
        )
        self.assertTrue(any("planned feature cannot claim" in error for error in traceability_errors(source, ROOT)))


if __name__ == "__main__":
    unittest.main()
