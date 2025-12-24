# Fix "Closed Border MISUNDERSTOOD" Issue

## Problem Summary
The current implementation validates that the world border is "closed" (all exits point to existing locations via `validate_border_closure()`). However, the game design requires the **opposite**: the border should always remain **open** at least at one point so the world can expand infinitely. Players should never be trapped in a fully enclosed area with no exits pointing to unexplored coordinates.

## Current Behavior (Incorrect)
- `validate_border_closure()` returns `True` when there are **no** unreachable exits (closed border)
- `find_unreachable_exits()` is named from the perspective of "bad" exits that need fixing
- Area generation in `ai_world.py` already has code trying to ensure dangling exits, but no validation

## Desired Behavior (Correct)
- The world should **always** have at least one exit pointing to an unexplored coordinate (open border)
- This ensures players can always trigger new world generation
- The `validate_border_closure()` method is misnamed - should be something like `validate_expansion_possible()`

## Implementation Steps

### 1. Rename and Invert `WorldGrid` Validation Methods

**File: `src/cli_rpg/world_grid.py`**

- Rename `validate_border_closure()` to `has_expansion_exits()`
- Invert the logic: return `True` if there ARE unreachable exits (this is now good)
- Rename `find_unreachable_exits()` to `find_frontier_exits()` for clarity (these are the exits that enable expansion)
- Add new method `ensure_expansion_possible()` that:
  1. Checks if there's at least one frontier exit
  2. If not, adds a dangling exit to a random frontier location
  3. Returns whether the world was modified

### 2. Update Tests

**File: `tests/test_world_grid.py`**

- Rename `TestWorldGridBorderValidation` to `TestWorldGridExpansionValidation`
- Update `test_validate_border_closure_true_when_closed` -> `test_has_expansion_exits_false_when_closed`
- Update `test_validate_border_closure_false_when_orphan` -> `test_has_expansion_exits_true_when_frontier_exists`
- Add new test `test_ensure_expansion_possible_adds_exit_when_closed`
- Add new test `test_ensure_expansion_possible_noop_when_already_open`

**File: `tests/test_area_generation.py`**

- Update `test_expand_area_border_closed` to `test_expand_area_preserves_expansion_exits`
- Verify that after area generation, there's still at least one frontier exit

### 3. Call `ensure_expansion_possible()` After Area Generation

**File: `src/cli_rpg/ai_world.py`**

- At the end of `expand_area()`, create a temporary `WorldGrid` from the world dict
- Call `ensure_expansion_possible()` to guarantee at least one frontier exit
- This ensures every area generation leaves the world expandable

### 4. Update ISSUES.md

- Move "Closed Border MISUNDERSTOOD" to Resolved Issues
- Document the solution

## Code Changes

### `world_grid.py` Changes

```python
def find_frontier_exits(self) -> List[Tuple[str, str, Tuple[int, int]]]:
    """Find exits pointing to unexplored coordinates (frontier exits).

    These exits enable world expansion - when a player travels through them,
    new areas can be generated. At least one frontier exit should always exist
    to ensure the world can grow infinitely.

    Returns:
        List of tuples (location_name, direction, target_coords) for each
        exit pointing to unexplored coordinates.
    """
    # Same implementation as current find_unreachable_exits()

def has_expansion_exits(self) -> bool:
    """Check if the world has at least one exit to unexplored territory.

    Returns True if there's at least one frontier exit that can trigger
    area generation. This is the desired state - the world should always
    be expandable.

    Returns:
        True if at least one frontier exit exists, False if world is closed.
    """
    return len(self.find_frontier_exits()) > 0

def ensure_expansion_possible(self) -> bool:
    """Ensure the world has at least one frontier exit.

    If no frontier exits exist, adds a dangling exit to a random edge
    location in a random available direction.

    Returns:
        True if the world was modified, False if already had frontier exits.
    """
    if self.has_expansion_exits():
        return False

    # Find edge locations (locations with fewer than 4 neighbors)
    # Add a dangling exit to one of them
    import random
    for location in self._by_name.values():
        if location.coordinates is None:
            continue
        available_dirs = [d for d in DIRECTION_OFFSETS.keys()
                         if d not in location.connections]
        if available_dirs:
            direction = random.choice(available_dirs)
            location.add_connection(direction, f"Unexplored {direction.title()}")
            return True
    return False

# Keep old method names as aliases for backward compatibility
find_unreachable_exits = find_frontier_exits
validate_border_closure = lambda self: not self.has_expansion_exits()
```

## Test Verification

Run: `pytest tests/test_world_grid.py tests/test_area_generation.py -v`
