"""Prevent public Protocol files from turning into implementation buckets again."""

import ast
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from melliatlas.agent import DeterministicPlanner, TreatmentPlanner
from melliatlas.agent.api import (
    EcologyPlanner,
    SiteInspector,
    TreatmentInspector,
    TreatmentPlannerPort,
)
from melliatlas.analyzers.api import EcologyOverlapAnalyzer, TreatmentNoticeAnalyzer
from melliatlas.jobs import InMemoryInvestigationService
from melliatlas.jobs.api import (
    CompletedInvestigationStore,
    EcologyPlannerFactory,
    InvestigationService,
    ScenarioProvider,
    TreatmentPlannerFactory,
)

CAPABILITIES = ("agent", "analyzers", "planning", "jobs")
CAPABILITY_ROOT = Path(__file__).resolve().parents[2] / "src" / "melliatlas"


def test_capabilities_have_no_generic_implementation_buckets() -> None:
    for capability in CAPABILITIES:
        assert not (CAPABILITY_ROOT / capability / "implementation.py").exists()


def test_api_files_contain_only_declarations_and_protocols() -> None:
    for capability in CAPABILITIES:
        path = CAPABILITY_ROOT / capability / "api.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in tree.body
        )
        # Public API modules declare structural ports and reexport immutable model types.
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                assert any(
                    isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
                )


def test_real_ports_are_structural_protocols() -> None:
    for port in (
        SiteInspector,
        TreatmentInspector,
        EcologyPlanner,
        EcologyOverlapAnalyzer,
        TreatmentNoticeAnalyzer,
        ScenarioProvider,
        InvestigationService,
        CompletedInvestigationStore,
    ):
        assert issubclass(port, Protocol)
    # The concrete service and planners do not inherit their public ports.
    assert Protocol not in InMemoryInvestigationService.__bases__
    assert Protocol not in DeterministicPlanner.__bases__
    assert Protocol not in TreatmentPlanner.__bases__


def test_injected_callbacks_are_position_only() -> None:
    # Callback implementations may use `_site`, `_scenario`, or another local name.
    for port, parameter_name in (
        (SiteInspector, "site"),
        (TreatmentInspector, "site"),
        (EcologyPlannerFactory, "scenario"),
        (TreatmentPlannerFactory, "scenario"),
    ):
        parameter = inspect.signature(port.__call__).parameters[parameter_name]
        assert parameter.kind is inspect.Parameter.POSITIONAL_ONLY


def test_snapshot_codec_uses_module_visible_parsers() -> None:
    path = CAPABILITY_ROOT / "jobs" / "snapshot_codec.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "codec_fields":
            assert node.names
            assert all(not name.name.startswith("_") for name in node.names)


# Static-only checks: Pyright validates structural assignments without needing
# to instantiate runtime services or introduce inert pytest fixtures.
if TYPE_CHECKING:

    def verify_concrete_port_assignability(
        service: InMemoryInvestigationService,
        ecology: DeterministicPlanner,
        treatment: TreatmentPlanner,
    ) -> tuple[InvestigationService, EcologyPlanner, TreatmentPlannerPort]:
        return service, ecology, treatment
