"""Public callable contracts for pure analyzers, independent of their algorithms.

The concrete functions are exported via the analyzers package facade.
An analyzer receives already loaded evidence; it never performs source I/O.
"""

from typing import Protocol

from melliatlas.planning.api import CandidateSite, EcologyOverlap, EcologyZone, TreatmentScreening
from melliatlas.sources.api import TreatmentNotice

# Bounded demonstration-only distance; it does not establish a safe treatment buffer.
DEFAULT_WATCH_RADIUS_KM = 7.0
MAX_DEMO_WATCH_RADIUS_KM = 50.0


class EcologyOverlapAnalyzer(Protocol):
    def __call__(
        self, site: CandidateSite, zones: tuple[EcologyZone, ...]
    ) -> tuple[EcologyOverlap, ...]: ...


class TreatmentNoticeAnalyzer(Protocol):
    def __call__(
        self,
        site: CandidateSite,
        notices: tuple[TreatmentNotice, ...],
        *,
        watch_radius_km: float = DEFAULT_WATCH_RADIUS_KM,
    ) -> tuple[TreatmentScreening, ...]: ...


__all__ = [
    "EcologyOverlapAnalyzer",
    "TreatmentNoticeAnalyzer",
    "DEFAULT_WATCH_RADIUS_KM",
    "MAX_DEMO_WATCH_RADIUS_KM",
]
