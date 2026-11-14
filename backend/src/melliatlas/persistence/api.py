"""PostGIS-backed completed investigation store with injected DB-API connections."""

import json
from collections.abc import Callable, Sequence
from typing import Protocol
from uuid import UUID

from melliatlas.jobs.api import (
    InvestigationSnapshot,
    InvestigationStatus,
    InvestigationStorageError,
    deserialize_completed_snapshot,
    serialize_completed_snapshot,
)


class DatabaseCursor(Protocol):
    def execute(self, query: str, params: Sequence[object] = ()) -> object: ...
    def fetchone(self) -> tuple[object, ...] | None: ...
    def close(self) -> None: ...


class DatabaseConnection(Protocol):
    def cursor(self) -> DatabaseCursor: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


ConnectionFactory = Callable[[], DatabaseConnection]


class PostgisCompletedInvestigationStore:
    """Owns PostgreSQL I/O; never updates or deletes completed results."""

    _SAVE = """
        INSERT INTO melliatlas_completed_investigations (
            id, payload, reference_version, created_at, completed_at, site_points
        ) VALUES (
            %s, %s::jsonb, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s::text), 4326)
        ) ON CONFLICT DO NOTHING RETURNING id
    """
    _LOAD = """
        SELECT payload::text FROM melliatlas_completed_investigations WHERE id = %s
    """

    def __init__(self, connect: ConnectionFactory) -> None:
        self._connect = connect

    def save(self, snapshot: InvestigationSnapshot) -> None:
        payload = serialize_completed_snapshot(snapshot)
        if snapshot.status is not InvestigationStatus.COMPLETED:
            raise ValueError("Only completed investigations may be persisted")
        geometry = (
            json.dumps(
                {
                    "type": "MultiPoint",
                    "coordinates": [
                        [stop.longitude, stop.latitude] for stop in snapshot.plan.stops
                    ],
                },
                allow_nan=False,
            )
            if snapshot.plan is not None
            else None
        )
        try:
            connection = self._connect()
        except Exception as error:
            raise InvestigationStorageError("Could not open persistence connection") from error
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    self._SAVE,
                    (
                        snapshot.id,
                        payload,
                        snapshot.reference_version,
                        snapshot.created_at,
                        snapshot.updated_at,
                        geometry,
                    ),
                )
                if cursor.fetchone() is None:
                    raise InvestigationStorageError("Completed investigation already exists")
                connection.commit()
            finally:
                cursor.close()
        except Exception as error:
            try:
                connection.rollback()
            except Exception:
                pass
            raise InvestigationStorageError("Could not save completed investigation") from error
        finally:
            connection.close()

    def load(self, identifier: UUID) -> InvestigationSnapshot | None:
        try:
            connection = self._connect()
        except Exception as error:
            raise InvestigationStorageError("Could not open persistence connection") from error
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(self._LOAD, (identifier,))
                row = cursor.fetchone()
            finally:
                cursor.close()
            if row is None:
                return None
            payload = row[0]
            if not isinstance(payload, str):
                raise ValueError("Stored JSON payload is not text")
            snapshot = deserialize_completed_snapshot(payload)
            if snapshot.id != identifier:
                raise ValueError("Stored investigation ID does not match primary key")
            return snapshot
        except Exception as error:
            raise InvestigationStorageError("Could not load completed investigation") from error
        finally:
            connection.close()
