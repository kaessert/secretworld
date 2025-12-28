# Plan: Regression Detection for Automated Playtesting

## Feature Spec

Implement `scripts/validation/regression.py` to detect feature regressions by comparing test runs against baselines. The system will:

1. **Store baselines** - Save coverage/assertion results from "known good" runs
2. **Compare runs** - Detect new failures, resolved issues, and coverage changes
3. **Generate reports** - Produce clear regression reports in JSON/text format

Key data structures:
- `RegressionBaseline`: Dataclass storing pass rates, coverage stats, assertion results per scenario
- `RegressionReport`: Dataclass with new failures, resolved issues, coverage deltas
- `RegressionDetector`: Class to compare run results against baseline and generate reports

## Tests (tests/test_validation_regression.py)

```python
# Test cases to write FIRST:

class TestRegressionBaseline:
    def test_baseline_creation_from_scenario_results()
    def test_baseline_serialization_roundtrip()
    def test_baseline_merge_multiple_runs()

class TestRegressionReport:
    def test_report_identifies_new_failures()
    def test_report_identifies_resolved_issues()
    def test_report_tracks_coverage_delta()
    def test_report_empty_when_no_changes()

class TestRegressionDetector:
    def test_detector_compare_identical_runs()
    def test_detector_compare_with_new_failure()
    def test_detector_compare_with_resolved_failure()
    def test_detector_coverage_regression_detected()
    def test_detector_coverage_improvement_detected()
    def test_detector_load_save_baseline()
```

## Implementation Steps

1. **Create `scripts/validation/regression.py`**:
   - `RegressionBaseline` dataclass with:
     - `scenarios: dict[str, ScenarioBaseline]` (pass/fail, assertion results)
     - `coverage: dict[str, float]` (percentage per category)
     - `timestamp: float`
     - `version: str`
     - `to_dict()`/`from_dict()` for JSON serialization
   - `RegressionReport` dataclass with:
     - `new_failures: list[FailureDiff]` (scenario/assertion that newly failed)
     - `resolved_issues: list[FailureDiff]` (previously failing, now passing)
     - `coverage_delta: dict[str, float]` (category -> delta)
     - `is_regression: bool` property (True if new_failures or coverage decreased)
     - `to_text()` for human-readable report
   - `RegressionDetector` class with:
     - `create_baseline(results: list[ScenarioResult], coverage: FeatureCoverage) -> RegressionBaseline`
     - `compare(baseline: RegressionBaseline, current: RegressionBaseline) -> RegressionReport`
     - `save_baseline(baseline: RegressionBaseline, path: Path)`
     - `load_baseline(path: Path) -> RegressionBaseline`

2. **Update `scripts/validation/__init__.py`**:
   - Export: `RegressionBaseline`, `RegressionReport`, `RegressionDetector`

3. **Create `scripts/baselines/` directory**:
   - Add `.gitkeep` for empty directory tracking

4. **Create `tests/test_validation_regression.py`**:
   - Implement all test cases listed above
   - Use mock ScenarioResult/FeatureCoverage objects

## Files to Create/Modify

| File | Action |
|------|--------|
| `scripts/validation/regression.py` | CREATE - Core regression detection logic |
| `scripts/validation/__init__.py` | MODIFY - Add exports |
| `scripts/baselines/.gitkeep` | CREATE - Directory for baseline storage |
| `tests/test_validation_regression.py` | CREATE - Unit tests |
