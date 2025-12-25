"""Tests for the rest command.

Spec: Add a `rest` command that allows players to heal outside of combat without
requiring potions. Heals 25% of max health, has alias 'r', blocked during combat.
"""

import pytest
from cli_rpg.main import handle_exploration_command, handle_combat_command
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.combat import CombatEncounter
from cli_rpg.models.enemy import Enemy


@pytest.fixture
def game_state():
    """Create basic game state for testing."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    world = {"Town": Location(name="Town", description="A quiet town")}
    return GameState(char, world, starting_location="Town")


@pytest.fixture
def game_state_in_combat(game_state):
    """Create game state with active combat."""
    enemy = Enemy(name="Goblin", health=50, max_health=50, attack_power=5, defense=2, xp_reward=10)
    game_state.current_combat = CombatEncounter(game_state.current_character, enemy)
    return game_state


class TestRestCommand:
    """Tests for 'rest' command - Spec: Heal 25% of max HP outside combat."""

    # Spec: Rest heals 25% of max HP
    def test_rest_heals_partial_health(self, game_state):
        """Spec: Rest heals 25% of max HP."""
        gs = game_state
        max_hp = gs.current_character.max_health
        gs.current_character.take_damage(max_hp // 2)  # Take 50% damage
        old_health = gs.current_character.health

        cont, msg = handle_exploration_command(gs, "rest", [])

        assert cont is True
        expected_heal = max(1, max_hp // 4)  # 25% of max, minimum 1
        assert gs.current_character.health == old_health + expected_heal

    # Spec: Returns error message when health is already full
    def test_rest_at_full_health_fails(self, game_state):
        """Spec: Cannot rest when already at full health."""
        gs = game_state
        assert gs.current_character.health == gs.current_character.max_health

        cont, msg = handle_exploration_command(gs, "rest", [])

        assert cont is True
        assert "full health" in msg.lower() or "already" in msg.lower()
        # Health should remain unchanged
        assert gs.current_character.health == gs.current_character.max_health

    # Spec: Healing doesn't exceed max_health
    def test_rest_caps_at_max_health(self, game_state):
        """Spec: Rest healing is capped at max health."""
        gs = game_state
        max_hp = gs.current_character.max_health
        # Take only 10% damage (less than 25% heal would restore)
        small_damage = max_hp // 10
        gs.current_character.take_damage(small_damage)

        cont, msg = handle_exploration_command(gs, "rest", [])

        assert cont is True
        assert gs.current_character.health == max_hp

    # Spec: The `r` shorthand works for rest
    def test_rest_alias_r(self):
        """Spec: 'r' alias expands to 'rest' command."""
        cmd, args = parse_command("r")
        assert cmd == "rest"
        assert args == []

    # Spec: Rest command unavailable in combat
    def test_rest_blocked_during_combat(self, game_state_in_combat):
        """Spec: Cannot rest while in combat."""
        gs = game_state_in_combat
        gs.current_character.take_damage(50)  # Damage player

        cont, msg = handle_combat_command(gs, "rest", [])

        assert cont is True
        # Should get error message about not being able to rest in combat
        assert "combat" in msg.lower() or "can't" in msg.lower() or "not" in msg.lower()

    # Spec: Message shows amount healed
    def test_rest_displays_heal_amount(self, game_state):
        """Spec: Rest message displays the amount of HP restored."""
        gs = game_state
        max_hp = gs.current_character.max_health
        gs.current_character.take_damage(max_hp // 2)  # Take 50% damage
        expected_heal = max(1, max_hp // 4)  # 25% of max HP

        cont, msg = handle_exploration_command(gs, "rest", [])

        assert cont is True
        assert str(expected_heal) in msg


class TestParseCommandRest:
    """Tests for parse_command with rest command."""

    def test_parse_rest_command(self):
        """Spec: 'rest' is a recognized command."""
        cmd, args = parse_command("rest")
        assert cmd == "rest"
        assert args == []

    def test_parse_rest_case_insensitive(self):
        """Spec: 'REST' is case-insensitive."""
        cmd, args = parse_command("REST")
        assert cmd == "rest"
        assert args == []

    def test_parse_r_alias(self):
        """Spec: 'r' expands to 'rest'."""
        cmd, args = parse_command("r")
        assert cmd == "rest"
        assert args == []


class TestHelpIncludesRest:
    """Test that help text includes rest command."""

    def test_help_includes_rest(self):
        """Spec: Command reference includes rest command."""
        from cli_rpg.main import get_command_reference
        help_text = get_command_reference()
        assert "rest" in help_text.lower()
        assert "(r)" in help_text  # Alias shown
