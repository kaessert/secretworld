"""Tests for default faction assignments by NPC role.

These tests verify Step 3 of the NPC generation enhancement plan:
- Merchants without explicit faction get "Merchant Guild"
- Guards without explicit faction get "Town Watch"
- Quest givers without explicit faction get "Adventurer's Guild"
- Explicit AI-provided factions are not overridden
"""

import pytest

from cli_rpg.ai_world import _create_npcs_from_data


class TestFactionRoleDefaults:
    """Test default faction assignment based on NPC role."""

    def test_merchant_defaults_to_merchant_guild(self):
        """Verify merchants without faction get Merchant Guild."""
        npcs_data = [
            {
                "name": "Trader Bob",
                "description": "A jovial trader with many wares.",
                "dialogue": "Welcome to my shop!",
                "role": "merchant"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 1
        assert npcs[0].faction == "Merchant Guild"

    def test_guard_defaults_to_town_watch(self):
        """Verify guards without faction get Town Watch."""
        npcs_data = [
            {
                "name": "Guard Helm",
                "description": "A stern-looking guard keeping watch.",
                "dialogue": "Move along, citizen.",
                "role": "guard"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 1
        assert npcs[0].faction == "Town Watch"

    def test_quest_giver_defaults_to_adventurers_guild(self):
        """Verify quest_givers without faction get Adventurer's Guild."""
        npcs_data = [
            {
                "name": "Elder Sage",
                "description": "A wise old figure who knows many secrets.",
                "dialogue": "Ah, a brave soul. I have a task for you.",
                "role": "quest_giver"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 1
        assert npcs[0].faction == "Adventurer's Guild"

    def test_explicit_faction_not_overridden(self):
        """Verify AI-provided faction is preserved, not replaced with default."""
        npcs_data = [
            {
                "name": "Dark Trader",
                "description": "A shady merchant with unusual goods.",
                "dialogue": "Looking for something... special?",
                "role": "merchant",
                "faction": "Thieves Guild"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 1
        assert npcs[0].faction == "Thieves Guild"

    def test_villager_no_default_faction(self):
        """Verify villagers without faction remain faction-less."""
        npcs_data = [
            {
                "name": "Simple Farmer",
                "description": "A hardworking farmer tending the fields.",
                "dialogue": "Good day to you!",
                "role": "villager"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 1
        assert npcs[0].faction is None

    def test_traveler_no_default_faction(self):
        """Verify travelers without faction remain faction-less."""
        npcs_data = [
            {
                "name": "Wandering Bard",
                "description": "A traveling musician.",
                "dialogue": "Care for a song?",
                "role": "traveler"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 1
        assert npcs[0].faction is None

    def test_innkeeper_no_default_faction(self):
        """Verify innkeepers without faction remain faction-less."""
        npcs_data = [
            {
                "name": "Friendly Innkeep",
                "description": "The proprietor of the local tavern.",
                "dialogue": "Room and board, good prices!",
                "role": "innkeeper"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 1
        assert npcs[0].faction is None

    def test_mixed_npcs_with_defaults(self):
        """Verify multiple NPCs get correct faction defaults."""
        npcs_data = [
            {
                "name": "Market Vendor",
                "description": "Sells fresh produce.",
                "dialogue": "Best prices in town!",
                "role": "merchant"
            },
            {
                "name": "Gate Guard",
                "description": "Watches the gate.",
                "dialogue": "State your business.",
                "role": "guard"
            },
            {
                "name": "Old Sage",
                "description": "Knows many quests.",
                "dialogue": "I need your help.",
                "role": "quest_giver"
            },
            {
                "name": "Local Farmer",
                "description": "Works the fields.",
                "dialogue": "Fine weather today.",
                "role": "villager"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 4
        assert npcs[0].faction == "Merchant Guild"
        assert npcs[1].faction == "Town Watch"
        assert npcs[2].faction == "Adventurer's Guild"
        assert npcs[3].faction is None

    def test_explicit_faction_with_various_roles(self):
        """Verify explicit factions work with all roles that get defaults."""
        npcs_data = [
            {
                "name": "Guild Merchant",
                "description": "Official guild trader.",
                "dialogue": "Guild rates apply.",
                "role": "merchant",
                "faction": "Mage Guild"
            },
            {
                "name": "Royal Guard",
                "description": "Palace protector.",
                "dialogue": "The king's will.",
                "role": "guard",
                "faction": "Royal Court"
            },
            {
                "name": "Temple Priest",
                "description": "Holy quest giver.",
                "dialogue": "The gods call.",
                "role": "quest_giver",
                "faction": "Temple of Light"
            }
        ]
        npcs = _create_npcs_from_data(npcs_data)

        assert len(npcs) == 3
        assert npcs[0].faction == "Mage Guild"
        assert npcs[1].faction == "Royal Court"
        assert npcs[2].faction == "Temple of Light"
