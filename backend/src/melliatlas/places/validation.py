"""Validation of owner-independent saved-place values."""

import re
from uuid import UUID

from melliatlas.geography import Wgs84AnalysisBounds, make_analysis_bounds
from melliatlas.territories.api import CountryCode

from .api import InvalidSavedPlace, SavedPlaceDraft

_REGION_ID = re.compile(r"^(ru|by):region:[a-z0-9-]{1,32}$")


def validate_owner(owner_id: object) -> None:
    if not isinstance(owner_id, UUID) or owner_id.int == 0:
        raise InvalidSavedPlace("A non-nil owner UUID is required")


def validate_revision(revision: object) -> None:
    if type(revision) is not int or revision < 1:
        raise InvalidSavedPlace("A positive expected revision is required")


def _name(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidSavedPlace("A place name is required")
    name = value.strip()
    if not 1 <= len(name) <= 120 or any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise InvalidSavedPlace("A place name must contain 1–120 printable characters")
    return name


def _country(value: object) -> CountryCode:
    if not isinstance(value, CountryCode):
        raise InvalidSavedPlace("Unsupported country")
    return value


def _region(value: object, country: CountryCode) -> str:
    if not isinstance(value, str) or not _REGION_ID.fullmatch(value):
        raise InvalidSavedPlace("Invalid canonical region identifier")
    if not value.startswith(f"{country.value.lower()}:region:"):
        raise InvalidSavedPlace("Region does not belong to the selected country")
    return value


def validate_draft(draft: SavedPlaceDraft) -> tuple[SavedPlaceDraft, Wgs84AnalysisBounds]:
    name = _name(draft.name)
    country = _country(draft.country)
    region_id = _region(draft.region_id, country)
    try:
        bounds = make_analysis_bounds(
            longitude=draft.longitude,
            latitude=draft.latitude,
            width_km=draft.width_km,
            height_km=draft.height_km,
        )
    except (ValueError, TypeError, OverflowError) as error:
        raise InvalidSavedPlace("Invalid WGS84 point or analysis rectangle") from error
    return (
        SavedPlaceDraft(
            name=name,
            country=country,
            region_id=region_id,
            longitude=float(draft.longitude),
            latitude=float(draft.latitude),
            width_km=bounds.width_km,
            height_km=bounds.height_km,
        ),
        bounds,
    )
