## Active Issues

### Documentation inconsistency: "up" and "down" directions
**Status**: OPEN

**Problem**: The README.md documentation lists "up, down" as valid movement directions:
> `go <direction>` - Move in a direction (north, south, east, west, up, down)

However:
1. The in-game help only mentions "north, south, east, west" (no up/down)
2. When a player tries `go up` or `go down`, they get "You can't go that way." with no indication these directions even exist in the game

**Steps to Reproduce**:
1. Start a new game
2. Create a character
3. Type `go up` or `go down`
4. Observe: "You can't go that way." - same as any invalid direction

**Expected Behavior**: Either:
- (A) Remove "up, down" from README if they're not supported, or
- (B) Add "up, down" to the in-game help, and ideally have locations that support vertical movement

**Actual Behavior**: README promises up/down directions but they don't appear to be functional or documented in-game.

---

## Resolved Issues

### Broken navigation link from Forest to Deep Woods
**Status**: RESOLVED

**Original Problem**: When the player navigates to the Forest (by going north from Town Square), the location shows "Exits: north, south". However, attempting to go north displays an internal error message: "Destination 'Deep Woods' not found in world."

**Solution Implemented**:
- Removed dangling exits from `create_default_world()` in `world.py` that pointed to non-existent locations ("Deep Woods" and "Crystal Cavern")
- Added test `test_default_world_all_exits_have_valid_destinations` to ensure all location exits point to valid destinations in the world
- Forest now only shows "Exits: south" and Cave only shows "Exits: west"

---

### Grid-based map structure
**Status**: RESOLVED

**Original Problem**: Map should be more logically laid out instead of connecting random locations to each other. There should be a logical representation of the map under the hood like a matrix.

**Solution Implemented**:
- Created `WorldGrid` class (`src/cli_rpg/world_grid.py`) with coordinate-based storage
- Locations now have optional `coordinates: Tuple[int, int]` field
- Direction offsets ensure spatial consistency: north=(0,+1), south=(0,-1), east=(+1,0), west=(-1,0)
- Moving north then south returns to the same location (geographic consistency)
- Bidirectional connections are automatically created based on coordinates
- Backward compatible with existing saves via `from_legacy_dict()`

**Test Coverage**: 38 new tests verify grid functionality:
- 20 WorldGrid unit tests
- 8 Location coordinate tests
- 10 Integration tests for movement roundtrips and save/load
