"""Public geographic reference contracts and dataset import boundaries."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal, Protocol, TypeAlias, TypedDict, runtime_checkable

from melliatlas.geography import Wgs84Crs


class CountryCode(StrEnum):
    RU = "RU"
    BY = "BY"


class TerritoryKind(StrEnum):
    COUNTRY = "country"
    REGION = "region"
    DISTRICT = "district"


class GeometryStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    INVALID = "invalid"


# GeoJSON positions use longitude first, latitude second.
Position: TypeAlias = tuple[float, float]


class PolygonWgs84(TypedDict):
    type: Literal["Polygon"]
    coordinates: list[list[Position]]


class MultiPolygonWgs84(TypedDict):
    type: Literal["MultiPolygon"]
    coordinates: list[list[list[Position]]]


GeometryWgs84: TypeAlias = PolygonWgs84 | MultiPolygonWgs84


@dataclass(frozen=True)
class Territory:
    id: str
    country: CountryCode
    kind: TerritoryKind
    name: str
    parent_id: str | None
    reference_id: str
    valid_on: date
    geometry_status: GeometryStatus
    name_ru: str | None = None


@dataclass(frozen=True)
class ReferenceManifest:
    reference_id: str
    snapshot_date: date
    retrieved_at: datetime
    source_uri: str
    license_id: str
    # SHA-256 of the canonical normalized territory and geometry payload.
    checksum_sha256: str
    coordinate_system: Wgs84Crs
    # The supplier's coverage statement, not a claim of verified completeness.
    declared_scope: str
    normalization_version: str


@dataclass(frozen=True)
class TerritoryGeometry:
    territory_id: str
    geometry: GeometryWgs84
    reference_id: str
    coordinate_system: Wgs84Crs


@dataclass(frozen=True)
class ReferenceSnapshot:
    manifest: ReferenceManifest
    territories: tuple[Territory, ...]
    geometries: tuple[TerritoryGeometry, ...]


@dataclass(frozen=True)
class ExpectedInventory:
    # Independently established IDs, never inferred from the imported snapshot.
    region_ids: dict[CountryCode, frozenset[str]]
    pilot_district_ids: dict[str, frozenset[str]]
    source_uri: str
    version: str


class TerritoryReferenceError(ValueError):
    pass


class TerritoryIncompleteError(TerritoryReferenceError):
    pass


class CatalogDepthUnsupported(ValueError):
    pass


class TerritoryNotFound(LookupError):
    pass


class ReferenceUnavailableError(LookupError):
    pass


class TerritoryCatalog(Protocol):
    async def list_regions(self, country: CountryCode) -> tuple[Territory, ...]: ...
    async def list_districts(self, region_id: str) -> tuple[Territory, ...]: ...
    async def get(self, territory_id: str) -> Territory | None: ...
    async def get_geometry(self, territory_id: str) -> TerritoryGeometry | None: ...


@dataclass(frozen=True)
class TerritoryAtPoint:
    region_id: str
    district_id: str | None


@runtime_checkable
class TerritoryPointLocator(Protocol):
    async def locate_point(
        self, *, country: CountryCode, longitude: float, latitude: float
    ) -> TerritoryAtPoint | None: ...


class SourceTerritoryCodeLookup(Protocol):
    """Resolve a source-specific numeric identifier from a canonical territory ID."""

    async def find_code(
        self, *, source_id: str, country: CountryCode, region_id: str
    ) -> int | None: ...


class SourceDistrictCodeLookup(Protocol):
    """Resolve a reviewed provider district ID without guessing from GeoJSON IDs."""

    async def find_district_code(
        self, *, source_id: str, country: CountryCode, region_id: str, district_id: str
    ) -> int | None: ...


class TerritoryImport(Protocol):
    async def validate_reference(
        self, snapshot: ReferenceSnapshot, inventory: ExpectedInventory
    ) -> None: ...
    async def apply_reference(
        self, snapshot: ReferenceSnapshot, inventory: ExpectedInventory
    ) -> None: ...
