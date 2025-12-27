"""Tests for region planning system.

Tests for:
- Region coordinate conversion (get_region_coords)
- Boundary proximity detection (check_region_boundary_proximity)
- Pre-generation of adjacent regions
- Region-based context lookup
- Serialization of region contexts with region coordinates
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.game_state import GameState


# ==============================================================================
# Test: get_region_coords - Region coordinate conversion
# ==============================================================================


class TestGetRegionCoords:
    """Test get_region_coords coordinate conversion function."""

    def test_get_region_coords_returns_floor_division(self):
        """Test (0,0) -> (0,0), (15,15) -> (0,0), (16,0) -> (1,0).

        Spec: Region size is 16x16, so:
        - Coordinates 0-15 in x/y map to region 0
        - Coordinates 16-31 in x/y map to region 1
        """
        from cli_rpg.world_tiles import get_region_coords

        # Origin
        assert get_region_coords(0, 0) == (0, 0)

        # Edge of first region
        assert get_region_coords(15, 15) == (0, 0)

        # Just over boundary in x
        assert get_region_coords(16, 0) == (1, 0)

        # Just over boundary in y
        assert get_region_coords(0, 16) == (0, 1)

        # Middle of second region
        assert get_region_coords(20, 25) == (1, 1)

        # Far coordinates
        assert get_region_coords(100, 100) == (6, 6)

    def test_get_region_coords_handles_negative(self):
        """Test (-1,-1) -> (-1,-1), (-16,-16) -> (-1,-1).

        Spec: Negative coordinates should use floor division:
        - -1 // 16 = -1 (not 0)
        - -16 // 16 = -1 (edge of region -1)
        - -17 // 16 = -2 (into region -2)
        """
        from cli_rpg.world_tiles import get_region_coords

        # Just across boundary (negative)
        assert get_region_coords(-1, -1) == (-1, -1)

        # Edge of region -1
        assert get_region_coords(-16, -16) == (-1, -1)

        # Into region -2
        assert get_region_coords(-17, -17) == (-2, -2)

        # Mixed positive/negative
        assert get_region_coords(-5, 5) == (-1, 0)
        assert get_region_coords(5, -5) == (0, -1)


# ==============================================================================
# Test: check_region_boundary_proximity - Boundary detection
# ==============================================================================


class TestCheckRegionBoundaryProximity:
    """Test check_region_boundary_proximity function."""

    def test_check_region_boundary_proximity_center(self):
        """Test (8,8) returns empty list (far from any boundary).

        Spec: Pre-generate when within 2 tiles of unvisited region boundary.
        (8,8) is 8 tiles from all edges of region (0,0), so no adjacent regions.
        """
        from cli_rpg.world_tiles import check_region_boundary_proximity

        result = check_region_boundary_proximity(8, 8)

        assert result == []

    def test_check_region_boundary_proximity_near_edge(self):
        """Test (14,8) returns [(1,0)] (2 tiles from east edge).

        Spec: 14 is within 2 tiles of boundary at x=16 (east edge of region 0).
        Should return adjacent region (1, 0).
        """
        from cli_rpg.world_tiles import check_region_boundary_proximity

        result = check_region_boundary_proximity(14, 8)

        assert (1, 0) in result
        assert len(result) == 1

    def test_check_region_boundary_proximity_corner(self):
        """Test (14,14) returns [(1,0), (0,1), (1,1)] (near 3 regions).

        Spec: (14, 14) is 2 tiles from both east (x=16) and north (y=16) edges.
        Should trigger pre-generation for all 3 adjacent regions.
        """
        from cli_rpg.world_tiles import check_region_boundary_proximity

        result = check_region_boundary_proximity(14, 14)

        # Should include all 3 adjacent regions at corner
        assert (1, 0) in result  # East
        assert (0, 1) in result  # North
        assert (1, 1) in result  # Northeast diagonal

        assert len(result) == 3

    def test_check_region_boundary_proximity_western_edge(self):
        """Test near western/southern edges (approaching negative regions)."""
        from cli_rpg.world_tiles import check_region_boundary_proximity

        # Near west edge (x=1 is 1 tile from x=0, boundary to region -1)
        result = check_region_boundary_proximity(1, 8)
        assert (-1, 0) in result

        # Near south edge
        result = check_region_boundary_proximity(8, 1)
        assert (0, -1) in result

    def test_check_region_boundary_proximity_on_boundary(self):
        """Test standing exactly on region boundary (x=16, y=0)."""
        from cli_rpg.world_tiles import check_region_boundary_proximity

        # At (16, 8) - inside region (1, 0), near boundary with (0, 0)
        result = check_region_boundary_proximity(16, 8)

        # Should detect adjacent region (0, 0) to the west
        assert (0, 0) in result


# ==============================================================================
# Test: Region context caching and lookup
# ==============================================================================


@pytest.fixture
def basic_character():
    """Create a basic character for testing."""
    return Character(
        name="TestHero",
        strength=10,
        dexterity=10,
        intelligence=10,
        character_class=CharacterClass.WARRIOR,
    )


@pytest.fixture
def basic_world():
    """Create a basic world for testing."""
    return {
        "Town Square": Location(
            name="Town Square",
            description="A bustling town center.",
            coordinates=(0, 0),
        ),
    }


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service for testing."""
    service = Mock()
    service.generate_world_context.return_value = WorldContext(
        theme="fantasy",
        theme_essence="A magical realm",
        naming_style="Celtic",
        tone="adventurous",
        generated_at=datetime.now(),
    )

    def create_region_context(**kwargs):
        """Create RegionContext with unique name based on region coords."""
        coords = kwargs.get("coordinates", (0, 0))
        return RegionContext(
            name=f"Region {coords[0]},{coords[1]}",
            theme="wilderness",
            danger_level="moderate",
            landmarks=["A landmark"],
            coordinates=coords,
            generated_at=datetime.now(),
        )

    service.generate_region_context.side_effect = create_region_context
    return service


class TestRegionContextLookup:
    """Test region-based context lookup."""

    def test_region_context_lookup_by_world_coords(
        self, basic_character, basic_world, mock_ai_service
    ):
        """Test different world coords in same region return same context.

        Spec: Region contexts are cached by region coordinates, not world coordinates.
        World coords (0,0) and (15,15) are both in region (0,0).
        """
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        # Get context for (0, 0) - region (0, 0)
        context1 = game_state.get_or_create_region_context((0, 0))

        # Get context for (15, 15) - still region (0, 0)
        context2 = game_state.get_or_create_region_context((15, 15))

        # Should be the same cached context
        assert context1 is context2

        # AI should only be called once
        assert mock_ai_service.generate_region_context.call_count == 1

    def test_different_regions_get_different_contexts(
        self, basic_character, basic_world, mock_ai_service
    ):
        """Test world coords in different regions get different contexts."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        # Get context for (0, 0) - region (0, 0)
        context1 = game_state.get_or_create_region_context((0, 0))

        # Get context for (16, 0) - region (1, 0)
        context2 = game_state.get_or_create_region_context((16, 0))

        # Should be different contexts
        assert context1 is not context2

        # AI should be called twice
        assert mock_ai_service.generate_region_context.call_count == 2


class TestPreGenerateAdjacentRegions:
    """Test pre-generation of adjacent region contexts."""

    def test_pregenerate_adjacent_regions_caches_contexts(
        self, basic_character, basic_world, mock_ai_service
    ):
        """Test that adjacent regions are pre-generated and cached.

        Spec: After pregenerate_adjacent_regions is called, the region_contexts
        dict should be populated with contexts for all detected adjacent regions.
        """
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        # Manually call the pre-generation (via move simulation at boundary)
        # At (14, 8), we're near region (1, 0)
        from cli_rpg.world_tiles import (
            check_region_boundary_proximity,
            get_region_coords,
        )

        adjacent = check_region_boundary_proximity(14, 8)

        # Pre-generate each adjacent region
        for region_coords in adjacent:
            # Convert region coords back to a representative world coord
            # (use center of region for clarity)
            world_x = region_coords[0] * 16 + 8
            world_y = region_coords[1] * 16 + 8
            game_state.get_or_create_region_context((world_x, world_y))

        # Verify region (1, 0) is now cached
        region_key = get_region_coords(24, 8)  # (1, 0)
        assert region_key in game_state.region_contexts


# ==============================================================================
# Test: Serialization of region contexts with region coordinates
# ==============================================================================


class TestRegionContextPersistence:
    """Test region context serialization with region coordinates as keys."""

    def test_region_context_persists_across_save_load(
        self, basic_character, basic_world
    ):
        """Test region contexts serialized with region coords as keys.

        Spec: Region contexts should be keyed by region coordinates (not world coords)
        and persist correctly through save/load cycle.
        """
        # Create game state and add region contexts with region-based keys
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            theme="fantasy",
        )

        # Simulate having cached some region contexts
        # These should be keyed by region coords
        game_state.region_contexts = {
            (0, 0): RegionContext(
                name="Central Plains",
                theme="pastoral farmland",
                danger_level="safe",
                landmarks=["The Old Mill"],
                coordinates=(8, 8),  # Representative world coord for center of region
            ),
            (1, 0): RegionContext(
                name="Eastern Woods",
                theme="dark forest",
                danger_level="moderate",
                landmarks=["Ancient Oak"],
                coordinates=(24, 8),
            ),
            (-1, 0): RegionContext(
                name="Western Hills",
                theme="rolling hills",
                danger_level="low",
                landmarks=["Shepherd's Rest"],
                coordinates=(-8, 8),
            ),
        }

        # Serialize
        data = game_state.to_dict()

        # Verify serialization format uses region coords
        assert "region_contexts" in data
        region_data = data["region_contexts"]

        # Should be a list of [coords, context] pairs
        assert isinstance(region_data, list)
        assert len(region_data) == 3

        # Check that coords are region coords (small numbers like 0, 1, -1)
        for coords, _ in region_data:
            assert abs(coords[0]) <= 1  # Region coords, not world coords
            assert abs(coords[1]) <= 1

        # Deserialize
        restored = GameState.from_dict(data)

        # Verify region contexts restored with correct keys
        assert len(restored.region_contexts) == 3
        assert (0, 0) in restored.region_contexts
        assert (1, 0) in restored.region_contexts
        assert (-1, 0) in restored.region_contexts

        # Verify content
        assert restored.region_contexts[(0, 0)].name == "Central Plains"
        assert restored.region_contexts[(1, 0)].name == "Eastern Woods"
        assert restored.region_contexts[(-1, 0)].name == "Western Hills"


# ==============================================================================
# Test: Move triggers pre-generation near boundary
# ==============================================================================


class TestMoveTriggersPregeneration:
    """Test that movement near region boundaries triggers pre-generation."""

    def test_move_triggers_pregeneration_near_boundary(
        self, basic_character, mock_ai_service
    ):
        """Test moving to (14,8) triggers pregeneration of adjacent regions.

        Spec: After successful move, check for nearby region boundaries
        and pre-generate contexts for detected adjacent regions.
        """
        # Create world with locations for movement test
        world = {
            "Start": Location(
                name="Start",
                description="Starting point.",
                coordinates=(13, 8),
            ),
            "Near Boundary": Location(
                name="Near Boundary",
                description="Near the eastern boundary.",
                coordinates=(14, 8),
            ),
        }

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location="Start",
            ai_service=mock_ai_service,
            theme="fantasy",
            # No chunk_manager - use coordinate-based movement only
        )

        # Initial state - no region contexts cached yet
        initial_region_count = len(game_state.region_contexts)

        # Move east to (14, 8) - near boundary with region (1, 0)
        success, _ = game_state.move("east")

        assert success

        # After move near boundary, adjacent region should be pre-generated
        # Region (1, 0) should now be in the cache
        from cli_rpg.world_tiles import get_region_coords

        # The key should be region coords (1, 0), not world coords
        assert (1, 0) in game_state.region_contexts or len(
            game_state.region_contexts
        ) > initial_region_count
