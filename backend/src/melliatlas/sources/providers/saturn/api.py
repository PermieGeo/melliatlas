"""Saturn provider API: offline decoding plus explicit experimental live reading.

The source-specific functions normalize the historically observed Russia-only
``/planapplybees`` JSON format. ``legacy_treatment.py`` decodes treatment claims,
``geometry.py`` validates optional WGS84 field geometries, and ``pagination.py``
validates progress through bounded pages. Provider-neutral ``TreatmentNotice``
and ``TreatmentProduct`` models are defined in ``sources.notices``.

The normalizer and pagination helpers have no I/O. An opt-in live reader
in ``live.py`` consumes one bounded response supplied by the composition-root
HTTPS transport. This is based on an observed historical public-page request,
not a verified current upstream API or permission for reuse. Missing application
dates and absent or invalid geometries remain unknown, not favorable findings;
a reported treatment is not evidence that spraying occurred or a site is safe.

The backend transport exists but remains disabled by default. Reuse
permission, live endpoint compatibility, archival provenance and completeness
are unverified; no automatic collection or synthetic fallback is provided. Use this API rather than the retired
``sources.saturn`` facade for Saturn-specific parsing.
"""

from melliatlas.sources.notices import TreatmentNotice, TreatmentProduct
from melliatlas.sources.providers.saturn.legacy_treatment import (
    SATURN_FIXTURE_PARSER_VERSION,
    parse_saturn_treatment_page,
)
from melliatlas.sources.providers.saturn.live import SaturnPublicTreatmentReader
from melliatlas.sources.providers.saturn.pagination import (
    MAX_PAGE_RECORDS,
    SaturnTreatmentPage,
    next_saturn_treatment_page,
)

__all__ = [
    "TreatmentProduct",
    "SaturnPublicTreatmentReader",
    "TreatmentNotice",
    "MAX_PAGE_RECORDS",
    "SATURN_FIXTURE_PARSER_VERSION",
    "SaturnTreatmentPage",
    "parse_saturn_treatment_page",
    "next_saturn_treatment_page",
]
