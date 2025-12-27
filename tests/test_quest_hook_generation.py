"""Tests for quest hook generation for quest_giver NPCs.

These tests verify Step 2 of the NPC generation enhancement plan:
- Quest giver NPCs receive populated offered_quests when AI service available
- Quest generation uses region landmarks for EXPLORE targets
- Non-quest-giver NPCs don't receive quest generation calls
- Quest generation fails gracefully when AI unavailable
"""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.ai_world import _create_npcs_from_data, _generate_quest_for_npc
from cli_rpg.models.quest import Quest, ObjectiveType
from cli_rpg.models.region_context import RegionContext
from cli_rpg.models.world_context import WorldContext


class TestQuestGenerationFunction:
    """Test the _generate_quest_for_npc helper function."""

    def test_generate_quest_returns_quest_object(self):
        """Verify _generate_quest_for_npc returns a Quest when AI succeeds."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.return_value = {
            "name": "Lost Artifact",
            "description": "Find the lost artifact in the ruins.",
            "objective_type": "explore",
            "target": "ancient temple",
            "target_count": 1,
            "gold_reward": 100,
            "xp_reward": 50,
        }

        quest = _generate_quest_for_npc(
            ai_service=mock_ai,
            npc_name="Elder Sage",
            location_name="Town Square",
            region_context=None,
            world_context=None,
            valid_locations=set(),
            valid_npcs=set(),
        )

        assert quest is not None
        assert quest.name == "Lost Artifact"
        assert quest.objective_type == ObjectiveType.EXPLORE
        assert quest.target == "ancient temple"
        assert quest.gold_reward == 100
        assert quest.xp_reward == 50
        assert quest.quest_giver == "Elder Sage"

    def test_generate_quest_returns_none_without_ai_service(self):
        """Verify _generate_quest_for_npc returns None when AI is None."""
        quest = _generate_quest_for_npc(
            ai_service=None,
            npc_name="Elder Sage",
            location_name="Town Square",
            region_context=None,
            world_context=None,
            valid_locations=set(),
            valid_npcs=set(),
        )

        assert quest is None

    def test_generate_quest_returns_none_on_exception(self):
        """Verify _generate_quest_for_npc returns None when AI raises exception."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.side_effect = Exception("AI error")

        quest = _generate_quest_for_npc(
            ai_service=mock_ai,
            npc_name="Elder Sage",
            location_name="Town Square",
            region_context=None,
            world_context=None,
            valid_locations=set(),
            valid_npcs=set(),
        )

        assert quest is None

    def test_generate_quest_includes_region_landmarks(self):
        """Verify region landmarks are added to valid_locations for EXPLORE quests."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.return_value = {
            "name": "Temple Quest",
            "description": "Explore the temple.",
            "objective_type": "explore",
            "target": "ancient temple",
            "target_count": 1,
            "gold_reward": 100,
            "xp_reward": 50,
        }

        region_context = RegionContext(
            name="Test Region",
            theme="ruins",
            danger_level="moderate",
            landmarks=["Ancient Temple", "Forgotten Shrine"],
            coordinates=(0, 0)
        )

        quest = _generate_quest_for_npc(
            ai_service=mock_ai,
            npc_name="Elder Sage",
            location_name="Town Square",
            region_context=region_context,
            world_context=None,
            valid_locations={"town square"},
            valid_npcs=set(),
        )

        # Check that generate_quest was called with landmarks in valid_locations
        call_kwargs = mock_ai.generate_quest.call_args[1]
        assert "ancient temple" in call_kwargs["valid_locations"]
        assert "forgotten shrine" in call_kwargs["valid_locations"]
        assert "town square" in call_kwargs["valid_locations"]

    def test_generate_quest_uses_world_context_theme(self):
        """Verify world_context theme is passed to AI service."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.return_value = {
            "name": "Dark Quest",
            "description": "Face the darkness.",
            "objective_type": "kill",
            "target": "shadow",
            "target_count": 3,
            "gold_reward": 150,
            "xp_reward": 75,
        }

        world_context = WorldContext(
            theme="dark fantasy",
            theme_essence="gothic horror",
            naming_style="ominous names"
        )

        quest = _generate_quest_for_npc(
            ai_service=mock_ai,
            npc_name="Dark Priest",
            location_name="Haunted Church",
            region_context=None,
            world_context=world_context,
            valid_locations=set(),
            valid_npcs=set(),
        )

        # Check that generate_quest was called with the world theme
        call_kwargs = mock_ai.generate_quest.call_args[1]
        assert call_kwargs["theme"] == "dark fantasy"


class TestQuestGiverNPCIntegration:
    """Test quest generation integration in _create_npcs_from_data."""

    def test_quest_giver_receives_quest_with_ai_service(self):
        """Verify quest_giver NPCs have offered_quests populated when AI provided."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.return_value = {
            "name": "Slay the Beast",
            "description": "Defeat the monster terrorizing the village.",
            "objective_type": "kill",
            "target": "beast",
            "target_count": 1,
            "gold_reward": 200,
            "xp_reward": 100,
        }

        npcs_data = [
            {
                "name": "Village Elder",
                "description": "A wise old leader seeking help.",
                "dialogue": "Please, brave adventurer, help us!",
                "role": "quest_giver"
            }
        ]

        npcs = _create_npcs_from_data(
            npcs_data,
            ai_service=mock_ai,
            location_name="Village Center",
        )

        assert len(npcs) == 1
        assert npcs[0].is_quest_giver is True
        assert len(npcs[0].offered_quests) == 1
        assert npcs[0].offered_quests[0].name == "Slay the Beast"

    def test_non_quest_giver_does_not_get_quest(self):
        """Verify non-quest_giver NPCs don't trigger quest generation."""
        mock_ai = MagicMock()

        npcs_data = [
            {
                "name": "Trader Bob",
                "description": "A merchant.",
                "dialogue": "Buy something!",
                "role": "merchant"
            }
        ]

        npcs = _create_npcs_from_data(
            npcs_data,
            ai_service=mock_ai,
            location_name="Market Square",
        )

        assert len(npcs) == 1
        assert npcs[0].is_quest_giver is False
        assert len(npcs[0].offered_quests) == 0
        # generate_quest should not have been called for merchant
        mock_ai.generate_quest.assert_not_called()

    def test_quest_giver_without_ai_service_has_empty_quests(self):
        """Verify quest_giver without AI service has empty offered_quests."""
        npcs_data = [
            {
                "name": "Sage",
                "description": "A wise one.",
                "dialogue": "I have tasks.",
                "role": "quest_giver"
            }
        ]

        npcs = _create_npcs_from_data(npcs_data)  # No ai_service

        assert len(npcs) == 1
        assert npcs[0].is_quest_giver is True
        assert len(npcs[0].offered_quests) == 0

    def test_quest_generation_failure_does_not_break_npc_creation(self):
        """Verify NPC is still created even if quest generation fails."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.side_effect = Exception("AI failure")

        npcs_data = [
            {
                "name": "Elder",
                "description": "Old and wise.",
                "dialogue": "Help me.",
                "role": "quest_giver"
            }
        ]

        npcs = _create_npcs_from_data(
            npcs_data,
            ai_service=mock_ai,
            location_name="Temple",
        )

        assert len(npcs) == 1
        assert npcs[0].name == "Elder"
        assert npcs[0].is_quest_giver is True
        assert len(npcs[0].offered_quests) == 0  # Quest failed but NPC still created

    def test_multiple_quest_givers_each_get_quest(self):
        """Verify multiple quest_givers each receive their own quest."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.side_effect = [
            {
                "name": "Quest One",
                "description": "First quest.",
                "objective_type": "kill",
                "target": "goblin",
                "target_count": 5,
                "gold_reward": 50,
                "xp_reward": 25,
            },
            {
                "name": "Quest Two",
                "description": "Second quest.",
                "objective_type": "explore",
                "target": "cave",
                "target_count": 1,
                "gold_reward": 75,
                "xp_reward": 40,
            },
        ]

        npcs_data = [
            {
                "name": "Elder One",
                "description": "First quest giver.",
                "dialogue": "First task.",
                "role": "quest_giver"
            },
            {
                "name": "Elder Two",
                "description": "Second quest giver.",
                "dialogue": "Second task.",
                "role": "quest_giver"
            },
        ]

        npcs = _create_npcs_from_data(
            npcs_data,
            ai_service=mock_ai,
            location_name="Town",
        )

        assert len(npcs) == 2
        assert npcs[0].offered_quests[0].name == "Quest One"
        assert npcs[1].offered_quests[0].name == "Quest Two"
        assert mock_ai.generate_quest.call_count == 2

    def test_context_parameters_passed_to_quest_generation(self):
        """Verify region/world context is passed through to quest generation."""
        mock_ai = MagicMock()
        mock_ai.generate_quest.return_value = {
            "name": "Context Quest",
            "description": "Uses context.",
            "objective_type": "explore",
            "target": "ruins",
            "target_count": 1,
            "gold_reward": 100,
            "xp_reward": 50,
        }

        world_context = WorldContext(
            theme="steampunk",
            theme_essence="gears and steam",
            naming_style="victorian"
        )
        region_context = RegionContext(
            name="Industrial Zone",
            theme="factories",
            danger_level="dangerous",
            landmarks=["Steam Tower", "Coal Mines"],
            coordinates=(5, 5)
        )

        npcs_data = [
            {
                "name": "Foreman",
                "description": "Factory boss with a task.",
                "dialogue": "Need help?",
                "role": "quest_giver"
            }
        ]

        npcs = _create_npcs_from_data(
            npcs_data,
            ai_service=mock_ai,
            location_name="Factory Floor",
            region_context=region_context,
            world_context=world_context,
            valid_locations={"factory floor", "warehouse"},
            valid_npcs={"worker"},
        )

        call_kwargs = mock_ai.generate_quest.call_args[1]
        assert call_kwargs["theme"] == "steampunk"
        assert "steam tower" in call_kwargs["valid_locations"]
        assert "coal mines" in call_kwargs["valid_locations"]
