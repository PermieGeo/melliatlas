"""Provider-specific sanitized source failure reasons.

These are internal diagnostic categories; public HTTP failures use the
provider-neutral SOURCE_READ_FAILED code and never reveal upstream details.
"""

from enum import StrEnum


class SaturnReadFailure(StrEnum):
    """Sanitized provider-only transport and decoder failures."""

    SATURN_PAGE_HTTP = "Public portal did not return HTTP 200"
    SATURN_PAGE_TYPE = "Public portal response is not JSON"
    SATURN_PAGE_ENCODING = "Unsupported public portal response encoding"
    SATURN_PAGE_SIZE = "Public portal response exceeds size budget"
    SATURN_PAGE_REQUEST = "Public portal request failed"
    SATURN_DIRECTORY_HTTP = "Public subject directory did not return HTTP 200"
    SATURN_DIRECTORY_TYPE = "Public subject directory response is not JSON"
    SATURN_DIRECTORY_ENCODING = "Unsupported public subject directory encoding"
    SATURN_DIRECTORY_SIZE = "Public subject directory exceeds size budget"
    SATURN_DIRECTORY_REQUEST = "Public subject directory request failed"
    SATURN_PAGE_FORMAT = "Unexpected public portal response format"
