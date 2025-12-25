"""Tests for Echo Choices Foundation - choice tracking system.

Spec: Track significant player decisions as the foundation for Phase 2 "Consequence" features.
"""
import pytest
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


@pytest.fixture
def basic_game_state():
    """Create a minimal GameState for testing."""
    character = Character(name="TestPlayer", strength=10, dexterity=10, intelligence=10)
    world = {
        "Town Square": Location(
            name="Town Square",
            description="The central plaza.",
            coordinates=(0, 0),
            category="town",
        )
    }
    return GameState(character, world, starting_location="Town Square")


# =============================================================================
# GameState Choice Tracking Tests
# =============================================================================

class TestRecordChoice:
    """Tests for record_choice() method."""

    def test_record_choice_adds_to_list(self, basic_game_state):
        """Spec: choice appears in choices list after recording."""
        gs = basic_game_state

        assert len(gs.choices) == 0

        gs.record_choice(
            choice_type="combat_mercy",
            choice_id="spare_bandit_001",
            description="Spared the bandit",
            target="Bandit"
        )

        assert len(gs.choices) == 1

    def test_record_choice_includes_all_fields(self, basic_game_state):
        """Spec: all fields populated correctly in recorded choice."""
        gs = basic_game_state

        gs.record_choice(
            choice_type="dialogue",
            choice_id="helped_villager_quest",
            description="Agreed to help the villager",
            target="Old Man"
        )

        choice = gs.choices[0]

        # Check all required fields
        assert choice["choice_type"] == "dialogue"
        assert choice["choice_id"] == "helped_villager_quest"
        assert choice["description"] == "Agreed to help the villager"
        assert choice["target"] == "Old Man"
        assert choice["location"] == "Town Square"
        assert "timestamp" in choice
        assert isinstance(choice["timestamp"], int)

    def test_record_choice_without_target(self, basic_game_state):
        """Spec: target is optional (None when not applicable)."""
        gs = basic_game_state

        gs.record_choice(
            choice_type="exploration",
            choice_id="entered_dark_cave",
            description="Entered the forbidden cave"
        )

        choice = gs.choices[0]
        assert choice["target"] is None


class TestHasChoice:
    """Tests for has_choice() method."""

    def test_has_choice_returns_true_for_recorded(self, basic_game_state):
        """Spec: returns True for existing choice."""
        gs = basic_game_state

        gs.record_choice(
            choice_type="quest",
            choice_id="accepted_dragon_hunt",
            description="Accepted the dragon hunt quest"
        )

        assert gs.has_choice("accepted_dragon_hunt") is True

    def test_has_choice_returns_false_for_missing(self, basic_game_state):
        """Spec: returns False for non-existent choice."""
        gs = basic_game_state

        assert gs.has_choice("nonexistent_choice") is False


class TestGetChoicesByType:
    """Tests for get_choices_by_type() method."""

    def test_get_choices_by_type_filters_correctly(self, basic_game_state):
        """Spec: only returns matching type."""
        gs = basic_game_state

        # Record choices of different types
        gs.record_choice(
            choice_type="combat_mercy",
            choice_id="spare_goblin",
            description="Spared the goblin"
        )
        gs.record_choice(
            choice_type="dialogue",
            choice_id="lied_to_guard",
            description="Lied to the guard"
        )
        gs.record_choice(
            choice_type="combat_mercy",
            choice_id="spare_orc",
            description="Spared the orc"
        )

        combat_choices = gs.get_choices_by_type("combat_mercy")

        assert len(combat_choices) == 2
        assert all(c["choice_type"] == "combat_mercy" for c in combat_choices)

    def test_get_choices_by_type_empty_when_no_matches(self, basic_game_state):
        """Spec: empty list if none match."""
        gs = basic_game_state

        gs.record_choice(
            choice_type="dialogue",
            choice_id="test",
            description="Test choice"
        )

        result = gs.get_choices_by_type("combat_flee")

        assert result == []


# =============================================================================
# Persistence Tests
# =============================================================================

class TestChoicesPersistence:
    """Tests for choices serialization and deserialization."""

    def test_choices_persist_in_save(self, basic_game_state):
        """Spec: save/load roundtrip preserves choices."""
        gs = basic_game_state

        # Record some choices
        gs.record_choice(
            choice_type="combat_flee",
            choice_id="flee_dragon",
            description="Fled from the dragon",
            target="Ancient Dragon"
        )
        gs.record_choice(
            choice_type="quest",
            choice_id="accepted_quest",
            description="Accepted the blacksmith's request"
        )

        # Serialize
        data = gs.to_dict()

        # Verify choices are in serialized data
        assert "choices" in data
        assert len(data["choices"]) == 2

        # Deserialize into new GameState
        restored_gs = GameState.from_dict(data)

        # Verify choices were restored
        assert len(restored_gs.choices) == 2
        assert restored_gs.has_choice("flee_dragon")
        assert restored_gs.has_choice("accepted_quest")

        # Verify choice details preserved
        flee_choice = [c for c in restored_gs.choices if c["choice_id"] == "flee_dragon"][0]
        assert flee_choice["choice_type"] == "combat_flee"
        assert flee_choice["target"] == "Ancient Dragon"

    def test_choices_backward_compatibility(self, basic_game_state):
        """Spec: old saves load with empty choices list."""
        gs = basic_game_state

        # Simulate old save data (no choices field)
        data = gs.to_dict()
        del data["choices"]  # Remove choices as if it's an old save

        # Should load without error
        restored_gs = GameState.from_dict(data)

        # Should have empty choices list
        assert hasattr(restored_gs, "choices")
        assert restored_gs.choices == []


# =============================================================================
# Integration Tests
# =============================================================================

class TestFleeIntegration:
    """Tests for flee combat recording a choice."""

    def test_flee_combat_records_choice(self, basic_game_state, monkeypatch):
        """Spec: fleeing combat records a choice."""
        import random
        from cli_rpg.models.enemy import Enemy
        from cli_rpg.combat import CombatEncounter
        from cli_rpg import main

        gs = basic_game_state

        # Create an enemy and put player in combat
        enemy = Enemy(
            name="Angry Goblin",
            level=1,
            health=20,
            max_health=20,
            attack_power=5,
            defense=2,
            xp_reward=10
        )
        gs.current_combat = CombatEncounter(gs.current_character, enemies=[enemy])
        gs.current_combat.is_active = True

        # Mock the flee roll to always succeed
        # Flee uses random.randint(1, 100) and succeeds if roll <= 50 + dex*2
        # With dex=10, flee_chance = 70, so roll of 1 always succeeds
        monkeypatch.setattr(random, 'randint', lambda a, b: 1)  # Always roll 1 = success

        # Execute flee command
        continue_game, message = main.handle_combat_command(gs, "flee", [])

        # Verify combat ended
        assert gs.current_combat is None

        # Verify choice was recorded
        assert gs.has_choice("flee_Angry Goblin")

        flee_choices = gs.get_choices_by_type("combat_flee")
        assert len(flee_choices) == 1
        assert flee_choices[0]["target"] == "Angry Goblin"
        assert "Fled from Angry Goblin" in flee_choices[0]["description"]
