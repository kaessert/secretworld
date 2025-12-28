"""Tests for YAML validation scenario files.

Validates that all YAML scenario files:
1. Parse without errors
2. Have valid assertion types
3. Use unique seeds across scenarios
"""

from pathlib import Path
from typing import Set

import pytest
import yaml

from scripts.validation.assertions import AssertionType
from scripts.validation.scenarios import Scenario


# Path to the scenarios directory
SCENARIOS_DIR = Path(__file__).parent.parent / "scripts" / "scenarios"


def get_all_scenario_files() -> list[Path]:
    """Get all YAML scenario files from the scenarios directory.

    Returns:
        List of paths to all .yaml files in the scenarios directory tree.
    """
    if not SCENARIOS_DIR.exists():
        return []
    return list(SCENARIOS_DIR.rglob("*.yaml"))


def load_yaml_file(path: Path) -> dict:
    """Load a YAML file and return its contents.

    Args:
        path: Path to the YAML file

    Returns:
        Parsed YAML content as a dict
    """
    with open(path, "r") as f:
        return yaml.safe_load(f)


class TestScenarioFileParsing:
    """Tests that all YAML scenario files parse correctly."""

    @pytest.mark.parametrize(
        "scenario_path",
        get_all_scenario_files(),
        ids=lambda p: str(p.relative_to(SCENARIOS_DIR.parent.parent)),
    )
    def test_yaml_parses_without_errors(self, scenario_path: Path):
        """Each scenario file should parse as valid YAML."""
        try:
            data = load_yaml_file(scenario_path)
            assert data is not None, f"Empty YAML file: {scenario_path}"
        except yaml.YAMLError as e:
            pytest.fail(f"YAML parse error in {scenario_path}: {e}")

    @pytest.mark.parametrize(
        "scenario_path",
        get_all_scenario_files(),
        ids=lambda p: str(p.relative_to(SCENARIOS_DIR.parent.parent)),
    )
    def test_scenario_loads_with_dataclass(self, scenario_path: Path):
        """Each scenario should load into the Scenario dataclass."""
        try:
            scenario = Scenario.from_yaml(scenario_path)
            assert scenario.name, f"Scenario must have a name: {scenario_path}"
            assert len(scenario.steps) > 0, f"Scenario must have steps: {scenario_path}"
        except Exception as e:
            pytest.fail(f"Failed to load scenario {scenario_path}: {e}")


class TestScenarioAssertions:
    """Tests that all assertions in scenario files are valid."""

    @pytest.mark.parametrize(
        "scenario_path",
        get_all_scenario_files(),
        ids=lambda p: str(p.relative_to(SCENARIOS_DIR.parent.parent)),
    )
    def test_assertions_have_valid_types(self, scenario_path: Path):
        """All assertions should use valid AssertionType enum values."""
        data = load_yaml_file(scenario_path)

        # Handle wrapped format
        scenario_data = data.get("scenario", data)
        steps = scenario_data.get("steps", [])

        valid_types = {t.name for t in AssertionType}

        for step_idx, step in enumerate(steps):
            assertions = step.get("assertions", [])
            for assertion_idx, assertion in enumerate(assertions):
                assertion_type = assertion.get("type")
                assert assertion_type in valid_types, (
                    f"Invalid assertion type '{assertion_type}' in "
                    f"{scenario_path}, step {step_idx + 1}, assertion {assertion_idx + 1}. "
                    f"Valid types: {valid_types}"
                )

    @pytest.mark.parametrize(
        "scenario_path",
        get_all_scenario_files(),
        ids=lambda p: str(p.relative_to(SCENARIOS_DIR.parent.parent)),
    )
    def test_steps_have_commands(self, scenario_path: Path):
        """All steps should have a command."""
        scenario = Scenario.from_yaml(scenario_path)

        for step_idx, step in enumerate(scenario.steps):
            assert step.command, (
                f"Step {step_idx + 1} in {scenario_path} must have a command"
            )


class TestScenarioSeeds:
    """Tests that scenario seeds are unique and valid."""

    def test_seeds_are_unique_across_scenarios(self):
        """All scenarios should have unique seeds to avoid test interference."""
        scenario_files = get_all_scenario_files()

        if not scenario_files:
            pytest.skip("No scenario files found")

        seeds: dict[int, Path] = {}

        for scenario_path in scenario_files:
            data = load_yaml_file(scenario_path)
            scenario_data = data.get("scenario", data)
            seed = scenario_data.get("seed")

            if seed is not None:
                assert seed not in seeds, (
                    f"Duplicate seed {seed} found in:\n"
                    f"  - {seeds[seed]}\n"
                    f"  - {scenario_path}"
                )
                seeds[seed] = scenario_path

    def test_seeds_are_in_expected_range(self):
        """Seeds should be in the designated range (42001-42999)."""
        scenario_files = get_all_scenario_files()

        if not scenario_files:
            pytest.skip("No scenario files found")

        for scenario_path in scenario_files:
            data = load_yaml_file(scenario_path)
            scenario_data = data.get("scenario", data)
            seed = scenario_data.get("seed")

            if seed is not None:
                assert 42001 <= seed <= 42999, (
                    f"Seed {seed} in {scenario_path} is outside expected range 42001-42999"
                )


class TestScenarioStructure:
    """Tests for proper scenario file structure."""

    def test_all_subdirectories_have_scenarios(self):
        """Each feature subdirectory should have at least one scenario."""
        expected_dirs = {"movement", "combat", "inventory", "npc", "exploration", "rest", "crafting"}

        if not SCENARIOS_DIR.exists():
            pytest.skip("Scenarios directory not found")

        actual_dirs = {d.name for d in SCENARIOS_DIR.iterdir() if d.is_dir()}

        for expected_dir in expected_dirs:
            assert expected_dir in actual_dirs, (
                f"Expected subdirectory '{expected_dir}' not found in {SCENARIOS_DIR}"
            )

            dir_path = SCENARIOS_DIR / expected_dir
            yaml_files = list(dir_path.glob("*.yaml"))
            assert len(yaml_files) > 0, (
                f"No YAML files found in {dir_path}"
            )

    def test_scenario_file_count(self):
        """There should be a minimum number of scenario files."""
        scenario_files = get_all_scenario_files()

        # Expect at least 10 scenario files (as per the plan)
        assert len(scenario_files) >= 10, (
            f"Expected at least 10 scenario files, found {len(scenario_files)}"
        )


class TestSpecificScenarios:
    """Tests for specific scenario content requirements."""

    def test_movement_scenarios_exist(self):
        """Movement scenarios should test navigation."""
        movement_dir = SCENARIOS_DIR / "movement"

        if not movement_dir.exists():
            pytest.skip("Movement directory not found")

        yaml_files = list(movement_dir.glob("*.yaml"))
        assert len(yaml_files) >= 3, "Expected at least 3 movement scenarios"

        # Check for specific files
        file_names = {f.name for f in yaml_files}
        assert "basic_navigation.yaml" in file_names, "basic_navigation.yaml not found"
        assert "subgrid_entry_exit.yaml" in file_names, "subgrid_entry_exit.yaml not found"
        assert "vertical_navigation.yaml" in file_names, "vertical_navigation.yaml not found"

    def test_combat_scenarios_exist(self):
        """Combat scenarios should test attack and flee."""
        combat_dir = SCENARIOS_DIR / "combat"

        if not combat_dir.exists():
            pytest.skip("Combat directory not found")

        yaml_files = list(combat_dir.glob("*.yaml"))
        assert len(yaml_files) >= 2, "Expected at least 2 combat scenarios"

        file_names = {f.name for f in yaml_files}
        assert "basic_attack.yaml" in file_names, "basic_attack.yaml not found"
        assert "flee_combat.yaml" in file_names, "flee_combat.yaml not found"

    def test_inventory_scenarios_exist(self):
        """Inventory scenarios should test equip and use."""
        inventory_dir = SCENARIOS_DIR / "inventory"

        if not inventory_dir.exists():
            pytest.skip("Inventory directory not found")

        yaml_files = list(inventory_dir.glob("*.yaml"))
        assert len(yaml_files) >= 2, "Expected at least 2 inventory scenarios"

        file_names = {f.name for f in yaml_files}
        assert "equip_unequip.yaml" in file_names, "equip_unequip.yaml not found"
        assert "use_item.yaml" in file_names, "use_item.yaml not found"

    def test_npc_scenarios_exist(self):
        """NPC scenarios should test talk and shop."""
        npc_dir = SCENARIOS_DIR / "npc"

        if not npc_dir.exists():
            pytest.skip("NPC directory not found")

        yaml_files = list(npc_dir.glob("*.yaml"))
        assert len(yaml_files) >= 2, "Expected at least 2 NPC scenarios"

        file_names = {f.name for f in yaml_files}
        assert "talk_dialogue.yaml" in file_names, "talk_dialogue.yaml not found"
        assert "shop_browse.yaml" in file_names, "shop_browse.yaml not found"

    def test_exploration_scenarios_exist(self):
        """Exploration scenarios should test look and map."""
        exploration_dir = SCENARIOS_DIR / "exploration"

        if not exploration_dir.exists():
            pytest.skip("Exploration directory not found")

        yaml_files = list(exploration_dir.glob("*.yaml"))
        assert len(yaml_files) >= 1, "Expected at least 1 exploration scenario"

        file_names = {f.name for f in yaml_files}
        assert "look_map.yaml" in file_names, "look_map.yaml not found"

    def test_rest_scenarios_exist(self):
        """Rest scenarios should test resting."""
        rest_dir = SCENARIOS_DIR / "rest"

        if not rest_dir.exists():
            pytest.skip("Rest directory not found")

        yaml_files = list(rest_dir.glob("*.yaml"))
        assert len(yaml_files) >= 1, "Expected at least 1 rest scenario"

        file_names = {f.name for f in yaml_files}
        assert "basic_rest.yaml" in file_names, "basic_rest.yaml not found"

    def test_crafting_scenarios_exist(self):
        """Crafting scenarios should test gather, craft, and recipes."""
        crafting_dir = SCENARIOS_DIR / "crafting"

        if not crafting_dir.exists():
            pytest.skip("Crafting directory not found")

        yaml_files = list(crafting_dir.glob("*.yaml"))
        assert len(yaml_files) >= 1, "Expected at least 1 crafting scenario"

        file_names = {f.name for f in yaml_files}
        assert "basic_crafting.yaml" in file_names, "basic_crafting.yaml not found"
