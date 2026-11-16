"""Explicit one-request Saturn subject capture; never run at application startup."""

import argparse
import sys
from pathlib import Path

from melliatlas.api.subject_capture import capture_subjects
from melliatlas.sources.api import SourceReadError
from melliatlas.sources.providers.saturn.http import get_public_subject_directory
from melliatlas.sources.providers.saturn.subjects import validate_subject_directory


def _validate_full_directory(raw: bytes) -> int:
    return len(validate_subject_directory(raw, min_entries=80))


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture one Saturn subject catalog for review")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        count, digest, captured_at = capture_subjects(
            args.output, get_public_subject_directory, _validate_full_directory
        )
    except (SourceReadError, ValueError, OSError) as exc:
        print(f"Saturn subject capture failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    print(f"Captured {count} Saturn subject entries")
    print(f"Capture SHA-256: {digest}")
    print(f"Captured at (UTC): {captured_at.isoformat()}")
    print("Review the local file before importing; coverage and reuse rights are unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
