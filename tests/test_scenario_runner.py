"""Tests for the YAML scenario runner.

Tests the scenario parsing, dataclass serialization, and execution
of scripted test sequences using the assertion framework.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.validation.assertions import Assertion, AssertionChecker, AssertionResult, AssertionType
from scripts.validation.scenarios import (
    Scenario,
    ScenarioRunner,
    ScenarioResult,
    ScenarioStep,
    StepResult,
)


# === YAML Parsing Tests ===


class TestYAMLParsing:
    """Tests for YAML scenario file parsing."""

    def test_parse_minimal_scenario(self, tmp_path: Path) -> None:
        """Test parsing a scenario with only name and one step."""
        yaml_content = """
scenario:
  name: "Minimal Test"
  steps:
    - command: "look"
"""
        scenario_file = tmp_path / "minimal.yaml"
        scenario_file.write_text(yaml_content)

        scenario = Scenario.from_yaml(scenario_file)

        assert scenario.name == "Minimal Test"
        assert len(scenario.steps) == 1
        assert scenario.steps[0].command == "look"
        assert scenario.description == ""
        assert scenario.seed is None
        assert scenario.config == {}
        assert scenario.setup == []

    def test_parse_full_scenario(self, tmp_path: Path) -> None:
        """Test parsing a scenario with all optional fields."""
        yaml_content = """
scenario:
  name: "Full Test"
  description: "A complete scenario with all fields"
  seed: 42
  config:
    max_commands: 100
    timeout: 60
  setup:
    - "dump-state"
    - "look"
  steps:
    - command: "go north"
      assertions:
        - type: COMMAND_VALID
"""
        scenario_file = tmp_path / "full.yaml"
        scenario_file.write_text(yaml_content)

        scenario = Scenario.from_yaml(scenario_file)

        assert scenario.name == "Full Test"
        assert scenario.description == "A complete scenario with all fields"
        assert scenario.seed == 42
        assert scenario.config == {"max_commands": 100, "timeout": 60}
        assert scenario.setup == ["dump-state", "look"]
        assert len(scenario.steps) == 1

    def test_parse_step_with_assertions(self, tmp_path: Path) -> None:
        """Test parsing a step with multiple assertion types."""
        yaml_content = """
scenario:
  name: "Assertion Test"
  steps:
    - command: "attack"
      wait_for: "in_combat"
      assertions:
        - type: STATE_EQUALS
          field: "in_combat"
          value: true
        - type: CONTENT_PRESENT
          field: "enemy"
        - type: COMMAND_VALID
"""
        scenario_file = tmp_path / "assertions.yaml"
        scenario_file.write_text(yaml_content)

        scenario = Scenario.from_yaml(scenario_file)
        step = scenario.steps[0]

        assert step.command == "attack"
        assert step.wait_for == "in_combat"
        assert len(step.assertions) == 3

        # Check first assertion
        assert step.assertions[0].type == AssertionType.STATE_EQUALS
        assert step.assertions[0].field == "in_combat"
        assert step.assertions[0].expected is True

        # Check second assertion
        assert step.assertions[1].type == AssertionType.CONTENT_PRESENT
        assert step.assertions[1].field == "enemy"

        # Check third assertion
        assert step.assertions[2].type == AssertionType.COMMAND_VALID

    def test_parse_assertion_types(self, tmp_path: Path) -> None:
        """Test parsing all 8 AssertionType values from YAML."""
        yaml_content = """
scenario:
  name: "All Types Test"
  steps:
    - command: "test"
      assertions:
        - type: STATE_EQUALS
          field: "health"
          value: 100
        - type: STATE_CONTAINS
          field: "inventory"
          value: "sword"
        - type: STATE_RANGE
          field: "gold"
          value:
            min: 0
            max: 1000
        - type: NARRATIVE_MATCH
          field: "last_narrative"
          value: ".*welcome.*"
        - type: COMMAND_VALID
          field: ""
        - type: COMMAND_EFFECT
          field: "health"
          value:
            from: 100
            to: 80
        - type: CONTENT_PRESENT
          field: "location"
        - type: CONTENT_QUALITY
          field: "description"
"""
        scenario_file = tmp_path / "all_types.yaml"
        scenario_file.write_text(yaml_content)

        scenario = Scenario.from_yaml(scenario_file)
        assertions = scenario.steps[0].assertions

        assert len(assertions) == 8
        assert assertions[0].type == AssertionType.STATE_EQUALS
        assert assertions[1].type == AssertionType.STATE_CONTAINS
        assert assertions[2].type == AssertionType.STATE_RANGE
        assert assertions[3].type == AssertionType.NARRATIVE_MATCH
        assert assertions[4].type == AssertionType.COMMAND_VALID
        assert assertions[5].type == AssertionType.COMMAND_EFFECT
        assert assertions[6].type == AssertionType.CONTENT_PRESENT
        assert assertions[7].type == AssertionType.CONTENT_QUALITY


# === Scenario Dataclass Tests ===


class TestScenarioSerialization:
    """Tests for scenario dataclass serialization."""

    def test_scenario_to_dict_from_dict(self) -> None:
        """Test roundtrip serialization of Scenario."""
        original = Scenario(
            name="Test Scenario",
            description="Test description",
            seed=123,
            config={"max_commands": 50},
            setup=["look"],
            steps=[
                ScenarioStep(
                    command="go north",
                    assertions=[
                        Assertion(
                            type=AssertionType.STATE_EQUALS,
                            field="location",
                            expected="Northern Plains",
                        )
                    ],
                    wait_for="location",
                )
            ],
        )

        data = original.to_dict()
        restored = Scenario.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.seed == original.seed
        assert restored.config == original.config
        assert restored.setup == original.setup
        assert len(restored.steps) == len(original.steps)
        assert restored.steps[0].command == original.steps[0].command
        assert restored.steps[0].wait_for == original.steps[0].wait_for
        assert len(restored.steps[0].assertions) == len(original.steps[0].assertions)

    def test_step_to_dict_from_dict(self) -> None:
        """Test roundtrip serialization of ScenarioStep."""
        original = ScenarioStep(
            command="attack goblin",
            assertions=[
                Assertion(
                    type=AssertionType.COMMAND_VALID,
                    field="",
                    expected=None,
                ),
                Assertion(
                    type=AssertionType.STATE_EQUALS,
                    field="in_combat",
                    expected=True,
                ),
            ],
            wait_for="in_combat",
        )

        data = original.to_dict()
        restored = ScenarioStep.from_dict(data)

        assert restored.command == original.command
        assert restored.wait_for == original.wait_for
        assert len(restored.assertions) == len(original.assertions)
        assert restored.assertions[0].type == original.assertions[0].type
        assert restored.assertions[1].field == original.assertions[1].field


# === ScenarioRunner Integration Tests ===


class TestScenarioRunner:
    """Tests for ScenarioRunner execution."""

    def test_runner_executes_steps_in_order(self) -> None:
        """Test that commands are sent sequentially."""
        scenario = Scenario(
            name="Order Test",
            steps=[
                ScenarioStep(command="look"),
                ScenarioStep(command="go north"),
                ScenarioStep(command="go south"),
            ],
        )

        commands_sent = []

        # Mock GameSession
        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()
            mock_session.state = MagicMock()
            mock_session.state.location = "Test Location"
            MockSession.return_value = mock_session

            # Track commands
            def track_command(cmd):
                commands_sent.append(cmd)
                return []

            mock_session._send_command = track_command
            mock_session._read_output = MagicMock(return_value=[])
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            runner.run_scenario(scenario)

        # Verify order (setup commands first, then scenario steps)
        assert "look" in commands_sent
        assert "go north" in commands_sent
        assert "go south" in commands_sent
        # Verify order
        look_idx = commands_sent.index("look")
        north_idx = commands_sent.index("go north")
        south_idx = commands_sent.index("go south")
        assert look_idx < north_idx < south_idx

    def test_runner_checks_assertions(self) -> None:
        """Test that assertions are evaluated per step."""
        scenario = Scenario(
            name="Assertion Check Test",
            steps=[
                ScenarioStep(
                    command="look",
                    assertions=[
                        Assertion(
                            type=AssertionType.STATE_EQUALS,
                            field="in_combat",
                            expected=False,
                        ),
                    ],
                ),
            ],
        )

        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()
            mock_session.state = MagicMock()
            mock_session.state.in_combat = False
            MockSession.return_value = mock_session
            mock_session._send_command = MagicMock()
            mock_session._read_output = MagicMock(return_value=[])
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            result = runner.run_scenario(scenario)

        assert result.passed is True
        assert result.assertions_passed == 1
        assert result.assertions_failed == 0

    def test_runner_returns_result(self) -> None:
        """Test that ScenarioResult is populated correctly."""
        scenario = Scenario(
            name="Result Test",
            steps=[
                ScenarioStep(command="look"),
                ScenarioStep(command="go north"),
            ],
        )

        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()
            mock_session.state = MagicMock()
            MockSession.return_value = mock_session
            mock_session._send_command = MagicMock()
            mock_session._read_output = MagicMock(return_value=[])
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            result = runner.run_scenario(scenario)

        assert result.scenario_name == "Result Test"
        assert result.steps_run == 2
        assert len(result.results) == 2
        assert result.duration >= 0

    def test_runner_handles_failed_assertion(self) -> None:
        """Test runner behavior when an assertion fails."""
        scenario = Scenario(
            name="Failure Test",
            steps=[
                ScenarioStep(
                    command="attack",
                    assertions=[
                        Assertion(
                            type=AssertionType.STATE_EQUALS,
                            field="in_combat",
                            expected=True,  # Will fail - we're not in combat
                        ),
                    ],
                ),
            ],
        )

        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()
            mock_session.state = MagicMock()
            mock_session.state.in_combat = False  # Assertion will fail
            MockSession.return_value = mock_session
            mock_session._send_command = MagicMock()
            mock_session._read_output = MagicMock(return_value=[])
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            result = runner.run_scenario(scenario)

        assert result.passed is False
        assert result.assertions_failed == 1
        assert result.steps_run == 1  # Still runs the step

    def test_runner_respects_wait_for(self) -> None:
        """Test that runner waits for state field before assertions."""
        scenario = Scenario(
            name="Wait For Test",
            steps=[
                ScenarioStep(
                    command="enter dungeon",
                    wait_for="location",
                    assertions=[
                        Assertion(
                            type=AssertionType.CONTENT_PRESENT,
                            field="location",
                            expected=None,
                        ),
                    ],
                ),
            ],
        )

        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()

            # Track read_output calls
            read_count = [0]

            # Create a mock state that starts empty and populates after reads
            mock_state = MagicMock()
            mock_state.location = ""  # Start empty

            def mock_read_output(*args, **kwargs):
                read_count[0] += 1
                # After first read, populate the location
                if read_count[0] >= 2:
                    mock_state.location = "Dungeon Entrance"
                return []

            mock_session.state = mock_state
            mock_session._process_messages = MagicMock()

            MockSession.return_value = mock_session
            mock_session._send_command = MagicMock()
            mock_session._read_output = mock_read_output
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            result = runner.run_scenario(scenario)

        # Should have waited and eventually passed (location populated)
        assert result.passed is True
        # Should have read output multiple times while waiting
        assert read_count[0] >= 2

    def test_runner_with_setup_commands(self) -> None:
        """Test that setup commands are run before steps."""
        scenario = Scenario(
            name="Setup Test",
            setup=["dump-state", "look"],
            steps=[
                ScenarioStep(command="go north"),
            ],
        )

        commands_sent = []

        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()
            mock_session.state = MagicMock()
            MockSession.return_value = mock_session

            def track_command(cmd):
                commands_sent.append(cmd)

            mock_session._send_command = track_command
            mock_session._read_output = MagicMock(return_value=[])
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            runner.run_scenario(scenario)

        # Setup commands should come before step commands
        assert "dump-state" in commands_sent
        assert "look" in commands_sent
        assert "go north" in commands_sent
        dump_idx = commands_sent.index("dump-state")
        look_idx = commands_sent.index("look")
        north_idx = commands_sent.index("go north")
        assert dump_idx < look_idx < north_idx

    def test_runner_uses_seed(self) -> None:
        """Test that runner passes seed to GameSession."""
        scenario = Scenario(
            name="Seed Test",
            seed=12345,
            steps=[ScenarioStep(command="look")],
        )

        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()
            mock_session.state = MagicMock()
            MockSession.return_value = mock_session
            mock_session._send_command = MagicMock()
            mock_session._read_output = MagicMock(return_value=[])
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            runner.run_scenario(scenario)

        # Check that GameSession was created with the seed
        MockSession.assert_called()
        call_kwargs = MockSession.call_args.kwargs
        assert call_kwargs.get("seed") == 12345

    def test_run_from_file(self, tmp_path: Path) -> None:
        """Test running a scenario from a YAML file path."""
        yaml_content = """
scenario:
  name: "File Test"
  steps:
    - command: "look"
"""
        scenario_file = tmp_path / "test.yaml"
        scenario_file.write_text(yaml_content)

        with patch("scripts.validation.scenarios.GameSession") as MockSession:
            mock_session = MagicMock()
            mock_session.state = MagicMock()
            MockSession.return_value = mock_session
            mock_session._send_command = MagicMock()
            mock_session._read_output = MagicMock(return_value=[])
            mock_session.start = MagicMock()
            mock_session.stop = MagicMock()

            runner = ScenarioRunner()
            result = runner.run(scenario_file)

        assert result.scenario_name == "File Test"
        assert result.steps_run == 1


# === StepResult and ScenarioResult Tests ===


class TestResultDataclasses:
    """Tests for result dataclass functionality."""

    def test_step_result_creation(self) -> None:
        """Test creating a StepResult."""
        assertion_result = AssertionResult(
            assertion=Assertion(
                type=AssertionType.COMMAND_VALID,
                field="",
                expected=None,
            ),
            passed=True,
        )
        step_result = StepResult(
            step_index=0,
            command="look",
            assertion_results=[assertion_result],
            output="You see a forest clearing.",
        )

        assert step_result.step_index == 0
        assert step_result.command == "look"
        assert len(step_result.assertion_results) == 1
        assert step_result.assertion_results[0].passed is True

    def test_scenario_result_all_passed(self) -> None:
        """Test ScenarioResult when all assertions pass."""
        result = ScenarioResult(
            scenario_name="Test",
            passed=True,
            steps_run=3,
            assertions_passed=5,
            assertions_failed=0,
            results=[],
            duration=1.5,
        )

        assert result.passed is True
        assert result.assertions_passed == 5
        assert result.assertions_failed == 0

    def test_scenario_result_some_failed(self) -> None:
        """Test ScenarioResult when some assertions fail."""
        result = ScenarioResult(
            scenario_name="Test",
            passed=False,
            steps_run=3,
            assertions_passed=3,
            assertions_failed=2,
            results=[],
            duration=2.0,
        )

        assert result.passed is False
        assert result.assertions_passed == 3
        assert result.assertions_failed == 2
