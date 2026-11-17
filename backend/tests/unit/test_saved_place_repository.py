"""Owner isolation, optimistic changes and transaction behavior for private places."""

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest

from melliatlas.persistence.saved_places import PostgisSavedPlaceRepository
from melliatlas.places.api import (
    InvalidSavedPlace,
    SavedPlaceConflict,
    SavedPlaceDraft,
    SavedPlaceLocationUnavailable,
    SavedPlaceNotFound,
    SavedPlaceRepository,
    SavedPlaceStorageError,
)
from melliatlas.territories.api import CountryCode

_OWNER = UUID("e52a78cd-9a87-46db-b351-ef95674d1021")
_OTHER = UUID("a877adf4-ec8d-40d9-989e-3dbe3c786570")
_NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)


class MemoryDatabase:
    def __init__(self) -> None:
        self.rows: dict[UUID, tuple[object, ...]] = {}
        self.connections: list[MemoryConnection] = []
        self.fail_commit = False
        self.region_mode = "valid"

    def connect(self) -> "MemoryConnection":
        result = MemoryConnection(self)
        self.connections.append(result)
        return result


class MemoryConnection:
    def __init__(self, db: MemoryDatabase) -> None:
        self.db = db
        self.pending: dict[UUID, tuple[object, ...] | None] = {}
        self.fetched: list[tuple[object, ...]] = []
        self.queries: list[tuple[str, tuple[object, ...]]] = []
        self.closed = False
        self.cursor_closed = False
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> "MemoryConnection":
        return self

    def _visible(self) -> dict[UUID, tuple[object, ...]]:
        result = dict(self.db.rows)
        for identifier, row in self.pending.items():
            if row is None:
                result.pop(identifier, None)
            else:
                result[identifier] = row
        return result

    def execute(self, query: str, params: Sequence[object] = ()) -> object:
        args = tuple(params)
        self.queries.append((query, args))
        if "FROM melliatlas_admin_geometry" in query:
            if self.db.region_mode == "valid":
                self.fetched = [("ru:region:smo",)]
            elif self.db.region_mode == "ambiguous":
                self.fetched = [("ru:region:smo",), ("ru:region:bry",)]
            else:
                self.fetched = []
        elif "INSERT INTO melliatlas_saved_place" in query:
            identifier, owner, name, country, region, lon, lat, width, height, geojson, srid = args
            assert srid == 4326
            assert isinstance(geojson, str)
            assert json.loads(geojson)["type"] == "MultiPolygon"
            assert isinstance(identifier, UUID)
            if identifier in self._visible():
                raise ValueError("Duplicate place UUID")
            row = (identifier, owner, name, country, region, lon, lat, width, height, 1, _NOW, _NOW)
            self.pending[identifier] = row
            self.fetched = [row]
        elif query.lstrip().startswith("UPDATE melliatlas_saved_place"):
            (
                name,
                country,
                region,
                lon,
                lat,
                width,
                height,
                geojson,
                srid,
                identifier,
                owner,
                expected,
            ) = args
            assert srid == 4326 and isinstance(geojson, str)
            assert isinstance(identifier, UUID)
            assert isinstance(expected, int)
            row = self._visible().get(identifier)
            if row is None or row[1] != owner or row[9] != expected:
                self.fetched = []
            else:
                updated = (
                    identifier,
                    owner,
                    name,
                    country,
                    region,
                    lon,
                    lat,
                    width,
                    height,
                    expected + 1,
                    _NOW,
                    _NOW,
                )
                self.pending[identifier] = updated
                self.fetched = [updated]
        elif query.lstrip().startswith("DELETE FROM melliatlas_saved_place"):
            identifier, owner, expected = args
            assert isinstance(identifier, UUID)
            row = self._visible().get(identifier)
            if row is None or row[1] != owner or row[9] != expected:
                self.fetched = []
            else:
                self.pending[identifier] = None
                self.fetched = [(identifier,)]
        elif "SELECT revision" in query:
            identifier, owner = args
            assert isinstance(identifier, UUID)
            row = self._visible().get(identifier)
            self.fetched = [(row[9],)] if row is not None and row[1] == owner else []
        elif "FROM melliatlas_saved_place" in query:
            if "WHERE id =" in query:
                identifier, owner = args
                assert isinstance(identifier, UUID)
                row = self._visible().get(identifier)
                self.fetched = [row] if row is not None and row[1] == owner else []
            else:
                (owner,) = args
                self.fetched = [row for row in self._visible().values() if row[1] == owner]
        else:
            raise AssertionError(f"Unexpected SQL: {query[:60]}")
        return None

    def fetchone(self) -> tuple[object, ...] | None:
        return self.fetched.pop(0) if self.fetched else None

    def commit(self) -> None:
        if self.db.fail_commit:
            raise RuntimeError("Synthetic database failure")
        for identifier, row in self.pending.items():
            if row is None:
                self.db.rows.pop(identifier, None)
            else:
                self.db.rows[identifier] = row
        self.pending.clear()
        self.commits += 1

    def rollback(self) -> None:
        self.pending.clear()
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True
        self.cursor_closed = True


def draft(
    *,
    name: str = "  Apiary Alpha  ",
    country: CountryCode = CountryCode.RU,
    region_id: str = "ru:region:smo",
    longitude: float = 31.3,
    latitude: float = 54.7,
    width_km: float = 15.0,
    height_km: float = 15.0,
) -> SavedPlaceDraft:
    return SavedPlaceDraft(name, country, region_id, longitude, latitude, width_km, height_km)


def test_owner_scoped_create_get_list_update_delete() -> None:
    db = MemoryDatabase()
    repo: SavedPlaceRepository = PostgisSavedPlaceRepository(db.connect)
    created = repo.create(owner_id=_OWNER, draft=draft())
    assert created.draft.name == "Apiary Alpha"
    assert created.revision == 1
    assert created.id != UUID(int=0)
    assert repo.get(owner_id=_OTHER, place_id=created.id) is None
    assert repo.list(owner_id=_OTHER) == ()
    assert repo.list(owner_id=_OWNER) == (created,)
    with pytest.raises(SavedPlaceNotFound):
        repo.update(owner_id=_OTHER, place_id=created.id, expected_revision=1, draft=draft())
    with pytest.raises(SavedPlaceNotFound):
        repo.delete(owner_id=_OTHER, place_id=created.id, expected_revision=1)
    changed = repo.update(
        owner_id=_OWNER, place_id=created.id, expected_revision=1, draft=draft(name="Second apiary")
    )
    assert changed.id == created.id
    assert changed.draft.name == "Second apiary"
    assert changed.revision == 2
    assert repo.get(owner_id=_OWNER, place_id=created.id) == changed
    with pytest.raises(SavedPlaceConflict):
        repo.update(owner_id=_OWNER, place_id=created.id, expected_revision=1, draft=draft())
    with pytest.raises(SavedPlaceConflict):
        repo.delete(owner_id=_OWNER, place_id=created.id, expected_revision=1)
    repo.delete(owner_id=_OWNER, place_id=created.id, expected_revision=2)
    assert repo.list(owner_id=_OWNER) == ()
    with pytest.raises(SavedPlaceNotFound):
        repo.delete(owner_id=_OWNER, place_id=created.id, expected_revision=2)
    assert all(connection.closed and connection.cursor_closed for connection in db.connections)


def test_unreviewed_region_is_fail_closed_and_rolls_back() -> None:
    db = MemoryDatabase()
    db.region_mode = "missing"
    repo = PostgisSavedPlaceRepository(db.connect)
    with pytest.raises(SavedPlaceLocationUnavailable):
        repo.create(owner_id=_OWNER, draft=draft())
    db.region_mode = "ambiguous"
    with pytest.raises(SavedPlaceLocationUnavailable):
        repo.create(owner_id=_OWNER, draft=draft())
    assert db.rows == {}
    assert all(connection.rollbacks == 1 for connection in db.connections)


@pytest.mark.parametrize(
    "bad",
    [
        draft(name="   "),
        draft(name="evil\nlog"),
        draft(name="x" * 121),
        draft(country=CountryCode.BY),
        draft(region_id="ru:district:wrong"),
        draft(latitude=float("nan")),
        draft(width_km=31),
        draft(height_km=0),
        draft(width_km=True),
    ],
)
def test_invalid_place_is_rejected_before_connection(bad: SavedPlaceDraft) -> None:
    db = MemoryDatabase()
    with pytest.raises(InvalidSavedPlace):
        PostgisSavedPlaceRepository(db.connect).create(owner_id=_OWNER, draft=bad)
    assert db.connections == []


def test_invalid_owner_and_revision_rejected_without_database_access() -> None:
    db = MemoryDatabase()
    repo = PostgisSavedPlaceRepository(db.connect)
    with pytest.raises(InvalidSavedPlace):
        repo.list(owner_id=UUID(int=0))
    with pytest.raises(InvalidSavedPlace):
        repo.update(owner_id=_OWNER, place_id=uuid4(), expected_revision=0, draft=draft())
    assert db.connections == []


def test_failed_commit_leaves_no_saved_place() -> None:
    db = MemoryDatabase()
    db.fail_commit = True
    with pytest.raises(SavedPlaceStorageError):
        PostgisSavedPlaceRepository(db.connect).create(owner_id=_OWNER, draft=draft())
    assert db.rows == {}
    assert db.connections[-1].rollbacks == 1
    assert db.connections[-1].closed


def test_antimeridian_area_persists_two_wgs84_polygons() -> None:
    db = MemoryDatabase()
    PostgisSavedPlaceRepository(db.connect).create(
        owner_id=_OWNER, draft=draft(longitude=179.99, latitude=0, width_km=20, height_km=20)
    )
    writes = [args for sql, args in db.connections[0].queries if "INSERT INTO" in sql]
    assert len(writes) == 1
    payload = writes[0][9]
    assert isinstance(payload, str)
    geo = json.loads(payload)
    assert len(geo["coordinates"]) == 2
    assert all(len(poly[0]) == 5 for poly in geo["coordinates"])


def test_migration_declares_owner_region_and_geography_constraints() -> None:
    from pathlib import Path

    source = Path(__file__).resolve().parents[2] / "migrations/0008_saved_places.sql"
    ddl = source.read_text(encoding="utf-8")
    assert "owner_id UUID NOT NULL" in ddl
    assert "FOREIGN KEY (region_id, country_code)" in ddl
    assert "GEOMETRY(MULTIPOLYGON, 4326)" in ddl


if TYPE_CHECKING:

    def verify_repository_port(store: PostgisSavedPlaceRepository) -> SavedPlaceRepository:
        return store


def test_saved_place_routes_are_not_registered_before_owner_authentication() -> None:
    from fastapi.routing import APIRoute

    from melliatlas.api.app import create_app

    app = create_app()
    assert all(
        not route.path.startswith("/api/v1/places")
        for route in app.routes
        if isinstance(route, APIRoute)
    )


def test_update_rejects_unreviewed_region_without_mutating_persisted_place() -> None:
    db = MemoryDatabase()
    repo = PostgisSavedPlaceRepository(db.connect)
    created = repo.create(owner_id=_OWNER, draft=draft())
    db.region_mode = "missing"
    with pytest.raises(SavedPlaceLocationUnavailable):
        repo.update(
            owner_id=_OWNER,
            place_id=created.id,
            expected_revision=1,
            draft=draft(name="Unverified region"),
        )
    assert repo.get(owner_id=_OWNER, place_id=created.id) == created
    assert db.connections[-2].rollbacks == 1
