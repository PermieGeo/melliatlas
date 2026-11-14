"""Offline normalized JSON import must validate independently supplied coverage."""

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

import pytest
from pydantic import ValidationError

from melliatlas.api.reference_loader import read_reference_documents, write_reference_report
from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import ExpectedInventory, ReferenceSnapshot


def _write_inputs(
    directory: Path, reference: ReferenceSnapshot, inventory: ExpectedInventory
) -> tuple[Path, Path]:
    snapshot_path = directory / "snapshot.json"
    inventory_path = directory / "independent-inventory.json"
    snapshot_path.write_text(json.dumps(asdict(reference), default=str), encoding="utf-8")
    inventory_path.write_text(
        json.dumps(
            {
                "region_ids": {
                    country.value: sorted(ids) for country, ids in inventory.region_ids.items()
                },
                "pilot_district_ids": {
                    region: sorted(ids) for region, ids in inventory.pilot_district_ids.items()
                },
                "source_uri": inventory.source_uri,
                "version": inventory.version,
            }
        ),
        encoding="utf-8",
    )
    return snapshot_path, inventory_path


def test_normalized_files_load_and_preserve_reference_metadata(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory], tmp_path: Path
) -> None:
    snapshot_path, inventory_path = _write_inputs(tmp_path, *reference_case)
    loaded, expected = read_reference_documents(snapshot_path, inventory_path)
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(loaded, expected))
    report = write_reference_report(loaded, expected)
    assert report["reference_id"] == "SYNTHETIC-TEST-ONLY"
    assert report["region_count"] == 5
    assert report["district_count"] == 2


def test_import_rejects_undeclared_json_fields(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory], tmp_path: Path
) -> None:
    snapshot_path, inventory_path = _write_inputs(tmp_path, *reference_case)
    data: dict[str, object] = json.loads(snapshot_path.read_text(encoding="utf-8"))
    data["unrecognized_field"] = "not permitted"
    snapshot_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        read_reference_documents(snapshot_path, inventory_path)
