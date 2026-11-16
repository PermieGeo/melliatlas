"""Stable public analyzers capability boundary.

Implementation is delegated to implementation.py; consumers should import
this module instead of depending on internal algorithm and storage details.
"""

from melliatlas.analyzers.implementation import (
    TreatmentProximity,
    TreatmentScreening,
    find_ecology_overlaps,
    screen_treatment_notices,
)

__all__ = [
    "find_ecology_overlaps",
    "screen_treatment_notices",
    "TreatmentProximity",
    "TreatmentScreening",
]
