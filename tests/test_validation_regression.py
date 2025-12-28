"""Unit tests for scripts/validation/regression.py.

Tests cover:
- RegressionBaseline creation and serialization
- RegressionReport generation and regression detection
- RegressionDetector comparison logic
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set

import pytest

from scripts.validation.coverage import (
    CoverageStats,
    FeatureCategory,
    FeatureCoverage,
)
from scripts.validation.regression import (
    FailureDiff,
    RegressionBaseline,
    RegressionDetector,
    RegressionReport,
    ScenarioBaseline,
)
from scripts.validation.scenarios import (
    ScenarioResult,
    StepResult,
)
from scripts.validation.assertions import AssertionResult, Assertion, AssertionType


# =============================================================================
# Test fixtures for creating mock data
# =============================================================================


def make_assertion_result(passed: bool, message: str = "") -> AssertionResult:
    """Create an AssertionResult for testing."""
    assertion = Assertion(
        type=AssertionType.STATE_EQUALS,
        field="test_field",
        expected="expected_value",
        message=message,
    )
    return AssertionResult(
        assertion=assertion,
        passed=passed,
        actual="actual_value" if not passed else "expected_value",
        error=message if not passed else "",
    )


def make_step_result(index: int, assertion_results: List[AssertionResult]) -> StepResult:
    """Create a StepResult for testing."""
    return StepResult(
        step_index=index,
        command=f"command_{index}",
        assertion_results=assertion_results,
        output=f"output_{index}",
    )


def make_scenario_result(
    name: str,
    passed: bool,
    assertions_passed: int = 1,
    assertions_failed: int = 0,
    failed_assertion_messages: Optional[List[str]] = None,
) -> ScenarioResult:
    """Create a ScenarioResult for testing."""
    results = []
    # Create step results with appropriate assertion results
    for i in range(assertions_passed):
        step = make_step_result(i, [make_assertion_result(True, f"passed_{i}")])
        results.append(step)

    if failed_assertion_messages:
        for i, msg in enumerate(failed_assertion_messages):
            step = make_step_result(
                assertions_passed + i,
                [make_assertion_result(False, msg)],
            )
            results.append(step)
    elif assertions_failed > 0:
        for i in range(assertions_failed):
            step = make_step_result(
                assertions_passed + i,
                [make_assertion_result(False, f"failed_{i}")],
            )
            results.append(step)

    return ScenarioResult(
        scenario_name=name,
        passed=passed,
        steps_run=assertions_passed + assertions_failed,
        assertions_passed=assertions_passed,
        assertions_failed=assertions_failed,
        results=results,
        duration=1.0,
    )


def make_feature_coverage(coverage_by_category: Dict[str, Set[str]]) -> FeatureCoverage:
    """Create a FeatureCoverage with specified features covered."""
    fc = FeatureCoverage()
    for category_name, features in coverage_by_category.items():
        category = FeatureCategory[category_name]
        for feature in features:
            fc.record(feature=feature, category=category, command="test")
    return fc


# =============================================================================
# Tests for RegressionBaseline
# =============================================================================


class TestRegressionBaseline:
    """Tests for RegressionBaseline dataclass."""

    def test_baseline_creation_from_scenario_results(self):
        """Test creating a baseline from scenario results."""
        # Spec: RegressionDetector.create_baseline() creates baseline from results
        results = [
            make_scenario_result("test_movement", passed=True, assertions_passed=3),
            make_scenario_result("test_combat", passed=False, assertions_passed=2, assertions_failed=1),
        ]
        coverage = make_feature_coverage({
            "MOVEMENT": {"movement.overworld", "movement.subgrid_entry"},
            "COMBAT": {"combat.attack"},
        })

        detector = RegressionDetector()
        baseline = detector.create_baseline(results, coverage)

        # Check scenarios were recorded
        assert "test_movement" in baseline.scenarios
        assert "test_combat" in baseline.scenarios
        assert baseline.scenarios["test_movement"].passed is True
        assert baseline.scenarios["test_combat"].passed is False

        # Check coverage was recorded
        assert FeatureCategory.MOVEMENT.name in baseline.coverage
        assert FeatureCategory.COMBAT.name in baseline.coverage

        # Check metadata
        assert baseline.timestamp > 0
        assert baseline.version != ""

    def test_baseline_serialization_roundtrip(self):
        """Test that baselines can be serialized and deserialized correctly."""
        # Spec: RegressionBaseline has to_dict()/from_dict() for JSON serialization
        original = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(
                    passed=True,
                    assertions_passed=5,
                    assertions_failed=0,
                    failed_assertions=[],
                ),
                "scenario_b": ScenarioBaseline(
                    passed=False,
                    assertions_passed=3,
                    assertions_failed=2,
                    failed_assertions=["assertion_x failed", "assertion_y failed"],
                ),
            },
            coverage={
                "MOVEMENT": 75.0,
                "COMBAT": 50.0,
            },
            timestamp=1234567890.0,
            version="1.0.0",
        )

        # Serialize
        data = original.to_dict()

        # Verify it's JSON-serializable
        json_str = json.dumps(data)
        assert json_str

        # Deserialize
        restored = RegressionBaseline.from_dict(data)

        # Verify roundtrip
        assert restored.scenarios["scenario_a"].passed is True
        assert restored.scenarios["scenario_b"].passed is False
        assert restored.scenarios["scenario_b"].failed_assertions == ["assertion_x failed", "assertion_y failed"]
        assert restored.coverage["MOVEMENT"] == 75.0
        assert restored.timestamp == 1234567890.0
        assert restored.version == "1.0.0"

    def test_baseline_merge_multiple_runs(self):
        """Test merging multiple run baselines into one."""
        # Spec: RegressionBaseline supports merging for aggregating runs
        baseline1 = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=True, assertions_passed=3, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 50.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        baseline2 = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=True, assertions_passed=3, assertions_failed=0, failed_assertions=[]),
                "scenario_b": ScenarioBaseline(passed=False, assertions_passed=2, assertions_failed=1, failed_assertions=["fail"]),
            },
            coverage={"MOVEMENT": 75.0, "COMBAT": 25.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        merged = detector.merge_baselines([baseline1, baseline2])

        # Merged should have all scenarios
        assert "scenario_a" in merged.scenarios
        assert "scenario_b" in merged.scenarios

        # Coverage should be the best values
        assert merged.coverage["MOVEMENT"] == 75.0
        assert merged.coverage["COMBAT"] == 25.0

        # Timestamp should be the latest
        assert merged.timestamp >= 2000.0


# =============================================================================
# Tests for RegressionReport
# =============================================================================


class TestRegressionReport:
    """Tests for RegressionReport dataclass."""

    def test_report_identifies_new_failures(self):
        """Test that new failures are correctly identified in report."""
        # Spec: RegressionReport.new_failures contains newly failing scenarios/assertions
        baseline = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=True, assertions_passed=3, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 50.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=False, assertions_passed=2, assertions_failed=1, failed_assertions=["health check"]),
            },
            coverage={"MOVEMENT": 50.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert len(report.new_failures) == 1
        assert report.new_failures[0].scenario_name == "scenario_a"
        assert "health check" in report.new_failures[0].message

    def test_report_identifies_resolved_issues(self):
        """Test that resolved issues are correctly identified in report."""
        # Spec: RegressionReport.resolved_issues contains previously failing, now passing
        baseline = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=False, assertions_passed=2, assertions_failed=1, failed_assertions=["health check"]),
            },
            coverage={"MOVEMENT": 50.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=True, assertions_passed=3, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 50.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert len(report.resolved_issues) == 1
        assert report.resolved_issues[0].scenario_name == "scenario_a"
        assert len(report.new_failures) == 0

    def test_report_tracks_coverage_delta(self):
        """Test that coverage changes are tracked correctly."""
        # Spec: RegressionReport.coverage_delta shows category -> delta
        baseline = RegressionBaseline(
            scenarios={},
            coverage={"MOVEMENT": 50.0, "COMBAT": 75.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={},
            coverage={"MOVEMENT": 75.0, "COMBAT": 50.0, "INVENTORY": 25.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        # MOVEMENT improved by 25
        assert report.coverage_delta["MOVEMENT"] == pytest.approx(25.0)
        # COMBAT decreased by 25
        assert report.coverage_delta["COMBAT"] == pytest.approx(-25.0)
        # INVENTORY is new (delta from 0)
        assert report.coverage_delta["INVENTORY"] == pytest.approx(25.0)

    def test_report_empty_when_no_changes(self):
        """Test that report is empty when there are no changes."""
        # Spec: RegressionReport should be empty when runs are identical
        baseline = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=True, assertions_passed=3, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 50.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        # Current is identical
        current = RegressionBaseline(
            scenarios={
                "scenario_a": ScenarioBaseline(passed=True, assertions_passed=3, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 50.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert len(report.new_failures) == 0
        assert len(report.resolved_issues) == 0
        assert report.coverage_delta.get("MOVEMENT", 0.0) == pytest.approx(0.0)
        assert report.is_regression is False


# =============================================================================
# Tests for RegressionDetector
# =============================================================================


class TestRegressionDetector:
    """Tests for RegressionDetector class."""

    def test_detector_compare_identical_runs(self):
        """Test comparing identical runs produces no regression."""
        # Spec: Identical runs should not be marked as regression
        baseline = RegressionBaseline(
            scenarios={
                "test_a": ScenarioBaseline(passed=True, assertions_passed=5, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 80.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={
                "test_a": ScenarioBaseline(passed=True, assertions_passed=5, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 80.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert report.is_regression is False

    def test_detector_compare_with_new_failure(self):
        """Test that new failure is detected as regression."""
        # Spec: New failures should be detected and marked as regression
        baseline = RegressionBaseline(
            scenarios={
                "test_a": ScenarioBaseline(passed=True, assertions_passed=5, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 80.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={
                "test_a": ScenarioBaseline(passed=False, assertions_passed=4, assertions_failed=1, failed_assertions=["coord check"]),
            },
            coverage={"MOVEMENT": 80.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert report.is_regression is True
        assert len(report.new_failures) == 1

    def test_detector_compare_with_resolved_failure(self):
        """Test that resolved failures are tracked (not a regression)."""
        # Spec: Resolved failures should be tracked but not flagged as regression
        baseline = RegressionBaseline(
            scenarios={
                "test_a": ScenarioBaseline(passed=False, assertions_passed=4, assertions_failed=1, failed_assertions=["coord check"]),
            },
            coverage={"MOVEMENT": 80.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={
                "test_a": ScenarioBaseline(passed=True, assertions_passed=5, assertions_failed=0, failed_assertions=[]),
            },
            coverage={"MOVEMENT": 80.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert report.is_regression is False
        assert len(report.resolved_issues) == 1

    def test_detector_coverage_regression_detected(self):
        """Test that decreased coverage is detected as regression."""
        # Spec: Coverage decrease should be marked as regression
        baseline = RegressionBaseline(
            scenarios={},
            coverage={"MOVEMENT": 80.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={},
            coverage={"MOVEMENT": 60.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert report.is_regression is True
        assert report.coverage_delta["MOVEMENT"] == pytest.approx(-20.0)

    def test_detector_coverage_improvement_detected(self):
        """Test that improved coverage is tracked (not a regression)."""
        # Spec: Coverage improvement should be tracked but not flagged as regression
        baseline = RegressionBaseline(
            scenarios={},
            coverage={"MOVEMENT": 60.0},
            timestamp=1000.0,
            version="1.0.0",
        )
        current = RegressionBaseline(
            scenarios={},
            coverage={"MOVEMENT": 80.0},
            timestamp=2000.0,
            version="1.0.0",
        )

        detector = RegressionDetector()
        report = detector.compare(baseline, current)

        assert report.is_regression is False
        assert report.coverage_delta["MOVEMENT"] == pytest.approx(20.0)

    def test_detector_load_save_baseline(self):
        """Test that baselines can be saved and loaded from disk."""
        # Spec: RegressionDetector provides save_baseline/load_baseline methods
        baseline = RegressionBaseline(
            scenarios={
                "test_scenario": ScenarioBaseline(
                    passed=True, assertions_passed=5, assertions_failed=0, failed_assertions=[]
                ),
            },
            coverage={"MOVEMENT": 75.0, "COMBAT": 50.0},
            timestamp=1234567890.0,
            version="1.0.0",
        )

        detector = RegressionDetector()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "baseline.json"

            # Save
            detector.save_baseline(baseline, path)
            assert path.exists()

            # Load
            loaded = detector.load_baseline(path)

            # Verify
            assert loaded.scenarios["test_scenario"].passed is True
            assert loaded.coverage["MOVEMENT"] == 75.0
            assert loaded.timestamp == 1234567890.0


class TestRegressionReportFormatting:
    """Tests for RegressionReport text formatting."""

    def test_to_text_with_failures(self):
        """Test text report with failures."""
        # Spec: RegressionReport.to_text() for human-readable report
        report = RegressionReport(
            new_failures=[
                FailureDiff(scenario_name="test_combat", message="health dropped too much"),
            ],
            resolved_issues=[],
            coverage_delta={"COMBAT": -10.0},
        )

        text = report.to_text()

        assert "REGRESSION DETECTED" in text or "regression" in text.lower()
        assert "test_combat" in text
        assert "health dropped too much" in text

    def test_to_text_no_issues(self):
        """Test text report with no issues."""
        report = RegressionReport(
            new_failures=[],
            resolved_issues=[],
            coverage_delta={},
        )

        text = report.to_text()

        assert "No regressions" in text or "no regression" in text.lower() or "passed" in text.lower()

    def test_to_text_with_resolved(self):
        """Test text report with resolved issues."""
        report = RegressionReport(
            new_failures=[],
            resolved_issues=[
                FailureDiff(scenario_name="test_movement", message="coord mismatch fixed"),
            ],
            coverage_delta={"MOVEMENT": 15.0},
        )

        text = report.to_text()

        assert "test_movement" in text
        # Should indicate positive change or improvement
        assert "resolved" in text.lower() or "fixed" in text.lower() or "improved" in text.lower()
