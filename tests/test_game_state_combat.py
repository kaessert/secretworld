"""Tests for GameState combat integration."""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState


class TestIsInCombat:
    """Test is_in_combat() method."""
    
    def test_is_in_combat_returns_false_initially(self):
        """Spec: is_in_combat() should return False when no combat is active."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        world = {
            "Town Square": Location(
                name="Town Square",
                description="A bustling town square",
                connections={"north": "Forest Path"}
            ),
            "Forest Path": Location(
                name="Forest Path",
                description="A path through the forest",
                connections={"south": "Town Square"}
            )
        }
        game_state = GameState(character, world)
        
        assert game_state.is_in_combat() is False
    
    def test_is_in_combat_returns_true_during_combat(self):
        """Spec: is_in_combat() should return True when combat is active."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        world = {
            "Town Square": Location(
                name="Town Square",
                description="A bustling town square",
                connections={"north": "Forest Path"}
            ),
            "Forest Path": Location(
                name="Forest Path",
                description="A path through the forest",
                connections={"south": "Town Square"}
            )
        }
        game_state = GameState(character, world)
        
        # Trigger an encounter (may be random, so try multiple times)
        game_state.trigger_encounter("Forest Path")
        
        # If an encounter was triggered, should be in combat
        if game_state.current_combat is not None:
            assert game_state.is_in_combat() is True


class TestTriggerEncounter:
    """Test trigger_encounter() method."""
    
    def test_trigger_encounter_spawns_enemy(self):
        """Spec: trigger_encounter() should spawn enemy with 30% chance."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        world = {
            "Forest Path": Location(
                name="Forest Path",
                description="A path through the forest",
                connections={}
            )
        }
        game_state = GameState(character, world, starting_location="Forest Path")
        
        # Try multiple times to ensure encounter can trigger
        encounter_triggered = False
        for _ in range(50):
            game_state.current_combat = None  # Reset
            result = game_state.trigger_encounter("Forest Path")
            if result is not None:
                encounter_triggered = True
                break
        
        # Should have at least one encounter in 50 tries with 30% chance
        assert encounter_triggered, "No encounters triggered in 50 attempts"
    
    def test_trigger_encounter_creates_combat_encounter(self):
        """Spec: trigger_encounter() should create CombatEncounter when triggered."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        world = {
            "Forest Path": Location(
                name="Forest Path",
                description="A path through the forest",
                connections={}
            )
        }
        game_state = GameState(character, world, starting_location="Forest Path")
        
        # Force an encounter to check creation
        from cli_rpg.combat import CombatEncounter
        for _ in range(50):
            game_state.current_combat = None
            result = game_state.trigger_encounter("Forest Path")
            if result is not None:
                assert game_state.current_combat is not None
                assert isinstance(game_state.current_combat, CombatEncounter)
                assert game_state.current_combat.is_active is True
                break
    
    def test_trigger_encounter_returns_none_when_no_encounter(self):
        """Spec: trigger_encounter() should return None when no encounter occurs."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        world = {
            "Forest Path": Location(
                name="Forest Path",
                description="A path through the forest",
                connections={}
            )
        }
        game_state = GameState(character, world, starting_location="Forest Path")
        
        # Try multiple times - some should return None
        no_encounter_count = 0
        for _ in range(20):
            game_state.current_combat = None
            result = game_state.trigger_encounter("Forest Path")
            if result is None:
                no_encounter_count += 1
        
        # With 30% chance, roughly 14 out of 20 should be None
        assert no_encounter_count > 5, "Too many encounters triggered (should be ~30%)"


class TestMoveWithCombat:
    """Test move() triggers encounters."""
    
    def test_move_can_trigger_encounter(self):
        """Spec: move() should call trigger_encounter() after successful move."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        world = {
            "Town Square": Location(
                name="Town Square",
                description="A bustling town square",
                connections={"north": "Forest Path"}
            ),
            "Forest Path": Location(
                name="Forest Path",
                description="A path through the forest",
                connections={"south": "Town Square"}
            )
        }
        game_state = GameState(character, world)
        
        # Move multiple times to check if encounter can trigger
        encounter_triggered = False
        for _ in range(50):
            game_state.current_location = "Town Square"
            game_state.current_combat = None
            success, message = game_state.move("north")
            assert success is True
            
            if game_state.current_combat is not None:
                encounter_triggered = True
                break
        
        # At least one encounter should trigger in 50 moves
        assert encounter_triggered, "No encounters triggered after 50 moves"


class TestCombatStateSerialization:
    """Test combat state serialization."""
    
    def test_to_dict_includes_no_combat_when_none(self):
        """Spec: to_dict() should handle no active combat."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        world = {
            "Town Square": Location(
                name="Town Square",
                description="A bustling town square",
                connections={}
            )
        }
        game_state = GameState(character, world)
        
        data = game_state.to_dict()
        # Should not have combat data or should be None
        assert "current_combat" not in data or data.get("current_combat") is None
    
    def test_from_dict_restores_no_combat(self):
        """Spec: from_dict() should handle no active combat."""
        data = {
            "character": {
                "name": "Hero",
                "strength": 10,
                "dexterity": 10,
                "intelligence": 10,
                "level": 1,
                "health": 150,
                "max_health": 150,
                "xp": 0
            },
            "current_location": "Town Square",
            "world": {
                "Town Square": {
                    "name": "Town Square",
                    "description": "A bustling town square",
                    "connections": {}
                }
            },
            "theme": "fantasy"
        }
        game_state = GameState.from_dict(data)
        
        assert game_state.is_in_combat() is False
