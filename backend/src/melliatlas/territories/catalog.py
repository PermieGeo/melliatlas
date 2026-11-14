"""Atomic, read-only-in-practice catalog snapshots for injected applications."""

from copy import deepcopy

from melliatlas.territories.api import (
    CatalogDepthUnsupported,
    CountryCode,
    ExpectedInventory,
    ReferenceSnapshot,
    ReferenceUnavailableError,
    Territory,
    TerritoryGeometry,
    TerritoryKind,
    TerritoryNotFound,
    TerritoryReferenceError,
)
from melliatlas.territories.validation import validate_reference


class InMemoryTerritoryCatalog:
    def __init__(self) -> None:
        self._snapshot: ReferenceSnapshot | None = None
        self._territories: dict[str, Territory] = {}
        self._geometries: dict[str, TerritoryGeometry] = {}
        self._pilot_regions: frozenset[str] = frozenset()

    async def validate_reference(
        self, snapshot: ReferenceSnapshot, inventory: ExpectedInventory
    ) -> None:
        validate_reference(snapshot, inventory)

    async def apply_reference(
        self, snapshot: ReferenceSnapshot, inventory: ExpectedInventory
    ) -> None:
        validate_reference(snapshot, inventory)
        if self._snapshot is not None:
            if self._snapshot.manifest != snapshot.manifest or self._snapshot != snapshot:
                raise TerritoryReferenceError(
                    "Catalog is immutable: a different reference needs a versioned store"
                )
            return
        # Do not retain caller-owned mutable GeoJSON arrays.
        copied = deepcopy(snapshot)
        self._snapshot = copied
        self._territories = {item.id: item for item in copied.territories}
        self._geometries = {item.territory_id: item for item in copied.geometries}
        self._pilot_regions = frozenset(inventory.pilot_district_ids)

    def _data(self) -> ReferenceSnapshot:
        if self._snapshot is None:
            raise ReferenceUnavailableError(
                "No validated RU/BY territory reference has been loaded"
            )
        return self._snapshot

    async def list_regions(self, country: CountryCode) -> tuple[Territory, ...]:
        self._data()
        return tuple(
            sorted(
                (
                    item
                    for item in self._territories.values()
                    if item.country is country and item.kind is TerritoryKind.REGION
                ),
                key=lambda item: item.id,
            )
        )

    async def list_districts(self, region_id: str) -> tuple[Territory, ...]:
        self._data()
        region = self._territories.get(region_id)
        if region is None:
            raise TerritoryNotFound(region_id)
        if region.kind is not TerritoryKind.REGION:
            raise TerritoryReferenceError("District navigation requires a region ID")
        if region_id not in self._pilot_regions:
            raise CatalogDepthUnsupported(region_id)
        return tuple(
            sorted(
                (
                    item
                    for item in self._territories.values()
                    if item.kind is TerritoryKind.DISTRICT and item.parent_id == region_id
                ),
                key=lambda item: item.id,
            )
        )

    async def get(self, territory_id: str) -> Territory | None:
        self._data()
        return self._territories.get(territory_id)

    async def get_geometry(self, territory_id: str) -> TerritoryGeometry | None:
        self._data()
        if territory_id not in self._territories:
            raise TerritoryNotFound(territory_id)
        item = self._geometries.get(territory_id)
        return deepcopy(item) if item is not None else None
