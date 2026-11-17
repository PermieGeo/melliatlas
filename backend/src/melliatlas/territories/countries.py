"""Supported country identity and presentation metadata, owned by territories."""

from types import MappingProxyType
from typing import Final, Mapping

from .api import CountryCode

_COUNTRY_NAMES: Final[Mapping[CountryCode, str]] = MappingProxyType(
    {CountryCode.RU: "Russia", CountryCode.BY: "Belarus"}
)


def supported_countries() -> tuple[tuple[CountryCode, str], ...]:
    """Expose only configured countries, without tying HTTP routes to enum members."""
    return tuple((code, _COUNTRY_NAMES[code]) for code in CountryCode if code in _COUNTRY_NAMES)
