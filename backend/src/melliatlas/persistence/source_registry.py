"""Provider mapping SQL and supported countries for the persistence adapter.

Adding a provider requires its own reviewed schema and explicit SQL registration.
Names and country limits are data in this adapter, not conditional domain logic.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, LiteralString, Mapping

from melliatlas.territories.api import CountryCode


@dataclass(frozen=True)
class SourceMappingQueries:
    supported_countries: frozenset[CountryCode]
    region: LiteralString
    district: LiteralString


SOURCE_MAPPING_QUERIES: Final[Mapping[str, SourceMappingQueries]] = MappingProxyType(
    {
        "saturn": SourceMappingQueries(
            supported_countries=frozenset({CountryCode.RU}),
            region="""
                SELECT saturn.subject_id
                FROM melliatlas_source_saturn AS saturn
                JOIN melliatlas_region AS region ON region.id = saturn.region_id
                WHERE saturn.region_id = %s AND region.country_code = %s
            """,
            district="""
                SELECT mapping.provider_district_code
                FROM melliatlas_source_saturn_district AS mapping
                JOIN melliatlas_admin_geometry AS district
                  ON district.territory_id = mapping.district_id AND district.kind = 'district'
                JOIN melliatlas_source_saturn AS subject
                  ON subject.region_id = district.region_id
                WHERE mapping.district_id = %s AND district.region_id = %s
                  AND district.country_code = %s
            """,
        ),
    }
)
