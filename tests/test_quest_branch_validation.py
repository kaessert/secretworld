"""Tests for QuestBranch validation (TDD)."""
import pytest
from cli_rpg.models.quest import QuestBranch, ObjectiveType


class TestBranchValidation:
    """Test QuestBranch validation rules."""

    def test_branch_requires_id(self):
        """Branch must have a unique id."""
        # Tests: Branch id is required and non-empty
        with pytest.raises(ValueError, match="id"):
            QuestBranch(
                id="",  # Empty id
                name="Test Branch",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_branch_requires_name(self):
        """Branch must have a display name."""
        # Tests: Branch name is required and non-empty
        with pytest.raises(ValueError, match="name"):
            QuestBranch(
                id="test",
                name="",  # Empty name
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_branch_requires_target(self):
        """Branch must have a target."""
        # Tests: Branch target is required and non-empty
        with pytest.raises(ValueError, match="target"):
            QuestBranch(
                id="test",
                name="Test Branch",
                objective_type=ObjectiveType.KILL,
                target="",  # Empty target
            )

    def test_branch_target_count_must_be_positive(self):
        """Branch target_count must be at least 1."""
        # Tests: target_count validation
        with pytest.raises(ValueError, match="target_count"):
            QuestBranch(
                id="test",
                name="Test Branch",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                target_count=0,
            )

    def test_branch_current_count_non_negative(self):
        """Branch current_count must be non-negative."""
        # Tests: current_count validation
        with pytest.raises(ValueError, match="current_count"):
            QuestBranch(
                id="test",
                name="Test Branch",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                current_count=-1,
            )

    def test_valid_branch_passes_validation(self):
        """Valid branch should pass all validation."""
        # Tests: Valid branches don't raise
        branch = QuestBranch(
            id="kill",
            name="Kill Target",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
            current_count=1,
            description="Slay the goblins",
            faction_effects={"Village": 10},
            gold_modifier=1.5,
            xp_modifier=0.8,
        )
        assert branch.id == "kill"
        assert branch.target_count == 3
        assert branch.current_count == 1
