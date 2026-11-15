"""Compatibility exports for the earlier Saturn parser module.

New implementation belongs to sources.providers.saturn; peers use sources.api.
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
