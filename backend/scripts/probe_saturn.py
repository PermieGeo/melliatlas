"""Manually inspect the historical Saturn page response without exposing records.

Run only after reviewing upstream access terms. Exactly one bounded HTTP request
is sent; no raw response, cookies, record IDs, coordinates or notices are logged.
"""

import argparse
import json
from dataclasses import asdict

from melliatlas.sources.providers.saturn.diagnostics import probe_one_page
from melliatlas.sources.providers.saturn.http import post_public_page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region-code", type=int, required=True, help="Upstream numeric RU subject code"
    )
    parser.add_argument("--page", type=int, default=0, help="One zero-based page, max 50")
    args = parser.parse_args()
    if not 1 <= args.region_code <= 999999 or not 0 <= args.page <= 50:
        parser.error("region-code must be 1..999999 and page must be 0..50")

    report = probe_one_page(
        region_code=args.region_code, page_number=args.page, transport=post_public_page
    )
    print(json.dumps(asdict(report), sort_keys=True, separators=(",", ":")))
    return 0 if report.outcome == "PARSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
