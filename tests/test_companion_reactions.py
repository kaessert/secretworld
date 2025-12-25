"""Tests for companion reactions to player choices.

These tests verify the companion reaction system where companions respond
to player choices based on their personality type.
"""
import pytest
from cli_rpg.models.companion import Companion
from cli_rpg.companion_reactions import (
    get_companion_reaction,
    process_companion_reactions,
    APPROVAL_BOND_CHANGE,
    DISAPPROVAL_BOND_CHANGE,
)


class TestCompanionPersonality:
    """Test companion personality field."""

    def test_companion_has_personality_field(self):
        """Companions should have a personality field."""
        companion = Companion(
            name="Kira",
            description="A fierce warrior",
            recruited_at="Arena",
            personality="warrior"
        )
        assert companion.personality == "warrior"

    def test_companion_default_personality_is_pragmatic(self):
        """Default personality is pragmatic (neutral)."""
        companion = Companion(
            name="Sage",
            description="A wise scholar",
            recruited_at="Library"
        )
        assert companion.personality == "pragmatic"


class TestReduceBond:
    """Test bond reduction for disapproval."""

    def test_reduce_bond_decreases_points(self):
        """reduce_bond should decrease bond_points."""
        companion = Companion(
            name="Kira",
            description="Test",
            recruited_at="Test",
            bond_points=30
        )
        companion.reduce_bond(5)
        assert companion.bond_points == 25

    def test_reduce_bond_cannot_go_below_zero(self):
        """Bond points cannot go negative."""
        companion = Companion(
            name="Kira",
            description="Test",
            recruited_at="Test",
            bond_points=2
        )
        companion.reduce_bond(10)
        assert companion.bond_points == 0


class TestGetCompanionReaction:
    """Test individual companion reactions to choices."""

    def test_warrior_approves_kill(self):
        """Warrior personality approves of combat kills."""
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            personality="warrior"
        )
        reaction = get_companion_reaction(companion, "combat_kill")
        assert reaction == "approval"

    def test_warrior_disapproves_flee(self):
        """Warrior personality disapproves of fleeing."""
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            personality="warrior"
        )
        reaction = get_companion_reaction(companion, "combat_flee")
        assert reaction == "disapproval"

    def test_pacifist_disapproves_kill(self):
        """Pacifist personality disapproves of killing."""
        companion = Companion(
            name="Dove",
            description="A healer",
            recruited_at="Temple",
            personality="pacifist"
        )
        reaction = get_companion_reaction(companion, "combat_kill")
        assert reaction == "disapproval"

    def test_pacifist_approves_flee(self):
        """Pacifist personality approves of fleeing."""
        companion = Companion(
            name="Dove",
            description="A healer",
            recruited_at="Temple",
            personality="pacifist"
        )
        reaction = get_companion_reaction(companion, "combat_flee")
        assert reaction == "approval"

    def test_pragmatic_is_neutral(self):
        """Pragmatic personality is neutral to most choices."""
        companion = Companion(
            name="Sage",
            description="A scholar",
            recruited_at="Library",
            personality="pragmatic"
        )
        assert get_companion_reaction(companion, "combat_kill") == "neutral"
        assert get_companion_reaction(companion, "combat_flee") == "neutral"


class TestProcessCompanionReactions:
    """Test processing reactions and returning messages."""

    def test_approval_increases_bond(self):
        """Approval should increase bond by APPROVAL_BOND_CHANGE."""
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            personality="warrior",
            bond_points=20
        )
        messages = process_companion_reactions([companion], "combat_kill")
        assert companion.bond_points == 20 + APPROVAL_BOND_CHANGE

    def test_disapproval_decreases_bond(self):
        """Disapproval should decrease bond by DISAPPROVAL_BOND_CHANGE."""
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            personality="warrior",
            bond_points=20
        )
        messages = process_companion_reactions([companion], "combat_flee")
        assert companion.bond_points == 20 + DISAPPROVAL_BOND_CHANGE  # Negative

    def test_neutral_no_change(self):
        """Neutral reaction should not change bond."""
        companion = Companion(
            name="Sage",
            description="A scholar",
            recruited_at="Library",
            personality="pragmatic",
            bond_points=20
        )
        messages = process_companion_reactions([companion], "combat_kill")
        assert companion.bond_points == 20

    def test_reaction_returns_message(self):
        """Processing reactions should return flavor messages."""
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            personality="warrior"
        )
        messages = process_companion_reactions([companion], "combat_kill")
        assert len(messages) > 0
        assert "Kira" in messages[0]

    def test_multiple_companions_react_independently(self):
        """Each companion should react based on their own personality."""
        warrior = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            personality="warrior",
            bond_points=20
        )
        pacifist = Companion(
            name="Dove",
            description="A healer",
            recruited_at="Temple",
            personality="pacifist",
            bond_points=20
        )
        messages = process_companion_reactions([warrior, pacifist], "combat_kill")
        assert warrior.bond_points == 20 + APPROVAL_BOND_CHANGE
        assert pacifist.bond_points == 20 + DISAPPROVAL_BOND_CHANGE
