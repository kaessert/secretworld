"""Validation framework for automated game state assertions during playtesting."""

from .assertions import (
    Assertion,
    AssertionChecker,
    AssertionResult,
    AssertionType,
)
from .coverage import (
    CoverageStats,
    FeatureCategory,
    FeatureCoverage,
    FeatureEvent,
    FEATURE_DEFINITIONS,
)

__all__ = [
    "Assertion",
    "AssertionChecker",
    "AssertionResult",
    "AssertionType",
    "CoverageStats",
    "FeatureCategory",
    "FeatureCoverage",
    "FeatureEvent",
    "FEATURE_DEFINITIONS",
]
