"""Tests for quest commands (quests, quest <name>)."""

import pytest

from cli_rpg.game_state import parse_command, GameState
from cli_rpg.main import handle_exploration_command, handle_combat_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.combat import CombatEncounter
from cli_rpg.models.enemy import Enemy


# ============================================================================
# parse_command Tests
# ============================================================================


def test_parse_quests_command():
    """Test that 'quests' command is recognized."""
    command, args = parse_command("quests")
    assert command == "quests"
    assert args == []


def test_parse_quests_shorthand():
    """Test that 'q' expands to 'quests'."""
    command, args = parse_command("q")
    assert command == "quests"
    assert args == []


def test_parse_quest_command():
    """Test that 'quest' command is recognized with arguments."""
    command, args = parse_command("quest Kill Goblins")
    assert command == "quest"
    # parse_command lowercases all parts
    assert args == ["kill", "goblins"]


def test_parse_quest_command_no_args():
    """Test that 'quest' command works without arguments."""
    command, args = parse_command("quest")
    assert command == "quest"
    assert args == []


# ============================================================================
# Helper fixtures
# ============================================================================


@pytest.fixture
def character():
    """Create a test character."""
    return Character(name="Hero", strength=10, dexterity=10, intelligence=10)


@pytest.fixture
def simple_world():
    """Create a simple world for testing."""
    return {
        "Town Square": Location(
            name="Town Square",
            description="A central square.",
            connections={"north": "Forest"},
            coordinates=(0, 0),
        )
    }


@pytest.fixture
def game_state(character, simple_world):
    """Create a test game state."""
    return GameState(character, simple_world, starting_location="Town Square")


@pytest.fixture
def active_quest():
    """Create an active quest with some progress."""
    quest = Quest(
        name="Kill Goblins",
        description="Defeat goblins threatening the village.",
        objective_type=ObjectiveType.KILL,
        target="Goblin",
        target_count=5,
        current_count=2,
        status=QuestStatus.ACTIVE,
    )
    return quest


@pytest.fixture
def completed_quest():
    """Create a completed quest."""
    quest = Quest(
        name="Find the Map",
        description="Locate the ancient treasure map.",
        objective_type=ObjectiveType.COLLECT,
        target="Ancient Map",
        target_count=1,
        current_count=1,
        status=QuestStatus.COMPLETED,
    )
    return quest


# ============================================================================
# handle_exploration_command Tests - quests command
# ============================================================================


def test_quests_shows_empty_when_no_quests(game_state):
    """Test that 'quests' shows 'No active quests' when character has no quests."""
    continue_game, message = handle_exploration_command(game_state, "quests", [])

    assert continue_game is True
    assert "No active quests" in message


def test_quests_shows_active_quests(game_state, active_quest):
    """Test that 'quests' lists quests with progress (e.g., 'Kill Goblins [2/5]')."""
    game_state.current_character.quests.append(active_quest)

    continue_game, message = handle_exploration_command(game_state, "quests", [])

    assert continue_game is True
    assert "Kill Goblins" in message
    assert "[2/5]" in message


def test_quests_shows_completed_quests(game_state, active_quest, completed_quest):
    """Test that 'quests' shows completed quests in a separate section."""
    game_state.current_character.quests.append(active_quest)
    game_state.current_character.quests.append(completed_quest)

    continue_game, message = handle_exploration_command(game_state, "quests", [])

    assert continue_game is True
    # Active quest should be shown
    assert "Kill Goblins" in message
    # Completed quest should be shown separately
    assert "Find the Map" in message
    assert "Completed" in message


# ============================================================================
# handle_exploration_command Tests - quest <name> command
# ============================================================================


def test_quest_detail_shows_quest_info(game_state, active_quest):
    """Test that 'quest <name>' shows full quest details."""
    game_state.current_character.quests.append(active_quest)

    continue_game, message = handle_exploration_command(game_state, "quest", ["Kill", "Goblins"])

    assert continue_game is True
    assert "Kill Goblins" in message
    assert "Defeat goblins threatening the village" in message
    # Should show objective type
    assert "kill" in message.lower()
    # Should show target
    assert "Goblin" in message
    # Should show progress
    assert "2" in message and "5" in message


def test_quest_detail_not_found(game_state):
    """Test that 'quest <name>' returns error for unknown quest."""
    continue_game, message = handle_exploration_command(game_state, "quest", ["Unknown", "Quest"])

    assert continue_game is True
    assert "not found" in message.lower() or "no quest" in message.lower()


def test_quest_detail_no_args(game_state):
    """Test that 'quest' without args shows usage hint."""
    continue_game, message = handle_exploration_command(game_state, "quest", [])

    assert continue_game is True
    # Should prompt for quest name
    assert "specify" in message.lower() or "which quest" in message.lower()


def test_quest_detail_partial_match(game_state, active_quest):
    """Test that 'quest' finds quests with partial name match (case-insensitive)."""
    game_state.current_character.quests.append(active_quest)

    # Should find "Kill Goblins" with partial match "kill"
    continue_game, message = handle_exploration_command(game_state, "quest", ["kill"])

    assert continue_game is True
    assert "Kill Goblins" in message


# ============================================================================
# Combat blocking tests
# ============================================================================


def test_quest_blocked_during_combat(game_state):
    """Test that quest commands return error during combat."""
    # Start combat
    enemy = Enemy(name="Goblin", health=50, max_health=50, attack_power=5, defense=2, xp_reward=10)
    game_state.current_combat = CombatEncounter(game_state.current_character, enemy)

    # Try quests command
    continue_game, message = handle_combat_command(game_state, "quests", [])

    assert continue_game is True
    assert "combat" in message.lower() or "can't" in message.lower()


def test_quest_detail_blocked_during_combat(game_state, active_quest):
    """Test that 'quest <name>' returns error during combat."""
    game_state.current_character.quests.append(active_quest)

    # Start combat
    enemy = Enemy(name="Goblin", health=50, max_health=50, attack_power=5, defense=2, xp_reward=10)
    game_state.current_combat = CombatEncounter(game_state.current_character, enemy)

    # Try quest detail command
    continue_game, message = handle_combat_command(game_state, "quest", ["kill", "goblins"])

    assert continue_game is True
    assert "combat" in message.lower() or "can't" in message.lower()
