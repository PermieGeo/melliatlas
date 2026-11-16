"""Independent fixture and lifecycle checks for bounded V01 analysis."""

from datetime import date
from uuid import UUID

import pytest
from pytest import MonkeyPatch

from melliatlas.jobs import implementation as job_implementation
from melliatlas.jobs.api import (
    InMemoryInvestigationService,
    InvalidInvestigationRequest,
    InvestigationRequest,
    InvestigationStatus,
)
from melliatlas.planning.api import TimeWindow, build_season_plan
from melliatlas.sources.providers.synthetic.api import SyntheticFixtureProvider
from melliatlas.territories.api import CountryCode


def _request(window: TimeWindow | None = None) -> InvestigationRequest:
    return InvestigationRequest(
        country=CountryCode.RU,
        territory_id="ru:region:smolensk",
        scenario_id="synthetic-ru-2026-v01",
        season=window or TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
        starting_point=None,
    )


def test_window_rejects_reversal_and_includes_same_day() -> None:
    with pytest.raises(ValueError):
        TimeWindow(date(2026, 5, 2), date(2026, 5, 1))
    assert TimeWindow(date(2026, 5, 1), date(2026, 5, 1)).start == date(2026, 5, 1)


def test_fixture_candidates_have_stable_evidence_and_order_independent_results() -> None:
    scenario = SyntheticFixtureProvider().load(
        country=CountryCode.RU,
        territory_id="ru:region:smolensk",
        scenario_id="synthetic-ru-2026-v01",
    )
    assert scenario is not None
    assert len(scenario.candidates) == 3
    assert all(
        candidate.evidence_id in {item.id for item in scenario.evidence}
        for candidate in scenario.candidates
    )
    window = TimeWindow(date(2026, 5, 1), date(2026, 8, 15))
    forward = build_season_plan(scenario.candidates, window)
    backward = build_season_plan(tuple(reversed(scenario.candidates)), window)
    assert forward == backward
    assert forward is not None
    assert len(forward.stops) == 3
    assert forward.relocations == 2
    for before, after in zip(forward.stops, forward.stops[1:]):
        assert before.window.end < after.window.start


def test_interim_state_is_readable_and_completed_history_is_immutable() -> None:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    created = service.submit(_request())
    assert isinstance(created.id, UUID)
    assert created.status == InvestigationStatus.QUEUED
    assert created.plan is None
    assert service.get(created.id) == created
    service.process(created.id)
    finished = service.get(created.id)
    assert finished is not None
    assert finished.status == InvestigationStatus.COMPLETED
    assert finished.plan is not None
    service.process(created.id)
    assert service.get(created.id) == finished
    assert service.record_count == 1


def test_invalid_fixture_never_creates_record() -> None:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    invalid = InvestigationRequest(
        country=CountryCode.BY,
        territory_id="ru:region:smolensk",
        scenario_id="synthetic-ru-2026-v01",
        season=TimeWindow(date(2026, 5, 1), date(2026, 8, 1)),
        starting_point=None,
    )
    with pytest.raises(InvalidInvestigationRequest):
        service.submit(invalid)
    assert service.record_count == 0


def test_each_application_owns_a_separate_nondurable_job_store() -> None:
    first = InMemoryInvestigationService(SyntheticFixtureProvider())
    second = InMemoryInvestigationService(SyntheticFixtureProvider())
    saved = first.submit(_request())
    assert second.get(saved.id) is None


def test_processing_fault_reports_failed_without_leaking_exception(
    monkeypatch: MonkeyPatch,
) -> None:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    queued = service.submit(_request())

    def fail(_candidates: object, _season: object) -> None:
        raise RuntimeError("internal secret to keep private")

    monkeypatch.setattr(job_implementation, "build_season_plan", fail)
    service.process(queued.id)
    failed = service.get(queued.id)
    assert failed is not None
    assert failed.status == InvestigationStatus.FAILED
    assert failed.outcome is None
    assert failed.plan is None
    assert failed.diagnostics == ("Synthetic analysis failed",)
    service.process(queued.id)
    assert service.get(queued.id) == failed
