"""Offline normalization of an observed legacy Saturn beekeeper treatment-page shape.

This module never contacts a provider. Decoded entries are unverified source claims,
not verified spraying events, licensed live data, or apiary safety assessments.
"""

from datetime import datetime, timezone
from typing import Literal, TypeGuard

from melliatlas.sources.notices import TreatmentNotice, TreatmentProduct
from melliatlas.sources.providers.saturn.geometry import parse_field_geometry
from melliatlas.sources.providers.saturn.pagination import MAX_PAGE_RECORDS, SaturnTreatmentPage
from melliatlas.territories.api import CountryCode

SATURN_FIXTURE_PARSER_VERSION = "saturn-planapplybees-legacy-v1"
MAX_UNIX_SECONDS = 253_402_300_799


def _is_mapping(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _object(value: object) -> dict[str, object] | None:
    if not _is_mapping(value):
        return None
    parsed: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            return None
        parsed[key] = item
    return parsed


def _nonnegative(value: object, *, maximum: int | None = None) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("Invalid source pagination integer")
    if maximum is not None and value > maximum:
        raise ValueError("Source pagination exceeds local resource budget")
    return value


def _identifier(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return str(value)
    return None


def _text(value: object) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _unix_timestamp(value: object) -> datetime | None:
    if isinstance(value, str):
        if not value.isascii() or not value.isdecimal() or len(value) > 12:
            return None
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_UNIX_SECONDS:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _hazard_class(value: object) -> Literal[1, 2, 3] | None:
    if isinstance(value, str) and value in ("1", "2", "3"):
        value = int(value)
    if isinstance(value, int) and not isinstance(value, bool):
        if value == 1:
            return 1
        if value == 2:
            return 2
        if value == 3:
            return 3
    return None


def _products(value: object) -> tuple[TreatmentProduct, ...]:
    if not _is_list(value):
        return ()
    if len(value) > 100:
        raise ValueError("Source product list exceeds local resource budget")
    result: list[TreatmentProduct] = []
    for item in value:
        product = _object(item)
        if product is None:
            continue
        result.append(
            TreatmentProduct(
                name=_text(product.get("patName")),
                crop=_text(product.get("regulationCropName")),
                reported_bee_hazard_class=_hazard_class(product.get("patProductDangerClassBee")),
            )
        )
    return tuple(result)


def parse_saturn_treatment_page(
    payload: object,
    *,
    captured_at: datetime,
    source_id: str = "saturn:fixture-treatment",
    source_uri: str | None = None,
) -> SaturnTreatmentPage:
    """Parse one offline fixture page; never perform network I/O or infer a live feed."""
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError("captured_at must be timezone-aware")
    if not source_id.strip():
        raise ValueError("source_id must be nonempty")
    if source_uri is not None and not source_uri.strip():
        raise ValueError("source_uri must be nonempty when supplied")
    page = _object(payload)
    if page is None:
        raise ValueError("Source page must be an object")
    content = page.get("content")
    if not _is_list(content) or len(content) > MAX_PAGE_RECORDS:
        raise ValueError("Source page must have a bounded content list")
    total_elements = _nonnegative(page.get("totalElements"))
    page_number = _nonnegative(page.get("number"))
    page_size = _nonnegative(page.get("size"), maximum=MAX_PAGE_RECORDS)
    count = _nonnegative(page.get("numberOfElements"), maximum=MAX_PAGE_RECORDS)
    total_pages = _nonnegative(page.get("totalPages"))
    if page_size == 0:
        raise ValueError("Source page size must be positive")
    last = page.get("last")
    if last is not None and not isinstance(last, bool):
        raise ValueError("Source last-page marker must be Boolean")
    pageable = _object(page.get("pageable"))
    if page.get("pageable") is not None and pageable is None:
        raise ValueError("Source pageable must be an object")
    if pageable is not None:
        nested_number = _nonnegative(pageable.get("pageNumber"))
        nested_size = _nonnegative(pageable.get("pageSize"), maximum=MAX_PAGE_RECORDS)
        if nested_size == 0:
            raise ValueError("Source page size must be positive")
        if page_number is not None and nested_number is not None and page_number != nested_number:
            raise ValueError("Conflicting source page numbers")
        if page_size is not None and nested_size is not None and page_size != nested_size:
            raise ValueError("Conflicting source page sizes")
        page_number = page_number if page_number is not None else nested_number
        page_size = page_size if page_size is not None else nested_size
    if count is not None and count != len(content):
        raise ValueError("Source page element count mismatch")

    notices: list[TreatmentNotice] = []
    seen_record_ids: set[str] = set()
    unidentified = 0
    for item in content:
        raw = _object(item)
        if raw is None:
            raise ValueError("Source page content must contain objects")
        if (
            raw.get("beeAcreage") is None
            and raw.get("planId") is not None
            and isinstance(raw.get("centerX"), (int, float))
            and isinstance(raw.get("centerY"), (int, float))
        ):
            raise ValueError("Saturn map-index centers are not treatment notices")
        acreage = _object(raw.get("beeAcreage"))
        if acreage is None:
            unidentified += 1
            continue
        record_id = _identifier(acreage.get("id"))
        if record_id is None:
            unidentified += 1
            continue
        if record_id in seen_record_ids:
            raise ValueError("Duplicate Saturn field identity in one page")
        seen_record_ids.add(record_id)
        flag = acreage.get("isUpdated")
        revised = flag if isinstance(flag, bool) else None
        scheduled_start = _unix_timestamp(
            acreage.get("planDateUpdate") if revised is True else acreage.get("planDate")
        )
        scheduled_end = _unix_timestamp(
            acreage.get("planDateEndUpdate") if revised is True else acreage.get("planDateEnd")
        )
        if flag is not None and revised is None:
            scheduled_start = None
            scheduled_end = None
        if scheduled_start is not None and scheduled_end is not None:
            if scheduled_end < scheduled_start:
                scheduled_start = None
                scheduled_end = None
        geometry = parse_field_geometry(_object(acreage.get("geo")))
        uncertainties = ["Unverified fixture record; no actual application is established"]
        if scheduled_start is None or scheduled_end is None:
            uncertainties.append(
                "Planned application interval is missing, revised or contradictory"
            )
        if geometry is None:
            uncertainties.append("Valid source-linked field polygon is unavailable")
        notices.append(
            TreatmentNotice(
                record_id=record_id,
                plan_id=_identifier(acreage.get("planId")),
                country=CountryCode.RU,
                source_id=source_id,
                source_uri=source_uri,
                parser_version="saturn-planapplybees-legacy-v1",
                source_mode="FIXTURE",
                synthetic=True,
                captured_at=captured_at,
                published_at=_unix_timestamp(acreage.get("datePublishing")),
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                revised=revised,
                contractor_name=_text(acreage.get("contractorName")),
                cadastral_number=_text(acreage.get("cadNum")),
                geometry=geometry,
                products=_products(raw.get("allPatList")),
                uncertainties=tuple(uncertainties),
            )
        )
    return SaturnTreatmentPage(
        notices=tuple(notices),
        unidentified_records=unidentified,
        page_number=page_number,
        total_elements=total_elements,
        page_size=page_size,
        total_pages=total_pages,
        last=last if isinstance(last, bool) else None,
    )
