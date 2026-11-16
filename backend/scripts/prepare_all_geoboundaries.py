"""Stage missing RU/BY ADM1/ADM2 layers with visible progress and safe reuse."""

import argparse
import json
import sys
from pathlib import Path

from prepare_geoboundaries import prepare

LAYERS = (("RU", "ADM1"), ("RU", "ADM2"), ("BY", "ADM1"), ("BY", "ADM2"))


def prepare_all(output_dir: Path) -> tuple[list[dict[str, object]], list[str]]:
    reports: list[dict[str, object]] = []
    errors: list[str] = []
    for country, level in LAYERS:
        print(f"\n==> {country}/{level}", file=sys.stderr, flush=True)
        try:
            report = prepare(country, level, output_dir)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            message = f"{country}/{level}: {exc}"
            print(f"ERROR {message}", file=sys.stderr, flush=True)
            errors.append(message)
        else:
            reports.append(report)
            print(
                f"{country}/{level}: {'REUSED' if report.get('reused') else 'STAGED'}; "
                f"{report['unit_count']} units; review={report['review_status']}",
                file=sys.stderr,
                flush=True,
            )
    return reports, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Download missing reviewed RU/BY boundary layers")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    reports, errors = prepare_all(args.output_dir)
    mismatches = [
        f"{report['country']}/{report['level']}"
        for report in reports
        if report["review_status"] == "inventory_mismatch"
    ]
    print(
        json.dumps(
            {"layers": reports, "errors": errors, "inventory_mismatches": mismatches},
            ensure_ascii=False,
            indent=2,
        )
    )
    if errors:
        raise SystemExit(1)
    if mismatches:
        print(
            "All downloads staged. Source inventory mismatches require review "
            "before PostGIS import.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    print(
        "All four layers staged. Review licenses and regional matches before import.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
