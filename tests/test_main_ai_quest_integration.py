"""Tests for AI-generated quest integration in NPC talk command.

This module tests the integration of AI quest generation when talking to
quest-giver NPCs who have no available quests.
"""

import pytest
from unittest.mock import Mock, patch

from cli_rpg.main import handle_exploration_command
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.quest import Quest, ObjectiveType


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_quest_response():
    """Valid AI-generated quest response."""
    return {
        "name": "Goblin Menace",
        "description": "Clear the goblins from the forest.",
        "objective_type": "kill",
        "target": "Goblin",
        "target_count": 5,
        "gold_reward": 100,
        "xp_reward": 75,
        "quest_giver": "Elder Marcus",
    }


@pytest.fixture
def quest_giver_npc():
    """Create a quest-giver NPC with no quests."""
    return NPC(
        name="Elder Marcus",
        description="A wise village elder",
        dialogue="Greetings, adventurer.",
        is_quest_giver=True,
        offered_quests=[],
    )


@pytest.fixture
def quest_giver_with_quest():
    """Create a quest-giver NPC with an existing quest."""
    quest = Quest(
        name="Rat Problem",
        description="Kill the rats in the cellar.",
        objective_type=ObjectiveType.KILL,
        target="Rat",
        target_count=3,
        gold_reward=50,
        xp_reward=30,
        quest_giver="Elder Marcus",
    )
    return NPC(
        name="Elder Marcus",
        description="A wise village elder",
        dialogue="Greetings, adventurer.",
        is_quest_giver=True,
        offered_quests=[quest],
    )


@pytest.fixture
def basic_location(quest_giver_npc):
    """Create a location with the quest-giver NPC."""
    return Location(
        name="Village Square",
        description="A bustling village square.",
        npcs=[quest_giver_npc],
    )


@pytest.fixture
def mock_ai_service(mock_quest_response):
    """Create a mock AI service that returns a valid quest."""
    service = Mock()
    service.generate_quest.return_value = mock_quest_response
    return service


@pytest.fixture
def game_state_with_ai(basic_location, mock_ai_service):
    """Create game state with AI service and quest-giver NPC."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    world = {"Village Square": basic_location}
    return GameState(
        char, world, starting_location="Village Square", ai_service=mock_ai_service, theme="fantasy"
    )


@pytest.fixture
def game_state_no_ai(quest_giver_npc):
    """Create game state without AI service."""
    location = Location(
        name="Village Square",
        description="A bustling village square.",
        npcs=[quest_giver_npc],
    )
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    world = {"Village Square": location}
    return GameState(char, world, starting_location="Village Square")


# =============================================================================
# Test: Quest-giver with no quests generates AI quest
# Spec: When AI available, quest-giver with empty offered_quests gets a generated quest added
# =============================================================================


class TestTalkQuestGiverNoQuestsGeneratesAIQuest:
    """Spec: When AI available, quest-giver with empty offered_quests gets a generated quest."""

    def test_talk_quest_giver_no_quests_generates_ai_quest(
        self, game_state_with_ai, mock_ai_service
    ):
        """Spec: AI generates quest for quest-giver with no offered_quests."""
        npc = game_state_with_ai.world["Village Square"].npcs[0]
        assert len(npc.offered_quests) == 0  # Precondition

        cont, output = handle_exploration_command(game_state_with_ai, "talk", ["Elder", "Marcus"])

        # AI service should have been called
        mock_ai_service.generate_quest.assert_called_once()
        call_kwargs = mock_ai_service.generate_quest.call_args[1]
        assert call_kwargs["theme"] == "fantasy"
        assert call_kwargs["npc_name"] == "Elder Marcus"
        assert call_kwargs["player_level"] == 1
        assert call_kwargs["location_name"] == "Village Square"

        # Quest should be added to NPC
        assert len(npc.offered_quests) == 1
        assert npc.offered_quests[0].name == "Goblin Menace"
        assert npc.offered_quests[0].quest_giver == "Elder Marcus"


# =============================================================================
# Test: Quest-giver with all quests accepted generates new quest
# Spec: Quest-giver whose quests are all accepted by player gets new quest generated
# =============================================================================


class TestTalkQuestGiverAllQuestsAcceptedGeneratesNew:
    """Spec: Quest-giver whose quests are all accepted generates a new quest."""

    def test_talk_quest_giver_all_quests_accepted_generates_new(
        self, quest_giver_with_quest, mock_ai_service, mock_quest_response
    ):
        """Spec: When player has already accepted all quests, generate new one."""
        location = Location(
            name="Village Square",
            description="A bustling village square.",
            npcs=[quest_giver_with_quest],
        )
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Village Square": location}
        gs = GameState(
            char, world, starting_location="Village Square", ai_service=mock_ai_service, theme="fantasy"
        )

        # Player accepts the existing quest (add to quests list directly)
        existing_quest = quest_giver_with_quest.offered_quests[0]
        char.quests.append(existing_quest)

        # Now talk to NPC - should generate new quest
        cont, output = handle_exploration_command(gs, "talk", ["Elder", "Marcus"])

        # AI should generate a new quest
        mock_ai_service.generate_quest.assert_called_once()

        # Should now have 2 quests
        assert len(quest_giver_with_quest.offered_quests) == 2
        assert quest_giver_with_quest.offered_quests[1].name == "Goblin Menace"


# =============================================================================
# Test: AI unavailable - no error
# Spec: Without AI service, no quest generation occurs (graceful skip)
# =============================================================================


class TestTalkQuestGiverAIUnavailableNoError:
    """Spec: Without AI service, no quest generation occurs."""

    def test_talk_quest_giver_ai_unavailable_no_error(self, game_state_no_ai):
        """Spec: Talk works normally without AI service, no generation."""
        npc = game_state_no_ai.world["Village Square"].npcs[0]
        assert len(npc.offered_quests) == 0

        cont, output = handle_exploration_command(game_state_no_ai, "talk", ["Elder", "Marcus"])

        assert cont is True
        assert "Elder Marcus" in output
        # No quests generated
        assert len(npc.offered_quests) == 0


# =============================================================================
# Test: AI failure - silent fallback
# Spec: AI exception doesn't break talk command
# =============================================================================


class TestTalkQuestGiverAIFailureSilentFallback:
    """Spec: AI exception doesn't break talk command."""

    def test_talk_quest_giver_ai_failure_silent_fallback(self, basic_location):
        """Spec: AI exception caught silently, talk continues normally."""
        failing_ai_service = Mock()
        failing_ai_service.generate_quest.side_effect = Exception("API Error")

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Village Square": basic_location}
        gs = GameState(
            char, world, starting_location="Village Square", ai_service=failing_ai_service, theme="fantasy"
        )

        npc = gs.world["Village Square"].npcs[0]
        assert len(npc.offered_quests) == 0

        # Talk should not raise, should complete normally
        cont, output = handle_exploration_command(gs, "talk", ["Elder", "Marcus"])

        assert cont is True
        assert "Elder Marcus" in output
        # No quest added due to failure
        assert len(npc.offered_quests) == 0


# =============================================================================
# Test: Generated quest appears in output
# Spec: Generated quest shows in "Available Quests:" output
# =============================================================================


class TestGeneratedQuestAppearsInAvailableQuestsOutput:
    """Spec: Generated quest shows in Available Quests: output."""

    def test_generated_quest_appears_in_available_quests_output(
        self, game_state_with_ai, mock_ai_service
    ):
        """Spec: After generation, quest shows in Available Quests section."""
        cont, output = handle_exploration_command(game_state_with_ai, "talk", ["Elder", "Marcus"])

        assert cont is True
        assert "Available Quests:" in output
        assert "Goblin Menace" in output
        assert "accept" in output.lower()  # Hint to accept
