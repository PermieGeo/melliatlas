"""The generated client enum contract must track the backend public enums."""

from pathlib import Path

from export_investigation_enums import OUTPUT, render_typescript

from melliatlas.jobs.api import InvestigationOutcomeKind, InvestigationStatus


def test_generated_frontend_enums_match_backend() -> None:
    assert (
        OUTPUT
        == Path(__file__).resolve().parents[3] / "web/src/api/generated/investigationEnums.ts"
    )
    assert OUTPUT.read_text(encoding="utf-8") == render_typescript()
    for status in InvestigationStatus:
        assert f'"{status.value}"' in render_typescript()
    for outcome in InvestigationOutcomeKind:
        assert f'"{outcome.value}"' in render_typescript()
