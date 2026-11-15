"""HTTP recovery tests with a fake store; real PostGIS is verified separately."""

import asyncio
from threading import get_ident
from uuid import UUID

import httpx

from melliatlas.api.app import create_app
from melliatlas.jobs.api import (
    InMemoryInvestigationService,
    InvestigationSnapshot,
    InvestigationStorageError,
)
from melliatlas.sources.providers.synthetic.api import (
    SYNTHETIC_SCENARIO_ID,
    SyntheticFixtureProvider,
)


class StubCompletedStore:
    def __init__(self) -> None:
        self.saved: dict[UUID, InvestigationSnapshot] = {}
        self.unavailable = False
        self.load_thread: int | None = None

    def save(self, snapshot: InvestigationSnapshot) -> None:
        self.saved[snapshot.id] = snapshot

    def load(self, identifier: UUID) -> InvestigationSnapshot | None:
        self.load_thread = get_ident()
        if self.unavailable:
            raise InvestigationStorageError("Simulated database outage")
        return self.saved.get(identifier)


def _request() -> dict[str, object]:
    return {
        "country": "RU",
        "territory_id": "ru:region:smolensk",
        "scenario_id": SYNTHETIC_SCENARIO_ID,
        "season_start": "2026-05-01",
        "season_end": "2026-08-15",
    }


def test_completed_result_can_be_reopened_after_new_app_composition() -> None:
    async def check() -> None:
        store = StubCompletedStore()
        first_app = create_app(
            investigations=InMemoryInvestigationService(
                SyntheticFixtureProvider(),
                store,
            )
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=first_app), base_url="http://testserver"
        ) as client:
            response = await client.post("/api/v1/investigations", json=_request())
            assert response.status_code == 202
            identifier = response.json()["id"]
            complete = await client.get(f"/api/v1/investigations/{identifier}")
            assert complete.status_code == 200
            assert complete.json()["status"] == "COMPLETED"

        second_app = create_app(
            investigations=InMemoryInvestigationService(
                SyntheticFixtureProvider(),
                store,
            )
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=second_app), base_url="http://testserver"
        ) as client:
            reopened = await client.get(f"/api/v1/investigations/{identifier}")
            assert reopened.status_code == 200
            assert reopened.json() == complete.json()

    asyncio.run(check())


def test_unavailable_persistent_store_returns_sanitized_503() -> None:
    async def check() -> None:
        store = StubCompletedStore()
        store.unavailable = True
        app = create_app(
            investigations=InMemoryInvestigationService(
                SyntheticFixtureProvider(),
                store,
            )
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.get(
                "/api/v1/investigations/00000000-0000-4000-8000-000000000001"
            )
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "INVESTIGATION_STORAGE_UNAVAILABLE"
            assert "Simulated" not in str(response.json())
            get_operation = app.openapi()["paths"]["/api/v1/investigations/{id}"]["get"]
            assert "503" in get_operation["responses"]

    asyncio.run(check())


def test_persistent_get_runs_off_the_event_loop() -> None:
    async def check() -> None:
        store = StubCompletedStore()
        loop_thread = get_ident()
        app = create_app(
            investigations=InMemoryInvestigationService(
                SyntheticFixtureProvider(),
                store,
            )
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.get(
                "/api/v1/investigations/00000000-0000-4000-8000-000000000001"
            )
            assert response.status_code == 404
            assert store.load_thread is not None
            assert store.load_thread != loop_thread

    asyncio.run(check())
