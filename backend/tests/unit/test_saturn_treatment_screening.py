"""MVP01-BE-R05/R14/R15: offline Saturn treatment evidence and conservative screening."""

import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from socket import socket
from unittest.mock import patch

import pytest

from melliatlas.analyzers import TreatmentProximity, screen_treatment_notices
from melliatlas.planning import CandidateSite, TimeWindow
from melliatlas.sources.providers.saturn.api import parse_saturn_treatment_page

CAPTURED_AT = datetime(2026, 5, 1, tzinfo=timezone.utc)
START = 1780617600  # 2026-06-05 UTC
END = 1780704000  # 2026-06-06 UTC
POLYGON = {
    "type": "Polygon",
    "coordinates": [[[32.0, 54.0], [32.04, 54.0], [32.04, 54.04], [32.0, 54.04], [32.0, 54.0]]],
}


def record(*, field_id: int = 71, geometry: object = POLYGON) -> dict[str, object]:
    return {
        "beeAcreage": {
            "id": field_id,
            "planId": 17,
            "contractorName": "FICTIONAL farm",
            "cadNum": "FICTIONAL-CAD-1",
            "planDate": START,
            "planDateEnd": END,
            "datePublishing": 1780185600,
            "geo": geometry,
        },
        "allPatList": [
            {
                "patName": "FICTIONAL product",
                "regulationCropName": "FICTIONAL crop",
                "patProductDangerClassBee": "2",
            }
        ],
    }


def page(*items: dict[str, object]) -> dict[str, object]:
    return {
        "content": list(items),
        "number": 0,
        "size": 20,
        "numberOfElements": len(items),
        "totalElements": len(items),
        "totalPages": 1,
        "last": True,
    }


def site(lon: float, lat: float = 54.02, start: date = date(2026, 6, 5)) -> CandidateSite:
    return CandidateSite(
        id="fixture-site",
        longitude=lon,
        latitude=lat,
        forage_window=TimeWindow(start, max(start, date(2026, 6, 20))),
        forage_level="MEDIUM",
        evidence_id="fixture-forage",
    )


def test_normalizes_per_field_identity_dates_products_and_unverified_claims() -> None:
    result = parse_saturn_treatment_page(
        page(record(field_id=71), record(field_id=72)), captured_at=CAPTURED_AT
    )
    assert len(result.notices) == 2
    first, second = result.notices
    assert first.record_id == "71" and second.record_id == "72"
    assert first.plan_id == second.plan_id == "17"
    assert first.country == "RU" and first.source_mode == "FIXTURE" and first.synthetic is True
    assert first.source_uri is None
    assert first.parser_version == "saturn-planapplybees-legacy-v1"
    assert first.scheduled_start == datetime.fromtimestamp(START, tz=timezone.utc)
    assert first.scheduled_end == datetime.fromtimestamp(END, tz=timezone.utc)
    assert first.published_at is not None
    assert first.scheduled_start is not None
    assert first.published_at < first.scheduled_start
    assert first.geometry is not None
    assert first.geometry["type"] == "Polygon"
    assert first.geometry["coordinates"][0][0] == (32.0, 54.0)
    assert first.products[0].reported_bee_hazard_class == 2
    assert "Unverified fixture" in first.uncertainties[0]


def test_updated_schedule_does_not_fall_back_to_obsolete_dates() -> None:
    updated = record()
    acreage = updated["beeAcreage"]
    assert isinstance(acreage, dict)
    acreage["isUpdated"] = True
    acreage["planDateUpdate"] = END
    acreage["planDateEndUpdate"] = END + 3600
    parsed = parse_saturn_treatment_page(page(updated), captured_at=CAPTURED_AT)
    assert parsed.notices[0].scheduled_start == datetime.fromtimestamp(END, tz=timezone.utc)
    del acreage["planDateUpdate"]
    parsed_missing = parse_saturn_treatment_page(page(updated), captured_at=CAPTURED_AT)
    assert parsed_missing.notices[0].scheduled_start is None
    assert parsed_missing.notices[0].scheduled_end is not None


def test_invalid_geometry_and_backwards_dates_are_unknown_not_discarded() -> None:
    broken = record(geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [0, 1]]]})
    acreage = broken["beeAcreage"]
    assert isinstance(acreage, dict)
    acreage["planDate"] = END
    acreage["planDateEnd"] = START
    parsed = parse_saturn_treatment_page(page(broken), captured_at=CAPTURED_AT)
    assert parsed.unidentified_records == 0
    assert parsed.notices[0].geometry is None
    assert parsed.notices[0].scheduled_start is None
    assert parsed.notices[0].scheduled_end is None
    assert any("contradictory" in note for note in parsed.notices[0].uncertainties)


def test_source_field_id_is_required_and_unsupported_hazard_is_not_invented() -> None:
    bad = record()
    acreage = bad["beeAcreage"]
    assert isinstance(acreage, dict)
    del acreage["id"]
    valid = record()
    products = valid["allPatList"]
    assert isinstance(products, list)
    products[0]["patProductDangerClassBee"] = 9
    result = parse_saturn_treatment_page(page(bad, valid), captured_at=CAPTURED_AT)
    assert result.unidentified_records == 1
    assert len(result.notices) == 1
    assert result.notices[0].products[0].reported_bee_hazard_class is None


def test_map_index_and_inconsistent_page_fail_before_processing() -> None:
    index: dict[str, object] = {"id": 1, "planId": 2, "centerX": 32.0, "centerY": 54.0}
    with pytest.raises(ValueError, match="not treatment notices"):
        parse_saturn_treatment_page(page(index), captured_at=CAPTURED_AT)
    inconsistent = page(record())
    inconsistent["pageable"] = {"pageNumber": 3, "pageSize": 20}
    with pytest.raises(ValueError, match="Conflicting source page numbers"):
        parse_saturn_treatment_page(inconsistent, captured_at=CAPTURED_AT)
    with pytest.raises(ValueError, match="bounded content"):
        parse_saturn_treatment_page({"content": [record()] * 201}, captured_at=CAPTURED_AT)
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_saturn_treatment_page(page(record()), captured_at=datetime(2026, 5, 1))


def test_known_field_overlap_and_nearby_warning_do_not_claim_safety() -> None:
    notices = parse_saturn_treatment_page(page(record()), captured_at=CAPTURED_AT).notices
    inside = screen_treatment_notices(site(32.02), notices)
    assert inside[0].proximity is TreatmentProximity.FIELD_INTERSECTION
    assert inside[0].approximate_distance_km == 0.0
    nearby = screen_treatment_notices(site(32.065), notices)
    assert nearby[0].proximity is TreatmentProximity.NEAR_REPORTED_FIELD
    assert nearby[0].approximate_distance_km is not None
    assert 0 < nearby[0].approximate_distance_km < 7
    far = screen_treatment_notices(site(34.0), notices)
    assert far[0].proximity is TreatmentProximity.OUTSIDE_SCREEN_RADIUS
    assert any("Wind" in warning for warning in far[0].warnings)


def test_missing_temporal_or_geometry_evidence_fails_to_unknown() -> None:
    absent_geometry = record(geometry=None)
    result = parse_saturn_treatment_page(page(absent_geometry), captured_at=CAPTURED_AT)
    assert screen_treatment_notices(site(32.02), result.notices)[0].proximity is (
        TreatmentProximity.UNKNOWN_GEOMETRY
    )
    missing_date = record()
    acreage = missing_date["beeAcreage"]
    assert isinstance(acreage, dict)
    del acreage["planDate"]
    result = parse_saturn_treatment_page(page(missing_date), captured_at=CAPTURED_AT)
    assert screen_treatment_notices(site(32.02), result.notices)[0].proximity is (
        TreatmentProximity.UNKNOWN_PERIOD
    )
    dated = parse_saturn_treatment_page(page(record()), captured_at=CAPTURED_AT)
    assert (
        screen_treatment_notices(site(32.02, start=date(2026, 7, 1)), dated.notices)[0].proximity
        is TreatmentProximity.OUTSIDE_STATED_PERIOD
    )


def test_no_io_or_unsolicited_saturn_fetch_during_fixture_screening() -> None:
    with patch.object(socket, "connect", side_effect=AssertionError("Network must stay disabled")):
        notices = parse_saturn_treatment_page(page(record()), captured_at=CAPTURED_AT).notices
        assert len(screen_treatment_notices(site(32.02), notices)) == 1


def test_screening_rejects_invalid_coordinates_or_radius() -> None:
    with pytest.raises(ValueError, match="watch_radius"):
        screen_treatment_notices(site(32.02), (), watch_radius_km=float("inf"))
    with pytest.raises(ValueError, match="WGS84"):
        screen_treatment_notices(site(181), ())


def test_pagination_validates_source_progress_without_fabricating_coverage() -> None:
    from melliatlas.sources.providers.saturn.api import next_saturn_treatment_page

    first_raw = page(record(field_id=71), record(field_id=72))
    first_raw.update({"size": 2, "totalElements": 3, "totalPages": 2, "last": False})
    first = parse_saturn_treatment_page(first_raw, captured_at=CAPTURED_AT)
    assert next_saturn_treatment_page(first, requested_page=0, requested_size=2) == 1
    last_raw = page(record(field_id=73))
    last_raw.update({"number": 1, "size": 2, "totalElements": 3, "totalPages": 2, "last": True})
    last = parse_saturn_treatment_page(last_raw, captured_at=CAPTURED_AT)
    assert next_saturn_treatment_page(last, requested_page=1, requested_size=2) is None
    with pytest.raises(ValueError, match="requested pagination"):
        next_saturn_treatment_page(last, requested_page=0, requested_size=2)
    malformed = page(record(field_id=74))
    malformed.update({"size": 2, "totalElements": 3, "totalPages": 2, "last": False})
    incomplete = parse_saturn_treatment_page(malformed, captured_at=CAPTURED_AT)
    with pytest.raises(ValueError, match="inconsistent"):
        next_saturn_treatment_page(incomplete, requested_page=0, requested_size=2)


def test_source_uri_is_retained_only_as_unverified_attribution() -> None:
    parsed = parse_saturn_treatment_page(
        page(record()),
        captured_at=CAPTURED_AT,
        source_uri="https://example.invalid/fictional-source-page",
    )
    assert parsed.notices[0].source_uri == "https://example.invalid/fictional-source-page"
    assert parsed.notices[0].source_mode == "FIXTURE"
    with pytest.raises(ValueError, match="source_uri"):
        parse_saturn_treatment_page(page(record()), captured_at=CAPTURED_AT, source_uri=" ")


def test_duplicate_field_identity_and_oversized_product_list_fail_explicitly() -> None:
    with pytest.raises(ValueError, match="Duplicate Saturn field"):
        parse_saturn_treatment_page(page(record(), record()), captured_at=CAPTURED_AT)
    oversized = record()
    oversized["allPatList"] = [{"patName": "FICTIONAL"}] * 101
    with pytest.raises(ValueError, match="product list"):
        parse_saturn_treatment_page(page(oversized), captured_at=CAPTURED_AT)


def test_unrecognized_revision_flag_does_not_revive_obsolete_dates() -> None:
    malformed = record()
    acreage = malformed["beeAcreage"]
    assert isinstance(acreage, dict)
    acreage["isUpdated"] = "true"
    parsed = parse_saturn_treatment_page(page(malformed), captured_at=CAPTURED_AT)
    assert parsed.notices[0].scheduled_start is None
    assert parsed.notices[0].scheduled_end is None


def test_public_notice_contract_is_available_before_any_provider_import() -> None:
    """Regression: unrelated HTTP modules must not fail pytest collection."""
    from melliatlas.analyzers import screen_treatment_notices as screen
    from melliatlas.sources import api as sources_api
    from melliatlas.sources.notices import TreatmentNotice as NoticeImplementation

    assert sources_api.TreatmentNotice is NoticeImplementation
    assert {"TreatmentNotice", "TreatmentProduct", "ScenarioProvider"} <= set(sources_api.__all__)
    assert not hasattr(sources_api, "parse_saturn_treatment_page")
    assert callable(screen)


def test_imports_do_not_require_provider_initialization_order() -> None:
    """Test fresh-interpreter import order, not only cached pytest modules."""
    env = os.environ.copy()
    root = Path(__file__).resolve().parents[2] / "src"
    env["PYTHONPATH"] = str(root)
    code = (
        "from melliatlas.analyzers import screen_treatment_notices; "
        "from melliatlas.sources.api import TreatmentNotice; "
        "from melliatlas.sources.providers.saturn.api import parse_saturn_treatment_page; "
        "from melliatlas.api.app import create_app; "
        "assert TreatmentNotice and parse_saturn_treatment_page and create_app"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_provider_compatibility_module_preserves_existing_exports() -> None:
    from melliatlas.sources.providers.saturn.api import parse_saturn_treatment_page as public_parser
    from melliatlas.sources.providers.saturn.legacy_treatment import (
        parse_saturn_treatment_page as legacy_parser,
    )

    assert public_parser is legacy_parser
