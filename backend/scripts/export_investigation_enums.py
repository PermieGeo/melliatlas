"""Generate and verify the client investigation enum contract from backend enums.

Run from the repository root; this only touches the generated TypeScript source.
"""

import argparse
from pathlib import Path

from melliatlas.jobs.api import InvestigationOutcomeKind, InvestigationStatus

OUTPUT = Path(__file__).resolve().parents[2] / "web/src/api/generated/investigationEnums.ts"


def _type_and_values(name: str, values: tuple[str, ...]) -> str:
    items = "\n".join(f'  "{value}",' for value in values)
    return f"export const {name} = [\n{items}\n] as const;\n"


def render_typescript() -> str:
    """Keep both runtime validators and union types synchronized to Python enums."""
    return (
        "// Generated from backend investigation enums. Do not edit manually.\n"
        + _type_and_values(
            "INVESTIGATION_STATUSES", tuple(status.value for status in InvestigationStatus)
        )
        + "export type InvestigationStatus = (typeof INVESTIGATION_STATUSES)[number];\n\n"
        + _type_and_values(
            "INVESTIGATION_OUTCOMES", tuple(outcome.value for outcome in InvestigationOutcomeKind)
        )
        + "export type Outcome = (typeof INVESTIGATION_OUTCOMES)[number];\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated TS is outdated")
    args = parser.parse_args()
    expected = render_typescript()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            parser.error("Generated investigation enums differ from backend: regenerate")
        return
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8")


if __name__ == "__main__":
    main()
