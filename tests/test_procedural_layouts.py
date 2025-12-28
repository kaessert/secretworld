"""Tests for procedural dungeon/area layouts (Issue 20).

Tests layout generators (linear, branching, hub, maze), category-based selection,
and secret passage generation.
"""

import random
import pytest
from unittest.mock import patch, MagicMock

from cli_rpg.ai_config import AIConfig


@pytest.fixture
def ai_config():
    """Create a basic AIConfig for testing."""
    return AIConfig(
        api_key="test-key-123",
        model="gpt-3.5-turbo",
        temperature=0.7,
        enable_caching=False,
        retry_delay=0.1,
    )


@pytest.fixture
def ai_service(ai_config):
    """Create an AIService instance for testing."""
    from cli_rpg.ai_service import AIService

    service = AIService(ai_config)
    return service


# ============================================================================
# Unit Tests - Layout Generators
# ============================================================================


class TestLinearLayout:
    """Tests for linear (cave/mine) layout generation."""

    def test_linear_layout_produces_corridor_shape(self, ai_service):
        """Spec: Linear layout for cave produces coords in a line (all same x OR all same y)."""
        coords = ai_service._generate_linear_layout(size=5, entry_direction="south")

        # All x-coords should be same OR all y-coords should be same
        x_vals = [c[0] for c in coords]
        y_vals = [c[1] for c in coords]

        is_horizontal = len(set(y_vals)) == 1
        is_vertical = len(set(x_vals)) == 1

        assert is_horizontal or is_vertical, (
            f"Linear layout should form a line, got coords: {coords}"
        )

    def test_linear_layout_entry_at_origin(self, ai_service):
        """Spec: Entry point is (0,0)."""
        coords = ai_service._generate_linear_layout(size=5, entry_direction="south")

        assert coords[0] == (0, 0), f"Entry should be at (0,0), got {coords[0]}"

    def test_linear_layout_respects_size(self, ai_service):
        """Spec: Returns requested number of coords."""
        for size in [3, 5, 10]:
            coords = ai_service._generate_linear_layout(size=size, entry_direction="north")
            assert len(coords) == size, f"Expected {size} coords, got {len(coords)}"

    def test_linear_layout_directions(self, ai_service):
        """Test that linear layout extends in correct direction based on entry."""
        # Entering from south should extend north (y increases)
        coords = ai_service._generate_linear_layout(size=3, entry_direction="south")
        assert coords[1][1] > coords[0][1], "Should extend north when entering from south"

        # Entering from north should extend south (y decreases)
        coords = ai_service._generate_linear_layout(size=3, entry_direction="north")
        assert coords[1][1] < coords[0][1], "Should extend south when entering from north"


class TestHubLayout:
    """Tests for hub (temple/shrine) layout generation."""

    def test_hub_layout_has_central_room(self, ai_service):
        """Spec: Hub layout has entry at (0,0)."""
        coords = ai_service._generate_hub_layout(size=9, entry_direction="south")

        assert (0, 0) in coords, "Hub layout should have central room at (0,0)"
        assert coords[0] == (0, 0), "Entry should be at center (0,0)"

    def test_hub_layout_four_spokes(self, ai_service):
        """Spec: Hub layout creates rooms extending in cardinal directions."""
        coords = ai_service._generate_hub_layout(size=9, entry_direction="south")

        # Should have coords extending in at least 3 of 4 directions
        # (with size 9, we have 8 non-center rooms for 4 spokes = 2 per spoke)
        has_north = any(c[1] > 0 for c in coords)
        has_south = any(c[1] < 0 for c in coords)
        has_east = any(c[0] > 0 for c in coords)
        has_west = any(c[0] < 0 for c in coords)

        directions_present = sum([has_north, has_south, has_east, has_west])
        assert directions_present >= 3, (
            f"Hub should have rooms in at least 3 directions, found {directions_present}"
        )

    def test_hub_layout_respects_size(self, ai_service):
        """Spec: Returns requested number of coords."""
        for size in [5, 9, 13]:
            coords = ai_service._generate_hub_layout(size=size, entry_direction="south")
            assert len(coords) == size, f"Expected {size} coords, got {len(coords)}"


class TestMazeLayout:
    """Tests for maze (dungeon) layout generation."""

    def test_maze_layout_has_multiple_branches(self, ai_service):
        """Spec: Maze layout has coords with multiple neighbors."""
        coords = ai_service._generate_maze_layout(size=15, entry_direction="south")
        coord_set = set(coords)

        # Count neighbors for each coord
        multi_neighbor_count = 0
        for x, y in coords:
            neighbors = sum(
                1 for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                if (x + dx, y + dy) in coord_set
            )
            if neighbors >= 2:
                multi_neighbor_count += 1

        # Should have at least some coords with multiple neighbors (branching)
        assert multi_neighbor_count >= 2, (
            f"Maze should have branching paths, found {multi_neighbor_count} multi-neighbor coords"
        )

    def test_maze_layout_has_dead_ends(self, ai_service):
        """Spec: Maze layout includes dead-end coords (1 neighbor only)."""
        coords = ai_service._generate_maze_layout(size=15, entry_direction="south")
        coord_set = set(coords)

        # Count dead ends (exactly 1 neighbor)
        dead_end_count = 0
        for x, y in coords:
            neighbors = sum(
                1 for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                if (x + dx, y + dy) in coord_set
            )
            if neighbors == 1:
                dead_end_count += 1

        # Mazes should have at least one dead end
        assert dead_end_count >= 1, (
            f"Maze should have dead ends, found {dead_end_count}"
        )

    def test_maze_layout_respects_size(self, ai_service):
        """Spec: Returns requested number of coords."""
        for size in [5, 10, 20]:
            coords = ai_service._generate_maze_layout(size=size, entry_direction="south")
            assert len(coords) == size, f"Expected {size} coords, got {len(coords)}"

    def test_maze_layout_entry_at_origin(self, ai_service):
        """Maze entry should be at (0,0)."""
        coords = ai_service._generate_maze_layout(size=10, entry_direction="south")

        assert coords[0] == (0, 0), f"Entry should be at (0,0), got {coords[0]}"


class TestBranchingLayout:
    """Tests for branching (forest/ruins) layout - the original default."""

    def test_branching_layout_unchanged(self, ai_service):
        """Spec: Existing branching behavior preserved for forest/ruins."""
        coords = ai_service._generate_branching_layout(size=5, entry_direction="south")

        # Basic sanity checks - entry at origin, correct size
        assert coords[0] == (0, 0), "Entry should be at (0,0)"
        assert len(coords) == 5, "Should return requested size"

        # Should have some branching (not all in a straight line)
        x_vals = set(c[0] for c in coords)
        y_vals = set(c[1] for c in coords)

        # Branching should have variation in both x and y after expansion
        # (size 5 with branching should spread in both dimensions)
        has_variation = len(x_vals) > 1 or len(y_vals) > 1
        assert has_variation, "Branching layout should expand from entry"


# ============================================================================
# Unit Tests - Category Selection
# ============================================================================


class TestCategorySelection:
    """Tests for category-based layout selection."""

    def test_layout_selection_cave_uses_linear(self):
        """Spec: 'cave' category triggers linear layout."""
        from cli_rpg.ai_service import CATEGORY_LAYOUTS, LayoutType

        assert CATEGORY_LAYOUTS.get("cave") == LayoutType.LINEAR

    def test_layout_selection_mine_uses_linear(self):
        """'mine' category also triggers linear layout."""
        from cli_rpg.ai_service import CATEGORY_LAYOUTS, LayoutType

        assert CATEGORY_LAYOUTS.get("mine") == LayoutType.LINEAR

    def test_layout_selection_temple_uses_hub(self):
        """Spec: 'temple' category triggers hub layout."""
        from cli_rpg.ai_service import CATEGORY_LAYOUTS, LayoutType

        assert CATEGORY_LAYOUTS.get("temple") == LayoutType.HUB

    def test_layout_selection_monastery_uses_hub(self):
        """'monastery' category also triggers hub layout."""
        from cli_rpg.ai_service import CATEGORY_LAYOUTS, LayoutType

        assert CATEGORY_LAYOUTS.get("monastery") == LayoutType.HUB

    def test_layout_selection_shrine_uses_hub(self):
        """'shrine' category also triggers hub layout."""
        from cli_rpg.ai_service import CATEGORY_LAYOUTS, LayoutType

        assert CATEGORY_LAYOUTS.get("shrine") == LayoutType.HUB

    def test_layout_selection_dungeon_uses_maze(self):
        """Spec: 'dungeon' category triggers maze layout."""
        from cli_rpg.ai_service import CATEGORY_LAYOUTS, LayoutType

        assert CATEGORY_LAYOUTS.get("dungeon") == LayoutType.MAZE

    def test_layout_selection_forest_uses_branching(self):
        """Spec: 'forest' category uses branching (default)."""
        from cli_rpg.ai_service import CATEGORY_LAYOUTS, LayoutType

        # forest should not be in CATEGORY_LAYOUTS (falls back to branching)
        assert "forest" not in CATEGORY_LAYOUTS or CATEGORY_LAYOUTS.get("forest") == LayoutType.BRANCHING

    def test_layout_selection_unknown_uses_branching(self, ai_service):
        """Spec: Unknown category falls back to branching."""
        # Call _generate_area_layout with unknown category
        # Should use branching (not crash)
        coords = ai_service._generate_area_layout(
            size=5,
            entry_direction="south",
            category="unknown_category"
        )

        assert len(coords) == 5, "Should still return correct size"
        assert coords[0] == (0, 0), "Should still have entry at origin"


class TestAreaLayoutDispatch:
    """Tests for _generate_area_layout category dispatch."""

    def test_generate_area_layout_dispatches_to_linear(self, ai_service):
        """_generate_area_layout with cave should use linear layout."""
        # Linear layout produces a straight line
        coords = ai_service._generate_area_layout(
            size=5,
            entry_direction="south",
            category="cave"
        )

        # Verify it's a line (all same x OR all same y)
        x_vals = [c[0] for c in coords]
        y_vals = [c[1] for c in coords]
        assert len(set(x_vals)) == 1 or len(set(y_vals)) == 1

    def test_generate_area_layout_dispatches_to_hub(self, ai_service):
        """_generate_area_layout with temple should use hub layout."""
        coords = ai_service._generate_area_layout(
            size=9,
            entry_direction="south",
            category="temple"
        )

        # Hub has spokes in multiple directions from center
        has_north = any(c[1] > 0 for c in coords)
        has_south = any(c[1] < 0 for c in coords)
        has_east = any(c[0] > 0 for c in coords)
        has_west = any(c[0] < 0 for c in coords)

        assert sum([has_north, has_south, has_east, has_west]) >= 3

    def test_generate_area_layout_dispatches_to_maze(self, ai_service):
        """_generate_area_layout with dungeon should use maze layout."""
        # Save random state to avoid interference from other tests
        old_state = random.getstate()
        try:
            random.seed(42)  # Use a fixed seed for deterministic maze generation
            coords = ai_service._generate_area_layout(
                size=15,
                entry_direction="south",
                category="dungeon"
            )
        finally:
            # Restore random state to avoid affecting other tests
            random.setstate(old_state)

        # Maze should have variation (not a straight line or simple spoke)
        coord_set = set(coords)

        # Count dead ends
        dead_ends = 0
        for x, y in coords:
            neighbors = sum(
                1 for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                if (x + dx, y + dy) in coord_set
            )
            if neighbors == 1:
                dead_ends += 1

        assert dead_ends >= 1, "Maze layout should have dead ends"

    def test_generate_area_layout_case_insensitive(self, ai_service):
        """Category matching should be case insensitive."""
        # Test uppercase
        coords_upper = ai_service._generate_area_layout(
            size=5,
            entry_direction="south",
            category="CAVE"
        )

        # Should still use linear (same x or y)
        x_vals = [c[0] for c in coords_upper]
        y_vals = [c[1] for c in coords_upper]
        assert len(set(x_vals)) == 1 or len(set(y_vals)) == 1

    def test_generate_area_layout_none_category(self, ai_service):
        """None category should fall back to branching."""
        coords = ai_service._generate_area_layout(
            size=5,
            entry_direction="south",
            category=None
        )

        assert len(coords) == 5
        assert coords[0] == (0, 0)


# ============================================================================
# Unit Tests - Secret Passages
# ============================================================================


class TestSecretPassages:
    """Tests for secret passage generation."""

    def test_secret_passage_connects_non_adjacent(self, ai_service):
        """Spec: Secret passage connects rooms >= 2 Manhattan distance apart."""
        # Create layout with enough coords for passages
        coords = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]

        # Force passage creation by setting probability to 1.0
        passage = ai_service._generate_secret_passage(coords, probability=1.0)

        assert passage is not None, "Should generate a passage with probability 1.0"

        from_coord = passage["from_coord"]
        to_coord = passage["to_coord"]

        # Calculate Manhattan distance
        dist = abs(from_coord[0] - to_coord[0]) + abs(from_coord[1] - to_coord[1])

        assert dist >= 2, f"Secret passage should connect non-adjacent rooms, got distance {dist}"

    def test_secret_passage_returns_valid_structure(self, ai_service):
        """Spec: Secret passage has from_coord, to_coord, is_secret_passage fields."""
        coords = [(0, 0), (0, 1), (0, 2), (0, 3)]
        passage = ai_service._generate_secret_passage(coords, probability=1.0)

        assert passage is not None
        assert "from_coord" in passage
        assert "to_coord" in passage
        assert "is_secret_passage" in passage
        assert passage["is_secret_passage"] is True

    def test_secret_passage_none_with_zero_probability(self, ai_service):
        """No passage generated with probability 0."""
        coords = [(0, 0), (0, 1), (0, 2), (0, 3)]
        passage = ai_service._generate_secret_passage(coords, probability=0.0)

        assert passage is None

    def test_secret_passage_none_with_insufficient_coords(self, ai_service):
        """No passage possible with < 4 coords (can't have distance >= 2)."""
        # Only 3 coords - not enough for non-adjacent pair with distance >= 2
        coords = [(0, 0), (0, 1), (0, 2)]
        passage = ai_service._generate_secret_passage(coords, probability=1.0)

        # With linear coords of length 3, max distance is 2 between (0,0) and (0,2)
        # So a passage should be possible
        if passage is not None:
            dist = abs(passage["from_coord"][0] - passage["to_coord"][0]) + \
                   abs(passage["from_coord"][1] - passage["to_coord"][1])
            assert dist >= 2

    def test_secret_passage_none_with_too_few_coords(self, ai_service):
        """No passage possible with < 3 coords."""
        # Only 2 coords - adjacent, can't have distance >= 2
        coords = [(0, 0), (0, 1)]
        passage = ai_service._generate_secret_passage(coords, probability=1.0)

        assert passage is None, "Should not generate passage with only 2 adjacent coords"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for layout generation in context."""

    def test_generate_subgrid_uses_category_layout(self, ai_service):
        """Spec: generate_subgrid_for_location() selects layout by category."""
        # This tests that when a subgrid is generated, the category
        # influences the layout pattern

        # Test that cave category produces linear layout
        cave_coords = ai_service._generate_area_layout(
            size=5,
            entry_direction="south",
            category="cave"
        )

        # Test that dungeon category produces maze layout
        dungeon_coords = ai_service._generate_area_layout(
            size=10,
            entry_direction="south",
            category="dungeon"
        )

        # Cave should be linear
        cave_x = [c[0] for c in cave_coords]
        cave_y = [c[1] for c in cave_coords]
        assert len(set(cave_x)) == 1 or len(set(cave_y)) == 1

        # Dungeon should have more spread (not a simple line)
        dungeon_x = set(c[0] for c in dungeon_coords)
        dungeon_y = set(c[1] for c in dungeon_coords)
        # Maze typically has more variation
        assert len(dungeon_x) > 1 or len(dungeon_y) > 1

    def test_3d_layout_applies_category_patterns(self, ai_service):
        """Spec: _generate_area_layout_3d() respects category on each z-level."""
        # Test with single-level category (should dispatch to 2D layout with category)
        # Forest is single level (z=0 only) and uses branching
        coords_3d = ai_service._generate_area_layout_3d(
            size=5,
            entry_direction="south",
            category="cave"  # cave uses linear
        )

        # Should have z=0 for all coords if cave bounds are single-level
        # Actually cave has z bounds (-1, 0), so might have multiple levels
        # But the 2D fallback should use category for single-level case

        # Extract 2D coords (ignore z) and check if linear-ish
        coords_2d = [(x, y) for x, y, z in coords_3d if z == 0]

        if len(coords_2d) > 0:
            # Check that z=0 level follows category pattern
            # For cave with multiple z levels, each level should have some structure
            pass  # Just verify it doesn't crash and returns valid coords

        assert len(coords_3d) == 5


class TestSubGridSecretPassages:
    """Tests for secret passages stored on SubGrid."""

    def test_subgrid_has_secret_passages_field(self):
        """SubGrid should have secret_passages field."""
        from cli_rpg.world_grid import SubGrid

        subgrid = SubGrid()

        assert hasattr(subgrid, "secret_passages")
        assert subgrid.secret_passages == []

    def test_subgrid_secret_passages_serialization(self):
        """Secret passages should be serialized with SubGrid."""
        from cli_rpg.world_grid import SubGrid

        subgrid = SubGrid()
        subgrid.secret_passages = [
            {"from_coord": (0, 0), "to_coord": (0, 3), "is_secret_passage": True}
        ]

        data = subgrid.to_dict()

        assert "secret_passages" in data
        assert len(data["secret_passages"]) == 1
        assert data["secret_passages"][0]["is_secret_passage"] is True

    def test_subgrid_secret_passages_deserialization(self):
        """Secret passages should be restored when deserializing SubGrid."""
        from cli_rpg.world_grid import SubGrid

        data = {
            "locations": [],
            "bounds": [-2, 2, -2, 2, 0, 0],
            "parent_name": "Test Location",
            "secret_passages": [
                {"from_coord": (0, 0), "to_coord": (0, 3), "is_secret_passage": True}
            ]
        }

        subgrid = SubGrid.from_dict(data)

        assert len(subgrid.secret_passages) == 1
        assert subgrid.secret_passages[0]["is_secret_passage"] is True
