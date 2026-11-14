"""Public API response models and stable error codes."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


class ApiErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_TERRITORY_REQUEST = "INVALID_TERRITORY_REQUEST"
    TERRITORY_REFERENCE_UNAVAILABLE = "TERRITORY_REFERENCE_UNAVAILABLE"
    TERRITORY_NOT_FOUND = "TERRITORY_NOT_FOUND"
    TERRITORY_GEOMETRY_MISSING = "TERRITORY_GEOMETRY_MISSING"
    DISTRICT_COVERAGE_UNSUPPORTED = "DISTRICT_COVERAGE_UNSUPPORTED"
    INVALID_INVESTIGATION_REQUEST = "INVALID_INVESTIGATION_REQUEST"
    INVESTIGATION_NOT_FOUND = "INVESTIGATION_NOT_FOUND"
    INVESTIGATION_STORAGE_UNAVAILABLE = "INVESTIGATION_STORAGE_UNAVAILABLE"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ApiErrorCode
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
