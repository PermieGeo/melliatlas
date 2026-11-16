"""Operator-only, exclusive local capture of a reviewed public directory response."""

import hashlib
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path


def capture_subjects(
    destination: Path, fetch: Callable[[], bytes], validate: Callable[[bytes], int]
) -> tuple[int, str, datetime]:
    """Reserve a private output first; never fetch when it cannot be written.

    Failed validation or transport removes the uncommitted capture file.
    """
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as destination_file:
            raw = fetch()
            count = validate(raw)
            captured_at = datetime.now(timezone.utc)
            destination_file.write(raw)
            destination_file.flush()
            os.fsync(destination_file.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return count, hashlib.sha256(raw).hexdigest(), captured_at
