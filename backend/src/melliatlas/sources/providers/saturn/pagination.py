"""Pagination envelope and conservative cursor advancement for Saturn fixtures."""

from dataclasses import dataclass

from melliatlas.sources.notices import TreatmentNotice

MAX_PAGE_RECORDS = 200


@dataclass(frozen=True)
class SaturnTreatmentPage:
    notices: tuple[TreatmentNotice, ...]
    unidentified_records: int
    page_number: int | None
    total_elements: int | None
    page_size: int | None
    total_pages: int | None
    last: bool | None


def next_saturn_treatment_page(
    page: SaturnTreatmentPage, *, requested_page: int, requested_size: int
) -> int | None:
    """Validate pagination before any future persistence or cursor advancement."""
    if requested_page < 0 or not 1 <= requested_size <= MAX_PAGE_RECORDS:
        raise ValueError("Invalid requested source pagination")
    count = len(page.notices) + page.unidentified_records
    offset = requested_page * requested_size
    total = page.total_elements
    total_pages = page.total_pages
    last = page.last
    if (page.page_number is not None and page.page_number != requested_page) or (
        page.page_size is not None and page.page_size != requested_size
    ):
        raise ValueError("Provider page does not match requested pagination")
    if total is not None and (offset + count > total or (offset >= total and requested_page > 0)):
        raise ValueError("Provider page total is inconsistent")
    if total_pages is not None and (
        (total_pages == 0 and (requested_page != 0 or count != 0 or last is False))
        or (
            total_pages > 0
            and (
                requested_page >= total_pages
                or count == 0
                or (requested_page < total_pages - 1 and count < requested_size)
                or (last is not None and last != (requested_page == total_pages - 1))
            )
        )
        or (total is not None and total_pages != (total + requested_size - 1) // requested_size)
    ):
        raise ValueError("Provider total page count is inconsistent")
    if (
        (total is not None and count < requested_size and offset + count < total)
        or (last is False and count < requested_size)
        or (total is not None and last is not None and last != (offset + requested_size >= total))
    ):
        raise ValueError("Provider reported inconsistent terminal page")
    if total is not None:
        return None if offset + requested_size >= total else requested_page + 1
    if total_pages is not None:
        return None if total_pages == 0 or requested_page == total_pages - 1 else requested_page + 1
    if last is not None:
        return None if last else requested_page + 1
    return None if count < requested_size else requested_page + 1
