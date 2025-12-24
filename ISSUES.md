## Active Issues

### Broken navigation link from Forest to Deep Woods
**Status**: OPEN

**Problem**: When the player navigates to the Forest (by going north from Town Square), the location shows "Exits: north, south". However, attempting to go north displays an internal error message: "Destination 'Deep Woods' not found in world."

**Steps to Reproduce**:
1. Start a new game with any character
2. From Town Square, type `go north` to reach Forest
3. Type `look` to confirm the location shows "Exits: north, south"
4. Type `go north` to attempt navigating further north

**Expected Behavior**: Either:
- Deep Woods location should exist and the player can navigate there, OR
- The Forest should not list "north" as an available exit

**Actual Behavior**: The player sees an error message "Destination 'Deep Woods' not found in world." which looks like a bug, not a user-friendly game message.

**Impact**: This creates a confusing dead-end where users see an exit that doesn't work, and get an error message that appears to be a bug rather than a game limitation.

---

---

## Resolved Issues

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
