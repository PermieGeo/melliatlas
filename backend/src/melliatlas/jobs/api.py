"""Public investigation ports and immutable lifecycle declarations.

In-memory orchestration and JSON persistence codecs are separate implementations.
Consumers inject these Protocols rather than depending on storage internals.
"""

from typing import Protocol
from uuid import UUID

from melliatlas.agent.api import EcologyPlanner, TreatmentPlannerPort
from melliatlas.planning.api import SyntheticScenario
from melliatlas.territories.api import CountryCode

from .models import (
    InvalidInvestigationRequest,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
    InvestigationStorageError,
)


class ScenarioProvider(Protocol):
    def load(
        self, *, country: CountryCode, territory_id: str, scenario_id: str
    ) -> SyntheticScenario | None: ...


class InvestigationService(Protocol):
    def submit(self, request: InvestigationRequest) -> InvestigationSnapshot: ...
    def get(self, identifier: UUID) -> InvestigationSnapshot | None: ...
    def process(self, identifier: UUID) -> None: ...


class CompletedInvestigationStore(Protocol):
    """Durable completed snapshots; in-flight jobs remain process-local."""

    def save(self, snapshot: InvestigationSnapshot) -> None: ...
    def load(self, identifier: UUID) -> InvestigationSnapshot | None: ...


class EcologyPlannerFactory(Protocol):
    def __call__(self, scenario: SyntheticScenario, /) -> EcologyPlanner: ...


class TreatmentPlannerFactory(Protocol):
    def __call__(self, scenario: SyntheticScenario, /) -> TreatmentPlannerPort: ...


__all__ = [
    "InvestigationStatus",
    "InvestigationOutcomeKind",
    "InvestigationRequest",
    "InvestigationSnapshot",
    "InvalidInvestigationRequest",
    "InvestigationStorageError",
    "ScenarioProvider",
    "InvestigationService",
    "CompletedInvestigationStore",
    "EcologyPlannerFactory",
    "TreatmentPlannerFactory",
]
