"""Shared bounded response limits for the experimental Saturn provider."""

from calendar import monthrange
from datetime import date

MAX_BODY_BYTES = 1_000_000
SOURCE_PAGE_SIZE = 10
MAX_SOURCE_RECORDS = 100
MAX_SOURCE_PAGE = MAX_SOURCE_RECORDS // SOURCE_PAGE_SIZE - 1


def valid_source_date_window(start: date, end: date) -> bool:
    """Allow up to one calendar year, clamping February 29 in a non-leap year."""
    if end < start:
        return False
    if start.year == date.max.year:
        return True
    latest_day = min(start.day, monthrange(start.year + 1, start.month)[1])
    return end <= date(start.year + 1, start.month, latest_day)
