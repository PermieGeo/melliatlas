"""Public, offline Saturn treatment-notice decoder and pagination API.

The source-specific functions normalize the historically observed Russia-only
``/planapplybees`` JSON format. ``legacy_treatment.py`` decodes treatment claims,
``geometry.py`` validates optional WGS84 field geometries, and ``pagination.py``
validates progress through bounded pages. Provider-neutral ``TreatmentNotice``
and ``TreatmentProduct`` models are defined in ``sources.notices``.

These functions process caller-supplied payloads without network or persistence
I/O. They do not imply current permission to access Saturn. Missing application
dates and absent or invalid geometries remain unknown, not favorable findings;
a reported treatment is not evidence that spraying occurred or a site is safe.

Live transport, access approval, provenance capture and immutable source records
require separately authorized work. Use this API rather than the retired
``sources.saturn`` facade for Saturn-specific parsing.
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
