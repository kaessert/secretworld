# Implementation Plan: Generate Whole Areas

## Summary
Modify the AI world generation to create complete thematic areas (clusters of 4-7 connected locations) instead of single locations, ensuring the world border is always "closed" (no inaccessible dangling exits).

## Spec

### Area Generation
1. When `expand_world()` is called, generate an entire area (4-7 locations) with a consistent theme instead of just one location
2. Areas have a coherent sub-theme that fits the world theme (e.g., "haunted graveyard" within "fantasy")
3. New AI method `generate_area()` returns multiple locations with internal connections

### Border Closure Guarantee (Critical)
1. **Closed border**: Every exit at the area's perimeter must either:
   - Point to an existing location in the world, OR
   - Point to a "frontier" placeholder that triggers area generation when visited
2. **Connectivity check**: Add `WorldGrid.find_unreachable_exits()` method that identifies exits leading to non-existent coordinates with no way to reach them
3. **Validation**: After area generation, validate that no "orphaned" exits exist (exits to coordinates that can't be reached from any frontier tile)

### Frontier Management
1. Mark perimeter locations as "frontier" tiles with placeholder exits
2. When player moves to a frontier exit -> triggers new area generation
3. All locations within an area's interior have real connections (not placeholders)

## Files to Modify

### 1. `src/cli_rpg/ai_service.py`
- Add `generate_area()` method that prompts AI for 4-7 connected locations with a sub-theme
- Prompt returns JSON array of locations with internal connections defined

### 2. `src/cli_rpg/ai_world.py`
- Rename `expand_world()` -> keep as thin wrapper for backward compat
- Add `expand_area()` that generates 4-7 location cluster
- Implement area placement logic that maintains grid consistency
- Add `_close_area_border()` helper to ensure all perimeter exits are valid or frontier

### 3. `src/cli_rpg/world_grid.py`
- Add `find_unreachable_exits()` method to detect orphaned exits
- Add `get_frontier_locations()` to find locations at world border with dangling exits
- Add `validate_border_closure()` that returns True if border is closed

### 4. `src/cli_rpg/game_state.py`
- Update `move()` to call `expand_area()` instead of `expand_world()` when hitting frontier

## Implementation Steps

### Step 1: Add border validation to WorldGrid
```python
# world_grid.py
def find_unreachable_exits(self) -> list[tuple[str, str, tuple[int, int]]]:
    """Find exits pointing to empty coordinates unreachable from any frontier.
    Returns: [(location_name, direction, target_coords), ...]
    """

def validate_border_closure(self) -> bool:
    """Return True if all dangling exits are reachable from player movement."""
```

### Step 2: Add `generate_area()` to AIService
```python
# ai_service.py
def generate_area(
    self,
    theme: str,
    sub_theme_hint: str,
    entry_direction: str,
    context_locations: list[str],
    size: int = 5
) -> list[dict]:
    """Generate cluster of connected locations.
    Returns: [{"name": ..., "description": ..., "relative_coords": (dx, dy), "connections": {...}}, ...]
    """
```

### Step 3: Add `expand_area()` to ai_world.py
```python
# ai_world.py
def expand_area(
    world: dict[str, Location],
    ai_service: AIService,
    from_location: str,
    direction: str,
    theme: str,
    target_coords: tuple[int, int]
) -> dict[str, Location]:
    """Generate and place an entire area cluster at target coords."""
```

### Step 4: Update `move()` in game_state.py
- Replace `expand_world()` call with `expand_area()`

## Tests to Write

### `tests/test_area_generation.py`
1. `test_expand_area_generates_multiple_locations` - Area has 4+ locations
2. `test_expand_area_locations_are_connected` - All area locations reachable from entry
3. `test_expand_area_border_closed` - No unreachable exits after expansion
4. `test_expand_area_preserves_existing_world` - Existing locations unchanged
5. `test_expand_area_entry_connects_to_source` - Entry point connects back to source
6. `test_generate_area_returns_location_list` - AIService returns valid list

### `tests/test_world_grid.py` (additions)
7. `test_find_unreachable_exits_empty_world` - No exits in single-location world
8. `test_find_unreachable_exits_detects_orphan` - Finds exit to unreachable coord
9. `test_validate_border_closure_true_when_closed` - Valid closed border
10. `test_validate_border_closure_false_when_orphan` - Detects orphaned exit

## Verification
- Run `pytest tests/test_area_generation.py tests/test_world_grid.py -v`
- Run full suite: `pytest`
