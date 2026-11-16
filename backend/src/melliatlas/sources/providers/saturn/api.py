"""Saturn-specific published data types and bounded page declarations.

The transport, source reader and offline parsing functions live in feature
modules and are explicitly exported by this provider's package facade.
"""

from melliatlas.sources.api import TreatmentNotice, TreatmentNoticeReader, TreatmentProduct

from .legacy_treatment import SATURN_FIXTURE_PARSER_VERSION
from .pagination import MAX_PAGE_RECORDS, SaturnTreatmentPage

__all__ = [
    "TreatmentNotice",
    "TreatmentNoticeReader",
    "TreatmentProduct",
    "SaturnTreatmentPage",
    "MAX_PAGE_RECORDS",
    "SATURN_FIXTURE_PARSER_VERSION",
]
