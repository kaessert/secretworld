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
from .regression import (
    FailureDiff,
    RegressionBaseline,
    RegressionDetector,
    RegressionReport,
    ScenarioBaseline,
)
from .scenarios import (
    Scenario,
    ScenarioResult,
    ScenarioRunner,
    ScenarioStep,
    StepResult,
)

__all__ = [
    "Assertion",
    "AssertionChecker",
    "AssertionResult",
    "AssertionType",
    "CoverageStats",
    "FailureDiff",
    "FeatureCategory",
    "FeatureCoverage",
    "FeatureEvent",
    "FEATURE_DEFINITIONS",
    "RegressionBaseline",
    "RegressionDetector",
    "RegressionReport",
    "Scenario",
    "ScenarioBaseline",
    "ScenarioResult",
    "ScenarioRunner",
    "ScenarioStep",
    "StepResult",
]
