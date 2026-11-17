"""Read-only PostGIS intersection of a bounded area with imported ADM2 polygons."""

import asyncio
from typing import Final, LiteralString

from melliatlas.geography import WGS84_SRID, make_analysis_bounds
from melliatlas.persistence.point_locator import ReadRows
from melliatlas.territories.api import (
    AreaDistrict,
    AreaDistrictCoverage,
    AreaDistrictResult,
    CountryCode,
    ReferenceUnavailableError,
    TerritoryNotFound,
)


class PostgisAreaDistrictLookup:
    """Return all known positive-area intersections, never assert complete coverage."""

    _REGIONS_AT_CENTER: Final[LiteralString] = """
        SELECT territory_id FROM melliatlas_admin_geometry
        WHERE country_code = %s AND kind = 'region'
          AND ST_Covers(boundary, ST_SetSRID(ST_MakePoint(%s, %s), %s))
        LIMIT 2
    """

    _INTERSECTIONS: Final[LiteralString] = """
        WITH search_area AS (
            SELECT ST_Union(
                ST_MakeEnvelope(%s, %s, %s, %s, %s),
                ST_MakeEnvelope(%s, %s, %s, %s, %s)
            ) AS geom
        )
        SELECT d.territory_id, d.region_id, d.name, d.reference_id
        FROM melliatlas_admin_geometry AS d CROSS JOIN search_area AS a
        WHERE d.country_code = %s AND d.kind = 'district'
          AND ST_Intersects(d.boundary, a.geom)
          AND ST_Area(ST_CollectionExtract(ST_Intersection(d.boundary, a.geom), 3)::geography) > 0
        ORDER BY d.territory_id
    """

    def __init__(self, read: ReadRows) -> None:
        self._read = read

    async def intersect_districts(
        self,
        *,
        country: CountryCode,
        region_id: str,
        longitude: float,
        latitude: float,
        width_km: float,
        height_km: float,
    ) -> AreaDistrictResult:
        bounds = make_analysis_bounds(
            longitude=longitude, latitude=latitude, width_km=width_km, height_km=height_km
        )
        if not region_id.startswith(f"{country.value.lower()}:region:"):
            raise ValueError("Region is not part of the selected country")
        regions = await asyncio.to_thread(
            self._read, self._REGIONS_AT_CENTER, (country.value, longitude, latitude, WGS84_SRID)
        )
        if not regions:
            raise TerritoryNotFound("No reviewed region contains the area center")
        if len(regions) != 1 or len(regions[0]) != 1 or not isinstance(regions[0][0], str):
            raise ReferenceUnavailableError("Ambiguous or invalid region at area center")
        if regions[0][0] != region_id:
            raise TerritoryNotFound("Area center lies outside the selected region")

        ranges = bounds.longitude_ranges
        first = ranges[0]
        second = ranges[1] if len(ranges) == 2 else first
        rows = await asyncio.to_thread(
            self._read,
            self._INTERSECTIONS,
            (
                first[0],
                bounds.south,
                first[1],
                bounds.north,
                WGS84_SRID,
                second[0],
                bounds.south,
                second[1],
                bounds.north,
                WGS84_SRID,
                country.value,
            ),
        )
        districts: list[AreaDistrict] = []
        seen: set[str] = set()
        for row in rows:
            match row:
                case (str(identifier), str(parent), str(name), str(reference)):
                    pass
                case _:
                    raise ReferenceUnavailableError("Invalid ADM2 intersection result")
            if (
                not identifier.startswith(f"{country.value.lower()}:district:")
                or not parent.startswith(f"{country.value.lower()}:region:")
                or not name.strip()
                or not reference.strip()
                or identifier in seen
            ):
                raise ReferenceUnavailableError("Ambiguous or invalid ADM2 intersection result")
            seen.add(identifier)
            districts.append(AreaDistrict(identifier, parent, name, reference))
        return AreaDistrictResult(
            bounds=bounds,
            districts=tuple(districts),
            coverage=AreaDistrictCoverage.UNVERIFIED if districts else AreaDistrictCoverage.MISSING,
        )
