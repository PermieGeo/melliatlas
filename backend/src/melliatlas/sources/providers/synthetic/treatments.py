"""Synthetic treatment page for the offline investigation walkthrough."""

from datetime import datetime, timezone

from melliatlas.sources.notices import TreatmentNotice
from melliatlas.sources.providers.saturn.legacy_treatment import parse_saturn_treatment_page

TREATMENT_FIXTURE_SOURCE_ID = "fixture:fictional-treatment-notices"
TREATMENT_FIXTURE_RECORD_ID = "fixture-treatment-field-71"


def treatment_fixture_notices() -> tuple[TreatmentNotice, ...]:
    """Decode a fictional legacy-shaped page without a provider or file read."""
    field = {
        "type": "Polygon",
        "coordinates": [
            [
                [31.98, 53.98],
                [32.02, 53.98],
                [32.02, 54.02],
                [31.98, 54.02],
                [31.98, 53.98],
            ]
        ],
    }
    payload = {
        "content": [
            {
                "beeAcreage": {
                    "id": TREATMENT_FIXTURE_RECORD_ID,
                    "planId": "fixture-plan-11",
                    "planDate": 1780617600,
                    "planDateEnd": 1780704000,
                    "datePublishing": 1780185600,
                    "isUpdated": False,
                    "geo": field,
                },
                "allPatList": [
                    {
                        "patName": "FICTIONAL demonstration product",
                        "regulationCropName": "FICTIONAL demonstration crop",
                        "patProductDangerClassBee": "2",
                    }
                ],
            }
        ],
        "number": 0,
        "size": 1,
        "numberOfElements": 1,
        "totalElements": 1,
        "totalPages": 1,
        "last": True,
    }
    page = parse_saturn_treatment_page(
        payload,
        captured_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
        source_id=TREATMENT_FIXTURE_SOURCE_ID,
    )
    if page.unidentified_records or len(page.notices) != 1:
        raise ValueError("Synthetic treatment fixture did not decode exactly one notice")
    return page.notices
