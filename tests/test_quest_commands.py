"""Tests for quest commands (quests, quest <name>)."""

import pytest

from cli_rpg.game_state import parse_command, GameState
from cli_rpg.main import handle_exploration_command, handle_combat_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.models.npc import NPC
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


# ============================================================================
# Tests for bug fix: accept command copies rewards
# ============================================================================


@pytest.fixture
def quest_giver_npc():
    """Create a quest-giving NPC with a quest that has rewards."""
    reward_quest = Quest(
        name="Kill the Rats",
        description="Clear the rats from the cellar",
        objective_type=ObjectiveType.KILL,
        target="Rat",
        target_count=5,
        status=QuestStatus.AVAILABLE,
        gold_reward=100,
        xp_reward=50,
        item_rewards=["Rat Tail"],
    )
    return NPC(
        name="Tavern Keeper",
        description="A busy innkeeper",
        dialogue="Welcome, traveler!",
        is_quest_giver=True,
        offered_quests=[reward_quest],
    )


@pytest.fixture
def game_state_with_npc(character, quest_giver_npc):
    """Create a game state with an NPC that offers quests."""
    location = Location(
        name="Town Square",
        description="A central square.",
        connections={"north": "Forest"},
        coordinates=(0, 0),
        npcs=[quest_giver_npc],
    )
    world = {"Town Square": location}
    return GameState(character, world, starting_location="Town Square")


def test_accept_quest_copies_gold_reward(game_state_with_npc, quest_giver_npc):
    """Test that accepting a quest copies the gold_reward field."""
    # Talk to NPC first to set current_npc
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])

    # Accept the quest
    handle_exploration_command(game_state_with_npc, "accept", ["kill", "the", "rats"])

    # Check that the quest was added with rewards
    char = game_state_with_npc.current_character
    assert len(char.quests) == 1
    accepted_quest = char.quests[0]
    assert accepted_quest.gold_reward == 100


def test_accept_quest_copies_xp_reward(game_state_with_npc, quest_giver_npc):
    """Test that accepting a quest copies the xp_reward field."""
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])
    handle_exploration_command(game_state_with_npc, "accept", ["kill", "the", "rats"])

    char = game_state_with_npc.current_character
    accepted_quest = char.quests[0]
    assert accepted_quest.xp_reward == 50


def test_accept_quest_copies_item_rewards(game_state_with_npc, quest_giver_npc):
    """Test that accepting a quest copies the item_rewards field."""
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])
    handle_exploration_command(game_state_with_npc, "accept", ["kill", "the", "rats"])

    char = game_state_with_npc.current_character
    accepted_quest = char.quests[0]
    assert accepted_quest.item_rewards == ["Rat Tail"]


def test_accept_quest_sets_quest_giver(game_state_with_npc, quest_giver_npc):
    """Test that accepting a quest sets the quest_giver field to NPC name."""
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])
    handle_exploration_command(game_state_with_npc, "accept", ["kill", "the", "rats"])

    char = game_state_with_npc.current_character
    accepted_quest = char.quests[0]
    assert accepted_quest.quest_giver == "Tavern Keeper"


# ============================================================================
# Tests for READY_TO_TURN_IN quest display
# ============================================================================


@pytest.fixture
def ready_to_turn_in_quest():
    """Create a quest that is ready to turn in."""
    return Quest(
        name="Goblin Hunt",
        description="Kill some goblins",
        objective_type=ObjectiveType.KILL,
        target="Goblin",
        target_count=3,
        current_count=3,
        status=QuestStatus.READY_TO_TURN_IN,
        quest_giver="Village Elder",
    )


def test_quests_command_shows_ready_to_turn_in_section(game_state, ready_to_turn_in_quest):
    """Test that 'quests' shows Ready to Turn In section."""
    game_state.current_character.quests.append(ready_to_turn_in_quest)

    continue_game, message = handle_exploration_command(game_state, "quests", [])

    assert continue_game is True
    assert "Ready to Turn In" in message
    assert "Goblin Hunt" in message
    assert "Village Elder" in message


def test_quest_detail_shows_quest_giver(game_state, ready_to_turn_in_quest):
    """Test that 'quest <name>' shows quest giver info."""
    game_state.current_character.quests.append(ready_to_turn_in_quest)

    continue_game, message = handle_exploration_command(game_state, "quest", ["goblin"])

    assert continue_game is True
    assert "Quest Giver: Village Elder" in message


def test_quest_detail_shows_ready_to_turn_in_status(game_state, ready_to_turn_in_quest):
    """Test that 'quest <name>' shows 'Ready To Turn In' status nicely."""
    game_state.current_character.quests.append(ready_to_turn_in_quest)

    continue_game, message = handle_exploration_command(game_state, "quest", ["goblin"])

    assert continue_game is True
    # Should format the status nicely
    assert "Ready To Turn In" in message


# ============================================================================
# Tests for complete command
# ============================================================================


def test_complete_command_requires_npc(game_state):
    """Test that 'complete' command requires talking to an NPC first."""
    continue_game, message = handle_exploration_command(game_state, "complete", ["some", "quest"])

    assert continue_game is True
    assert "talk to an npc" in message.lower()


def test_complete_command_requires_quest_name(game_state_with_npc, quest_giver_npc):
    """Test that 'complete' command requires a quest name argument."""
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])

    continue_game, message = handle_exploration_command(game_state_with_npc, "complete", [])

    assert continue_game is True
    assert "specify" in message.lower() or "which quest" in message.lower()


def test_complete_command_requires_ready_to_turn_in_status(game_state_with_npc, quest_giver_npc, active_quest):
    """Test that 'complete' command only works for READY_TO_TURN_IN quests."""
    game_state_with_npc.current_character.quests.append(active_quest)  # ACTIVE status
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])

    continue_game, message = handle_exploration_command(game_state_with_npc, "complete", ["kill", "goblins"])

    assert continue_game is True
    assert "no quest ready to turn in" in message.lower()


def test_complete_command_requires_matching_quest_giver(game_state_with_npc, quest_giver_npc, ready_to_turn_in_quest):
    """Test that 'complete' verifies quest giver matches current NPC."""
    # Quest was given by "Village Elder" but we're talking to "Tavern Keeper"
    game_state_with_npc.current_character.quests.append(ready_to_turn_in_quest)
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])

    continue_game, message = handle_exploration_command(game_state_with_npc, "complete", ["goblin"])

    assert continue_game is True
    assert "Village Elder" in message
    assert "can't turn in" in message.lower()


def test_complete_command_grants_rewards_and_sets_completed(game_state_with_npc, quest_giver_npc):
    """Test that 'complete' grants rewards and sets status to COMPLETED."""
    # Accept a quest first
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])
    handle_exploration_command(game_state_with_npc, "accept", ["kill", "the", "rats"])

    # Manually complete the quest objectives
    quest = game_state_with_npc.current_character.quests[0]
    quest.current_count = quest.target_count
    quest.status = QuestStatus.READY_TO_TURN_IN

    initial_gold = game_state_with_npc.current_character.gold
    initial_xp = game_state_with_npc.current_character.xp

    # Turn in the quest (use partial match "rats")
    continue_game, message = handle_exploration_command(game_state_with_npc, "complete", ["rats"])

    assert continue_game is True
    assert "Quest completed" in message
    assert quest.status == QuestStatus.COMPLETED
    assert game_state_with_npc.current_character.gold == initial_gold + 100
    assert game_state_with_npc.current_character.xp >= initial_xp + 50


def test_complete_command_shows_reward_messages(game_state_with_npc, quest_giver_npc):
    """Test that 'complete' shows reward messages."""
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])
    handle_exploration_command(game_state_with_npc, "accept", ["kill", "the", "rats"])

    quest = game_state_with_npc.current_character.quests[0]
    quest.current_count = quest.target_count
    quest.status = QuestStatus.READY_TO_TURN_IN

    continue_game, message = handle_exploration_command(game_state_with_npc, "complete", ["rats"])

    assert "100 gold" in message
    assert "50 XP" in message or "Gained 50" in message
    assert "Rat Tail" in message


# ============================================================================
# Tests for turn-in indicator in NPC dialogue
# ============================================================================


def test_talk_shows_turn_in_ready_quests(game_state_with_npc, quest_giver_npc):
    """Test that talking to NPC shows quests ready to turn in."""
    # Accept and complete quest
    handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])
    handle_exploration_command(game_state_with_npc, "accept", ["kill", "the", "rats"])

    quest = game_state_with_npc.current_character.quests[0]
    quest.current_count = quest.target_count
    quest.status = QuestStatus.READY_TO_TURN_IN

    # Talk again
    continue_game, message = handle_exploration_command(game_state_with_npc, "talk", ["tavern", "keeper"])

    assert "Quests ready to turn in" in message
    assert "Kill the Rats" in message
    assert "complete" in message.lower()


# ============================================================================
# Tests for abandon command
# ============================================================================


def test_parse_abandon_command():
    """Test that 'abandon' command is recognized."""
    command, args = parse_command("abandon Kill Goblins")
    assert command == "abandon"
    # parse_command lowercases all parts
    assert args == ["kill", "goblins"]


def test_abandon_quest_removes_active_quest(game_state, active_quest):
    """Test that abandoning removes quest from character's quest list."""
    game_state.current_character.quests.append(active_quest)
    assert len(game_state.current_character.quests) == 1

    continue_game, message = handle_exploration_command(game_state, "abandon", ["kill", "goblins"])

    assert continue_game is True
    assert len(game_state.current_character.quests) == 0
    assert "abandoned" in message.lower()
    assert "Kill Goblins" in message


def test_abandon_quest_not_found(game_state):
    """Test that abandoning unknown quest returns error."""
    continue_game, message = handle_exploration_command(game_state, "abandon", ["unknown", "quest"])

    assert continue_game is True
    assert "not found" in message.lower() or "no quest" in message.lower()


def test_abandon_quest_no_args(game_state):
    """Test that 'abandon' without args prompts for quest name."""
    continue_game, message = handle_exploration_command(game_state, "abandon", [])

    assert continue_game is True
    assert "specify" in message.lower() or "which quest" in message.lower()


def test_abandon_quest_partial_match(game_state, active_quest):
    """Test that 'abandon' finds quests with partial name match (case-insensitive)."""
    game_state.current_character.quests.append(active_quest)

    # Should find "Kill Goblins" with partial match "kill"
    continue_game, message = handle_exploration_command(game_state, "abandon", ["kill"])

    assert continue_game is True
    assert len(game_state.current_character.quests) == 0
    assert "Kill Goblins" in message


def test_abandon_cannot_abandon_completed(game_state, completed_quest):
    """Test that 'abandon' returns error for COMPLETED status quests."""
    game_state.current_character.quests.append(completed_quest)

    continue_game, message = handle_exploration_command(game_state, "abandon", ["find", "the", "map"])

    assert continue_game is True
    # Quest should still be in the list
    assert len(game_state.current_character.quests) == 1
    # Should show error about quest not being active
    assert "active" in message.lower() or "can't abandon" in message.lower() or "cannot abandon" in message.lower()


def test_abandon_cannot_abandon_ready_to_turn_in(game_state, ready_to_turn_in_quest):
    """Test that 'abandon' returns error for READY_TO_TURN_IN status quests."""
    game_state.current_character.quests.append(ready_to_turn_in_quest)

    continue_game, message = handle_exploration_command(game_state, "abandon", ["goblin"])

    assert continue_game is True
    # Quest should still be in the list
    assert len(game_state.current_character.quests) == 1
    # Should show error about quest not being active
    assert "active" in message.lower() or "can't abandon" in message.lower() or "cannot abandon" in message.lower()


def test_abandon_blocked_during_combat(game_state, active_quest):
    """Test that 'abandon' returns combat error during combat."""
    game_state.current_character.quests.append(active_quest)

    # Start combat
    enemy = Enemy(name="Goblin", health=50, max_health=50, attack_power=5, defense=2, xp_reward=10)
    game_state.current_combat = CombatEncounter(game_state.current_character, enemy)

    # Try abandon command
    continue_game, message = handle_combat_command(game_state, "abandon", ["kill", "goblins"])

    assert continue_game is True
    assert "combat" in message.lower() or "can't" in message.lower()
