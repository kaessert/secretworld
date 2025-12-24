## Active Issues

### Confusing error message when trying to sell equipped items
**Status**: ACTIVE

**Problem**: When a player tries to sell an item that is currently equipped, the error message "You don't have 'item name' in your inventory" is confusing and unhelpful.

**Steps to Reproduce**:
1. Start a new game and create a character
2. Fight enemies until you receive a weapon drop (e.g., "Old Dagger")
3. Use `equip Old Dagger` to equip the weapon
4. Use `inventory` to verify the item appears in the equipped slot
5. Use `talk Merchant` to open the shop
6. Use `sell Old Dagger` to attempt to sell the equipped item

**Expected Behavior**: The game should provide a clear message like "You can't sell Old Dagger because it's currently equipped. Unequip it first with 'unequip weapon'."

**Actual Behavior**: The game displays "You don't have 'old dagger' in your inventory." which is confusing because:
- The item IS visible in the inventory display (in the equipped section)
- The message doesn't explain WHY the sell failed
- The user doesn't get guidance on how to properly sell the item (unequip first)

**Impact**: Poor user experience - players may think they lost their item or that the game is bugged, when in reality they just need to unequip the item first.

---

## Resolved Issues

### Documentation inconsistency: "up" and "down" directions
**Status**: RESOLVED

**Original Problem**: The README.md documentation listed "up, down" as valid movement directions, but the grid system uses 2D coordinates only (north, south, east, west).

**Solution Implemented**:
- Removed "up, down" from the README.md `go <direction>` documentation
- README now matches the in-game help which only mentions cardinal directions

---

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
