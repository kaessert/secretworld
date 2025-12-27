"""Tests for companion persistence in GameState serialization."""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.companion import Companion, BondLevel
from cli_rpg.game_state import GameState


def create_test_game_state(companions=None):
    """Create a minimal game state for testing."""
    character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
    location = Location(
        name="Town Square",
        description="A bustling town center",
        coordinates=(0, 0)
    )
    world = {"Town Square": location}
    game_state = GameState(character, world, "Town Square")

    if companions:
        game_state.companions = companions

    return game_state


class TestGameStateCompanionsSerialization:
    """Tests for GameState companions serialization."""

    def test_gamestate_companions_serialization(self):
        """Test that companions are included in GameState.to_dict()."""
        # Spec: Update to_dict() to serialize companions
        companions = [
            Companion(
                name="Elara",
                description="A wandering minstrel",
                recruited_at="Town Square",
                bond_points=30
            ),
            Companion(
                name="Gareth",
                description="A retired soldier",
                recruited_at="Barracks",
                bond_points=75
            ),
        ]
        game_state = create_test_game_state(companions=companions)

        data = game_state.to_dict()

        assert "companions" in data
        assert len(data["companions"]) == 2
        assert data["companions"][0]["name"] == "Elara"
        assert data["companions"][0]["bond_points"] == 30
        assert data["companions"][1]["name"] == "Gareth"
        assert data["companions"][1]["bond_points"] == 75

    def test_gamestate_companions_deserialization(self):
        """Test that companions are restored in GameState.from_dict()."""
        # Spec: Update from_dict() to deserialize companions
        # First create a game state with companions and serialize it
        companions = [
            Companion(
                name="Elara",
                description="A wandering minstrel",
                recruited_at="Town Square",
                bond_points=50
            ),
        ]
        original_state = create_test_game_state(companions=companions)
        data = original_state.to_dict()

        # Now deserialize
        restored_state = GameState.from_dict(data)

        assert len(restored_state.companions) == 1
        restored_companion = restored_state.companions[0]
        assert restored_companion.name == "Elara"
        assert restored_companion.description == "A wandering minstrel"
        assert restored_companion.recruited_at == "Town Square"
        assert restored_companion.bond_points == 50
        assert restored_companion.get_bond_level() == BondLevel.TRUSTED

    def test_gamestate_companions_backward_compatibility(self):
        """Test that old saves without companions load with empty companions list."""
        # Spec: Empty list for old saves (backward compatibility)
        # Create data without companions key (simulating old save format)
        character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        location = Location(
            name="Town Square",
            description="A bustling town center",
            coordinates=(0, 0)
        )

        # Manually create save data without companions
        data = {
            "character": character.to_dict(),
            "current_location": "Town Square",
            "world": {"Town Square": location.to_dict()},
            "theme": "fantasy"
            # Note: no "companions" key
        }

        restored_state = GameState.from_dict(data)

        # Should have empty companions list, not None or error
        assert hasattr(restored_state, "companions")
        assert restored_state.companions == []

    def test_gamestate_empty_companions_serialization(self):
        """Test that empty companions list serializes correctly."""
        game_state = create_test_game_state(companions=[])

        data = game_state.to_dict()

        assert "companions" in data
        assert data["companions"] == []

    def test_gamestate_companions_roundtrip(self):
        """Test full roundtrip serialization preserves companion data."""
        companions = [
            Companion(
                name="Elara",
                description="A wandering minstrel",
                recruited_at="Town Square",
                bond_points=25  # Exactly at ACQUAINTANCE threshold
            ),
            Companion(
                name="Gareth",
                description="A retired soldier",
                recruited_at="Barracks",
                bond_points=100  # Max DEVOTED
            ),
        ]
        original_state = create_test_game_state(companions=companions)

        # Roundtrip
        data = original_state.to_dict()
        restored_state = GameState.from_dict(data)

        assert len(restored_state.companions) == 2

        # Check first companion
        c1 = restored_state.companions[0]
        assert c1.name == "Elara"
        assert c1.bond_points == 25
        assert c1.get_bond_level() == BondLevel.ACQUAINTANCE

        # Check second companion
        c2 = restored_state.companions[1]
        assert c2.name == "Gareth"
        assert c2.bond_points == 100
        assert c2.get_bond_level() == BondLevel.DEVOTED
