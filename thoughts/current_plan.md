# Implementation Plan: Fix "World not truly infinite" bug

## Problem Summary

Players can fully explore the world and hit boundaries despite it being advertised as infinite. The core issue is that:
1. When a player moves in a direction with no connection, they get "You can't go that way"
2. All connections lead to existing locations (especially without AI)
3. No new locations are generated on demand when exploring unexplored directions

## Root Cause Analysis

Looking at `game_state.py` `move()` method (lines 254-373):
- Line 284: If no connection exists in a direction, returns "You can't go that way"
- Line 298-322: If connection exists but target coordinates are empty, only tries expansion with AI service
- Line 321-322: Without AI service, returns "You can't go that way"

The issue: The world only expands when there's already a dangling connection AND AI is available. Without AI, or when all connections are resolved, the world becomes closed.

## Solution

### Core Fix
Modify the movement logic to:
1. **Always allow movement in valid cardinal directions** (north/south/east/west)
2. **Generate new locations on-demand** when moving to unexplored coordinates
3. **Provide fallback generation** when AI is unavailable

### Implementation Steps

#### Step 1: Add fallback location generation to `world.py`

Add a new function `generate_fallback_location()` that creates template-based locations without AI:

```python
def generate_fallback_location(
    direction: str,
    source_location: Location,
    target_coords: tuple[int, int]
) -> Location:
    """Generate a fallback location when AI is unavailable."""
    # Use direction and source context to pick appropriate template
    # Similar to how spawn_enemies works without AI
```

#### Step 2: Update `game_state.py` `move()` method

Modify the coordinate-based movement logic (lines 282-322):

1. **Remove the exit-required check** (line 284-285) for cardinal directions
2. **Always calculate target coordinates** for valid directions
3. **If target location doesn't exist**: Generate one (AI or fallback)
4. **Add the new location** to the world with proper bidirectional connections

Key changes:
- Line 284: Remove `if not current.has_connection(direction)` check for cardinal directions
- Line 298-322: Expand to include fallback generation when AI unavailable

#### Step 3: Ensure new locations have frontier exits

When generating new locations (in `ai_world.py` or fallback):
- Always add at least one dangling connection pointing to unexplored territory
- This is already partially implemented in `expand_world()` lines 420-429

### Files to Modify

1. **`src/cli_rpg/world.py`**: Add `generate_fallback_location()` function
2. **`src/cli_rpg/game_state.py`**: Update `move()` to always allow expansion in valid directions
3. **`src/cli_rpg/world_grid.py`**: No changes needed (already has `ensure_expansion_possible()`)

### Test Plan

#### New Tests to Add

1. **`test_infinite_world_without_ai.py`**:
   - Test that moving in any cardinal direction always succeeds (creates location if needed)
   - Test that newly created locations have frontier exits
   - Test that returning to previous locations works correctly
   - Test that the world never becomes "closed" (always has expansion options)

2. **Update existing tests**:
   - `test_initial_world_dead_end_prevention.py`: Verify starting location behavior
   - `test_e2e_world_expansion.py`: Add test for fallback generation

#### Test Cases

```python
def test_move_to_unexplored_direction_creates_location():
    """Moving in a valid direction with no exit creates a new location."""
    # Create minimal world with no exits in some directions
    # Move in an unexplored direction
    # Assert: move succeeds and new location exists

def test_world_never_becomes_closed():
    """World always has at least one frontier exit after expansion."""
    # Create world, explore multiple times
    # After each move, verify has_expansion_exits() returns True

def test_fallback_location_has_proper_connections():
    """Fallback-generated locations have bidirectional connections."""
    # Create world without AI
    # Move to create fallback location
    # Assert: proper connections in both directions
```

### Implementation Order

1. Add `generate_fallback_location()` to `world.py`
2. Write tests for the new function
3. Update `move()` in `game_state.py` to use fallback
4. Write integration tests
5. Run full test suite to ensure no regressions
