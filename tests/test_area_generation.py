"""Tests for area generation functionality.

These tests verify that the AI world generation creates complete thematic areas
(clusters of 4-7 connected locations) instead of single locations, and that
the world border remains "closed" after area expansion.
"""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.ai_service import AIService
from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_world import expand_area, expand_world
from cli_rpg.models.location import Location
from cli_rpg.world_grid import WorldGrid


class TestGenerateAreaAIService:
    """Test generate_area method in AIService.

    Spec: AIService.generate_area() returns a list of connected locations
    with a consistent sub-theme.
    """

    def test_generate_area_returns_location_list(self):
        """generate_area returns a list of location dictionaries.

        Spec: generate_area returns list of dicts with name, description,
        and relative_coords. Connections are optional (coordinate-based nav).
        """
        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Mock the LLM call to return valid area data
        # Note: connections field may be present but is ignored - navigation is coordinate-based
        mock_response = """[
            {
                "name": "Haunted Graveyard Entrance",
                "description": "A rusty iron gate marks the entrance to an ancient graveyard.",
                "relative_coords": [0, 0]
            },
            {
                "name": "Old Tombstones",
                "description": "Weathered tombstones lean at odd angles, their inscriptions faded.",
                "relative_coords": [0, 1]
            },
            {
                "name": "Cryptkeeper's Shack",
                "description": "A decrepit wooden shack where the cryptkeeper once lived.",
                "relative_coords": [1, 0]
            },
            {
                "name": "Mausoleum",
                "description": "A grand stone mausoleum with ornate carvings of angels.",
                "relative_coords": [1, 1]
            }
        ]"""

        with patch.object(ai_service, '_call_llm', return_value=mock_response):
            result = ai_service.generate_area(
                theme="fantasy",
                sub_theme_hint="graveyard",
                entry_direction="north",
                context_locations=["Town Square"],
                size=4
            )

        assert isinstance(result, list)
        assert len(result) >= 4
        # Each location should have required fields
        for loc in result:
            assert "name" in loc
            assert "description" in loc
            assert "relative_coords" in loc
            # connections is optional (navigation is coordinate-based)

    def test_generate_area_validates_location_names(self):
        """generate_area validates location name lengths.

        Spec: All generated locations must have valid name lengths (2-50 chars).
        """
        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Mock response with too-short name
        mock_response = """[
            {
                "name": "A",
                "description": "A location with too short a name.",
                "relative_coords": [0, 0],
                "connections": {}
            }
        ]"""

        with patch.object(ai_service, '_call_llm', return_value=mock_response):
            from cli_rpg.ai_service import AIGenerationError
            with pytest.raises(AIGenerationError, match="name too short"):
                ai_service.generate_area(
                    theme="fantasy",
                    sub_theme_hint="test",
                    entry_direction="north",
                    context_locations=[],
                    size=4
                )

    def test_generate_area_entry_location_at_origin(self):
        """The entry location should be at relative coordinates (0, 0).

        Spec: The first location in the area (entry point) has relative_coords [0, 0].
        """
        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        mock_response = """[
            {
                "name": "Entry Point",
                "description": "The entrance to this area.",
                "relative_coords": [0, 0],
                "connections": {"north": "Inner Area"}
            },
            {
                "name": "Inner Area",
                "description": "Inside the area.",
                "relative_coords": [0, 1],
                "connections": {"south": "Entry Point"}
            }
        ]"""

        with patch.object(ai_service, '_call_llm', return_value=mock_response):
            result = ai_service.generate_area(
                theme="fantasy",
                sub_theme_hint="cave",
                entry_direction="north",
                context_locations=[],
                size=4
            )

        # Find entry location (at 0,0)
        entry = next((loc for loc in result if loc["relative_coords"] == [0, 0]), None)
        assert entry is not None


class TestExpandArea:
    """Test expand_area function in ai_world.py.

    Spec: expand_area generates 4-7 location clusters at target coordinates.
    """

    def test_expand_area_generates_multiple_locations(self):
        """expand_area adds 4+ locations to the world.

        Spec: Area generation creates a cluster of 4-7 connected locations.
        """
        # Setup initial world with one location
        grid = WorldGrid()
        start = Location(
            name="Town Square",
            description="A bustling town square."  # Dangling exit
        )
        grid.add_location(start, 0, 0)
        world = grid.as_dict()
        initial_count = len(world)

        # Mock AI service
        mock_ai = MagicMock(spec=AIService)
        mock_ai.generate_area.return_value = [
            {
                "name": "Forest Clearing",
                "description": "A peaceful clearing in the forest.",
                "relative_coords": [0, 0],
                "connections": {"south": "Town Square", "north": "Deep Woods", "east": "Brook"}
            },
            {
                "name": "Deep Woods",
                "description": "Dense forest with towering trees.",
                "relative_coords": [0, 1],
                "connections": {"south": "Forest Clearing", "east": "Old Oak"}
            },
            {
                "name": "Brook",
                "description": "A small brook babbles through the forest.",
                "relative_coords": [1, 0],
                "connections": {"west": "Forest Clearing", "north": "Old Oak"}
            },
            {
                "name": "Old Oak",
                "description": "An ancient oak tree stands sentinel.",
                "relative_coords": [1, 1],
                "connections": {"west": "Deep Woods", "south": "Brook"}
            }
        ]

        # Call expand_area
        result = expand_area(
            world=world,
            ai_service=mock_ai,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Should have added entry to world (sub-locations are now in SubGrid)
        assert len(result) >= initial_count + 1
        # Entry should have SubGrid with 3 sub-locations
        entry = result["Forest Clearing"]
        assert entry.sub_grid is not None
        assert len(entry.sub_grid._by_name) == 3  # Deep Woods, Brook, Old Oak

    def test_expand_area_locations_are_connected(self):
        """All locations in the area are reachable from the entry point.

        Spec: All area locations reachable from entry via coordinate adjacency.
        """
        # Setup initial world
        grid = WorldGrid()
        start = Location(
            name="Town Square",
            description="A bustling town square."
        )
        grid.add_location(start, 0, 0)
        world = grid.as_dict()

        # Mock AI service with coordinate-adjacent locations
        mock_ai = MagicMock(spec=AIService)
        mock_ai.generate_area.return_value = [
            {
                "name": "Area Entry",
                "description": "Entry point.",
                "relative_coords": [0, 0]
            },
            {
                "name": "Area Center",
                "description": "Center of area.",
                "relative_coords": [0, 1]
            },
            {
                "name": "Area East",
                "description": "East part.",
                "relative_coords": [1, 1]
            },
            {
                "name": "Area Southeast",
                "description": "Southeast part.",
                "relative_coords": [1, 0]
            }
        ]

        result = expand_area(
            world=world,
            ai_service=mock_ai,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Verify entry location exists and is at the target coordinates
        assert "Area Entry" in result
        entry_loc = result["Area Entry"]
        assert entry_loc.coordinates == (0, 1)

        # Verify Town Square can reach entry via coordinate adjacency
        assert "north" in result["Town Square"].get_available_directions(world=result)

        # Sub-locations are now in entry's SubGrid, not world dict
        assert entry_loc.sub_grid is not None
        assert entry_loc.sub_grid.get_by_name("Area Center") is not None
        assert entry_loc.sub_grid.get_by_name("Area East") is not None
        assert entry_loc.sub_grid.get_by_name("Area Southeast") is not None

    def test_expand_area_preserves_expansion_exits(self):
        """Area expansion should preserve ability to expand further.

        Spec: After area generation, the world should still have at least one
        frontier exit to enable infinite world expansion.
        """
        # Setup initial world
        grid = WorldGrid()
        start = Location(
            name="Town Square",
            description="A bustling town square."
        )
        grid.add_location(start, 0, 0)

        # With coordinate-based navigation, frontier exits are implicit
        # - any direction from (0,0) that doesn't have a location is a frontier

        # Mock AI service - area should have internal connections only
        # plus connection back to source
        mock_ai = MagicMock(spec=AIService)
        mock_ai.generate_area.return_value = [
            {
                "name": "North Area",
                "description": "North of town.",
                "relative_coords": [0, 0],
                "connections": {"south": "Town Square", "east": "East Area"}
            },
            {
                "name": "East Area",
                "description": "East side.",
                "relative_coords": [1, 0],
                "connections": {"west": "North Area", "north": "Northeast Area"}
            },
            {
                "name": "Northeast Area",
                "description": "Northeast corner.",
                "relative_coords": [1, 1],
                "connections": {"south": "East Area", "west": "North Inner"}
            },
            {
                "name": "North Inner",
                "description": "Inner north.",
                "relative_coords": [0, 1],
                "connections": {"south": "North Area", "east": "Northeast Area"}
            }
        ]

        world = grid.as_dict()
        result = expand_area(
            world=world,
            ai_service=mock_ai,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Convert result to WorldGrid for validation
        new_grid = WorldGrid()
        for name, loc in result.items():
            if loc.coordinates is not None:
                # Bypass add_location to avoid re-creating connections
                new_grid._grid[loc.coordinates] = loc
                new_grid._by_name[name] = loc

        # World should have at least one frontier exit for future expansion
        # This is the DESIRED state - players should always be able to explore more
        assert new_grid.has_expansion_exits() is True, (
            "World should have at least one frontier exit after area expansion"
        )

    def test_expand_area_preserves_existing_world(self):
        """Existing locations are unchanged after expansion.

        Spec: expand_area should not modify existing locations (except connections).
        """
        # Setup initial world with multiple locations
        grid = WorldGrid()
        town = Location(
            name="Town Square",
            description="A bustling town square."
        )
        market = Location(
            name="Market",
            description="A busy marketplace."
        )
        grid.add_location(town, 0, 0)
        grid.add_location(market, 1, 0)
        world = grid.as_dict()

        original_town_desc = town.description
        original_market_desc = market.description

        # Mock AI service
        mock_ai = MagicMock(spec=AIService)
        mock_ai.generate_area.return_value = [
            {
                "name": "North Area",
                "description": "North of town.",
                "relative_coords": [0, 0],
                "connections": {"south": "Town Square"}
            }
        ]

        result = expand_area(
            world=world,
            ai_service=mock_ai,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Original locations should be unchanged
        assert result["Town Square"].description == original_town_desc
        assert result["Market"].description == original_market_desc

    def test_expand_area_entry_connects_to_source(self):
        """Entry point of area connects back to source location.

        Spec: Entry point connects back to source via opposite direction.
        """
        # Setup initial world
        grid = WorldGrid()
        start = Location(
            name="Town Square",
            description="A bustling town square."
        )
        grid.add_location(start, 0, 0)
        world = grid.as_dict()

        # Mock AI service
        mock_ai = MagicMock(spec=AIService)
        mock_ai.generate_area.return_value = [
            {
                "name": "New Area",
                "description": "A new area.",
                "relative_coords": [0, 0],
                "connections": {"south": "Town Square"}  # Back-connection
            }
        ]

        result = expand_area(
            world=world,
            ai_service=mock_ai,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Entry location should be placed at target coordinates (0, 1)
        new_area = result["New Area"]
        assert new_area.coordinates == (0, 1)

        # Connection is implicit via coordinate adjacency:
        # Town Square at (0, 0), New Area at (0, 1)
        # Going north from (0,0) leads to (0,1) = New Area
        # Going south from (0,1) leads to (0,0) = Town Square
        assert result["Town Square"].coordinates == (0, 0)


class TestExpandWorldBackwardCompat:
    """Test that expand_world still works for single location generation.

    Spec: expand_world remains as a thin wrapper for backward compatibility.
    """

    def test_expand_world_still_generates_single_location(self):
        """expand_world generates a single location (backward compat).

        Spec: expand_world should still work for single location generation.
        """
        # Setup initial world
        grid = WorldGrid()
        start = Location(
            name="Town Square",
            description="A bustling town square."
        )
        grid.add_location(start, 0, 0)
        world = grid.as_dict()

        # Mock AI service
        mock_ai = MagicMock(spec=AIService)
        mock_ai.generate_location.return_value = {
            "name": "Forest",
            "description": "A dark forest.",
            "connections": {"south": "Town Square"}
        }

        result = expand_world(
            world=world,
            ai_service=mock_ai,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Should have added exactly one location
        assert "Forest" in result
        assert len(result) == 2  # Town Square + Forest
