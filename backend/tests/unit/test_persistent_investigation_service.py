"""Contract tests for optional completed-store integration, not real PostGIS evidence."""

from datetime import date
from uuid import UUID

from melliatlas.jobs import (
    InMemoryInvestigationService,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
)
from melliatlas.planning import TimeWindow
from melliatlas.sources.providers.synthetic.api import (
    SYNTHETIC_SCENARIO_ID,
    SyntheticFixtureProvider,
)
from melliatlas.territories.api import CountryCode


class RecordingStore:
    def __init__(self) -> None:
        self.rows: dict[UUID, InvestigationSnapshot] = {}
        self.fail_write = False
        self.fail_read = False

    def save(self, snapshot: InvestigationSnapshot) -> None:
        assert snapshot.status == InvestigationStatus.COMPLETED
        if self.fail_write:
            raise OSError("unavailable database")
        if snapshot.id in self.rows:
            raise ValueError("duplicate result")
        self.rows[snapshot.id] = snapshot

    def load(self, identifier: UUID) -> InvestigationSnapshot | None:
        if self.fail_read:
            raise OSError("unavailable database")
        return self.rows.get(identifier)


def _request() -> InvestigationRequest:
    return InvestigationRequest(
        CountryCode.RU,
        "ru:region:smolensk",
        SYNTHETIC_SCENARIO_ID,
        TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
        None,
    )


def test_completed_result_reopens_with_a_fresh_service_instance() -> None:
    store = RecordingStore()
    first = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    queued = first.submit(_request())
    assert store.rows == {}
    first.process(queued.id)
    finished = first.get(queued.id)
    assert finished is not None
    assert finished.status == InvestigationStatus.COMPLETED
    assert set(store.rows) == {queued.id}
    reopened = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    assert reopened.record_count == 0
    assert reopened.get(queued.id) == finished
    assert reopened.get(queued.id) == finished


def test_failed_save_is_not_presented_as_completed() -> None:
    store = RecordingStore()
    store.fail_write = True
    service = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    queued = service.submit(_request())
    service.process(queued.id)
    result = service.get(queued.id)
    assert result is not None
    assert result.status == InvestigationStatus.FAILED
    assert result.plan is None
    assert result.outcome is None
    assert result.diagnostics == ("Investigation persistence failed",)
    assert store.rows == {}


def test_in_flight_jobs_are_never_durably_saved() -> None:
    store = RecordingStore()
    service = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    queued = service.submit(_request())
    assert queued.status == InvestigationStatus.QUEUED
    assert store.rows == {}
    assert InMemoryInvestigationService(SyntheticFixtureProvider(), store).get(queued.id) is None
