"""Regression detection for automated playtesting.

This module provides functionality to detect feature regressions by comparing
test runs against baselines. It tracks pass rates, coverage stats, and
assertion results to identify new failures and resolved issues.

Classes:
    ScenarioBaseline: Baseline data for a single scenario
    RegressionBaseline: Complete baseline for a test run
    FailureDiff: Represents a failure difference between runs
    RegressionReport: Report of differences between baseline and current run
    RegressionDetector: Main class for comparing runs and generating reports
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from scripts.validation.coverage import FeatureCoverage, FeatureCategory
from scripts.validation.scenarios import ScenarioResult


# Version for baseline format compatibility
BASELINE_VERSION = "1.0.0"


@dataclass
class ScenarioBaseline:
    """Baseline data for a single scenario.

    Attributes:
        passed: Whether the scenario passed
        assertions_passed: Number of assertions that passed
        assertions_failed: Number of assertions that failed
        failed_assertions: List of failure messages for failed assertions
    """

    passed: bool
    assertions_passed: int
    assertions_failed: int
    failed_assertions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "passed": self.passed,
            "assertions_passed": self.assertions_passed,
            "assertions_failed": self.assertions_failed,
            "failed_assertions": self.failed_assertions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioBaseline":
        """Deserialize from dictionary."""
        return cls(
            passed=data["passed"],
            assertions_passed=data["assertions_passed"],
            assertions_failed=data["assertions_failed"],
            failed_assertions=data.get("failed_assertions", []),
        )


@dataclass
class RegressionBaseline:
    """Complete baseline for a test run.

    Stores scenario results and coverage stats for comparison against
    future runs.

    Attributes:
        scenarios: Dict mapping scenario name to ScenarioBaseline
        coverage: Dict mapping category name to coverage percentage
        timestamp: Unix timestamp when baseline was created
        version: Baseline format version for compatibility
    """

    scenarios: Dict[str, ScenarioBaseline]
    coverage: Dict[str, float]
    timestamp: float
    version: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "scenarios": {name: sb.to_dict() for name, sb in self.scenarios.items()},
            "coverage": self.coverage,
            "timestamp": self.timestamp,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionBaseline":
        """Deserialize from dictionary."""
        scenarios = {
            name: ScenarioBaseline.from_dict(sb_data)
            for name, sb_data in data.get("scenarios", {}).items()
        }
        return cls(
            scenarios=scenarios,
            coverage=data.get("coverage", {}),
            timestamp=data.get("timestamp", 0.0),
            version=data.get("version", BASELINE_VERSION),
        )


@dataclass
class FailureDiff:
    """Represents a failure difference between runs.

    Attributes:
        scenario_name: Name of the affected scenario
        message: Description of the failure or change
    """

    scenario_name: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureDiff":
        """Deserialize from dictionary."""
        return cls(
            scenario_name=data["scenario_name"],
            message=data["message"],
        )


@dataclass
class RegressionReport:
    """Report of differences between baseline and current run.

    Attributes:
        new_failures: List of scenarios/assertions that newly failed
        resolved_issues: List of previously failing, now passing
        coverage_delta: Dict mapping category name to coverage change
    """

    new_failures: List[FailureDiff] = field(default_factory=list)
    resolved_issues: List[FailureDiff] = field(default_factory=list)
    coverage_delta: Dict[str, float] = field(default_factory=dict)

    @property
    def is_regression(self) -> bool:
        """Check if this report indicates a regression.

        Returns True if there are new failures OR if any coverage category
        decreased significantly.
        """
        if self.new_failures:
            return True

        # Check for significant coverage decrease (any negative delta)
        for delta in self.coverage_delta.values():
            if delta < 0:
                return True

        return False

    def to_text(self) -> str:
        """Generate human-readable report text."""
        lines = []

        if self.is_regression:
            lines.append("=" * 60)
            lines.append("REGRESSION DETECTED")
            lines.append("=" * 60)
        else:
            lines.append("=" * 60)
            lines.append("No regressions detected - All checks passed")
            lines.append("=" * 60)

        # New failures section
        if self.new_failures:
            lines.append("")
            lines.append("NEW FAILURES:")
            lines.append("-" * 40)
            for failure in self.new_failures:
                lines.append(f"  - {failure.scenario_name}: {failure.message}")

        # Resolved issues section
        if self.resolved_issues:
            lines.append("")
            lines.append("RESOLVED ISSUES:")
            lines.append("-" * 40)
            for resolved in self.resolved_issues:
                lines.append(f"  - {resolved.scenario_name}: {resolved.message}")

        # Coverage delta section
        coverage_changes = {k: v for k, v in self.coverage_delta.items() if abs(v) > 0.01}
        if coverage_changes:
            lines.append("")
            lines.append("COVERAGE CHANGES:")
            lines.append("-" * 40)
            for category, delta in sorted(coverage_changes.items()):
                sign = "+" if delta > 0 else ""
                lines.append(f"  {category}: {sign}{delta:.1f}%")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "new_failures": [f.to_dict() for f in self.new_failures],
            "resolved_issues": [r.to_dict() for r in self.resolved_issues],
            "coverage_delta": self.coverage_delta,
            "is_regression": self.is_regression,
        }


class RegressionDetector:
    """Compares test runs against baselines to detect regressions.

    This class provides methods to:
    - Create baselines from scenario results and coverage data
    - Compare current runs against baselines
    - Save and load baselines from disk
    - Merge multiple baselines
    """

    def create_baseline(
        self,
        results: List[ScenarioResult],
        coverage: FeatureCoverage,
    ) -> RegressionBaseline:
        """Create a baseline from scenario results and coverage.

        Args:
            results: List of ScenarioResult from running scenarios
            coverage: FeatureCoverage tracker with recorded events

        Returns:
            RegressionBaseline suitable for future comparisons
        """
        scenarios: Dict[str, ScenarioBaseline] = {}

        for result in results:
            # Collect failed assertion messages
            failed_assertions: List[str] = []
            for step_result in result.results:
                for assertion_result in step_result.assertion_results:
                    if not assertion_result.passed:
                        # Use error attribute, or message from assertion, or str representation
                        msg = (
                            assertion_result.error
                            or assertion_result.assertion.message
                            or str(assertion_result.assertion)
                        )
                        failed_assertions.append(msg)

            scenarios[result.scenario_name] = ScenarioBaseline(
                passed=result.passed,
                assertions_passed=result.assertions_passed,
                assertions_failed=result.assertions_failed,
                failed_assertions=failed_assertions,
            )

        # Extract coverage percentages by category
        coverage_stats = coverage.get_coverage_by_category()
        coverage_dict: Dict[str, float] = {}
        for category in FeatureCategory:
            stats = coverage_stats.get(category)
            if stats and stats.total > 0:
                percentage = (stats.covered / stats.total) * 100
                coverage_dict[category.name] = percentage

        return RegressionBaseline(
            scenarios=scenarios,
            coverage=coverage_dict,
            timestamp=time.time(),
            version=BASELINE_VERSION,
        )

    def compare(
        self,
        baseline: RegressionBaseline,
        current: RegressionBaseline,
    ) -> RegressionReport:
        """Compare a current run against a baseline.

        Args:
            baseline: The baseline to compare against
            current: The current run results

        Returns:
            RegressionReport with differences
        """
        new_failures: List[FailureDiff] = []
        resolved_issues: List[FailureDiff] = []
        coverage_delta: Dict[str, float] = {}

        # Compare scenarios
        all_scenarios = set(baseline.scenarios.keys()) | set(current.scenarios.keys())

        for scenario_name in all_scenarios:
            baseline_scenario = baseline.scenarios.get(scenario_name)
            current_scenario = current.scenarios.get(scenario_name)

            if baseline_scenario and current_scenario:
                # Both exist - check for status change
                if baseline_scenario.passed and not current_scenario.passed:
                    # New failure
                    message = (
                        current_scenario.failed_assertions[0]
                        if current_scenario.failed_assertions
                        else "Scenario failed"
                    )
                    new_failures.append(FailureDiff(
                        scenario_name=scenario_name,
                        message=message,
                    ))
                elif not baseline_scenario.passed and current_scenario.passed:
                    # Resolved
                    message = (
                        baseline_scenario.failed_assertions[0]
                        if baseline_scenario.failed_assertions
                        else "Issue resolved"
                    )
                    resolved_issues.append(FailureDiff(
                        scenario_name=scenario_name,
                        message=message,
                    ))

            elif current_scenario and not baseline_scenario:
                # New scenario - only report if failed
                if not current_scenario.passed:
                    message = (
                        current_scenario.failed_assertions[0]
                        if current_scenario.failed_assertions
                        else "New scenario failed"
                    )
                    new_failures.append(FailureDiff(
                        scenario_name=scenario_name,
                        message=message,
                    ))

        # Compare coverage
        all_categories = set(baseline.coverage.keys()) | set(current.coverage.keys())

        for category in all_categories:
            baseline_cov = baseline.coverage.get(category, 0.0)
            current_cov = current.coverage.get(category, 0.0)
            delta = current_cov - baseline_cov

            if abs(delta) > 0.001:  # Only record meaningful deltas
                coverage_delta[category] = delta

        return RegressionReport(
            new_failures=new_failures,
            resolved_issues=resolved_issues,
            coverage_delta=coverage_delta,
        )

    def merge_baselines(self, baselines: List[RegressionBaseline]) -> RegressionBaseline:
        """Merge multiple baselines into one.

        Takes the best coverage values and combines all scenarios.
        Uses the latest timestamp.

        Args:
            baselines: List of baselines to merge

        Returns:
            Merged RegressionBaseline
        """
        if not baselines:
            return RegressionBaseline(
                scenarios={},
                coverage={},
                timestamp=time.time(),
                version=BASELINE_VERSION,
            )

        # Merge scenarios (later baselines override earlier)
        merged_scenarios: Dict[str, ScenarioBaseline] = {}
        for baseline in baselines:
            merged_scenarios.update(baseline.scenarios)

        # Merge coverage (take best values)
        merged_coverage: Dict[str, float] = {}
        for baseline in baselines:
            for category, value in baseline.coverage.items():
                if category not in merged_coverage or value > merged_coverage[category]:
                    merged_coverage[category] = value

        # Use latest timestamp
        latest_timestamp = max(b.timestamp for b in baselines)

        return RegressionBaseline(
            scenarios=merged_scenarios,
            coverage=merged_coverage,
            timestamp=latest_timestamp,
            version=BASELINE_VERSION,
        )

    def save_baseline(self, baseline: RegressionBaseline, path: Path) -> None:
        """Save a baseline to disk as JSON.

        Args:
            baseline: Baseline to save
            path: Path to save to
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(baseline.to_dict(), f, indent=2)

    def load_baseline(self, path: Path) -> RegressionBaseline:
        """Load a baseline from disk.

        Args:
            path: Path to load from

        Returns:
            Loaded RegressionBaseline
        """
        with open(path, "r") as f:
            data = json.load(f)
        return RegressionBaseline.from_dict(data)
