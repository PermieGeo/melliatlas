"""Explicit PostgreSQL adapter for private, owner-scoped saved analysis places."""

import json
from collections.abc import Callable
from datetime import datetime
from typing import Final, LiteralString, NoReturn, TypeVar
from uuid import UUID, uuid4

from melliatlas.geography import WGS84_SRID, Wgs84AnalysisBounds
from melliatlas.places import validate_draft, validate_owner, validate_revision
from melliatlas.places.api import (
    InvalidSavedPlace,
    SavedPlace,
    SavedPlaceConflict,
    SavedPlaceDraft,
    SavedPlaceLocationUnavailable,
    SavedPlaceNotFound,
    SavedPlaceStorageError,
)
from melliatlas.territories.api import CountryCode

from .api import ConnectionFactory, DatabaseCursor

_Result = TypeVar("_Result")


class PostgisSavedPlaceRepository:
    """Caller-supplied owner UUIDs; never authenticate or enable HTTP access itself."""

    _REGION_AT_CENTER: Final[LiteralString] = """
        SELECT territory_id FROM melliatlas_admin_geometry
        WHERE country_code = %s AND kind = 'region'
          AND ST_Covers(boundary, ST_SetSRID(ST_MakePoint(%s, %s), %s))
        LIMIT 2
    """
    _INSERT: Final[LiteralString] = """
        INSERT INTO melliatlas_saved_place (
            id, owner_id, name, country_code, region_id, longitude, latitude,
            width_km, height_km, boundary, revision, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            ST_SetSRID(ST_GeomFromGeoJSON(%s::text), %s), 1,
            transaction_timestamp(), transaction_timestamp()
        )
        RETURNING id, owner_id, name, country_code, region_id, longitude, latitude,
            width_km, height_km, revision, created_at, updated_at
    """
    _GET: Final[LiteralString] = """
        SELECT id, owner_id, name, country_code, region_id, longitude, latitude,
            width_km, height_km, revision, created_at, updated_at
        FROM melliatlas_saved_place WHERE id = %s AND owner_id = %s
    """
    _LIST: Final[LiteralString] = """
        SELECT id, owner_id, name, country_code, region_id, longitude, latitude,
            width_km, height_km, revision, created_at, updated_at
        FROM melliatlas_saved_place WHERE owner_id = %s
        ORDER BY updated_at DESC, id
    """
    _UPDATE: Final[LiteralString] = """
        UPDATE melliatlas_saved_place
        SET name = %s, country_code = %s, region_id = %s,
            longitude = %s, latitude = %s, width_km = %s, height_km = %s,
            boundary = ST_SetSRID(ST_GeomFromGeoJSON(%s::text), %s),
            revision = revision + 1, updated_at = transaction_timestamp()
        WHERE id = %s AND owner_id = %s AND revision = %s
        RETURNING id, owner_id, name, country_code, region_id, longitude, latitude,
            width_km, height_km, revision, created_at, updated_at
    """
    _DELETE: Final[LiteralString] = """
        DELETE FROM melliatlas_saved_place
        WHERE id = %s AND owner_id = %s AND revision = %s RETURNING id
    """
    _REVISION: Final[LiteralString] = """
        SELECT revision FROM melliatlas_saved_place WHERE id = %s AND owner_id = %s
    """

    def __init__(self, connect: ConnectionFactory) -> None:
        self._connect = connect

    def _run(self, action: Callable[[DatabaseCursor], _Result], *, write: bool) -> _Result:
        try:
            connection = self._connect()
        except Exception as error:
            raise SavedPlaceStorageError("Could not open saved-place storage") from error
        try:
            try:
                cursor = connection.cursor()
                try:
                    result = action(cursor)
                    if write:
                        connection.commit()
                    return result
                finally:
                    cursor.close()
            except (InvalidSavedPlace, SavedPlaceNotFound, SavedPlaceConflict):
                if write:
                    connection.rollback()
                raise
            except Exception as error:
                if write:
                    connection.rollback()
                raise SavedPlaceStorageError("Saved-place storage operation failed") from error
        finally:
            connection.close()

    @classmethod
    def _confirm_region(cls, cursor: DatabaseCursor, draft: SavedPlaceDraft) -> None:
        cursor.execute(
            cls._REGION_AT_CENTER,
            (draft.country.value, draft.longitude, draft.latitude, WGS84_SRID),
        )
        first = cursor.fetchone()
        second = cursor.fetchone()
        if first != (draft.region_id,) or second is not None:
            raise SavedPlaceLocationUnavailable("No unique reviewed region contains place center")

    @staticmethod
    def _area_json(bounds: Wgs84AnalysisBounds) -> str:
        polygons: list[list[list[list[float]]]] = []
        for west, east in bounds.longitude_ranges:
            polygons.append(
                [
                    [
                        [west, bounds.south],
                        [east, bounds.south],
                        [east, bounds.north],
                        [west, bounds.north],
                        [west, bounds.south],
                    ]
                ]
            )
        return json.dumps({"type": "MultiPolygon", "coordinates": polygons}, allow_nan=False)

    @staticmethod
    def _number(value: object) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Invalid stored numeric value")
        return float(value)

    @classmethod
    def _saved_place(cls, row: tuple[object, ...], owner_id: UUID) -> SavedPlace:
        if len(row) != 12:
            raise ValueError("Unexpected saved-place database row")
        (
            place_id,
            row_owner,
            name,
            country_code,
            region_id,
            longitude,
            latitude,
            width_km,
            height_km,
            revision,
            created_at,
            updated_at,
        ) = row
        if (
            not isinstance(place_id, UUID)
            or row_owner != owner_id
            or not isinstance(name, str)
            or not isinstance(region_id, str)
            or not isinstance(country_code, str)
            or not isinstance(revision, int)
            or isinstance(revision, bool)
            or revision < 1
            or not isinstance(created_at, datetime)
            or not isinstance(updated_at, datetime)
            or created_at.tzinfo is None
            or updated_at.tzinfo is None
            or created_at.utcoffset() is None
            or updated_at.utcoffset() is None
            or updated_at < created_at
        ):
            raise ValueError("Invalid saved-place database row")
        try:
            draft, _ = validate_draft(
                SavedPlaceDraft(
                    name=name,
                    country=CountryCode(country_code),
                    region_id=region_id,
                    longitude=cls._number(longitude),
                    latitude=cls._number(latitude),
                    width_km=cls._number(width_km),
                    height_km=cls._number(height_km),
                )
            )
        except ValueError as error:
            raise ValueError("Invalid stored place values") from error
        if name != draft.name:
            raise ValueError("Noncanonical stored place name")
        return SavedPlace(place_id, owner_id, draft, revision, created_at, updated_at)

    @classmethod
    def _check_revision(cls, cursor: DatabaseCursor, owner_id: UUID, place_id: UUID) -> NoReturn:
        cursor.execute(cls._REVISION, (place_id, owner_id))
        if cursor.fetchone() is None:
            raise SavedPlaceNotFound("Saved place not found")
        raise SavedPlaceConflict("Saved place was modified concurrently")

    def create(self, *, owner_id: UUID, draft: SavedPlaceDraft) -> SavedPlace:
        validate_owner(owner_id)
        normalized, bounds = validate_draft(draft)
        identifier = uuid4()

        def insert(cursor: DatabaseCursor) -> SavedPlace:
            self._confirm_region(cursor, normalized)
            cursor.execute(
                self._INSERT,
                (
                    identifier,
                    owner_id,
                    normalized.name,
                    normalized.country.value,
                    normalized.region_id,
                    normalized.longitude,
                    normalized.latitude,
                    normalized.width_km,
                    normalized.height_km,
                    self._area_json(bounds),
                    WGS84_SRID,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise SavedPlaceStorageError("Saved-place insert returned no record")
            return self._saved_place(row, owner_id)

        return self._run(insert, write=True)

    def get(self, *, owner_id: UUID, place_id: UUID) -> SavedPlace | None:
        validate_owner(owner_id)

        def lookup(cursor: DatabaseCursor) -> SavedPlace | None:
            cursor.execute(self._GET, (place_id, owner_id))
            row = cursor.fetchone()
            return self._saved_place(row, owner_id) if row is not None else None

        return self._run(lookup, write=False)

    def list(self, *, owner_id: UUID) -> tuple[SavedPlace, ...]:
        validate_owner(owner_id)

        def lookup(cursor: DatabaseCursor) -> tuple[SavedPlace, ...]:
            cursor.execute(self._LIST, (owner_id,))
            places: list[SavedPlace] = []
            while (row := cursor.fetchone()) is not None:
                places.append(self._saved_place(row, owner_id))
            return tuple(places)

        return self._run(lookup, write=False)

    def update(
        self, *, owner_id: UUID, place_id: UUID, expected_revision: int, draft: SavedPlaceDraft
    ) -> SavedPlace:
        validate_owner(owner_id)
        validate_revision(expected_revision)
        normalized, bounds = validate_draft(draft)

        def update_row(cursor: DatabaseCursor) -> SavedPlace:
            self._confirm_region(cursor, normalized)
            cursor.execute(
                self._UPDATE,
                (
                    normalized.name,
                    normalized.country.value,
                    normalized.region_id,
                    normalized.longitude,
                    normalized.latitude,
                    normalized.width_km,
                    normalized.height_km,
                    self._area_json(bounds),
                    WGS84_SRID,
                    place_id,
                    owner_id,
                    expected_revision,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                self._check_revision(cursor, owner_id, place_id)
            return self._saved_place(row, owner_id)

        return self._run(update_row, write=True)

    def delete(self, *, owner_id: UUID, place_id: UUID, expected_revision: int) -> None:
        validate_owner(owner_id)
        validate_revision(expected_revision)

        def delete_row(cursor: DatabaseCursor) -> None:
            cursor.execute(self._DELETE, (place_id, owner_id, expected_revision))
            if cursor.fetchone() is None:
                self._check_revision(cursor, owner_id, place_id)

        self._run(delete_row, write=True)
