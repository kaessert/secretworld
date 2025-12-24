## Active Issues

### Users requested a map

There should be a map command displaying a map

---

### Shop buy command requires exact item name - misleading error message
**Status**: ACTIVE

**Problem**: When using the `buy <item>` command in a shop, users must type the EXACT full item name. Partial name matching does not work, and the error message is misleading.

**Steps to Reproduce**:
1. Create a new character and start the game
2. Use `talk merchant` to open a shop
3. Use `shop` to see the inventory (shows: "Health Potion", "Iron Sword", "Leather Armor")
4. Try `buy sword`

**Expected Behavior**: Either:
- The command should recognize "sword" and buy "Iron Sword", OR
- The error message should say something like: "Did you mean 'Iron Sword'? Please type the full item name."

**Actual Behavior**: The game shows: `The shop doesn't have 'sword'.`

This is misleading because:
- The shop DOES have a sword (Iron Sword)
- Users naturally try abbreviated names (sword, potion, armor)
- The same confusing behavior occurs with: `buy iron`, `buy potion`, `buy health`, `buy armor`, `buy leather`

**Note**: The game DOES support case-insensitive matching (`buy iron sword` works correctly), but not partial name matching.

---

## Resolved Issues

### Cannot quit or exit the game during combat
**Status**: RESOLVED

**Original Problem**: During combat, the player cannot use the `quit` command to exit the game. All commands except `attack`, `defend`, `cast`, `flee`, and `status` are blocked with the message: "✗ Can't do that during combat! Use: attack, defend, cast, flee, or status"

**Solution Implemented**:
- Added `quit` command handler to `handle_combat_command()` in `main.py`
- Shows a warning about being in combat and prompts user to save before quitting
- If user confirms with 'y', saves the game before exiting to main menu
- Updated `handle_combat_command()` return type to match `handle_exploration_command()` signature
- Added tests for quit command during combat behavior

---

### Unknown command error message is incomplete
**Status**: RESOLVED

**Original Problem**: When a user enters an unknown command during exploration, the error message doesn't list all available commands. Specifically, it's missing `talk`, `shop`, `buy`, and `sell`.

**Solution Implemented**:
- Updated the unknown command error message in `main.py` to include all available commands
- Now displays: `'look', 'go', 'talk', 'shop', 'buy', 'sell', 'status', 'inventory', 'equip', 'unequip', 'use', 'save', or 'quit'`
- Both instances of the error message (lines 420 and 423) were updated

---

### Health potions can be wasted when at full health
**Status**: RESOLVED

**Original Problem**: When a player uses a Health Potion while at full health, the potion is consumed but heals 0 HP. The game shows the message "You used Health Potion and healed 0 health!" and considers this a successful action.

**Solution Implemented**:
- Added a check in `Character.use_item()` to verify the player is not at full health before consuming a healing item
- Returns `(False, "You're already at full health!")` when attempting to use a healing potion at full health
- The potion remains in the inventory when rejected
- Added `test_use_health_potion_at_full_health` test to verify the behavior

---

### Confusing error message when trying to sell equipped items
**Status**: RESOLVED

**Original Problem**: When a player tries to sell an item that is currently equipped, the error message "You don't have 'item name' in your inventory" is confusing and unhelpful.

**Solution Implemented**:
- Added check in `main.py` sell command handler to detect when item is equipped
- Now displays helpful message: "You can't sell [Item] because it's currently equipped. Unequip it first with 'unequip weapon'." (or 'unequip armor' for armor items)
- Added tests `test_sell_equipped_weapon_shows_helpful_message` and `test_sell_equipped_armor_shows_helpful_message`

---

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
