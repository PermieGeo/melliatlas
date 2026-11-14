"""Tests for typed completed-snapshot round trips independent of any database."""

import json
from datetime import date

import pytest

from melliatlas.jobs.api import (
    InMemoryInvestigationService,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
    deserialize_completed_snapshot,
    serialize_completed_snapshot,
)
from melliatlas.planning.api import TimeWindow
from melliatlas.sources.api import SYNTHETIC_SCENARIO_ID, SyntheticFixtureProvider
from melliatlas.territories.api import CountryCode


def _completed(*, evidence_limited: bool = False) -> InvestigationSnapshot:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    request = InvestigationRequest(
        country=CountryCode.RU,
        territory_id="ru:region:smolensk",
        scenario_id=SYNTHETIC_SCENARIO_ID,
        season=TimeWindow(
            date(2026, 5, 10),
            date(2026, 5, 10) if evidence_limited else date(2026, 8, 15),
        ),
        starting_point=(32.0, 54.0),
    )
    queued = service.submit(request)
    service.process(queued.id)
    finished = service.get(queued.id)
    assert finished is not None
    return finished


@pytest.mark.parametrize("evidence_limited", [False, True])
def test_roundtrip_preserves_typed_result_and_private_start(evidence_limited: bool) -> None:
    original = _completed(evidence_limited=evidence_limited)
    restored = deserialize_completed_snapshot(serialize_completed_snapshot(original))
    assert restored == original
    assert restored.status == InvestigationStatus.COMPLETED
    assert restored.request.starting_point == (32.0, 54.0)
    assert restored.outcome == (
        InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
        if evidence_limited
        else InvestigationOutcomeKind.PLAN_FOUND
    )


def test_codec_refuses_non_completed_and_malformed_payloads() -> None:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    pending = service.submit(
        InvestigationRequest(
            CountryCode.RU,
            "ru:region:smolensk",
            SYNTHETIC_SCENARIO_ID,
            TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            None,
        )
    )
    with pytest.raises(ValueError, match="Only completed"):
        serialize_completed_snapshot(pending)
    with pytest.raises((ValueError, TypeError)):
        deserialize_completed_snapshot("[]")
    with pytest.raises((ValueError, KeyError)):
        deserialize_completed_snapshot('{"status":"COMPLETED"}')
    with pytest.raises(ValueError, match="not a completed"):
        deserialize_completed_snapshot(
            serialize_completed_snapshot(_completed()).replace(
                '"status": "COMPLETED"', '"status": "RUNNING"'
            )
        )


@pytest.mark.parametrize(
    ("section", "field", "bad_value"),
    [
        ("request", "starting_point", [32.0]),
        ("request", "starting_point", [True, 54.0]),
        ("request", "season", "2026-06-01"),
        ("plan", "relocations", "1"),
        ("plan", "stops", "not-a-list"),
        ("evidence", "synthetic", False),
        ("evidence", "source_mode", "LIVE"),
    ],
)
def test_codec_rejects_malformed_nested_fields(section: str, field: str, bad_value: object) -> None:
    payload = json.loads(serialize_completed_snapshot(_completed()))
    if section == "evidence":
        payload["evidence"][0][field] = bad_value
    else:
        payload[section][field] = bad_value
    with pytest.raises((ValueError, TypeError)):
        deserialize_completed_snapshot(json.dumps(payload))


def test_codec_rejects_bad_snapshot_object_and_nonfinite_coordinate() -> None:
    original = json.loads(serialize_completed_snapshot(_completed()))
    original["request"]["starting_point"] = [float("nan"), 54.0]
    with pytest.raises(ValueError, match="finite number"):
        deserialize_completed_snapshot(json.dumps(original))
