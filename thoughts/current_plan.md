# Implementation Plan: YAML Scenario Format and Runner

## Spec

YAML scenario runner that executes scripted test sequences using the existing assertion framework.

### YAML Format
```yaml
scenario:
  name: "Scenario Name"
  description: "Optional description"
  seed: 42  # Optional fixed seed
  config:
    max_commands: 100
    timeout: 60
  setup:  # Optional commands before steps
    - "dump-state"
  steps:
    - command: "look"
      wait_for: "location"  # Optional: wait for state field to be populated
      assertions:
        - type: STATE_EQUALS
          field: "in_combat"
          value: false
        - type: CONTENT_PRESENT
          field: "location"
    - command: "go north"
      assertions:
        - type: COMMAND_VALID
    - command: "attack"
      wait_for: "in_combat"
      assertions:
        - type: STATE_EQUALS
          field: "in_combat"
          value: true
```

### ScenarioRunner API
```python
@dataclass
class ScenarioResult:
    scenario_name: str
    passed: bool
    steps_run: int
    assertions_passed: int
    assertions_failed: int
    results: list[StepResult]
    duration: float

class ScenarioRunner:
    def run(self, scenario_path: Path) -> ScenarioResult
    def run_scenario(self, scenario: Scenario) -> ScenarioResult
```

---

## Tests (tests/test_scenario_runner.py)

### 1. YAML Parsing Tests
- `test_parse_minimal_scenario` - name and one step only
- `test_parse_full_scenario` - all optional fields (description, seed, config, setup)
- `test_parse_step_with_assertions` - multiple assertion types per step
- `test_parse_assertion_types` - all 8 AssertionType values from YAML

### 2. Scenario Dataclass Tests
- `test_scenario_to_dict_from_dict` - roundtrip serialization
- `test_step_to_dict_from_dict` - step serialization

### 3. ScenarioRunner Integration Tests
- `test_runner_executes_steps_in_order` - commands sent sequentially
- `test_runner_checks_assertions` - assertions evaluated per step
- `test_runner_returns_result` - ScenarioResult populated correctly
- `test_runner_handles_failed_assertion` - continues/stops based on config
- `test_runner_respects_wait_for` - waits for state field before assertions

---

## Implementation Steps

### 1. Create `scripts/validation/scenarios.py`

```python
# Dataclasses
@dataclass
class ScenarioStep:
    command: str
    assertions: list[Assertion] = field(default_factory=list)
    wait_for: Optional[str] = None

@dataclass
class Scenario:
    name: str
    steps: list[ScenarioStep]
    description: str = ""
    seed: Optional[int] = None
    config: dict = field(default_factory=dict)
    setup: list[str] = field(default_factory=list)

    def to_dict() -> dict
    @classmethod
    def from_dict(data: dict) -> Scenario
    @classmethod
    def from_yaml(path: Path) -> Scenario

@dataclass
class StepResult:
    step_index: int
    command: str
    assertion_results: list[AssertionResult]
    output: str

@dataclass
class ScenarioResult:
    scenario_name: str
    passed: bool
    steps_run: int
    assertions_passed: int
    assertions_failed: int
    results: list[StepResult]
    duration: float
```

### 2. Implement ScenarioRunner class

```python
class ScenarioRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checker = AssertionChecker()

    def run(self, scenario_path: Path) -> ScenarioResult:
        scenario = Scenario.from_yaml(scenario_path)
        return self.run_scenario(scenario)

    def run_scenario(self, scenario: Scenario) -> ScenarioResult:
        # 1. Create GameSession with scenario.seed
        # 2. Run setup commands
        # 3. For each step:
        #    a. Send command
        #    b. Wait for output / wait_for condition
        #    c. Check assertions against current state
        #    d. Record StepResult
        # 4. Return ScenarioResult
```

### 3. YAML parsing helper

```python
def _parse_assertion(data: dict) -> Assertion:
    """Convert YAML assertion dict to Assertion dataclass."""
    return Assertion(
        type=AssertionType[data["type"]],
        field=data.get("field", ""),
        expected=data.get("value"),  # 'value' in YAML, 'expected' in Assertion
        message=data.get("message", ""),
    )
```

### 4. Update `scripts/validation/__init__.py`

Export new classes:
- `Scenario`, `ScenarioStep`, `StepResult`, `ScenarioResult`
- `ScenarioRunner`

### 5. Create tests file `tests/test_scenario_runner.py`

Test all spec points as outlined above.

---

## File Changes Summary

| File | Action |
|------|--------|
| `scripts/validation/scenarios.py` | CREATE - Scenario, ScenarioStep, ScenarioResult, StepResult, ScenarioRunner |
| `scripts/validation/__init__.py` | EDIT - Add exports |
| `tests/test_scenario_runner.py` | CREATE - Unit tests |

---

## Dependencies

- `pyyaml` - for YAML parsing (check if already in requirements)
- Existing: `scripts/validation/assertions.py` (AssertionType, Assertion, AssertionChecker)
- Existing: `scripts/ai_agent.py` (GameSession for running game)
- Existing: `scripts/state_parser.py` (AgentState for state tracking)
