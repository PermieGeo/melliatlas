"""Opt-in, single-page read from the historically observed public Saturn endpoint.

This is experimental transport, not an official stable API or evidence of data
reuse permission. Do not follow redirects, retry, crawl, or supply credentials.
"""

import json
from collections.abc import Callable
from datetime import date, datetime, time, timezone

from melliatlas.sources.api import SourceReadError, TreatmentNoticePage
from melliatlas.sources.providers.saturn.failures import SaturnReadFailure
from melliatlas.sources.providers.saturn.legacy_treatment import parse_saturn_treatment_page
from melliatlas.sources.providers.saturn.limits import (
    MAX_BODY_BYTES,
    MAX_SOURCE_PAGE,
    SOURCE_PAGE_SIZE,
    valid_source_date_window,
)
from melliatlas.sources.providers.saturn.pagination import next_saturn_treatment_page
from melliatlas.territories.api import CountryCode

SATURN_SOURCE_ID = "saturn:public-beekeeper-portal"


class SaturnPublicTreatmentReader:
    """Read one explicit RU page, returning attributed claims without safety inferences."""

    def __init__(self, transport: Callable[[bytes], bytes]) -> None:
        self._transport = transport

    def read_page(
        self,
        *,
        country: CountryCode,
        region_code: int,
        page_number: int,
        district_code: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TreatmentNoticePage:
        if country is not CountryCode.RU:
            raise ValueError("Saturn is restricted to RU")
        if type(region_code) is not int or not 1 <= region_code <= 999999:
            raise ValueError("Saturn region code must be a positive provider identifier")
        if type(page_number) is not int or not 0 <= page_number <= MAX_SOURCE_PAGE:
            raise ValueError("Saturn page is outside the bounded manual range")
        if district_code is not None and (
            type(district_code) is not int or not 1 <= district_code <= 999999
        ):
            raise ValueError("Saturn district code must be a reviewed positive identifier")
        if (start_date is None) != (end_date is None):
            raise ValueError("Both Saturn date limits are required")
        if start_date is not None and end_date is not None:
            if not valid_source_date_window(start_date, end_date):
                raise ValueError("Saturn date interval must be ordered and at most one year")
        source_filter: dict[str, int | str] = {"subject": region_code}
        if district_code is not None:
            source_filter["district"] = district_code
        if start_date is not None and end_date is not None:
            source_filter["startDateUpdateMap"] = (
                datetime.combine(start_date, time.min, tzinfo=timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
            source_filter["endDateUpdateMap"] = (
                datetime.combine(end_date, time(23, 59, 59, 999000), tzinfo=timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
        body = json.dumps(
            {
                "pageNumber": page_number,
                "pageSize": SOURCE_PAGE_SIZE,
                "sortColumn": "datePublishing",
                "sortDirection": "desc",
                "beekeperSearchFilter": source_filter,
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
            if len(page.notices) + page.unidentified_records > SOURCE_PAGE_SIZE:
                raise ValueError("Saturn returned more than the requested page size")
            next_page = next_saturn_treatment_page(
                page, requested_page=page_number, requested_size=SOURCE_PAGE_SIZE
            )
            # Preserve the source cursor for the HTTP layer to report truncation.
            # Further reads remain forbidden by MAX_SOURCE_PAGE.
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
