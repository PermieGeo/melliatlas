"""PostgreSQL-backed independent first-order region directory and source-code links.

No implicit database migrations, network collection, or administrative geometry loads.
"""

import asyncio
from collections.abc import Sequence
from datetime import date
from typing import Final, LiteralString, Mapping

from melliatlas.persistence.api import ConnectionFactory
from melliatlas.persistence.source_registry import SOURCE_MAPPING_QUERIES, SourceMappingQueries
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

    def __init__(
        self,
        connect: ConnectionFactory,
        source_mappings: Mapping[str, SourceMappingQueries] = SOURCE_MAPPING_QUERIES,
    ) -> None:
        self._connect = connect
        self._source_mappings = source_mappings

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
        # PostgreSQL returns untyped driver values; validate column order before domain mapping.
        match row:
            case (
                str(identifier),
                str(country_code),
                str(name),
                str(reference),
                date() as valid_on,
            ):
                pass
            case _:
                raise ReferenceUnavailableError("Invalid region database record")
        try:
            country = CountryCode(country_code)
        except ValueError as exc:
            raise ReferenceUnavailableError("Invalid region country") from exc
        if not identifier.startswith(f"{country.value.lower()}:region:"):
            raise ReferenceUnavailableError("Invalid canonical region identifier")
        return Territory(
            id=identifier,
            country=country,
            kind=TerritoryKind.REGION,
            name=name,
            parent_id=country.value,
            reference_id=reference,
            valid_on=valid_on,
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
        source = self._source_mappings.get(source_id)
        if source is None or country not in source.supported_countries:
            return None
        rows = await asyncio.to_thread(self._read, source.region, (region_id, country.value))
        if not rows:
            return None
        if len(rows) != 1 or len(rows[0]) != 1 or type(rows[0][0]) is not int:
            raise ReferenceUnavailableError("Invalid source region mapping")
        return rows[0][0]

    async def find_district_code(
        self, *, source_id: str, country: CountryCode, region_id: str, district_id: str
    ) -> int | None:
        source = self._source_mappings.get(source_id)
        if source is None or country not in source.supported_countries:
            return None
        rows = await asyncio.to_thread(
            self._read, source.district, (district_id, region_id, country.value)
        )
        if not rows:
            return None
        if len(rows) != 1 or len(rows[0]) != 1 or type(rows[0][0]) is not int:
            raise ReferenceUnavailableError("Invalid reviewed source district mapping")
        return rows[0][0]
