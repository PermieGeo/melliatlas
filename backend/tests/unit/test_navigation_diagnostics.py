"""Read-only navigation diagnosis checks API results against imported region rows."""

import pytest
from diagnose_admin_navigation import audit_regions

REGIONS = (("ru:region:smo", "Smolensk", 3), ("ru:region:mos", "Moscow", 0))


def test_matching_ru_regions_and_districts() -> None:
    def fetch(path: str) -> object:
        if "regions?" in path:
            return [
                {"id": "ru:region:smo", "country": "RU", "kind": "region"},
                {"id": "ru:region:mos", "country": "RU", "kind": "region"},
            ]
        if "smo" in path:
            return [
                {
                    "id": f"ru:district:{index}",
                    "country": "RU",
                    "kind": "district",
                    "parent_id": "ru:region:smo",
                }
                for index in range(3)
            ]
        return []

    audit = audit_regions("RU", REGIONS, fetch)
    assert audit.regions_checked == 2
    assert audit.database_districts == audit.api_districts == 3
    assert audit.empty_regions == ("ru:region:mos (Moscow)",)
    assert not audit.issues


def test_missing_api_districts_are_reported_without_fabricating_coverage() -> None:
    def fetch(path: str) -> object:
        if "regions?" in path:
            return [
                {"id": identifier, "country": "RU", "kind": "region"}
                for identifier, _, _ in REGIONS
            ]
        return []

    audit = audit_regions("RU", REGIONS, fetch)
    assert len(audit.issues) == 1
    assert audit.issues[0].region_id == "ru:region:smo"
    assert audit.issues[0].database_count == 3
    assert audit.issues[0].api_count == 0


def test_cross_country_districts_are_rejected() -> None:
    def fetch(path: str) -> object:
        if "regions?" in path:
            return [{"id": "ru:region:smo", "country": "RU", "kind": "region"}]
        return [
            {
                "id": "by:district:1",
                "country": "BY",
                "kind": "district",
                "parent_id": "by:region:vi",
            }
        ]

    audit = audit_regions("RU", REGIONS[:1], fetch)
    assert len(audit.issues) == 1
    assert audit.issues[0].api_count is None
    assert "parent" in audit.issues[0].reason


def test_mismatched_region_catalog_fails_closed() -> None:
    def fetch(_path: str) -> object:
        return [{"id": "by:region:vi", "country": "BY", "kind": "region"}]

    with pytest.raises(ValueError, match="invalid region catalog"):
        audit_regions("RU", REGIONS, fetch)


def test_target_region_uses_full_country_catalog_for_validation() -> None:
    def fetch(path: str) -> object:
        if "regions?" in path:
            return [
                {"id": identifier, "country": "RU", "kind": "region"}
                for identifier, _, _ in REGIONS
            ]
        return []

    audit = audit_regions("RU", REGIONS, fetch, "ru:region:smo")
    assert audit.regions_checked == 1
    assert audit.database_districts == 3
    assert len(audit.issues) == 1

    with pytest.raises(ValueError, match="Selected region ID"):
        audit_regions("RU", REGIONS, fetch, "ru:region:unknown")
