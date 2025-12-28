"""YAML scenario runner for scripted test sequences.

Executes scripted test sequences using the existing assertion framework.
Provides structured scenarios with steps, assertions, and wait conditions.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from scripts.ai_agent import GameSession
from scripts.state_parser import AgentState
from scripts.validation.assertions import Assertion, AssertionChecker, AssertionResult, AssertionType


@dataclass
class ScenarioStep:
    """A single step in a scenario with command and optional assertions.

    Attributes:
        command: The command to execute
        assertions: List of assertions to check after the command
        wait_for: Optional state field to wait for before checking assertions
    """

    command: str
    assertions: List[Assertion] = field(default_factory=list)
    wait_for: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize step to dictionary."""
        return {
            "command": self.command,
            "assertions": [a.to_dict() for a in self.assertions],
            "wait_for": self.wait_for,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioStep":
        """Deserialize step from dictionary."""
        assertions = [Assertion.from_dict(a) for a in data.get("assertions", [])]
        return cls(
            command=data["command"],
            assertions=assertions,
            wait_for=data.get("wait_for"),
        )


@dataclass
class Scenario:
    """A complete test scenario with metadata and steps.

    Attributes:
        name: Scenario name
        steps: List of scenario steps to execute
        description: Optional description
        seed: Optional fixed seed for reproducibility
        config: Optional configuration dictionary
        setup: Optional setup commands to run before steps
    """

    name: str
    steps: List[ScenarioStep]
    description: str = ""
    seed: Optional[int] = None
    config: Dict[str, Any] = field(default_factory=dict)
    setup: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize scenario to dictionary."""
        return {
            "scenario": {
                "name": self.name,
                "description": self.description,
                "seed": self.seed,
                "config": self.config,
                "setup": self.setup,
                "steps": [s.to_dict() for s in self.steps],
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        """Deserialize scenario from dictionary.

        Args:
            data: Dictionary with optional 'scenario' wrapper key

        Returns:
            Scenario instance
        """
        # Handle both wrapped and unwrapped formats
        if "scenario" in data:
            scenario_data = data["scenario"]
        else:
            scenario_data = data

        steps = [ScenarioStep.from_dict(s) for s in scenario_data.get("steps", [])]

        return cls(
            name=scenario_data["name"],
            steps=steps,
            description=scenario_data.get("description", ""),
            seed=scenario_data.get("seed"),
            config=scenario_data.get("config", {}),
            setup=scenario_data.get("setup", []),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "Scenario":
        """Load scenario from a YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Scenario instance
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


def _parse_assertion(data: Dict[str, Any]) -> Assertion:
    """Convert YAML assertion dict to Assertion dataclass.

    Args:
        data: YAML assertion dictionary

    Returns:
        Assertion dataclass instance
    """
    return Assertion(
        type=AssertionType[data["type"]],
        field=data.get("field", ""),
        expected=data.get("value"),  # 'value' in YAML, 'expected' in Assertion
        message=data.get("message", ""),
    )


# Override ScenarioStep.from_dict to use our YAML-specific parsing
_original_step_from_dict = ScenarioStep.from_dict


@classmethod
def _step_from_dict_yaml(cls, data: Dict[str, Any]) -> "ScenarioStep":
    """Deserialize step from YAML dictionary format."""
    assertions = []
    for a_data in data.get("assertions", []):
        # Handle YAML format (uses 'value' instead of 'expected')
        if "type" in a_data and isinstance(a_data.get("type"), str):
            assertions.append(_parse_assertion(a_data))
        else:
            assertions.append(Assertion.from_dict(a_data))

    return cls(
        command=data["command"],
        assertions=assertions,
        wait_for=data.get("wait_for"),
    )


ScenarioStep.from_dict = _step_from_dict_yaml


@dataclass
class StepResult:
    """Result of executing a single scenario step.

    Attributes:
        step_index: Index of the step in the scenario
        command: The command that was executed
        assertion_results: Results of checking assertions
        output: Raw output from the command
    """

    step_index: int
    command: str
    assertion_results: List[AssertionResult]
    output: str


@dataclass
class ScenarioResult:
    """Result of running a complete scenario.

    Attributes:
        scenario_name: Name of the scenario
        passed: Whether all assertions passed
        steps_run: Number of steps executed
        assertions_passed: Count of passed assertions
        assertions_failed: Count of failed assertions
        results: List of step results
        duration: Total execution time in seconds
    """

    scenario_name: str
    passed: bool
    steps_run: int
    assertions_passed: int
    assertions_failed: int
    results: List[StepResult]
    duration: float


class ScenarioRunner:
    """Runs YAML scenarios against the game.

    Executes scripted test sequences using GameSession and validates
    state using the assertion framework.
    """

    def __init__(self, verbose: bool = False):
        """Initialize the runner.

        Args:
            verbose: If True, print debug information
        """
        self.verbose = verbose
        self.checker = AssertionChecker()

    def run(self, scenario_path: Path) -> ScenarioResult:
        """Run a scenario from a YAML file.

        Args:
            scenario_path: Path to the YAML scenario file

        Returns:
            ScenarioResult with execution details
        """
        scenario = Scenario.from_yaml(scenario_path)
        return self.run_scenario(scenario)

    def run_scenario(self, scenario: Scenario) -> ScenarioResult:
        """Execute a scenario and return results.

        Args:
            scenario: Scenario to execute

        Returns:
            ScenarioResult with execution details
        """
        start_time = time.time()

        # Determine seed (use scenario seed or generate one)
        seed = scenario.seed if scenario.seed is not None else int(time.time())

        # Create GameSession with scenario configuration
        max_commands = scenario.config.get("max_commands", 1000)
        timeout = scenario.config.get("timeout", 300)

        session = GameSession(
            seed=seed,
            max_commands=max_commands,
            timeout=timeout,
            verbose=self.verbose,
            enable_checkpoints=False,  # Disable for testing
        )

        step_results: List[StepResult] = []
        assertions_passed = 0
        assertions_failed = 0
        all_passed = True

        try:
            session.start()

            # Wait for initial game startup
            time.sleep(0.5)
            session._read_output(wait_time=0.5, min_lines=1)

            # Run setup commands
            for setup_cmd in scenario.setup:
                session._send_command(setup_cmd)
                session._read_output(wait_time=0.2)

            # Run scenario steps
            for step_index, step in enumerate(scenario.steps):
                step_result = self._execute_step(session, step, step_index)
                step_results.append(step_result)

                # Count assertions
                for ar in step_result.assertion_results:
                    if ar.passed:
                        assertions_passed += 1
                    else:
                        assertions_failed += 1
                        all_passed = False

        finally:
            session.stop()

        duration = time.time() - start_time

        return ScenarioResult(
            scenario_name=scenario.name,
            passed=all_passed,
            steps_run=len(step_results),
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            results=step_results,
            duration=duration,
        )

    def _execute_step(
        self,
        session: GameSession,
        step: ScenarioStep,
        step_index: int,
    ) -> StepResult:
        """Execute a single scenario step.

        Args:
            session: Active GameSession
            step: Step to execute
            step_index: Index of this step

        Returns:
            StepResult with execution details
        """
        # Send command
        session._send_command(step.command)

        # Wait for output
        output_lines = session._read_output(wait_time=0.3, min_lines=1)
        output = "\n".join(output_lines)

        # Process output to update state
        session._process_messages(output_lines)

        # Handle wait_for condition
        if step.wait_for:
            self._wait_for_field(session, step.wait_for)

        # Check assertions
        assertion_results: List[AssertionResult] = []
        for assertion in step.assertions:
            result = self._check_assertion(session, assertion, output)
            assertion_results.append(result)

        return StepResult(
            step_index=step_index,
            command=step.command,
            assertion_results=assertion_results,
            output=output,
        )

    def _wait_for_field(
        self,
        session: GameSession,
        field: str,
        max_wait: float = 5.0,
        poll_interval: float = 0.1,
    ) -> bool:
        """Wait for a state field to be populated.

        Args:
            session: Active GameSession
            field: State field to wait for
            max_wait: Maximum time to wait in seconds
            poll_interval: Time between checks

        Returns:
            True if field became populated, False if timeout
        """
        start = time.time()

        while time.time() - start < max_wait:
            # Check if field is populated
            value = self._get_state_field(session.state, field)
            if value is not None and value != "" and value != []:
                return True

            # Read more output and update state
            output = session._read_output(wait_time=poll_interval)
            if output:
                session._process_messages(output)

        return False

    def _get_state_field(self, state: AgentState, field: str) -> Any:
        """Get a field value from state using dot notation.

        Args:
            state: AgentState to query
            field: Field path (e.g., "character.health")

        Returns:
            Field value or None if not found
        """
        if not field:
            return state

        parts = field.split(".")
        value = state

        for part in parts:
            if value is None:
                return None
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)

        return value

    def _check_assertion(
        self,
        session: GameSession,
        assertion: Assertion,
        output: str,
    ) -> AssertionResult:
        """Check an assertion against current state.

        Args:
            session: Active GameSession
            assertion: Assertion to check
            output: Command output text

        Returns:
            AssertionResult with check details
        """
        # Convert AgentState to dict for the checker
        state = session.state

        # Use the assertion checker
        return self.checker.check(
            assertion=assertion,
            state=state,
            prev_state=None,  # TODO: Track previous state if needed
            output=output,
        )
