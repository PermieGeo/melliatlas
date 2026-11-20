"""Opt-in, single-page read from the historically observed public Saturn endpoint.

This is experimental transport, not an official stable API or evidence of data
reuse permission. Do not follow redirects, retry, crawl, or supply credentials.
"""

import json
import logging
from collections.abc import Callable
from datetime import date, datetime, time, timezone
from time import perf_counter
from typing import TypeGuard
from uuid import uuid4

from melliatlas.sources.api import SourceReadError, TreatmentNotice, TreatmentNoticePage
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
_LOG = logging.getLogger("melliatlas.sources.providers.saturn")


def _is_dict(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return _is_dict(value) and all(isinstance(key, str) for key in value)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _reported_code_counts(payload: object, key: str, expected: int | None) -> tuple[int, int, int]:
    """Count source-declared matches, mismatches and absent codes without exposing records."""
    if expected is None or not _is_object(payload):
        return (0, 0, 0)
    content = payload.get("content")
    if not _is_list(content):
        return (0, 0, 0)
    matched = different = missing = 0
    for item in content:
        if not _is_object(item):
            continue
        acreage = item.get("beeAcreage")
        if not _is_object(acreage):
            continue
        reported = acreage.get(key)
        if reported is None:
            missing += 1
        elif type(reported) is int and reported == expected:
            matched += 1
        else:
            different += 1
    return matched, different, missing


def _reported_date_counts(
    notices: tuple[TreatmentNotice, ...], start: date | None, end: date | None
) -> tuple[int, int, int]:
    """Compare normalized application intervals to the requested window, not publication dates."""
    if start is None or end is None:
        return (0, 0, 0)
    overlapping = outside = unknown = 0
    for notice in notices:
        if notice.scheduled_start is None or notice.scheduled_end is None:
            unknown += 1
        elif notice.scheduled_end.date() < start or notice.scheduled_start.date() > end:
            outside += 1
        else:
            overlapping += 1
    return overlapping, outside, unknown


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
        read_id = uuid4().hex[:12]
        started = perf_counter()
        _LOG.info(
            "saturn.read.start id=%s endpoint=planapplybees page=%d size=%d "
            "subject=%d district=%s date_from=%s date_to=%s bbox_filter=none",
            read_id,
            page_number,
            SOURCE_PAGE_SIZE,
            region_code,
            district_code,
            source_filter.get("startDateUpdateMap"),
            source_filter.get("endDateUpdateMap"),
        )
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
        except SourceReadError as error:
            reason = next(
                (failure.name for failure in SaturnReadFailure if failure.value == str(error)),
                "UNKNOWN_SOURCE_ERROR",
            )
            _LOG.warning(
                "saturn.read.failed id=%s stage=transport_or_size reason=%s elapsed_ms=%d",
                read_id,
                reason,
                round((perf_counter() - started) * 1000),
            )
            raise
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            _LOG.warning(
                "saturn.read.failed id=%s stage=decode_or_pagination kind=%s elapsed_ms=%d",
                read_id,
                type(error).__name__,
                round((perf_counter() - started) * 1000),
            )
            raise SourceReadError(SaturnReadFailure.SATURN_PAGE_FORMAT) from error

        subject_match, subject_other, subject_missing = _reported_code_counts(
            payload, "subject", region_code
        )
        district_match, district_other, district_missing = _reported_code_counts(
            payload, "district", district_code
        )
        date_overlap, date_outside, date_unknown = _reported_date_counts(
            page.notices, start_date, end_date
        )
        geometry_count = sum(notice.geometry is not None for notice in page.notices)
        _LOG.info(
            "saturn.read.done id=%s elapsed_ms=%d bytes=%d page=%d "
            "source_total=%s source_pages=%s source_size=%s source_last=%s "
            "notices=%d unidentified=%d geometry=%d "
            "subject_match=%d subject_other=%d subject_missing=%d "
            "district_match=%d district_other=%d district_missing=%d "
            "date_overlap=%d date_outside=%d date_unknown=%d "
            "next_page=%s bbox_filter=none",
            read_id,
            round((perf_counter() - started) * 1000),
            len(raw),
            page_number,
            page.total_elements,
            page.total_pages,
            page.page_size,
            page.last,
            len(page.notices),
            page.unidentified_records,
            geometry_count,
            subject_match,
            subject_other,
            subject_missing,
            district_match,
            district_other,
            district_missing,
            date_overlap,
            date_outside,
            date_unknown,
            next_page,
        )
        if subject_other or district_other or date_outside:
            _LOG.warning(
                "saturn.read.scope_anomaly id=%s subject_other=%d "
                "district_other=%d date_outside=%d; "
                "missing source district codes are inconclusive",
                read_id,
                subject_other,
                district_other,
                date_outside,
            )
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
