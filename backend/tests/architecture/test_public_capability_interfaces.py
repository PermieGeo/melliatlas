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


def _executable_api_declarations(source: str) -> list[str]:
    """Reject executable functions and methods while allowing typed value declarations."""
    tree = ast.parse(source)
    violations: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.append(node.name)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            violations.append("module-level expression")
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
            violations.append("module-level call")
        if not isinstance(node, ast.ClassDef):
            continue
        is_protocol = any(
            isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
        )
        for member in node.body:
            if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            statements = [
                statement
                for statement in member.body
                if not (
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                )
            ]
            declaration_only = (
                len(statements) == 1
                and isinstance(statements[0], ast.Expr)
                and (
                    isinstance(statements[0].value, ast.Constant)
                    and statements[0].value.value is Ellipsis
                )
            )
            if not is_protocol or not declaration_only:
                violations.append(f"{node.name}.{member.name}")
    return violations


def test_every_capability_api_file_is_declarative() -> None:
    for path in sorted(CAPABILITY_ROOT.rglob("api.py")):
        assert _executable_api_declarations(path.read_text(encoding="utf-8")) == [], path


def test_api_guard_rejects_concrete_methods_and_protocol_bodies() -> None:
    assert _executable_api_declarations("def execute(): return 1") == ["execute"]
    assert _executable_api_declarations("connect()") == ["module-level expression"]
    assert _executable_api_declarations("backend = create_backend()") == ["module-level call"]
    assert _executable_api_declarations("class Store:\n    def save(self): return None") == [
        "Store.save"
    ]
    assert _executable_api_declarations(
        "from typing import Protocol\nclass Port(Protocol):\n    def get(self): return 1"
    ) == ["Port.get"]
    assert (
        _executable_api_declarations(
            "from typing import Protocol\nclass Port(Protocol):\n    def get(self): ..."
        )
        == []
    )


def test_provider_facades_export_implementations_not_contract_modules() -> None:
    from melliatlas.persistence import PostgisCompletedInvestigationStore
    from melliatlas.persistence import api as persistence_api
    from melliatlas.sources.api import ScenarioProvider
    from melliatlas.sources.providers import saturn, synthetic, weather
    from melliatlas.sources.providers.saturn import api as saturn_api
    from melliatlas.sources.providers.synthetic import api as synthetic_api
    from melliatlas.sources.providers.weather import api as weather_api

    assert PostgisCompletedInvestigationStore.__module__ == "melliatlas.persistence.postgis_store"
    assert not hasattr(persistence_api, "PostgisCompletedInvestigationStore")
    assert isinstance(synthetic.SyntheticFixtureProvider(), ScenarioProvider)
    assert not hasattr(synthetic_api, "SyntheticFixtureProvider")
    assert not hasattr(saturn_api, "SaturnPublicTreatmentReader")
    assert saturn.SaturnPublicTreatmentReader.__module__.endswith(".saturn.live")
    assert not hasattr(weather_api, "OpenMeteoForecastReader")
    assert weather.OpenMeteoForecastReader.__module__.endswith(".weather.forecast")


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
