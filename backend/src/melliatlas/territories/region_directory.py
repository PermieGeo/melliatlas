"""Read-only, name-only catalog for a pinned administrative subdivision list."""

from collections.abc import Sequence

from melliatlas.territories.api import (
    CatalogDepthUnsupported,
    CountryCode,
    Territory,
    TerritoryGeometry,
    TerritoryKind,
    TerritoryNotFound,
)


class RegionDirectoryCatalog:
    """Expose known region names without implying approved geometry or district coverage."""

    def __init__(self, regions: Sequence[Territory]) -> None:
        self._regions = {item.id: item for item in regions}
        if len(self._regions) != len(regions) or any(
            item.kind is not TerritoryKind.REGION for item in regions
        ):
            raise ValueError("Region directory requires unique first-order identities")

    async def list_regions(self, country: CountryCode) -> tuple[Territory, ...]:
        return tuple(
            sorted(
                (item for item in self._regions.values() if item.country is country),
                key=lambda item: (item.name, item.id),
            )
        )

    async def list_districts(self, region_id: str) -> tuple[Territory, ...]:
        if region_id not in self._regions:
            raise TerritoryNotFound(region_id)
        raise CatalogDepthUnsupported(region_id)

    async def get(self, territory_id: str) -> Territory | None:
        return self._regions.get(territory_id)

    async def get_geometry(self, territory_id: str) -> TerritoryGeometry | None:
        if territory_id not in self._regions:
            raise TerritoryNotFound(territory_id)
        return None
