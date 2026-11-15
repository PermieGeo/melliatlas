"""Public offline Saturn decoder and pagination exports.

This module performs no network I/O; source transport requires separate approval.
"""

from melliatlas.sources.notices import TreatmentNotice, TreatmentProduct
from melliatlas.sources.providers.saturn.legacy_treatment import (
    SATURN_FIXTURE_PARSER_VERSION,
    parse_saturn_treatment_page,
)
from melliatlas.sources.providers.saturn.pagination import (
    MAX_PAGE_RECORDS,
    SaturnTreatmentPage,
    next_saturn_treatment_page,
)

__all__ = [
    "TreatmentProduct",
    "TreatmentNotice",
    "MAX_PAGE_RECORDS",
    "SATURN_FIXTURE_PARSER_VERSION",
    "SaturnTreatmentPage",
    "parse_saturn_treatment_page",
    "next_saturn_treatment_page",
]
