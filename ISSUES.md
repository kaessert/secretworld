## Active Issues

### Map should always show the user in the center and could show two fields around the user
**Status**: ACTIVE

=== MAP ===
    -2 -1  0
 1   S  F  E
 0      C  @


### Support Anthropic API Key
**Status**: ACTIVE

Also support Anthropic next to OpenAI

###  High prio: Generate whole areas
**Status**: ACTIVE

instead of generating just the next exit, we should always generate whole areas which should cover different topics
there should be a method of checking if the world border is completely closed, there might be still a situation where
all exits are visited and no way of getting to a tile whih triggers regeneration, THIS SHOULD BE AVOIDED in any case

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

### Cannot use health potions during combat when they are needed most
**Status**: RESOLVED

**Original Problem**: Players could not use the `use <item>` command during combat, which meant health potions could not be used when they were most needed - during combat when HP is low. The game displayed: `"Can't do that during combat! Use: attack, defend, cast, flee, status, help, or quit"`

**Solution Implemented**:
- Added `use` command handler in `handle_combat_command()` in `main.py`
- Command validates item exists, delegates to `Character.use_item()` for consumption
- Using an item counts as the player's turn, triggering enemy retaliation
- Failed item usage (wrong item type, full health, etc.) does NOT trigger enemy turn
- Updated help text to list `use <item>` in Combat Commands section
- Added 6 new tests in `tests/test_main_combat_integration.py` covering various use cases

---

### Help command is not self-documenting - 'help' not listed in its own output
**Status**: RESOLVED

**Original Problem**: The `help` command displays a list of all available commands, but the `help` command itself is not listed in that output. This meant users had no documented way to rediscover the `help` command if they forgot about it.

**Solution Implemented**:
- Added `help` command to the `get_command_reference()` output in `main.py`
- Placed after `map` and before `save` in the exploration commands section
- Added test `test_get_command_reference_includes_help_command()` to verify the fix

---

### CRITICAL: Cannot load saved games after leveling up - stat validation breaks saved games
**Status**: RESOLVED

**Original Problem**: When players level up in combat, their stats increase beyond the initial 1-20 character creation limit. However, the save/load validation incorrectly enforced this 1-20 limit when loading saved games, causing all saves of leveled-up characters to fail to load with error: "strength must be at most 20"

**Solution Implemented**:
- Modified `Character.from_dict()` to handle stats above 20 from level-ups
- Stats are temporarily capped to pass initial `__post_init__()` validation, then restored to actual values
- Derived stats (`max_health`, `constitution`) are recalculated from actual strength after restoration
- The 1-20 limit now correctly applies only to character creation, not to loading saved games
- Added tests in `test_character_leveling.py` and updated `test_persistence.py`

---

### REGRESSION: Help command not working during gameplay
**Status**: RESOLVED

**Original Problem**: The `help` command was documented in README.md and shown in error messages, but it returned "Unknown command" when typed during gameplay. While `handle_exploration_command()` and `handle_combat_command()` had handlers for the `help` command, the `parse_command()` function did not include `"help"` in its `known_commands` set, causing it to return `("unknown", [])` before the handlers could process it.

**Solution Implemented**:
- Added `"help"` to the `known_commands` set in `parse_command()` function in `game_state.py`
- Added `test_parse_command_help()` test to verify the fix

---

### No help command to view command reference during gameplay
**Status**: RESOLVED

**Original Problem**: The detailed command reference (with descriptions) was only shown once at the start of a new adventure. There was no `help` command to view it again during gameplay.

**Solution Implemented**:
- Created `get_command_reference()` function in `main.py` that returns the formatted command reference
- Added `help` command handler to `handle_exploration_command()` for use during exploration
- Added `help` command handler to `handle_combat_command()` for use during combat
- Refactored welcome messages in `start_game()` and game load to use `get_command_reference()`
- Updated unknown command error messages to suggest `help` command
- Added 8 new tests in `test_main_help_command.py`

---

### In-game help message still mentions "up, down" as valid directions
**Status**: RESOLVED

**Original Problem**: When a user types `go` without specifying a direction, the error message says "Go where? Specify a direction (north, south, east, west, up, down)". However, "up" and "down" are not valid directions in the 2D grid system.

**Solution Implemented**:
- Updated the error message in `main.py` line 271 to only list valid directions: "Go where? Specify a direction (north, south, east, west)"
- This now matches the README.md documentation which was previously corrected

---

### Users requested a map
**Status**: RESOLVED

**Original Problem**: There should be a map command displaying a map.

**Solution Implemented**:
- Created `map_renderer.py` with `render_map()` function
- Added `map` command to exploration commands
- Map displays ASCII grid with coordinate axes
- Current location marked with `@`, other locations with first letter abbreviation
- Includes legend mapping symbols to location names
- Gracefully handles legacy saves without coordinates (shows "No map available" message)
- Map command blocked during combat

---

### Cannot quit or exit the game during combat
**Status**: RESOLVED

**Original Problem**: During combat, the player cannot use the `quit` command to exit the game. All commands except `attack`, `defend`, `cast`, `flee`, and `status` are blocked with the message: "✗ Can't do that during combat! Use: attack, defend, cast, flee, or status"

**Solution Implemented**:
- Added `quit` command handler to `handle_combat_command()` in `main.py`
- Shows a warning that saving is disabled during combat and combat progress will be lost
- User can confirm with 'y' to quit without saving, or 'n' to cancel and return to combat
- Updated `handle_combat_command()` return type to match `handle_exploration_command()` signature
- Added tests for quit command during combat behavior

**Note**: This behavior was later refined to fix the save exploit (see "Inconsistent save behavior during combat" below).

---

### Inconsistent save behavior during combat allows exploiting quit to escape fights
**Status**: RESOLVED

**Original Problem**: The game had inconsistent save behavior during combat:
1. Using the `save` command during combat correctly blocked with: `✗ Can't do that during combat!`
2. BUT using `quit` during combat and answering 'y' to "Save before quitting?" successfully saved the game
3. When this save was loaded, the combat encounter was lost - the enemy disappeared

This allowed players to exploit the system to escape losing fights by quitting, saving, and reloading.

**Solution Implemented**:
- Changed quit prompt during combat from "Save before quitting?" to "Quit without saving?"
- Removed the save functionality during combat quit (matching `save` command behavior)
- Added explicit warning that saving is disabled during combat and combat progress will be lost
- Answering 'n' now cancels the quit and returns to combat
- Updated tests to verify the new behavior

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

---

### CRITICAL: AI generation failures silently falling back to default world
**Status**: RESOLVED

**Original Problem**: When AI generation failed (invalid API key, network issues, etc.), the game silently fell back to the default world without informing the user. This made debugging difficult and users were unaware that they weren't getting AI-generated content.

**Solution Implemented**:
- Added `is_ai_strict_mode()` function in `config.py` that reads `CLI_RPG_REQUIRE_AI` environment variable
- Strict mode is enabled by default (when env var is unset or "true")
- In strict mode, AI generation failures prompt the user with three options:
  1. Retry AI generation
  2. Use default world (explicit fallback)
  3. Return to main menu
- Added `strict` parameter to `create_world()` and `start_game()` functions
- Set `CLI_RPG_REQUIRE_AI=false` to restore silent fallback behavior for backward compatibility

**Test Coverage**: 9 new tests added:
- 6 tests in `tests/test_config.py` for `is_ai_strict_mode()`
- 3 tests in `tests/test_world.py` for strict mode behavior
