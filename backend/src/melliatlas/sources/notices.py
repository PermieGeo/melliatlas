"""Provider-neutral, unverified claims about planned field treatments."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from melliatlas.territories.api import CountryCode, GeometryWgs84


@dataclass(frozen=True)
class TreatmentProduct:
    name: str | None
    crop: str | None
    reported_bee_hazard_class: Literal[1, 2, 3] | None


@dataclass(frozen=True)
class TreatmentNotice:
    """A claimed future treatment, not evidence that any spraying occurred."""

    record_id: str
    plan_id: str | None
    country: CountryCode
    source_id: str
    source_uri: str | None
    parser_version: Literal["saturn-planapplybees-legacy-v1"]
    source_mode: Literal["FIXTURE", "LIVE"]
    synthetic: bool
    captured_at: datetime
    published_at: datetime | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    revised: bool | None
    contractor_name: str | None
    cadastral_number: str | None
    geometry: GeometryWgs84 | None
    products: tuple[TreatmentProduct, ...]
    uncertainties: tuple[str, ...]
