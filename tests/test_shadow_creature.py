"""Tests for shadow creature attack at 100% dread.

This tests the spec: When dread reaches 100%, trigger a Shadow Creature combat encounter.
(As documented in models/dread.py line 9: "100%: Shadow creature attack triggered")
"""
import pytest
from unittest.mock import patch, MagicMock

from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState
from cli_rpg.shadow_creature import (
    spawn_shadow_creature,
    SHADOW_CREATURE_NAME,
    SHADOW_CREATURE_DESCRIPTION,
    SHADOW_VICTORY_DREAD_REDUCTION,
    check_and_trigger_shadow_attack,
)


def create_test_character():
    """Create a test character."""
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


def create_test_world():
    """Create a test world."""
    town = Location(
        name="Town Square",
        description="A town.",
        coordinates=(0, 0),
        category="town"
    )
    cave = Location(
        name="Dark Cave",
        description="A cave.",
        coordinates=(0, 1),
        category="cave"
    )
    return {"Town Square": town, "Dark Cave": cave}


class TestSpawnShadowCreature:
    """Test shadow creature spawning. Tests spawn_shadow_creature() function."""

    def test_spawn_returns_enemy(self):
        """spawn_shadow_creature returns an Enemy instance."""
        # Tests: Shadow creature spawning creates proper Enemy object
        enemy = spawn_shadow_creature(level=5)
        assert isinstance(enemy, Enemy)

    def test_spawn_has_shadow_name(self):
        """Shadow creature has the correct name."""
        # Tests: Shadow creature has correct themed name
        enemy = spawn_shadow_creature(level=1)
        assert enemy.name == SHADOW_CREATURE_NAME

    def test_spawn_has_description(self):
        """Shadow creature has a description."""
        # Tests: Shadow creature has flavor description
        enemy = spawn_shadow_creature(level=1)
        assert enemy.description == SHADOW_CREATURE_DESCRIPTION

    def test_spawn_scales_with_level(self):
        """Shadow creature stats scale with player level."""
        # Tests: Shadow creature difficulty scales appropriately
        enemy_low = spawn_shadow_creature(level=1)
        enemy_high = spawn_shadow_creature(level=10)
        assert enemy_high.health > enemy_low.health
        assert enemy_high.attack_power > enemy_low.attack_power

    def test_spawn_has_ascii_art(self):
        """Shadow creature has ASCII art."""
        # Tests: Shadow creature has visual representation
        enemy = spawn_shadow_creature(level=1)
        assert enemy.ascii_art != ""

    def test_spawn_has_attack_flavor(self):
        """Shadow creature has attack flavor text."""
        # Tests: Shadow creature has themed attack descriptions
        enemy = spawn_shadow_creature(level=1)
        assert enemy.attack_flavor != ""

    def test_spawn_not_boss(self):
        """Shadow creature is not marked as boss."""
        # Tests: Shadow creature is a special encounter but not a boss
        enemy = spawn_shadow_creature(level=1)
        assert enemy.is_boss is False


class TestCheckAndTriggerShadowAttack:
    """Test the shadow attack trigger logic. Tests check_and_trigger_shadow_attack()."""

    def test_triggers_at_100_dread(self):
        """Shadow attack triggers when dread is 100."""
        # Tests: Core trigger condition - shadow attacks at critical dread
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 100

        result = check_and_trigger_shadow_attack(game_state)

        assert result is not None
        assert game_state.is_in_combat()
        assert SHADOW_CREATURE_NAME in game_state.current_combat.enemy.name

    def test_no_trigger_below_100(self):
        """Shadow attack does not trigger below 100 dread."""
        # Tests: No false positives - shadow only attacks at critical level
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 99

        result = check_and_trigger_shadow_attack(game_state)

        assert result is None
        assert not game_state.is_in_combat()

    def test_no_trigger_if_already_in_combat(self):
        """Shadow attack does not trigger if already in combat."""
        # Tests: Shadow doesn't interrupt existing combat
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 100

        # Start a combat first
        from cli_rpg.combat import CombatEncounter
        dummy_enemy = Enemy(
            name="Goblin", health=10, max_health=10, attack_power=5, defense=1, xp_reward=10
        )
        game_state.current_combat = CombatEncounter(char, enemies=[dummy_enemy])
        game_state.current_combat.is_active = True

        result = check_and_trigger_shadow_attack(game_state)

        assert result is None
        # Combat should still be with goblin, not shadow
        assert "Goblin" in game_state.current_combat.enemy.name

    def test_returns_combat_message(self):
        """Trigger returns a descriptive message."""
        # Tests: Player gets dramatic feedback when shadow attacks
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 100

        result = check_and_trigger_shadow_attack(game_state)

        assert "shadow" in result.lower() or "darkness" in result.lower()


class TestShadowCreatureInGameState:
    """Test integration with GameState movement."""

    def test_move_at_100_dread_triggers_shadow(self):
        """Moving when at 100% dread triggers shadow creature."""
        # Tests: Shadow integrates with movement system
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Set dread to 100 before move
        char.dread_meter.dread = 100

        # Move (patch random to prevent regular encounters)
        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            with patch("cli_rpg.random_encounters.random.random", return_value=0.9):
                success, message = game_state.move("north")

        assert success
        assert game_state.is_in_combat()
        assert SHADOW_CREATURE_NAME in game_state.current_combat.enemy.name

    def test_reaching_100_during_move_triggers_shadow(self):
        """If dread reaches 100 during move, shadow triggers."""
        # Tests: Shadow triggers even if dread crosses threshold during move
        char = create_test_character()
        # Create dungeon with high dread increase
        town = Location(
            name="Town Square",
            description="A town.",
            coordinates=(0, 0),
            category="town"
        )
        dungeon = Location(
            name="Deep Dungeon",
            description="A very dark dungeon.",
            coordinates=(0, 1),
            category="dungeon"
        )
        world = {"Town Square": town, "Deep Dungeon": dungeon}
        game_state = GameState(char, world, "Town Square")

        # Set dread just below threshold so dungeon move crosses it
        char.dread_meter.dread = 90  # Dungeon adds 15, will reach 100+

        # Move (patch random to prevent regular encounters)
        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            with patch("cli_rpg.random_encounters.random.random", return_value=0.9):
                success, message = game_state.move("north")

        assert success
        assert game_state.is_in_combat()
        assert SHADOW_CREATURE_NAME in game_state.current_combat.enemy.name


class TestShadowDefeatDreadReduction:
    """Test that defeating shadow creature reduces dread."""

    def test_victory_dread_reduction_constant(self):
        """Verify the dread reduction constant is set correctly."""
        # Tests: The constant for dread reduction on victory is defined
        assert SHADOW_VICTORY_DREAD_REDUCTION == 50

    def test_shadow_combat_starts_correctly(self):
        """Shadow creature combat starts with proper state."""
        # Tests: Combat encounter is properly initialized
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 100

        # Trigger shadow attack
        check_and_trigger_shadow_attack(game_state)

        assert game_state.is_in_combat()
        assert game_state.current_combat.is_active
        shadow = game_state.current_combat.enemy
        assert shadow.name == SHADOW_CREATURE_NAME
        assert shadow.health > 0
