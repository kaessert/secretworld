"""Tests for quest difficulty UI display and AI parsing integration.

These tests verify:
- Quest journal shows difficulty indicator (Spec: journal display)
- Quest details shows difficulty and level (Spec: details display)
- NPC quest list shows difficulty (Spec: NPC display)
- Accept command copies difficulty fields (Spec: clone on accept)
- AI parsing handles difficulty fields (Spec: AI integration)
"""

import pytest

from cli_rpg.game_state import GameState
from cli_rpg.main import handle_exploration_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.quest import Quest, QuestDifficulty, QuestStatus, ObjectiveType
from cli_rpg.models.npc import NPC


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
            coordinates=(0, 0),
        )
    }


@pytest.fixture
def game_state(character, simple_world):
    """Create a test game state."""
    return GameState(character, simple_world, starting_location="Town Square")


# ============================================================================
# TestQuestDifficultyDisplay - Journal and Details View
# ============================================================================


class TestQuestDifficultyDisplay:
    """Tests for difficulty display in quest journal and details - Spec: UI display."""

    def test_journal_shows_difficulty_indicator_trivial(self, game_state):
        """Test that journal shows '.' indicator for trivial quests."""
        # Spec: diff_icons = {"trivial": ".", ...}
        quest = Quest(
            name="Easy Task",
            description="A trivial task.",
            objective_type=ObjectiveType.KILL,
            target="Rat",
            status=QuestStatus.ACTIVE,
            difficulty=QuestDifficulty.TRIVIAL,
        )
        game_state.current_character.quests.append(quest)

        continue_game, message = handle_exploration_command(game_state, "quests", [])

        assert continue_game is True
        # Trivial should have "." indicator
        assert ". Easy Task" in message

    def test_journal_shows_difficulty_indicator_easy(self, game_state):
        """Test that journal shows '-' indicator for easy quests."""
        # Spec: diff_icons = {..., "easy": "-", ...}
        quest = Quest(
            name="Simple Task",
            description="An easy task.",
            objective_type=ObjectiveType.COLLECT,
            target="Herb",
            status=QuestStatus.ACTIVE,
            difficulty=QuestDifficulty.EASY,
        )
        game_state.current_character.quests.append(quest)

        continue_game, message = handle_exploration_command(game_state, "quests", [])

        assert continue_game is True
        # Easy should have "-" indicator
        assert "- Simple Task" in message

    def test_journal_shows_difficulty_indicator_normal(self, game_state):
        """Test that journal shows '~' indicator for normal quests."""
        # Spec: diff_icons = {..., "normal": "~", ...}
        quest = Quest(
            name="Standard Task",
            description="A normal task.",
            objective_type=ObjectiveType.EXPLORE,
            target="Cave",
            status=QuestStatus.ACTIVE,
            difficulty=QuestDifficulty.NORMAL,
        )
        game_state.current_character.quests.append(quest)

        continue_game, message = handle_exploration_command(game_state, "quests", [])

        assert continue_game is True
        # Normal should have "~" indicator
        assert "~ Standard Task" in message

    def test_journal_shows_difficulty_indicator_hard(self, game_state):
        """Test that journal shows '!' indicator for hard quests."""
        # Spec: diff_icons = {..., "hard": "!", ...}
        quest = Quest(
            name="Tough Task",
            description="A hard task.",
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            status=QuestStatus.ACTIVE,
            difficulty=QuestDifficulty.HARD,
        )
        game_state.current_character.quests.append(quest)

        continue_game, message = handle_exploration_command(game_state, "quests", [])

        assert continue_game is True
        # Hard should have "!" indicator
        assert "! Tough Task" in message

    def test_journal_shows_difficulty_indicator_deadly(self, game_state):
        """Test that journal shows '!!' indicator for deadly quests."""
        # Spec: diff_icons = {..., "deadly": "!!"}
        quest = Quest(
            name="Impossible Task",
            description="A deadly task.",
            objective_type=ObjectiveType.KILL,
            target="Elder Dragon",
            status=QuestStatus.ACTIVE,
            difficulty=QuestDifficulty.DEADLY,
        )
        game_state.current_character.quests.append(quest)

        continue_game, message = handle_exploration_command(game_state, "quests", [])

        assert continue_game is True
        # Deadly should have "!!" indicator
        assert "!! Impossible Task" in message

    def test_quest_details_shows_difficulty_and_level(self, game_state):
        """Test that quest details view shows difficulty and recommended level."""
        # Spec: Display "Difficulty: Hard (Recommended: Lv.10)" in details
        quest = Quest(
            name="Boss Hunt",
            description="Hunt the mighty boss.",
            objective_type=ObjectiveType.KILL,
            target="Boss",
            status=QuestStatus.ACTIVE,
            difficulty=QuestDifficulty.HARD,
            recommended_level=10,
        )
        game_state.current_character.quests.append(quest)

        continue_game, message = handle_exploration_command(game_state, "quest", ["boss", "hunt"])

        assert continue_game is True
        assert "Difficulty: Hard (Recommended: Lv.10)" in message

    def test_quest_details_shows_normal_difficulty_by_default(self, game_state):
        """Test that quest details shows normal difficulty for default quests."""
        # Spec: Default difficulty is NORMAL, level 1
        quest = Quest(
            name="Basic Quest",
            description="A basic quest.",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            status=QuestStatus.ACTIVE,
        )
        game_state.current_character.quests.append(quest)

        continue_game, message = handle_exploration_command(game_state, "quest", ["basic", "quest"])

        assert continue_game is True
        assert "Difficulty: Normal (Recommended: Lv.1)" in message


# ============================================================================
# TestNPCQuestDisplay - NPC offered quests display
# ============================================================================


class TestNPCQuestDisplay:
    """Tests for difficulty display in NPC quest offers - Spec: NPC display."""

    def test_npc_available_quests_shows_difficulty(self, game_state):
        """Test that NPC quest list shows difficulty rating."""
        # Spec: Show difficulty in format "- Quest Name [Hard]"
        quest = Quest(
            name="Dangerous Mission",
            description="A dangerous mission.",
            objective_type=ObjectiveType.KILL,
            target="Troll",
            status=QuestStatus.AVAILABLE,
            difficulty=QuestDifficulty.HARD,
            recommended_level=8,
        )
        npc = NPC(
            name="Quest Giver",
            description="A quest giving NPC.",
            dialogue="I have work for you.",
            is_quest_giver=True,
            offered_quests=[quest],
        )
        # Set up NPC in current location
        location = game_state.get_current_location()
        location.npcs.append(npc)
        game_state.current_npc = npc

        # Simulate talking to the NPC (which would show available quests)
        continue_game, message = handle_exploration_command(game_state, "talk", ["quest", "giver"])

        assert continue_game is True
        # Should show difficulty in the quest list
        assert "Dangerous Mission [Hard]" in message

    def test_npc_available_quests_shows_all_difficulty_levels(self, game_state):
        """Test that NPC quest list shows correct difficulty for all levels."""
        # Create quests with different difficulties
        quests = [
            Quest(
                name="Trivial Quest",
                description="Easy peasy.",
                objective_type=ObjectiveType.COLLECT,
                target="Flower",
                status=QuestStatus.AVAILABLE,
                difficulty=QuestDifficulty.TRIVIAL,
            ),
            Quest(
                name="Deadly Quest",
                description="Certain death.",
                objective_type=ObjectiveType.KILL,
                target="Ancient Dragon",
                status=QuestStatus.AVAILABLE,
                difficulty=QuestDifficulty.DEADLY,
            ),
        ]
        npc = NPC(
            name="Quest Master",
            description="A master of quests.",
            dialogue="Choose your destiny.",
            is_quest_giver=True,
            offered_quests=quests,
        )
        location = game_state.get_current_location()
        location.npcs.append(npc)
        game_state.current_npc = npc

        continue_game, message = handle_exploration_command(game_state, "talk", ["quest", "master"])

        assert continue_game is True
        assert "Trivial Quest [Trivial]" in message
        assert "Deadly Quest [Deadly]" in message


# ============================================================================
# TestQuestDifficultyClone - Accept command clones difficulty
# ============================================================================


class TestQuestDifficultyClone:
    """Tests for difficulty cloning when accepting quests - Spec: clone on accept."""

    def test_accept_copies_difficulty(self, game_state):
        """Test that accept command copies difficulty field from NPC quest."""
        # Spec: Clone difficulty from matching_quest
        quest = Quest(
            name="Hard Challenge",
            description="A challenging quest.",
            objective_type=ObjectiveType.KILL,
            target="Ogre",
            status=QuestStatus.AVAILABLE,
            difficulty=QuestDifficulty.HARD,
        )
        npc = NPC(
            name="Guild Master",
            description="Head of the adventurers guild.",
            dialogue="Welcome to the guild.",
            is_quest_giver=True,
            offered_quests=[quest],
        )
        location = game_state.get_current_location()
        location.npcs.append(npc)
        game_state.current_npc = npc

        # Accept the quest
        continue_game, message = handle_exploration_command(game_state, "accept", ["hard", "challenge"])

        assert continue_game is True
        assert "Quest accepted" in message

        # Verify the cloned quest has correct difficulty
        accepted = next(
            (q for q in game_state.current_character.quests if "Hard Challenge" in q.name),
            None,
        )
        assert accepted is not None
        assert accepted.difficulty == QuestDifficulty.HARD

    def test_accept_copies_recommended_level(self, game_state):
        """Test that accept command copies recommended_level from NPC quest."""
        # Spec: Clone recommended_level from matching_quest
        quest = Quest(
            name="Level Check",
            description="A quest for high level players.",
            objective_type=ObjectiveType.KILL,
            target="Demon",
            status=QuestStatus.AVAILABLE,
            difficulty=QuestDifficulty.DEADLY,
            recommended_level=15,
        )
        npc = NPC(
            name="Elder",
            description="A wise elder.",
            dialogue="I have seen much.",
            is_quest_giver=True,
            offered_quests=[quest],
        )
        location = game_state.get_current_location()
        location.npcs.append(npc)
        game_state.current_npc = npc

        # Accept the quest
        continue_game, message = handle_exploration_command(game_state, "accept", ["level", "check"])

        assert continue_game is True

        # Verify the cloned quest has correct recommended level
        accepted = next(
            (q for q in game_state.current_character.quests if "Level Check" in q.name),
            None,
        )
        assert accepted is not None
        assert accepted.recommended_level == 15


# ============================================================================
# TestQuestDifficultyAIParsing - AI response parsing
# ============================================================================


class TestQuestDifficultyAIParsing:
    """Tests for AI quest difficulty parsing - Spec: AI integration."""

    def test_parse_quest_includes_difficulty(self):
        """Test that _parse_quest_response extracts difficulty field."""
        # Spec: Parse difficulty from AI response
        from cli_rpg.ai_service import AIService, AIGenerationError

        service = AIService.__new__(AIService)  # Create without __init__
        service.client = None  # We'll mock the parsing method

        # Create mock data as if returned from AI
        mock_data = {
            "name": "Test Quest",
            "description": "A test quest.",
            "objective_type": "kill",
            "target": "Goblin",
            "target_count": 3,
            "gold_reward": 50,
            "xp_reward": 30,
            "difficulty": "hard",
            "recommended_level": 8,
        }

        # Call the parser (normally this parses JSON, but we test the dict handling)
        # We need to test the actual parsing method
        result = service._parse_quest_response(str(mock_data).replace("'", '"'), "Test NPC")

        assert result["difficulty"] == "hard"

    def test_parse_quest_includes_recommended_level(self):
        """Test that _parse_quest_response extracts recommended_level field."""
        # Spec: Parse recommended_level from AI response
        from cli_rpg.ai_service import AIService

        service = AIService.__new__(AIService)
        service.client = None

        mock_data = {
            "name": "Level Quest",
            "description": "A level quest.",
            "objective_type": "kill",
            "target": "Goblin",
            "target_count": 1,
            "gold_reward": 100,
            "xp_reward": 50,
            "difficulty": "deadly",
            "recommended_level": 12,
        }

        result = service._parse_quest_response(str(mock_data).replace("'", '"'), "Test NPC")

        assert result["recommended_level"] == 12

    def test_parse_quest_defaults_difficulty_when_missing(self):
        """Test that _parse_quest_response defaults difficulty when not in response."""
        # Spec: Default to "normal" and 1 when missing
        from cli_rpg.ai_service import AIService

        service = AIService.__new__(AIService)
        service.client = None

        # Data without difficulty fields (simulating older AI response)
        # Using kill objective which validates against VALID_ENEMY_TYPES
        mock_data = {
            "name": "Old Quest",
            "description": "An old format quest.",
            "objective_type": "kill",
            "target": "Wolf",
            "target_count": 1,
            "gold_reward": 30,
            "xp_reward": 20,
        }

        result = service._parse_quest_response(str(mock_data).replace("'", '"'), "Test NPC")

        assert result["difficulty"] == "normal"
        assert result["recommended_level"] == 1
