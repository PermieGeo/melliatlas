"""Public, provider-independent contracts for owner-scoped saved analysis places."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from melliatlas.territories.api import CountryCode


@dataclass(frozen=True)
class SavedPlaceDraft:
    name: str
    country: CountryCode
    region_id: str
    longitude: float
    latitude: float
    width_km: float = 15.0
    height_km: float = 15.0


@dataclass(frozen=True)
class SavedPlace:
    id: UUID
    owner_id: UUID
    draft: SavedPlaceDraft
    revision: int
    created_at: datetime
    updated_at: datetime


class InvalidSavedPlace(ValueError):
    """Draft dimensions, naming, or selected geographic region are invalid."""


class SavedPlaceLocationUnavailable(InvalidSavedPlace):
    """No unique, reviewed ADM1 polygon covers the center in its selected region."""


class SavedPlaceNotFound(LookupError):
    """Place is missing or inaccessible to the supplied owner."""


class SavedPlaceConflict(ValueError):
    """The supplied revision is stale."""


class SavedPlaceStorageError(RuntimeError):
    """Persistence failed without exposing SQL, credentials, or coordinates."""


class SavedPlaceRepository(Protocol):
    def create(self, *, owner_id: UUID, draft: SavedPlaceDraft) -> SavedPlace: ...
    def get(self, *, owner_id: UUID, place_id: UUID) -> SavedPlace | None: ...
    def list(self, *, owner_id: UUID) -> tuple[SavedPlace, ...]: ...
    def update(
        self, *, owner_id: UUID, place_id: UUID, expected_revision: int, draft: SavedPlaceDraft
    ) -> SavedPlace: ...
    def delete(self, *, owner_id: UUID, place_id: UUID, expected_revision: int) -> None: ...
