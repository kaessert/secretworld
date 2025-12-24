# Fix Circular Map Wrapping in World Grid

## Problem
When players traverse the world, going repeatedly in one direction wraps back to previously visited locations (e.g., west → west → west returns to earlier locations like Frostbite Peak → Spectral Caverns → Frostbite Peak). This happens because AI-generated locations create bidirectional connections that form loops.

## Root Cause
The `GameState.move()` method follows existing `Location.connections` without checking if the destination coordinate is already occupied. When a location has a connection like `west: "Spectral Caverns"` that points to an already-visited location, it follows that connection instead of generating a new location at the unexplored coordinate.

## Spec
**Coordinate-based movement**: When moving in a direction, the game should:
1. Calculate the target coordinates based on current position + direction offset
2. If target coordinates are unoccupied → generate new location there
3. If target coordinates are occupied by an existing location → move there
4. Never wrap back to previously visited locations via connections that would violate coordinate consistency

**Infinite expansion**: The world should extend infinitely in all directions by generating new locations when the player reaches unexplored coordinates.

## Tests

### File: `tests/test_world_grid.py`
Add tests to verify no-wrap behavior:

```python
class TestWorldGridNoWrapping:
    """Test that world grid does not wrap circularly."""

    def test_repeated_direction_extends_world(self):
        """Going west repeatedly should not return to start."""
        grid = WorldGrid()
        loc0 = Location(name="Start", description="Origin")
        loc1 = Location(name="West1", description="First west")
        loc2 = Location(name="West2", description="Second west")
        grid.add_location(loc0, 0, 0)
        grid.add_location(loc1, -1, 0)
        grid.add_location(loc2, -2, 0)

        # Going west from West2 should find no neighbor (needs generation)
        neighbor = grid.get_neighbor(-2, 0, "west")
        assert neighbor is None  # No wrap-around

    def test_coordinates_are_consistent_after_movement(self):
        """Moving west then east should return to same coordinates."""
        grid = WorldGrid()
        start = Location(name="Start", description="Origin")
        west = Location(name="West", description="West")
        grid.add_location(start, 0, 0)
        grid.add_location(west, -1, 0)

        # West of (0,0) is (-1,0)
        assert grid.get_neighbor(0, 0, "west").coordinates == (-1, 0)
        # East of (-1,0) is (0,0)
        assert grid.get_neighbor(-1, 0, "east").coordinates == (0, 0)
```

### File: `tests/test_game_state.py`
Add integration test for movement with coordinate checking:

```python
def test_move_uses_coordinates_not_just_connections(self, tmp_path, monkeypatch):
    """Movement should check coordinates to avoid circular wrapping."""
    # Setup world with locations that have misleading connections
    character = Character("Hero", strength=10, dexterity=10, intelligence=10)

    loc_a = Location("A", "Location A", coordinates=(0, 0))
    loc_b = Location("B", "Location B", coordinates=(-1, 0))

    # B has a west connection that would loop back to A (wrong!)
    loc_a.connections = {"west": "B"}
    loc_b.connections = {"east": "A", "west": "A"}  # Bad: west should NOT point to A

    world = {"A": loc_a, "B": loc_b}
    game_state = GameState(character, world, "A")

    # Move west to B
    success, msg = game_state.move("west")
    assert success
    assert game_state.current_location == "B"

    # Move west from B - should NOT go to A (that's at 0,0, not -2,0)
    # Without AI, this should fail with "destination not found" or trigger generation
    success, msg = game_state.move("west")
    # If AI not available, move fails because coordinate (-2,0) is empty
    # The key is it should NOT follow the incorrect "west": "A" connection
```

## Implementation

### Step 1: Update `GameState.move()` to use coordinate-based logic
**File**: `src/cli_rpg/game_state.py`

Modify the move method to:
1. Get current location's coordinates
2. Calculate target coordinates
3. Check if a location exists at target coordinates in grid
4. If target occupied by different location than connection suggests → use grid's location
5. If target empty → trigger AI generation or fail

```python
def move(self, direction: str) -> tuple[bool, str]:
    current = self.get_current_location()

    # Validate direction
    valid_game_directions = {"north", "south", "east", "west"}
    if direction not in valid_game_directions:
        return (False, "Invalid direction. Use: north, south, east, or west.")

    # Get current coordinates
    if current.coordinates is None:
        # Legacy location without coordinates - fall back to connection-based movement
        # (existing behavior for backward compatibility)
        ...

    # Calculate target coordinates
    from cli_rpg.world_grid import DIRECTION_OFFSETS
    dx, dy = DIRECTION_OFFSETS[direction]
    target_coords = (current.coordinates[0] + dx, current.coordinates[1] + dy)

    # Find location at target coordinates
    target_location = self._get_location_by_coordinates(target_coords)

    if target_location is not None:
        # Location exists at target - move there
        self.current_location = target_location.name
        ...
    else:
        # No location at target - generate with AI or fail
        if self.ai_service is not None and AI_AVAILABLE:
            # Generate new location at target_coords
            ...
        else:
            return (False, "You can't go that way.")
```

### Step 2: Add coordinate lookup helper to GameState
**File**: `src/cli_rpg/game_state.py`

Add method to find location by coordinates:

```python
def _get_location_by_coordinates(self, coords: tuple[int, int]) -> Optional[Location]:
    """Find a location by its coordinates.

    Args:
        coords: (x, y) coordinate tuple

    Returns:
        Location at those coordinates, or None if not found
    """
    for location in self.world.values():
        if location.coordinates == coords:
            return location
    return None
```

### Step 3: Update `expand_world()` to accept target coordinates
**File**: `src/cli_rpg/ai_world.py`

Modify expand_world to take target coordinates and ensure new location is placed there:

```python
def expand_world(
    world: dict[str, Location],
    ai_service: AIService,
    from_location: str,
    direction: str,
    theme: str,
    target_coords: Optional[tuple[int, int]] = None  # NEW parameter
) -> dict[str, Location]:
    ...
    # Use target_coords if provided, otherwise calculate from source
    if target_coords is not None:
        new_coordinates = target_coords
    elif source_loc.coordinates is not None and direction in DIRECTION_OFFSETS:
        dx, dy = DIRECTION_OFFSETS[direction]
        new_coordinates = (source_loc.coordinates[0] + dx, source_loc.coordinates[1] + dy)
    ...
```

### Step 4: Run full test suite
```bash
pytest tests/test_world_grid.py -v
pytest tests/test_game_state.py -v -k "move"
pytest  # Full suite
```

## Summary
The fix changes movement from connection-based to coordinate-based:
- **Before**: Follow `location.connections[direction]` to find destination
- **After**: Calculate target coordinates, find/generate location at those coordinates

This ensures spatial consistency and prevents circular wrapping while maintaining backward compatibility with legacy saves without coordinates.
