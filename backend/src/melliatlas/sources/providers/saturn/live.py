"""Opt-in, single-page read from the historically observed public Saturn endpoint.

This is experimental transport, not an official stable API or evidence of data
reuse permission. Do not follow redirects, retry, crawl, or supply credentials.
"""

import json
from collections.abc import Callable
from datetime import datetime, timezone

from melliatlas.sources.api import SourceReadError, TreatmentNoticePage
from melliatlas.sources.providers.saturn.failures import SaturnReadFailure
from melliatlas.sources.providers.saturn.legacy_treatment import parse_saturn_treatment_page
from melliatlas.sources.providers.saturn.limits import MAX_BODY_BYTES
from melliatlas.sources.providers.saturn.pagination import next_saturn_treatment_page
from melliatlas.territories.api import CountryCode

SATURN_SOURCE_ID = "saturn:public-beekeeper-portal"
PAGE_SIZE = 10
MAX_PAGE = 50


class SaturnPublicTreatmentReader:
    """Read one explicit RU page, returning attributed claims without safety inferences."""

    def __init__(self, transport: Callable[[bytes], bytes]) -> None:
        self._transport = transport

    def read_page(
        self, *, country: CountryCode, region_code: int, page_number: int
    ) -> TreatmentNoticePage:
        if country is not CountryCode.RU:
            raise ValueError("Saturn is restricted to RU")
        if type(region_code) is not int or not 1 <= region_code <= 999999:
            raise ValueError("Saturn region code must be a positive provider identifier")
        if type(page_number) is not int or not 0 <= page_number <= MAX_PAGE:
            raise ValueError("Saturn page is outside the bounded manual range")
        body = json.dumps(
            {
                "pageNumber": page_number,
                "pageSize": PAGE_SIZE,
                "sortColumn": "datePublishing",
                "sortDirection": "desc",
                "beekeperSearchFilter": {"subject": region_code},
            },
            separators=(",", ":"),
        ).encode("utf-8")
        try:
            raw = self._transport(body)
            if len(raw) > MAX_BODY_BYTES:
                raise SourceReadError(SaturnReadFailure.SATURN_PAGE_SIZE)
            payload: object = json.loads(raw)
            now = datetime.now(timezone.utc)
            page = parse_saturn_treatment_page(
                payload,
                captured_at=now,
                source_id=SATURN_SOURCE_ID,
                source_uri="https://bee.fgis-saturn.ru/",
                source_mode="LIVE",
            )
            next_page = next_saturn_treatment_page(
                page, requested_page=page_number, requested_size=PAGE_SIZE
            )
            if next_page is not None and next_page > MAX_PAGE:
                next_page = None
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            raise SourceReadError(SaturnReadFailure.SATURN_PAGE_FORMAT) from error
        return TreatmentNoticePage(
            source_id=SATURN_SOURCE_ID,
            country=CountryCode.RU,
            region_code=region_code,
            captured_at=now,
            page_number=page_number,
            next_page=next_page,
            total_elements=page.total_elements,
            unidentified_records=page.unidentified_records,
            notices=page.notices,
        )
