"""Typed HTTP boundary for the synthetic, non-durable investigation workflow."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse
from melliatlas.jobs.api import (
    InvalidInvestigationRequest,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationService,
    InvestigationSnapshot,
    InvestigationStatus,
)
from melliatlas.planning.api import TimeWindow
from melliatlas.territories.api import CountryCode


class StartingPointDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)


class InvestigationCreateDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: CountryCode
    territory_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    season_start: date
    season_end: date
    starting_point: StartingPointDto | None = None


class InvestigationRequestDto(BaseModel):
    country: CountryCode
    territory_id: str
    scenario_id: str
    season_start: date
    season_end: date


class SeasonStopDto(BaseModel):
    site_id: str
    longitude: float
    latitude: float
    start: date
    end: date
    forage_level: Literal["LOW", "MEDIUM", "HIGH"]
    evidence_ids: tuple[str, ...]


class SeasonPlanDto(BaseModel):
    stops: tuple[SeasonStopDto, ...]
    relocations: int
    rationale: str


class EvidenceSummaryDto(BaseModel):
    id: str
    source_id: str
    source_mode: Literal["FIXTURE"]
    synthetic: Literal[True]
    effective_start: date
    effective_end: date
    uncertainty: str


class InvestigationResponse(BaseModel):
    id: UUID
    status: InvestigationStatus
    request: InvestigationRequestDto
    created_at: datetime
    updated_at: datetime
    outcome: InvestigationOutcomeKind | None
    plan: SeasonPlanDto | None
    evidence: tuple[EvidenceSummaryDto, ...]
    decision_trace: tuple[str, ...]
    diagnostics: tuple[str, ...]
    reference_version: str
    limitations: tuple[str, ...]
    synthetic: Literal[True]


def _present(snapshot: InvestigationSnapshot) -> InvestigationResponse:
    plan: SeasonPlanDto | None = None
    if snapshot.plan is not None:
        plan = SeasonPlanDto(
            stops=tuple(
                SeasonStopDto(
                    site_id=stop.site_id,
                    longitude=stop.longitude,
                    latitude=stop.latitude,
                    start=stop.window.start,
                    end=stop.window.end,
                    forage_level=stop.forage_level,
                    evidence_ids=stop.evidence_ids,
                )
                for stop in snapshot.plan.stops
            ),
            relocations=snapshot.plan.relocations,
            rationale=snapshot.plan.rationale,
        )
    return InvestigationResponse(
        id=snapshot.id,
        status=snapshot.status,
        request=InvestigationRequestDto(
            country=snapshot.request.country,
            territory_id=snapshot.request.territory_id,
            scenario_id=snapshot.request.scenario_id,
            season_start=snapshot.request.season.start,
            season_end=snapshot.request.season.end,
        ),
        created_at=snapshot.created_at,
        updated_at=snapshot.updated_at,
        outcome=snapshot.outcome,
        plan=plan,
        evidence=tuple(
            EvidenceSummaryDto(
                id=item.id,
                source_id=item.source_id,
                source_mode=item.source_mode,
                synthetic=item.synthetic,
                effective_start=item.effective_window.start,
                effective_end=item.effective_window.end,
                uncertainty=item.uncertainty,
            )
            for item in snapshot.evidence
        ),
        decision_trace=snapshot.decision_trace,
        diagnostics=snapshot.diagnostics,
        reference_version=snapshot.reference_version,
        limitations=snapshot.limitations,
        synthetic=True,
    )


def _error(status: int, code: ApiErrorCode, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(
            mode="json"
        ),
    )


def create_investigation_router(service: InvestigationService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])

    @router.post(
        "",
        response_model=InvestigationResponse,
        status_code=202,
        responses={422: {"model": ErrorResponse}},
    )
    async def create_investigation(
        request: InvestigationCreateDto, tasks: BackgroundTasks
    ) -> InvestigationResponse | JSONResponse:
        try:
            season = TimeWindow(request.season_start, request.season_end)
            point = (
                (request.starting_point.longitude, request.starting_point.latitude)
                if request.starting_point is not None
                else None
            )
            snapshot = service.submit(
                InvestigationRequest(
                    country=request.country,
                    territory_id=request.territory_id,
                    scenario_id=request.scenario_id,
                    season=season,
                    starting_point=point,
                )
            )
        except (InvalidInvestigationRequest, ValueError):
            return _error(
                422,
                ApiErrorCode.INVALID_INVESTIGATION_REQUEST,
                "Unsupported synthetic investigation request",
            )
        tasks.add_task(service.process, snapshot.id)
        return _present(snapshot)

    @router.get(
        "/{id}",
        response_model=InvestigationResponse,
        responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    )
    async def read_investigation(id: UUID) -> InvestigationResponse | JSONResponse:
        snapshot = service.get(id)
        if snapshot is None:
            return _error(404, ApiErrorCode.INVESTIGATION_NOT_FOUND, "Unknown investigation")
        return _present(snapshot)

    return router
