"""Verify reported hazard classes through the public completed-snapshot codec."""

import json
from datetime import date

import pytest

from melliatlas.jobs import (
    InMemoryInvestigationService,
    InvestigationRequest,
    InvestigationStatus,
    deserialize_completed_snapshot,
    serialize_completed_snapshot,
)
from melliatlas.planning import TimeWindow
from melliatlas.sources.providers.synthetic import SYNTHETIC_SCENARIO_ID, SyntheticFixtureProvider
from melliatlas.territories.api import CountryCode


def _snapshot_with_reported_hazard(hazard: object) -> str:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    queued = service.submit(
        InvestigationRequest(
            country=CountryCode.RU,
            territory_id="ru:region:smolensk",
            scenario_id=SYNTHETIC_SCENARIO_ID,
            season=TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            starting_point=None,
        )
    )
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None and completed.status is InvestigationStatus.COMPLETED

    payload = json.loads(serialize_completed_snapshot(completed))
    evidence = payload["evidence"][0]
    payload["treatment_review"] = {
        "screenings": [
            {
                "site_id": "fixture-site-alpha",
                "source_record_id": evidence["id"],
                "source_id": evidence["source_id"],
                "proximity": "OUTSIDE_SCREEN_RADIUS",
                "approximate_distance_km": None,
                "warnings": [],
                "captured_at": None,
                "scheduled_start": None,
                "scheduled_end": None,
                "source_uri": None,
                "products": [{"name": "Example", "crop": None, "bee_hazard_class": hazard}],
            }
        ],
        "avoided_site_ids": [],
        "warnings": [],
    }
    return json.dumps(payload)


@pytest.mark.parametrize("hazard", [1, 2, 3])
def test_stored_hazard_map_preserves_reported_class(hazard: int) -> None:
    restored = deserialize_completed_snapshot(_snapshot_with_reported_hazard(hazard))
    assert restored.treatment_review is not None
    assert restored.treatment_review.screenings[0].products[0].bee_hazard_class == hazard


@pytest.mark.parametrize("hazard", [True, False, 0, 4, "2", 2.0])
def test_stored_hazard_map_rejects_unverified_values(hazard: object) -> None:
    with pytest.raises(ValueError, match="bee hazard class"):
        deserialize_completed_snapshot(_snapshot_with_reported_hazard(hazard))


def test_stored_hazard_map_allows_unreported_value() -> None:
    restored = deserialize_completed_snapshot(_snapshot_with_reported_hazard(None))
    assert restored.treatment_review is not None
    assert restored.treatment_review.screenings[0].products[0].bee_hazard_class is None
