# Implementation Plan: Natural Terrain Transitions

## Summary
Add "transition distance" weights to WFC generation that penalize placing extreme biome jumps (like desert near forest) even when the adjacency rules technically allow an intermediate tile. This creates wider transition zones instead of single-tile buffers.

## Spec

The goal is to prevent thin transition zones like: `forest → plains (1 tile) → desert`. Instead, transitions should span multiple tiles to feel natural.

**Approach**: Add a "biome distance" penalty system where tiles incompatible with nearby tiles (within 2-3 tile radius) receive reduced weights during WFC collapse.

### Biome Distance Rules
```
Group A (temperate wet): forest, swamp
Group B (hot dry): desert
Group C (aquatic): water, beach
Group D (mountainous): mountain, foothills
Neutral (bridges all): plains, hills
```

When collapsing a cell, if there's a Group A tile within 2 tiles, Group B tiles get 0.1x weight penalty (and vice versa). Neutral tiles and same-group tiles are unaffected.

### Key Changes
1. Add `BIOME_GROUPS` constant mapping terrains to biome groups
2. Add `INCOMPATIBLE_GROUPS` mapping which groups conflict
3. Add `get_nearby_tiles()` helper in ChunkManager to check 2-tile radius
4. Modify `_collapse_cell()` to apply distance penalties based on nearby tiles

---

## Tests (`tests/test_terrain_transitions.py`)

```python
"""Tests for natural terrain transition distances."""

class TestBiomeGroups:
    def test_biome_groups_defined():
        """BIOME_GROUPS maps all terrain types to a group."""

    def test_incompatible_groups_symmetric():
        """INCOMPATIBLE_GROUPS is symmetric (A conflicts B = B conflicts A)."""

class TestTransitionWeightPenalty:
    def test_get_nearby_tiles_returns_tiles_in_radius():
        """get_nearby_tiles(grid, x, y, radius=2) returns all collapsed tiles within radius."""

    def test_collapse_applies_distance_penalty():
        """When forest is 2 tiles away, desert gets 0.1x weight in collapse."""

    def test_neutral_terrain_unaffected():
        """Plains/hills don't receive penalties from any nearby biome."""

class TestTransitionZoneWidth:
    def test_forest_desert_transition_minimum_3_tiles():
        """Statistical: minimum 3 tiles between forest and desert in generated chunks."""
        # Generate 20 chunks, verify no forest within 2 tiles of desert

    def test_swamp_desert_transition_minimum_3_tiles():
        """Statistical: minimum 3 tiles between swamp and desert."""
```

---

## Implementation Steps

### 1. Add biome group constants to `world_tiles.py`

```python
# After ADJACENCY_RULES (around line 114)

# Biome groups for transition distance penalties
BIOME_GROUPS: Dict[str, str] = {
    "forest": "temperate",
    "swamp": "temperate",
    "desert": "arid",
    "water": "aquatic",
    "beach": "aquatic",
    "mountain": "alpine",
    "foothills": "alpine",
    "plains": "neutral",
    "hills": "neutral",
}

# Groups that conflict (feel jarring if within 2 tiles of each other)
INCOMPATIBLE_GROUPS: Set[Tuple[str, str]] = {
    ("temperate", "arid"),  # forest/swamp too close to desert feels wrong
    ("arid", "temperate"),  # symmetric
}

def get_distance_penalty(terrain: str, nearby_terrains: Set[str]) -> float:
    """Calculate weight penalty based on nearby incompatible biomes.

    Args:
        terrain: The terrain type being considered for collapse
        nearby_terrains: Set of terrain types within penalty radius

    Returns:
        Multiplier (1.0 = no penalty, 0.1 = severe penalty)
    """
    terrain_group = BIOME_GROUPS.get(terrain)
    if terrain_group == "neutral":
        return 1.0  # Neutral terrain is never penalized

    for nearby in nearby_terrains:
        nearby_group = BIOME_GROUPS.get(nearby)
        if (terrain_group, nearby_group) in INCOMPATIBLE_GROUPS:
            return 0.1  # 90% weight reduction

    return 1.0
```

### 2. Add `get_nearby_tiles()` helper to `wfc_chunks.py`

```python
# In ChunkManager class (around line 365)

def _get_nearby_collapsed_tiles(
    self,
    grid: Dict[Tuple[int, int], WFCCell],
    x: int,
    y: int,
    radius: int = 2
) -> Set[str]:
    """Get terrain types of collapsed tiles within radius.

    Args:
        grid: Current WFC grid
        x, y: Center coordinates
        radius: Search radius (default 2)

    Returns:
        Set of terrain types from collapsed cells within radius
    """
    nearby = set()
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue
            cell = grid.get((x + dx, y + dy))
            if cell and cell.collapsed and cell.tile:
                nearby.add(cell.tile)
    return nearby
```

### 3. Modify `_collapse_cell()` in `wfc_chunks.py`

```python
# Modify existing _collapse_cell (around line 365)

def _collapse_cell(
    self,
    cell: WFCCell,
    rng: random.Random,
    grid: Optional[Dict[Tuple[int, int], WFCCell]] = None,  # NEW
) -> str:
    """Collapse a cell to a single tile using weighted random selection.

    Applies distance penalties when incompatible biomes are nearby.
    """
    if len(cell.possible_tiles) == 0:
        raise ValueError(f"Cannot collapse cell {cell.coords} with no options")

    tiles = sorted(cell.possible_tiles)
    weights = [self._get_weight(tile) for tile in tiles]

    # Apply distance penalties if grid provided
    if grid is not None:
        from cli_rpg.world_tiles import get_distance_penalty
        nearby = self._get_nearby_collapsed_tiles(grid, cell.coords[0], cell.coords[1])
        weights = [w * get_distance_penalty(t, nearby) for w, t in zip(weights, tiles)]

    selected = rng.choices(tiles, weights=weights, k=1)[0]
    # ... rest unchanged
```

### 4. Update call sites to pass grid

In `_try_generate_with_constraints()` around line 296:
```python
# Change:
self._collapse_cell(min_cell, rng)
# To:
self._collapse_cell(min_cell, rng, grid)
```

### 5. Apply same change to `wfc.py` WFCGenerator

Similar changes to `WFCGenerator._collapse_cell()` and `_try_generate_chunk()` to pass the grid.

---

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/world_tiles.py` | Add `BIOME_GROUPS`, `INCOMPATIBLE_GROUPS`, `get_distance_penalty()` |
| `src/cli_rpg/wfc_chunks.py` | Add `_get_nearby_collapsed_tiles()`, modify `_collapse_cell()` signature |
| `src/cli_rpg/wfc.py` | Same pattern: modify `_collapse_cell()` to accept grid and apply penalties |
| `tests/test_terrain_transitions.py` | New test file with ~8 tests |
