"""One operator-initiated capture of the public Smolensk Saturn district dictionary.

The capture is private, exclusive, bounded and never imported automatically.
Review external-service terms before making a request.
"""

import argparse
import sys
from pathlib import Path

from melliatlas.api.subject_capture import capture_subjects
from melliatlas.sources.api import SourceReadError
from melliatlas.sources.providers.saturn.districts import validate_district_directory
from melliatlas.sources.providers.saturn.http import get_smolensk_district_directory
from melliatlas.territories.api import CountryCode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        count, digest, captured_at = capture_subjects(
            args.output,
            get_smolensk_district_directory,
            lambda raw: len(validate_district_directory(raw, country=CountryCode.RU)),
        )
    except (SourceReadError, ValueError, OSError) as exc:
        print(f"District capture failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    print(f"Captured {count} Saturn Smolensk district entries")
    print(f"Capture SHA-256: {digest}")
    print(f"Captured at (UTC): {captured_at.isoformat()}")
    print("Review the complete local capture before approving an import")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
