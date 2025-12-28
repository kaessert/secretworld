"""Tests for QuestNetworkManager integration with GameState."""

import pytest
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.models.quest_network import QuestNetworkManager
from cli_rpg.models.location import Location


@pytest.fixture
def basic_game_state():
    """Create a minimal GameState for testing."""
    character = Character(
        name="Tester",
        character_class=CharacterClass.WARRIOR,
        strength=14,
        dexterity=10,
        intelligence=8,
    )
    world = {
        "Town Square": Location(
            name="Town Square",
            description="A central plaza.",
            coordinates=(0, 0),
        )
    }
    return GameState(character, world, starting_location="Town Square")


class TestQuestNetworkIntegration:
    """Tests for GameState.quest_network integration."""

    # Spec: GameState has quest_network attribute
    def test_game_state_has_quest_network(self, basic_game_state):
        """GameState should have a quest_network attribute."""
        assert hasattr(basic_game_state, "quest_network")
        assert isinstance(basic_game_state.quest_network, QuestNetworkManager)

    # Spec: Quest network is empty initially
    def test_quest_network_initially_empty(self, basic_game_state):
        """Quest network should start empty."""
        assert basic_game_state.quest_network.get_all_quests() == []

    # Spec: register_quest adds to network
    def test_register_quest_adds_to_network(self, basic_game_state):
        """register_quest should add quest to network."""
        quest = Quest(
            name="Kill Goblins",
            description="Defeat 5 goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
        )
        basic_game_state.register_quest(quest)

        assert basic_game_state.quest_network.get_quest("Kill Goblins") is quest

    # Spec: get_available_quests returns quests with met prerequisites
    def test_get_available_quests(self, basic_game_state):
        """get_available_quests should filter by completed prerequisites."""
        quest1 = Quest(
            name="First Quest",
            description="The beginning.",
            objective_type=ObjectiveType.KILL,
            target="rat",
        )
        quest2 = Quest(
            name="Second Quest",
            description="Requires first.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            prerequisite_quests=["First Quest"],
        )
        basic_game_state.register_quest(quest1)
        basic_game_state.register_quest(quest2)

        # No quests completed - only quest1 available
        available = basic_game_state.get_available_quests()
        assert quest1 in available
        assert quest2 not in available

        # Complete first quest (add to character quests with completed status)
        quest1.status = QuestStatus.COMPLETED
        basic_game_state.current_character.quests.append(quest1)

        # Now both should be available
        available = basic_game_state.get_available_quests()
        assert quest1 in available
        assert quest2 in available

    # Spec: get_completed_quest_names returns list of completed quest names
    def test_get_completed_quest_names(self, basic_game_state):
        """get_completed_quest_names should return names of completed quests."""
        quest1 = Quest(
            name="First Quest",
            description="The beginning.",
            objective_type=ObjectiveType.KILL,
            target="rat",
            status=QuestStatus.COMPLETED,
        )
        quest2 = Quest(
            name="Second Quest",
            description="Still active.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            status=QuestStatus.ACTIVE,
        )
        basic_game_state.current_character.quests.extend([quest1, quest2])

        completed = basic_game_state.get_completed_quest_names()
        assert "First Quest" in completed
        assert "Second Quest" not in completed


class TestQuestNetworkSerialization:
    """Tests for quest_network serialization with GameState."""

    def test_quest_network_serialized(self, basic_game_state):
        """Quest network should be included in to_dict."""
        quest = Quest(
            name="Kill Goblins",
            description="Defeat 5 goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            chain_id="goblin_war",
            chain_position=1,
        )
        basic_game_state.register_quest(quest)

        data = basic_game_state.to_dict()
        assert "quest_network" in data
        assert len(data["quest_network"]["quests"]) == 1

    def test_quest_network_deserialized(self, basic_game_state):
        """Quest network should be restored from from_dict."""
        quest = Quest(
            name="Kill Goblins",
            description="Defeat 5 goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            chain_id="goblin_war",
            chain_position=1,
        )
        basic_game_state.register_quest(quest)

        data = basic_game_state.to_dict()
        restored = GameState.from_dict(data)

        restored_quest = restored.quest_network.get_quest("Kill Goblins")
        assert restored_quest is not None
        assert restored_quest.chain_id == "goblin_war"
        assert restored_quest.chain_position == 1

    def test_backward_compatibility_no_quest_network(self, basic_game_state):
        """from_dict should handle saves without quest_network."""
        data = basic_game_state.to_dict()
        del data["quest_network"]  # Simulate old save

        restored = GameState.from_dict(data)
        assert isinstance(restored.quest_network, QuestNetworkManager)
        assert restored.quest_network.get_all_quests() == []


class TestChainProgression:
    """Tests for quest chain progression queries."""

    def test_get_chain_progression(self, basic_game_state):
        """get_chain_progression should return (completed, total) for chain."""
        q1 = Quest(
            name="Chain Quest 1",
            description="First.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            chain_id="main",
            chain_position=1,
            status=QuestStatus.COMPLETED,
        )
        q2 = Quest(
            name="Chain Quest 2",
            description="Second.",
            objective_type=ObjectiveType.KILL,
            target="orc",
            chain_id="main",
            chain_position=2,
            status=QuestStatus.ACTIVE,
        )
        basic_game_state.register_quest(q1)
        basic_game_state.register_quest(q2)
        basic_game_state.current_character.quests.extend([q1, q2])

        completed, total = basic_game_state.get_chain_progression("main")
        assert completed == 1
        assert total == 2

    def test_get_next_in_chain(self, basic_game_state):
        """get_next_in_chain should return first incomplete quest."""
        q1 = Quest(
            name="Chain Quest 1",
            description="First.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            chain_id="main",
            chain_position=1,
            status=QuestStatus.COMPLETED,
        )
        q2 = Quest(
            name="Chain Quest 2",
            description="Second.",
            objective_type=ObjectiveType.KILL,
            target="orc",
            chain_id="main",
            chain_position=2,
        )
        basic_game_state.register_quest(q1)
        basic_game_state.register_quest(q2)
        basic_game_state.current_character.quests.append(q1)

        next_quest = basic_game_state.get_next_in_chain("main")
        assert next_quest.name == "Chain Quest 2"
