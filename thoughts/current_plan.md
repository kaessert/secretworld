# Strategic Frontier Exit Placement

## Spec

When generating named locations (POIs), strategically place exits that point toward unexplored regions rather than back toward explored territory. This guides players toward new content and creates a sense of world expansion.

**Behavior:**
1. When a new named location is generated, analyze which directions lead to unexplored regions
2. Prioritize exits pointing toward unexplored regions (higher chance of interesting content hints)
3. Location descriptions should hint at unexplored regions in those directions
4. The `find_frontier_exits()` method should optionally prioritize directions leading to unexplored regions

**Not in scope:**
- Terrain transitions (separate sub-task)
- Location clustering (separate sub-task)
- Blocking any exits (all passable terrain remains traversable)

## Tests

Create `tests/test_strategic_frontier_exits.py`:

```python
# 1. Test get_unexplored_region_directions returns correct directions
def test_get_unexplored_region_directions_returns_directions_toward_unexplored_regions():
    """Directions toward regions with no explored tiles are identified."""

# 2. Test prioritized_frontier_exits puts unexplored regions first
def test_prioritized_frontier_exits_orders_by_exploration():
    """Exits toward unexplored regions are listed before explored ones."""

# 3. Test location description includes frontier hints
def test_named_location_description_includes_frontier_hints():
    """When generating named locations, descriptions hint at unexplored directions."""

# 4. Test frontier analysis handles edge cases
def test_frontier_analysis_handles_single_location():
    """Single location shows all directions as unexplored."""

# 5. Test frontier analysis respects region boundaries
def test_frontier_analysis_uses_region_coords():
    """Uses REGION_SIZE to determine unexplored regions, not individual tiles."""
```

## Implementation Steps

### 1. Add `get_unexplored_region_directions()` to `world_tiles.py`

```python
def get_unexplored_region_directions(
    world_x: int,
    world_y: int,
    explored_regions: set[tuple[int, int]],
) -> list[str]:
    """Return directions pointing toward unexplored regions.

    Args:
        world_x: Current world x coordinate
        world_y: Current world y coordinate
        explored_regions: Set of (region_x, region_y) tuples that have been visited

    Returns:
        List of direction names pointing toward unexplored regions, sorted by priority
    """
```

### 2. Add `get_prioritized_frontier_exits()` to `WorldGrid` in `world_grid.py`

```python
def get_prioritized_frontier_exits(
    self,
    explored_regions: Optional[set[tuple[int, int]]] = None
) -> List[Tuple[str, str, Tuple[int, int]]]:
    """Find frontier exits prioritized by unexplored regions.

    Similar to find_frontier_exits() but orders results to prefer
    directions leading to unexplored regions.

    Args:
        explored_regions: Optional set of visited region coordinates.
                         If None, uses region analysis from current locations.

    Returns:
        List of (location_name, direction, target_coords) prioritized
        with unexplored region directions first.
    """
```

### 3. Add `get_explored_regions()` to `GameState` in `game_state.py`

```python
def get_explored_regions(self) -> set[tuple[int, int]]:
    """Return set of region coordinates that have been explored.

    Analyzes all locations in world grid to determine which regions
    (REGION_SIZE x REGION_SIZE tile areas) have been visited.

    Returns:
        Set of (region_x, region_y) tuples
    """
```

### 4. Update `expand_area()` in `ai_world.py` to include frontier hints

Pass unexplored directions to the AI prompt so generated location descriptions can hint at interesting content in unexplored directions.

### 5. Add `FRONTIER_DESCRIPTION_HINTS` to `ai_config.py`

```python
FRONTIER_DESCRIPTION_HINTS: Dict[str, str] = {
    "north": "To the north, the land rises toward unknown heights.",
    "south": "Southward, unexplored territory beckons.",
    "east": "The eastern horizon holds mysteries yet to be discovered.",
    "west": "Westward paths lead to lands untraveled.",
}
```

## Files to Modify

| File | Change |
|------|--------|
| `src/cli_rpg/world_tiles.py` | Add `get_unexplored_region_directions()` |
| `src/cli_rpg/world_grid.py` | Add `get_prioritized_frontier_exits()` |
| `src/cli_rpg/game_state.py` | Add `get_explored_regions()` |
| `src/cli_rpg/ai_world.py` | Pass frontier hints to location generation |
| `src/cli_rpg/ai_config.py` | Add `FRONTIER_DESCRIPTION_HINTS` |
| `tests/test_strategic_frontier_exits.py` | New test file |

## Verification

```bash
pytest tests/test_strategic_frontier_exits.py -v
pytest tests/test_world_grid.py -v
pytest tests/test_world_tiles.py -v
pytest --cov=src/cli_rpg
```
