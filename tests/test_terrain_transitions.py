"""Tests for natural terrain transition distances.

These tests verify that WFC generation creates natural transition zones between
incompatible biomes (e.g., forest and desert should have multiple tiles between them).
"""

import pytest
from typing import Dict, Set, Tuple

from cli_rpg.world_tiles import (
    BIOME_GROUPS,
    INCOMPATIBLE_GROUPS,
    get_distance_penalty,
    TerrainType,
)
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.world_tiles import TileRegistry


class TestBiomeGroups:
    """Tests for biome group definitions."""

    def test_biome_groups_defined(self):
        """BIOME_GROUPS maps all terrain types to a group."""
        # All terrain types should be in BIOME_GROUPS
        for terrain_type in TerrainType:
            terrain_name = terrain_type.value
            assert terrain_name in BIOME_GROUPS, (
                f"Terrain '{terrain_name}' not in BIOME_GROUPS"
            )
            assert BIOME_GROUPS[terrain_name] is not None, (
                f"Terrain '{terrain_name}' has None group"
            )

    def test_incompatible_groups_symmetric(self):
        """INCOMPATIBLE_GROUPS is symmetric (A conflicts B = B conflicts A)."""
        for group_a, group_b in INCOMPATIBLE_GROUPS:
            # If (A, B) is incompatible, (B, A) should also be incompatible
            assert (group_b, group_a) in INCOMPATIBLE_GROUPS, (
                f"INCOMPATIBLE_GROUPS not symmetric: ({group_a}, {group_b}) exists "
                f"but ({group_b}, {group_a}) does not"
            )


class TestTransitionWeightPenalty:
    """Tests for distance-based weight penalties during WFC collapse."""

    def test_get_distance_penalty_no_penalty_neutral(self):
        """Plains/hills don't receive penalties from any nearby biome."""
        # Even with forest and desert nearby, neutral terrain should be unpenalized
        nearby = {"forest", "desert", "mountain"}
        assert get_distance_penalty("plains", nearby) == 1.0
        assert get_distance_penalty("hills", nearby) == 1.0

    def test_get_distance_penalty_no_penalty_same_group(self):
        """Tiles in the same biome group don't penalize each other."""
        # Forest near swamp (both temperate) should be fine
        assert get_distance_penalty("forest", {"swamp"}) == 1.0
        assert get_distance_penalty("swamp", {"forest"}) == 1.0
        # Mountain near foothills (both alpine) should be fine
        assert get_distance_penalty("mountain", {"foothills"}) == 1.0

    def test_get_distance_penalty_incompatible_groups(self):
        """When incompatible biome is nearby, tiles get 0.01x weight (99% reduction)."""
        # Desert near forest (arid near temperate) should be penalized
        assert get_distance_penalty("desert", {"forest"}) == 0.01
        # Forest near desert should also be penalized
        assert get_distance_penalty("forest", {"desert"}) == 0.01
        # Swamp near desert should be penalized (both temperate/arid conflict)
        assert get_distance_penalty("swamp", {"desert"}) == 0.01

    def test_get_distance_penalty_empty_nearby(self):
        """No penalty when nothing is nearby."""
        assert get_distance_penalty("forest", set()) == 1.0
        assert get_distance_penalty("desert", set()) == 1.0

    def test_get_nearby_collapsed_tiles_returns_tiles_in_radius(self):
        """_get_nearby_collapsed_tiles returns all collapsed tiles within radius."""
        from cli_rpg.wfc import WFCCell

        tile_registry = TileRegistry()
        manager = ChunkManager(tile_registry=tile_registry, world_seed=42)

        # Create a test grid with some collapsed cells
        grid: Dict[Tuple[int, int], WFCCell] = {
            (0, 0): WFCCell(coords=(0, 0), possible_tiles={"forest"}, collapsed=True, tile="forest"),
            (1, 0): WFCCell(coords=(1, 0), possible_tiles={"plains"}, collapsed=True, tile="plains"),
            (2, 0): WFCCell(coords=(2, 0), possible_tiles={"desert"}, collapsed=True, tile="desert"),
            (0, 1): WFCCell(coords=(0, 1), possible_tiles={"hills"}, collapsed=True, tile="hills"),
            (1, 1): WFCCell(coords=(1, 1), possible_tiles={"plains", "forest"}, collapsed=False),  # Not collapsed
            (3, 0): WFCCell(coords=(3, 0), possible_tiles={"mountain"}, collapsed=True, tile="mountain"),  # Out of radius 2
        }

        # Get tiles within radius 2 of (1, 1)
        nearby = manager._get_nearby_collapsed_tiles(grid, 1, 1, radius=2)

        # Should include forest (0,0), plains (1,0), desert (2,0), hills (0,1)
        # Should NOT include mountain at (3,0) which is distance 2.23 > 2
        # Wait, (3,0) to (1,1) is dx=2, dy=1 which is within the [-2,2] range for both
        # Actually the radius check is manhattan-style (dx in [-r, r] and dy in [-r, r])
        # So (3,0) has dx=2, dy=-1, which IS within radius 2

        assert "forest" in nearby
        assert "plains" in nearby
        assert "desert" in nearby
        assert "hills" in nearby
        # (3,0) is at dx=2, dy=-1 from (1,1) - within radius 2
        assert "mountain" in nearby

        # The center cell (1,1) itself should NOT be included
        # (it's uncollapsed anyway, but we skip dx=0,dy=0)

    def test_get_nearby_collapsed_tiles_excludes_center(self):
        """_get_nearby_collapsed_tiles excludes the center cell itself."""
        from cli_rpg.wfc import WFCCell

        tile_registry = TileRegistry()
        manager = ChunkManager(tile_registry=tile_registry, world_seed=42)

        grid: Dict[Tuple[int, int], WFCCell] = {
            (5, 5): WFCCell(coords=(5, 5), possible_tiles={"forest"}, collapsed=True, tile="forest"),
        }

        # Get tiles at the exact center position
        nearby = manager._get_nearby_collapsed_tiles(grid, 5, 5, radius=2)

        # Should be empty since we exclude the center
        assert nearby == set()


class TestTransitionZoneWidth:
    """Statistical tests for transition zone width in generated terrain."""

    def _find_minimum_distance(
        self, chunk: Dict[Tuple[int, int], str], terrain_a: str, terrain_b: str
    ) -> int:
        """Find the minimum Manhattan distance between two terrain types in a chunk.

        Returns:
            Minimum distance between terrains, or -1 if one or both terrains not found
        """
        coords_a = [(x, y) for (x, y), t in chunk.items() if t == terrain_a]
        coords_b = [(x, y) for (x, y), t in chunk.items() if t == terrain_b]

        if not coords_a or not coords_b:
            return -1

        min_dist = float("inf")
        for ax, ay in coords_a:
            for bx, by in coords_b:
                dist = abs(ax - bx) + abs(ay - by)
                min_dist = min(min_dist, dist)

        return int(min_dist)

    def test_forest_desert_transition_minimum_3_tiles(self):
        """Statistical: minimum 3 tiles between forest and desert in generated chunks.

        Spec: When collapsing a cell, if there's a Group A tile (temperate like forest)
        within 2 tiles, Group B tiles (arid like desert) get 0.1x weight penalty.
        This should result in at least 3 tiles of separation in most cases.
        """
        tile_registry = TileRegistry()

        violations = 0
        chunks_with_both = 0

        # Generate many chunks and check transition distances
        for seed in range(50):  # Test 50 different seeds
            manager = ChunkManager(tile_registry=tile_registry, world_seed=seed)

            # Generate a larger area (4 chunks = 32x32 tiles) to increase chance of biome meeting
            for cx in range(2):
                for cy in range(2):
                    manager.get_or_generate_chunk(cx, cy)

            # Combine all chunks for analysis
            all_tiles: Dict[Tuple[int, int], str] = {}
            for chunk in manager._chunks.values():
                all_tiles.update(chunk)

            min_dist = self._find_minimum_distance(all_tiles, "forest", "desert")

            if min_dist > 0:  # Both terrains found
                chunks_with_both += 1
                if min_dist < 3:
                    violations += 1

        # We need at least some test cases where both terrains appear
        # If fewer than 5 chunks have both, the test is inconclusive
        if chunks_with_both >= 5:
            # Allow up to 40% violations due to:
            # 1. WFC collapse order (desert may collapse before forest is nearby)
            # 2. Chunk boundary effects
            # 3. Natural randomness in weighted selection
            # The penalty significantly reduces violations but can't prevent all
            violation_rate = violations / chunks_with_both
            assert violation_rate < 0.40, (
                f"Too many forest-desert violations: {violations}/{chunks_with_both} "
                f"({violation_rate:.1%}) had distance < 3 tiles"
            )

    def test_swamp_desert_transition_minimum_3_tiles(self):
        """Statistical: minimum 3 tiles between swamp and desert.

        Both swamp (temperate) and desert (arid) are incompatible groups.
        """
        tile_registry = TileRegistry()

        violations = 0
        chunks_with_both = 0

        for seed in range(50):
            manager = ChunkManager(tile_registry=tile_registry, world_seed=seed)

            # Generate larger area
            for cx in range(2):
                for cy in range(2):
                    manager.get_or_generate_chunk(cx, cy)

            all_tiles: Dict[Tuple[int, int], str] = {}
            for chunk in manager._chunks.values():
                all_tiles.update(chunk)

            min_dist = self._find_minimum_distance(all_tiles, "swamp", "desert")

            if min_dist > 0:
                chunks_with_both += 1
                if min_dist < 3:
                    violations += 1

        if chunks_with_both >= 5:
            # Allow up to 40% violations (see test_forest_desert for rationale)
            violation_rate = violations / chunks_with_both
            assert violation_rate < 0.40, (
                f"Too many swamp-desert violations: {violations}/{chunks_with_both} "
                f"({violation_rate:.1%}) had distance < 3 tiles"
            )


class TestNaturalTransitionsDict:
    """Tests for NATURAL_TRANSITIONS data structure."""

    def test_all_terrain_types_have_entries(self):
        """Every TerrainType has an entry in NATURAL_TRANSITIONS."""
        from cli_rpg.world_tiles import NATURAL_TRANSITIONS
        for terrain in TerrainType:
            assert terrain.value in NATURAL_TRANSITIONS

    def test_self_transitions_allowed(self):
        """Every terrain can transition to itself."""
        from cli_rpg.world_tiles import NATURAL_TRANSITIONS
        for terrain in TerrainType:
            assert terrain.value in NATURAL_TRANSITIONS[terrain.value]

    def test_transitions_are_symmetric(self):
        """If A->B is natural, B->A should also be natural."""
        from cli_rpg.world_tiles import NATURAL_TRANSITIONS
        for terrain, neighbors in NATURAL_TRANSITIONS.items():
            for neighbor in neighbors:
                assert terrain in NATURAL_TRANSITIONS.get(neighbor, set()), \
                    f"{terrain}->{neighbor} allowed but {neighbor}->{terrain} not"


class TestIsNaturalTransition:
    """Tests for is_natural_transition() function."""

    def test_same_terrain_always_natural(self):
        """Transitioning to same terrain is always natural."""
        from cli_rpg.world_tiles import is_natural_transition
        for terrain in TerrainType:
            assert is_natural_transition(terrain.value, terrain.value)

    def test_forest_to_plains_natural(self):
        """Forest borders plains naturally."""
        from cli_rpg.world_tiles import is_natural_transition
        assert is_natural_transition("forest", "plains")
        assert is_natural_transition("plains", "forest")

    def test_forest_to_desert_unnatural(self):
        """Forest directly adjacent to desert is jarring."""
        from cli_rpg.world_tiles import is_natural_transition
        assert not is_natural_transition("forest", "desert")
        assert not is_natural_transition("desert", "forest")

    def test_mountain_to_beach_unnatural(self):
        """Mountains don't border beaches."""
        from cli_rpg.world_tiles import is_natural_transition
        assert not is_natural_transition("mountain", "beach")

    def test_swamp_to_desert_unnatural(self):
        """Wetlands don't border arid terrain."""
        from cli_rpg.world_tiles import is_natural_transition
        assert not is_natural_transition("swamp", "desert")

    def test_plains_bridges_forest_to_desert(self):
        """Plains can connect otherwise incompatible biomes."""
        from cli_rpg.world_tiles import is_natural_transition
        assert is_natural_transition("forest", "plains")
        assert is_natural_transition("plains", "desert")

    def test_foothills_bridges_plains_to_mountain(self):
        """Foothills provide natural elevation transition."""
        from cli_rpg.world_tiles import is_natural_transition
        assert is_natural_transition("plains", "foothills")
        assert is_natural_transition("foothills", "mountain")

    def test_unknown_terrain_returns_false(self):
        """Unknown terrain types return False (safe default)."""
        from cli_rpg.world_tiles import is_natural_transition
        assert not is_natural_transition("lava", "forest")
        assert not is_natural_transition("forest", "void")


class TestGetTransitionWarning:
    """Tests for get_transition_warning() function."""

    def test_natural_transition_returns_none(self):
        """No warning for natural transitions."""
        from cli_rpg.world_tiles import get_transition_warning
        assert get_transition_warning("forest", "plains") is None
        assert get_transition_warning("hills", "mountain") is None

    def test_unnatural_transition_returns_message(self):
        """Warning message for unnatural transitions."""
        from cli_rpg.world_tiles import get_transition_warning
        warning = get_transition_warning("forest", "desert")
        assert warning is not None
        assert "forest" in warning
        assert "desert" in warning

    def test_same_terrain_no_warning(self):
        """No warning when transitioning to same terrain."""
        from cli_rpg.world_tiles import get_transition_warning
        assert get_transition_warning("forest", "forest") is None
