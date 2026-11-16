"""Stable public jobs capability boundary.

Implementation is delegated to implementation.py; consumers should import
this module instead of depending on internal algorithm and storage details.
"""

from melliatlas.jobs.implementation import (
    CompletedInvestigationStore,
    EcologyPlannerFactory,
    InMemoryInvestigationService,
    InvalidInvestigationRequest,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationService,
    InvestigationSnapshot,
    InvestigationStatus,
    InvestigationStorageError,
    ScenarioProvider,
    TreatmentPlannerFactory,
    deserialize_completed_snapshot,
    serialize_completed_snapshot,
)

__all__ = [
    "InvestigationStatus",
    "InvestigationOutcomeKind",
    "InvestigationRequest",
    "InvestigationSnapshot",
    "InvalidInvestigationRequest",
    "ScenarioProvider",
    "InvestigationService",
    "InvestigationStorageError",
    "CompletedInvestigationStore",
    "serialize_completed_snapshot",
    "deserialize_completed_snapshot",
    "InMemoryInvestigationService",
    "EcologyPlannerFactory",
    "TreatmentPlannerFactory",
]
