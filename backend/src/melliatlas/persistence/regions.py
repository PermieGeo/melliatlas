"""PostgreSQL-backed independent first-order region directory and source-code links.

No implicit database migrations, network collection, or administrative geometry loads.
"""

import asyncio
from collections.abc import Sequence
from datetime import date
from typing import Final, LiteralString

from melliatlas.persistence.api import ConnectionFactory
from melliatlas.territories.api import (
    CatalogDepthUnsupported,
    CountryCode,
    GeometryStatus,
    ReferenceUnavailableError,
    Territory,
    TerritoryGeometry,
    TerritoryKind,
    TerritoryNotFound,
)


class PostgresRegionCatalog:
    """Read an already seeded regional directory; provider IDs never become territory IDs."""

    _REGIONS: Final[LiteralString] = """
        SELECT id, country_code, name, reference_id, valid_on
        FROM melliatlas_region WHERE country_code = %s ORDER BY name, id
    """
    _REGION: Final[LiteralString] = """
        SELECT id, country_code, name, reference_id, valid_on
        FROM melliatlas_region WHERE id = %s
    """
    _SOURCE_CODE: Final[LiteralString] = """
        SELECT saturn.subject_id
        FROM melliatlas_source_saturn AS saturn
        JOIN melliatlas_region AS region ON region.id = saturn.region_id
        WHERE saturn.region_id = %s AND region.country_code = 'RU'
    """

    def __init__(self, connect: ConnectionFactory) -> None:
        self._connect = connect

    def _read(
        self, sql: LiteralString, parameters: Sequence[object]
    ) -> tuple[tuple[object, ...], ...]:
        try:
            connection = self._connect()
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(sql, parameters)
                    rows: list[tuple[object, ...]] = []
                    while (row := cursor.fetchone()) is not None:
                        rows.append(row)
                    return tuple(rows)
                finally:
                    cursor.close()
            finally:
                connection.close()
        except Exception as exc:
            raise ReferenceUnavailableError("Region database unavailable") from exc

    @staticmethod
    def _region(row: tuple[object, ...]) -> Territory:
        if (
            len(row) != 5
            or not isinstance(row[0], str)
            or not isinstance(row[1], str)
            or not isinstance(row[2], str)
            or not isinstance(row[3], str)
            or not isinstance(row[4], date)
        ):
            raise ReferenceUnavailableError("Invalid region database record")
        try:
            country = CountryCode(row[1])
        except ValueError as exc:
            raise ReferenceUnavailableError("Invalid region country") from exc
        if not row[0].startswith(f"{country.value.lower()}:region:"):
            raise ReferenceUnavailableError("Invalid canonical region identifier")
        return Territory(
            id=row[0],
            country=country,
            kind=TerritoryKind.REGION,
            name=row[2],
            parent_id=country.value,
            reference_id=row[3],
            valid_on=row[4],
            geometry_status=GeometryStatus.MISSING,
        )

    async def list_regions(self, country: CountryCode) -> tuple[Territory, ...]:
        rows = await asyncio.to_thread(self._read, self._REGIONS, (country.value,))
        if not rows:
            raise ReferenceUnavailableError("Country has no seeded region directory")
        regions = tuple(self._region(row) for row in rows)
        if any(region.country is not country for region in regions):
            raise ReferenceUnavailableError("Country-scoped region query mismatch")
        return regions

    async def get(self, territory_id: str) -> Territory | None:
        rows = await asyncio.to_thread(self._read, self._REGION, (territory_id,))
        return self._region(rows[0]) if len(rows) == 1 else None

    async def list_districts(self, region_id: str) -> tuple[Territory, ...]:
        if await self.get(region_id) is None:
            raise TerritoryNotFound(region_id)
        raise CatalogDepthUnsupported(region_id)

    async def get_geometry(self, territory_id: str) -> TerritoryGeometry | None:
        if await self.get(territory_id) is None:
            raise TerritoryNotFound(territory_id)
        return None

    async def find_code(
        self, *, source_id: str, country: CountryCode, region_id: str
    ) -> int | None:
        if source_id != "saturn" or country is not CountryCode.RU:
            return None
        rows = await asyncio.to_thread(self._read, self._SOURCE_CODE, (region_id,))
        if not rows:
            return None
        if len(rows) != 1 or len(rows[0]) != 1 or type(rows[0][0]) is not int:
            raise ReferenceUnavailableError("Invalid Saturn region mapping")
        return rows[0][0]
