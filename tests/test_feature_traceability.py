"""Validate feature ownership against schema and developer-controlled acceptance."""

from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CROSS_REF = ROOT / "docs/specs/feature-cross-ref.yaml"
SCHEMA = ROOT / "docs/specs/feature-cross-ref.schema.json"
STATE = ROOT / "docs/specs/STATE.json"


class _StrictSafeLoader(yaml.SafeLoader):
    """Reject duplicate mapping fields instead of silently overriding approval data."""


def _unique_mapping(loader: _StrictSafeLoader, node: yaml.MappingNode) -> dict[str, object]:
    result: dict[str, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError(f"Duplicate YAML mapping key: {key}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


_StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _schema_errors(instance: object, schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: str(list(item.absolute_path)))
    ]


def parse_feature_entries(source: str) -> list[dict[str, object]]:
    """Parse ordinary YAML and validate the full cross-reference schema."""
    try:
        parsed: object = yaml.load(source, Loader=_StrictSafeLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid cross-reference YAML: {exc}") from exc
    errors = _schema_errors(parsed, SCHEMA)
    if errors:
        raise ValueError("Invalid feature cross-reference schema: " + "; ".join(errors))
    assert isinstance(parsed, dict)
    entries = parsed["features"]
    assert isinstance(entries, list)
    return entries


def _file_exists(root: Path, relative: str) -> bool:
    path = (root / relative).resolve()
    return path.is_relative_to(root.resolve()) and path.is_file()


def traceability_errors(
    source: str, root: Path, checkpoint: dict[str, object] | None = None
) -> list[str]:
    """Check feature maturity, real code owners, and independently recorded acceptance."""
    try:
        entries = parse_feature_entries(source)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if checkpoint is None:
        checkpoint = json.loads((root / "docs/specs/STATE.json").read_text(encoding="utf-8"))
    state_errors = _schema_errors(checkpoint, root / "docs/specs/state.schema.json")
    if state_errors:
        return [f"Invalid acceptance checkpoint: {issue}" for issue in state_errors]

    catalog = (root / "docs/FEATURES.md").read_text(encoding="utf-8")
    known = set(re.findall(r"(?m)^\| `([A-Z0-9_.]+)` \|", catalog))
    specs = (root / "docs/specs/active/subspecs/subspec-01-backend-planning.md").read_text(
        encoding="utf-8"
    )
    umbrella = (root / "docs/specs/umbrella_spec_melliatlas.md").read_text(
        encoding="utf-8"
    )
    known_acceptance = set(re.findall(r"\bMVP01-BE-A\d{2}\b", specs)) | set(
        re.findall(r"\bMVP-\d{2}\.A\d{2}\b", umbrella)
    )
    recorded: dict[str, dict[str, object]] = {}
    for record in checkpoint["featureAcceptances"]:
        feature_id = record["featureId"]
        if feature_id in recorded:
            errors.append(f"{feature_id}: duplicate feature acceptance record")
        recorded[feature_id] = record
        if feature_id not in known:
            errors.append(f"{feature_id}: accepted feature is not in feature catalog")
        for acceptance_id in record["acceptanceIds"]:
            if acceptance_id not in known_acceptance:
                errors.append(f"{feature_id}: unknown accepted criterion {acceptance_id}")
        for path in [*record["evidenceFiles"], record["approvalReference"]]:
            if not _file_exists(root, path):
                errors.append(f"{feature_id}: missing acceptance evidence or approval reference {path}")

    seen: set[str] = set()
    for entry in entries:
        feature_id = entry["feature_id"]
        status = entry["implementation_status"]
        owners = entry["owners"]
        tests = entry["test_files"]
        if feature_id in seen:
            errors.append(f"{feature_id}: duplicate feature ID")
        seen.add(feature_id)
        if feature_id not in known:
            errors.append(f"{feature_id}: not in feature catalog")
        if status == "planned" and (owners or tests):
            errors.append(f"{feature_id}: planned feature cannot claim implementation owners/tests")
        if status in {"partial", "verified"} and (not owners or not tests):
            errors.append(f"{feature_id}: {status} feature requires code and test owners")
        if status == "verified" and feature_id not in recorded:
            errors.append(f"{feature_id}: verified feature lacks developer acceptance record")
        if feature_id in recorded and status != "verified":
            errors.append(f"{feature_id}: accepted feature must have verified status")
        for link in [*entry["spec_paths"], *tests]:
            if not _file_exists(root, link):
                errors.append(f"{feature_id}: missing linked file {link}")
        for owner in owners:
            file_name, sep, symbol = owner.partition("#")
            file_path = root / file_name
            if not _file_exists(root, file_name):
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
    for feature_id in recorded.keys() - seen:
        errors.append(f"{feature_id}: acceptance record has no feature entry")
    return errors


class FeatureTraceabilityTests(unittest.TestCase):
    def _source(self) -> str:
        return CROSS_REF.read_text(encoding="utf-8")

    def _checkpoint(self) -> dict[str, object]:
        return json.loads(STATE.read_text(encoding="utf-8"))

    def test_schema_requires_explicit_implementation_status(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        entry = schema["properties"]["features"]["items"]
        self.assertIn("implementation_status", entry["required"])
        self.assertEqual(
            ["planned", "partial", "verified"],
            entry["properties"]["implementation_status"]["enum"],
        )

    def test_every_record_links_real_owners_and_tests(self) -> None:
        self.assertEqual([], traceability_errors(self._source(), ROOT))

    def test_web_slice_is_partial_without_fabricating_validated_basemap(self) -> None:
        records = {entry["feature_id"]: entry for entry in parse_feature_entries(self._source())}
        for feature_id in ("WEB.INVESTIGATIONS", "WEB.MAP_TIMELINE"):
            with self.subTest(feature_id=feature_id):
                self.assertEqual("partial", records[feature_id]["implementation_status"])
                self.assertTrue(records[feature_id]["owners"])
                self.assertTrue(records[feature_id]["test_files"])
        self.assertEqual("planned", records["MAP.BASEMAP"]["implementation_status"])
        self.assertEqual([], records["MAP.BASEMAP"]["owners"])
        for feature_id in (
            "GEOGRAPHY.RU_REGIONS", "GEOGRAPHY.BY_REGIONS",
            "GEOGRAPHY.PILOT_DISTRICTS", "DATA.PROVENANCE",
        ):
            with self.subTest(feature_id=feature_id):
                self.assertEqual("partial", records[feature_id]["implementation_status"])

    def test_false_implementation_owner_is_rejected(self) -> None:
        source = self._source().replace(
            "backend/src/melliatlas/territories/api.py#TerritoryCatalog",
            "backend/src/melliatlas/territories/api.py#NonexistentCatalog",
            1,
        )
        self.assertTrue(
            any("missing public symbol" in error for error in traceability_errors(source, ROOT))
        )

    def test_premature_implementation_claim_is_rejected(self) -> None:
        source = self._source().replace(
            "  - feature_id: MAP.BASEMAP\n    implementation_status: planned",
            "  - feature_id: MAP.BASEMAP\n    implementation_status: partial",
            1,
        )
        self.assertTrue(
            any("partial feature requires" in error for error in traceability_errors(source, ROOT))
        )

    def test_planned_feature_cannot_claim_health_as_owner(self) -> None:
        source = self._source().replace(
            "  - feature_id: MAP.BASEMAP\n    implementation_status: planned\n    stages: [MVP-01]\n"
            "    spec_paths: [docs/specs/active/subspecs/subspec-01-backend-planning.md]\n"
            "    owners: []\n    test_files: []",
            "  - feature_id: MAP.BASEMAP\n    implementation_status: planned\n    stages: [MVP-01]\n"
            "    spec_paths: [docs/specs/active/subspecs/subspec-01-backend-planning.md]\n"
            "    owners:\n      - backend/src/melliatlas/api/app.py#create_app\n"
            "    test_files:\n      - backend/tests/contract/test_api_smoke.py",
            1,
        )
        self.assertTrue(
            any("planned feature cannot claim" in error for error in traceability_errors(source, ROOT))
        )

    def test_unaccepted_feature_cannot_become_verified(self) -> None:
        source = self._source().replace(
            "  - feature_id: GEOGRAPHY.RU_REGIONS\n    implementation_status: partial",
            "  - feature_id: GEOGRAPHY.RU_REGIONS\n    implementation_status: verified",
            1,
        )
        self.assertIn(
            "GEOGRAPHY.RU_REGIONS: verified feature lacks developer acceptance record",
            traceability_errors(source, ROOT),
        )

    def test_ordinary_yaml_syntax_is_supported(self) -> None:
        source = self._source().replace(
            "stages: [MVP-01]", "stages:\n      - MVP-01", 1
        ).replace("implementation_status: partial", 'implementation_status: "partial"', 1)
        self.assertEqual([], traceability_errors(source, ROOT))

    def test_duplicate_yaml_keys_are_rejected(self) -> None:
        source = self._source().replace(
            "    implementation_status: partial",
            "    implementation_status: partial\n    implementation_status: verified",
            1,
        )
        self.assertTrue(
            any("Duplicate YAML mapping key" in error for error in traceability_errors(source, ROOT))
        )

    def test_invalid_schema_and_unsafe_yaml_are_rejected(self) -> None:
        bad = self._source().replace("stages: [MVP-01]", "stages: deprecated", 1)
        self.assertTrue(any("schema" in error.lower() for error in traceability_errors(bad, ROOT)))
        self.assertTrue(
            any("YAML" in error for error in traceability_errors("features: !!python/object/apply:os.system ['echo unsafe']", ROOT))
        )

    def test_invalid_acceptance_record_is_rejected(self) -> None:
        state = self._checkpoint()
        state["featureAcceptances"] = [
            {
                "featureId": "GEOGRAPHY.RU_REGIONS",
                "acceptanceIds": ["MVP01-BE-A99"],
                "evidenceFiles": ["backend/tests/contract/test_territory_api.py"],
                "approvalReference": "docs/specs/README.md",
            }
        ]
        self.assertTrue(
            any("unknown accepted criterion" in error for error in traceability_errors(self._source(), ROOT, state))
        )

    def test_acceptance_record_does_not_leave_feature_partial(self) -> None:
        state = self._checkpoint()
        state["featureAcceptances"] = [
            {
                "featureId": "GEOGRAPHY.RU_REGIONS",
                "acceptanceIds": ["MVP01-BE-A02"],
                "evidenceFiles": ["backend/tests/contract/test_territory_api.py"],
                "approvalReference": "docs/specs/README.md",
            }
        ]
        self.assertIn(
            "GEOGRAPHY.RU_REGIONS: accepted feature must have verified status",
            traceability_errors(self._source(), ROOT, state),
        )

    def test_schema_rejects_acceptance_without_evidence(self) -> None:
        state = self._checkpoint()
        state["featureAcceptances"] = [{"featureId": "GEOGRAPHY.RU_REGIONS"}]
        self.assertTrue(
            any("Invalid acceptance checkpoint" in error for error in traceability_errors(self._source(), ROOT, state))
        )


if __name__ == "__main__":
    unittest.main()
