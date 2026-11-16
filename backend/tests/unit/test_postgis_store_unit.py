"""SQL adapter tests using a recording driver; not a substitute for PostGIS integration."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

import pytest

from melliatlas.jobs import (
    InMemoryInvestigationService,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
    InvestigationStorageError,
)
from melliatlas.persistence import PostgisCompletedInvestigationStore
from melliatlas.planning import TimeWindow
from melliatlas.sources.providers.synthetic import (
    SYNTHETIC_SCENARIO_ID,
    SyntheticFixtureProvider,
)
from melliatlas.territories.api import CountryCode


class RecordingDatabase:
    def __init__(self) -> None:
        self.rows: dict[UUID, str] = {}
        self.connections: list[RecordingConnection] = []
        self.fail_commit = False

    def connect(self) -> "RecordingConnection":
        connection = RecordingConnection(self)
        self.connections.append(connection)
        return connection


class RecordingConnection:
    def __init__(self, database: RecordingDatabase) -> None:
        self.database = database
        self.uncommitted: dict[UUID, str] = {}
        self.closed = False
        self.committed = 0
        self.rolled_back = 0
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.cursor_closed = False
        self.next_row: tuple[object, ...] | None = None

    def cursor(self) -> "RecordingConnection":
        return self

    def execute(self, query: str, params: Sequence[object] = ()) -> None:
        self.executed.append((query, tuple(params)))
        if "INSERT INTO" in query:
            identifier, serialized, _, _, _, geometry = params
            assert isinstance(identifier, UUID)
            assert isinstance(serialized, str)
            if geometry is not None:
                assert isinstance(geometry, str)
                assert '"MultiPoint"' in geometry
            if identifier in self.database.rows or identifier in self.uncommitted:
                self.next_row = None
            else:
                self.uncommitted[identifier] = serialized
                self.next_row = (identifier,)
        elif "SELECT payload" in query:
            (identifier,) = params
            assert isinstance(identifier, UUID)
            payload = self.database.rows.get(identifier)
            self.next_row = (payload,) if payload is not None else None
        else:
            raise AssertionError("Unexpected query")

    def fetchone(self) -> tuple[object, ...] | None:
        return self.next_row

    def commit(self) -> None:
        if self.database.fail_commit:
            raise OSError("Synthetic failed database commit")
        self.database.rows.update(self.uncommitted)
        self.uncommitted.clear()
        self.committed += 1

    def rollback(self) -> None:
        self.uncommitted.clear()
        self.rolled_back += 1

    def close(self) -> None:
        self.closed = True
        self.cursor_closed = True


def _finished() -> InvestigationSnapshot:
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
    finished = service.get(queued.id)
    assert finished is not None
    return finished


def test_persisted_completed_snapshot_survives_separate_connections() -> None:
    database = RecordingDatabase()
    repo = PostgisCompletedInvestigationStore(database.connect)
    finished = _finished()
    repo.save(finished)
    assert len(database.connections) == 1
    assert database.connections[0].committed == 1
    assert database.connections[0].closed
    query, params = database.connections[0].executed[0]
    assert "%s" in query
    assert "ST_GeomFromGeoJSON" in query
    assert params[0] == finished.id
    assert params[2] == finished.reference_version
    assert repo.load(finished.id) == finished
    assert repo.load(uuid4()) is None
    assert all(item.closed for item in database.connections)


def test_conflicting_save_rolls_back_instead_of_overwriting_history() -> None:
    database = RecordingDatabase()
    repo = PostgisCompletedInvestigationStore(database.connect)
    finished = _finished()
    repo.save(finished)
    original_payload = database.rows[finished.id]
    with pytest.raises(InvestigationStorageError):
        repo.save(replace(finished, limitations=("Different historical conclusions",)))
    assert database.rows[finished.id] == original_payload
    assert database.connections[-1].rolled_back == 1
    assert database.connections[-1].closed


def test_database_commit_failure_is_rolled_back() -> None:
    database = RecordingDatabase()
    repo = PostgisCompletedInvestigationStore(database.connect)
    database.fail_commit = True
    finished = _finished()
    with pytest.raises(InvestigationStorageError):
        repo.save(finished)
    assert finished.id not in database.rows
    assert database.connections[-1].rolled_back == 1
    assert database.connections[-1].closed
    assert database.connections[-1].uncommitted == {}


def test_non_completed_snapshot_cannot_be_saved() -> None:
    database = RecordingDatabase()
    repo = PostgisCompletedInvestigationStore(database.connect)
    with pytest.raises(ValueError, match="Only completed"):
        repo.save(replace(_finished(), status=InvestigationStatus.RUNNING))
    assert database.connections == []


def test_load_rejects_inconsistent_json_record() -> None:
    database = RecordingDatabase()
    identifier = uuid4()
    database.rows[identifier] = '{"status":"COMPLETED"}'
    repo = PostgisCompletedInvestigationStore(database.connect)
    with pytest.raises(InvestigationStorageError):
        repo.load(identifier)
    assert database.connections[-1].closed


def test_insufficient_evidence_save_has_no_site_geometry() -> None:
    database = RecordingDatabase()
    repo = PostgisCompletedInvestigationStore(database.connect)
    service = InMemoryInvestigationService(SyntheticFixtureProvider(), repo)
    queued = service.submit(
        InvestigationRequest(
            country=CountryCode.RU,
            territory_id="ru:region:smolensk",
            scenario_id=SYNTHETIC_SCENARIO_ID,
            season=TimeWindow(date(2026, 5, 1), date(2026, 5, 20)),
            starting_point=(32.0, 54.0),
        )
    )
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None
    assert completed.status is InvestigationStatus.COMPLETED
    assert completed.plan is None
    query, parameters = database.connections[0].executed[0]
    assert "ST_GeomFromGeoJSON" in query
    assert parameters[-1] is None
    assert repo.load(queued.id) == completed
