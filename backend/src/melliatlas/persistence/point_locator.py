"""PostGIS point-containment lookup, isolated from geometry serialization.

ST_Covers includes boundary points. LIMIT 2 deliberately exposes ambiguous
joins rather than silently selecting one of overlapping administrative polygons.
"""

import asyncio
from collections.abc import Callable, Sequence
from typing import Final, LiteralString

from melliatlas.geography import WGS84_SRID, is_wgs84_position
from melliatlas.territories.api import CountryCode, ReferenceUnavailableError, TerritoryAtPoint

ReadRows = Callable[[LiteralString, Sequence[object]], tuple[tuple[object, ...], ...]]


class PostgisPointLocator:
    """Read a unique containing region and its optional containing district."""

    _REGIONS: Final[LiteralString] = """
        SELECT territory_id FROM melliatlas_admin_geometry
        WHERE country_code = %s AND kind = 'region'
          AND ST_Covers(boundary, ST_SetSRID(ST_MakePoint(%s, %s), %s))
        LIMIT 2
    """
    _DISTRICTS: Final[LiteralString] = """
        SELECT territory_id FROM melliatlas_admin_geometry
        WHERE region_id = %s AND kind = 'district'
          AND ST_Covers(boundary, ST_SetSRID(ST_MakePoint(%s, %s), %s))
        LIMIT 2
    """

    def __init__(self, read: ReadRows) -> None:
        self._read = read

    @staticmethod
    def _unique_id(rows: tuple[tuple[object, ...], ...], kind: str) -> str | None:
        # Two rows mean an ambiguous spatial join, not a valid first match.
        match rows:
            case ():
                return None
            case ((str(identifier),),):
                return identifier
            case _:
                raise ReferenceUnavailableError(f"Overlapping or invalid {kind} reference at point")

    async def locate_point(
        self, *, country: CountryCode, longitude: float, latitude: float
    ) -> TerritoryAtPoint | None:
        if not is_wgs84_position(longitude, latitude):
            raise ValueError("Invalid WGS84 point")
        regions = await asyncio.to_thread(
            self._read, self._REGIONS, (country.value, longitude, latitude, WGS84_SRID)
        )
        region_id = self._unique_id(regions, "region")
        if region_id is None:
            return None
        districts = await asyncio.to_thread(
            self._read, self._DISTRICTS, (region_id, longitude, latitude, WGS84_SRID)
        )
        return TerritoryAtPoint(
            region_id=region_id,
            district_id=self._unique_id(districts, "district"),
        )
