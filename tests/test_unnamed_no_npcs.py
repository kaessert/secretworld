"""Tests for unnamed locations not spawning NPCs.

Spec: Unnamed locations (is_named=False) should not spawn NPCs.
NPCs belong only inside named sub-locations (villages, dungeons).
"You don't find shopkeepers standing in random forests."
"""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC


class TestUnnamedLocationNoNPCs:
    """Tests that unnamed locations have no NPCs."""

    def test_unnamed_location_from_template_has_no_npcs(self):
        """Unnamed locations from templates should have empty npcs list.

        Spec: Unnamed locations created in game_state.py at line 551-558 have no NPCs.
        """
        # Create an unnamed location (mimics game_state._generate_unnamed_location logic)
        location = Location(
            name="Dense Forest (0,1)",
            description="Tall trees block out most of the sunlight.",
            coordinates=(0, 1),
            category="wilderness",
            terrain="forest",
            is_named=False,
        )

        # Verify no NPCs
        assert location.npcs == [], "Unnamed locations should have no NPCs"
        assert location.is_named is False

    def test_named_location_can_have_npcs(self):
        """Named locations can have NPCs added to them.

        Spec: Named locations continue to generate NPCs normally.
        """
        # Create a named location
        location = Location(
            name="Thornwood Village",
            description="A quaint village nestled in the forest.",
            coordinates=(5, 5),
            category="village",
            is_named=True,
        )

        # Add an NPC
        merchant = NPC(
            name="Elara the Merchant",
            description="A friendly trader with wares from distant lands.",
            dialogue="Welcome, traveler! Care to see my wares?",
            is_merchant=True
        )
        location.npcs.append(merchant)

        # Verify NPCs can be added
        assert len(location.npcs) == 1
        assert location.npcs[0].name == "Elara the Merchant"
        assert location.is_named is True


class TestExpandWorldNPCGeneration:
    """Tests for expand_world NPC generation based on is_named."""

    def test_expand_world_unnamed_skips_npcs(self):
        """expand_world should skip NPC generation when location is unnamed.

        Spec: AI-generated overworld locations with is_named=False skip NPC generation.
        """
        from cli_rpg.ai_world import expand_world

        # Create mock AI service
        mock_ai = MagicMock()

        # AI returns a location with is_named=False (unnamed location)
        mock_ai.generate_location_with_context.return_value = {
            "name": "Windswept Hills (3,4)",
            "description": "Rolling hills stretch to the horizon.",
            "category": "wilderness",
            "is_named": False,
        }

        # This should NOT be called for unnamed locations
        mock_ai.generate_npcs_for_location.return_value = [
            {"name": "Should Not Appear", "description": "Ghost NPC", "role": "villager"}
        ]

        # Create minimal world
        world = {
            "Starting Town": Location(
                name="Starting Town",
                description="A small town.",
                coordinates=(0, 0)
            )
        }

        # Mock world context and region context
        mock_world_ctx = MagicMock()
        mock_region_ctx = MagicMock()

        # Expand world
        expand_world(
            world=world,
            ai_service=mock_ai,
            from_location="Starting Town",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
            world_context=mock_world_ctx,
            region_context=mock_region_ctx,
        )

        # Verify generate_npcs_for_location was NOT called
        mock_ai.generate_npcs_for_location.assert_not_called()

        # Verify the new location has no NPCs
        new_loc = world.get("Windswept Hills (3,4)")
        assert new_loc is not None
        assert new_loc.npcs == [], "Unnamed location should have no NPCs"

    def test_expand_world_named_generates_npcs(self):
        """expand_world should generate NPCs when location is named.

        Spec: Named locations continue to generate NPCs normally.
        """
        from cli_rpg.ai_world import expand_world

        # Create mock AI service
        mock_ai = MagicMock()

        # AI returns a named location (is_named=True or missing, defaults to True)
        mock_ai.generate_location_with_context.return_value = {
            "name": "Dragon's Rest Inn",
            "description": "A cozy tavern popular with adventurers.",
            "category": "town",
            "is_named": True,
        }

        # NPCs should be generated for named locations
        mock_ai.generate_npcs_for_location.return_value = [
            {"name": "Bartender Bob", "description": "A jolly innkeeper", "role": "merchant"}
        ]

        # Create minimal world
        world = {
            "Starting Town": Location(
                name="Starting Town",
                description="A small town.",
                coordinates=(0, 0)
            )
        }

        # Mock world context and region context
        mock_world_ctx = MagicMock()
        mock_region_ctx = MagicMock()

        # Expand world
        expand_world(
            world=world,
            ai_service=mock_ai,
            from_location="Starting Town",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
            world_context=mock_world_ctx,
            region_context=mock_region_ctx,
        )

        # Verify generate_npcs_for_location WAS called
        mock_ai.generate_npcs_for_location.assert_called_once()

        # Verify the new location has NPCs
        new_loc = world.get("Dragon's Rest Inn")
        assert new_loc is not None
        assert len(new_loc.npcs) == 1
        assert new_loc.npcs[0].name == "Bartender Bob"

    def test_expand_world_defaults_to_named_when_not_specified(self):
        """expand_world should treat locations as named when is_named not in response.

        Spec: Default True for backward compatibility.
        """
        from cli_rpg.ai_world import expand_world

        # Create mock AI service
        mock_ai = MagicMock()

        # AI returns location WITHOUT is_named field (backward compatibility)
        mock_ai.generate_location_with_context.return_value = {
            "name": "Mysterious Grove",
            "description": "Ancient trees whisper secrets.",
            "category": "forest",
            # Note: is_named is NOT specified
        }

        mock_ai.generate_npcs_for_location.return_value = []

        world = {
            "Starting Town": Location(
                name="Starting Town",
                description="A small town.",
                coordinates=(0, 0)
            )
        }

        mock_world_ctx = MagicMock()
        mock_region_ctx = MagicMock()

        expand_world(
            world=world,
            ai_service=mock_ai,
            from_location="Starting Town",
            direction="east",
            theme="fantasy",
            target_coords=(1, 0),
            world_context=mock_world_ctx,
            region_context=mock_region_ctx,
        )

        # Should still try to generate NPCs (backward compatible default)
        mock_ai.generate_npcs_for_location.assert_called_once()


class TestExpandAreaNPCGeneration:
    """Tests for expand_area NPC generation based on is_named."""

    def test_expand_area_unnamed_skips_npcs(self):
        """expand_area should skip NPC population for unnamed locations.

        Spec: Fallback locations with is_named=False have no NPCs.

        Note: expand_area places sub-locations in the entry's SubGrid, not world dict.
        """
        from cli_rpg.ai_world import expand_area

        # Create mock AI service
        mock_ai = MagicMock()

        # AI returns area with mix of named and unnamed locations
        # Entry location (0, 0) goes to world, sub-location (1, 0) goes to SubGrid
        mock_ai.generate_area_with_context.return_value = [
            {
                "name": "Village Square",
                "description": "The heart of the village.",
                "category": "village",
                "relative_coords": (0, 0),
                "is_named": True,
                "npcs": [
                    {"name": "Village Elder", "description": "Wise leader", "role": "quest_giver"}
                ]
            },
            {
                "name": "Forest Path",
                "description": "A winding path through trees.",
                "category": "wilderness",
                "relative_coords": (1, 0),
                "is_named": False,
                "npcs": [
                    # AI might still return NPCs for unnamed - these should be ignored
                    {"name": "Ghost NPC", "description": "Should not appear", "role": "villager"}
                ]
            }
        ]

        world = {
            "Starting Town": Location(
                name="Starting Town",
                description="A small town.",
                coordinates=(0, 0)
            )
        }

        mock_world_ctx = MagicMock()
        mock_region_ctx = MagicMock()

        expand_area(
            world=world,
            ai_service=mock_ai,
            from_location="Starting Town",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
            world_context=mock_world_ctx,
            region_context=mock_region_ctx,
        )

        # Entry location (Village Square) should be in world and have NPC
        village = world.get("Village Square")
        assert village is not None
        assert len(village.npcs) == 1
        assert village.npcs[0].name == "Village Elder"

        # Sub-location (Forest Path) is in entry's SubGrid, not world dict
        assert village.sub_grid is not None, "Entry location should have SubGrid for sub-locations"

        # Find the unnamed location in the SubGrid
        forest = village.sub_grid.get_by_name("Forest Path")
        assert forest is not None, "Unnamed location should be in SubGrid"
        assert forest.npcs == [], "Unnamed area location should have no NPCs"

    def test_expand_area_defaults_named_for_npcs(self):
        """expand_area should populate NPCs when is_named not specified (default True).

        Spec: Default True for backward compatibility.
        """
        from cli_rpg.ai_world import expand_area

        mock_ai = MagicMock()

        # AI returns location without is_named field
        mock_ai.generate_area_with_context.return_value = [
            {
                "name": "Old Ruins",
                "description": "Crumbling stone walls.",
                "category": "ruins",
                "relative_coords": (0, 0),
                # Note: is_named not specified
                "npcs": [
                    {"name": "Archaeologist", "description": "Studying ruins", "role": "quest_giver"}
                ]
            }
        ]

        world = {
            "Starting Town": Location(
                name="Starting Town",
                description="A small town.",
                coordinates=(0, 0)
            )
        }

        mock_world_ctx = MagicMock()
        mock_region_ctx = MagicMock()

        expand_area(
            world=world,
            ai_service=mock_ai,
            from_location="Starting Town",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
            world_context=mock_world_ctx,
            region_context=mock_region_ctx,
        )

        # Should have NPCs (backward compatible default)
        ruins = world.get("Old Ruins")
        assert ruins is not None
        assert len(ruins.npcs) == 1
        assert ruins.npcs[0].name == "Archaeologist"
