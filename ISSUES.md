## Active Issues

_No active issues_

## Resolved Issues

### Misleading error message when trying to equip an already-equipped item
**Status**: RESOLVED

**Description**: When a user tried to run `equip <item>` on an item that was already equipped, the error message shown was "You don't have '<item>' in your inventory." This was misleading because the item was visible in the inventory display (shown with "[Weapon]" or "[Armor]" prefix).

**Fix**: Added a check in the `equip` command handler to detect if the item is already equipped as weapon or armor before returning the generic "not found" error. The new message clearly indicates the item is already equipped: "{Item Name} is already equipped."

This follows the same pattern as the `use` command fix for equipped items.

### Misleading error message when trying to 'use' an equipped item
**Status**: RESOLVED

**Description**: When a user tried to use the `use` command on an item that was currently equipped (e.g., `use Steel Spear` when Steel Spear was equipped as their weapon), the game showed the error message "You don't have 'steel spear' in your inventory." This was misleading because the user had the item - it was equipped, not missing.

**Fix**: Updated both exploration and combat `use` command handlers to check if the target item is currently equipped before returning the "not found" error. The new messages clearly indicate why the item cannot be used:
- "{Item Name} is currently equipped as your weapon and cannot be used."
- "{Item Name} is currently equipped as your armor and cannot be used."

This matches the pattern already used by `sell` and `drop` commands in the codebase.

### Unclear error message when trying to equip non-equippable items
**Status**: RESOLVED

**Description**: When a user tries to equip a consumable item (like "Life Draught" or "Healing Elixir"), the error message was simply "You can't equip Life Draught." This message didn't explain *why* the item couldn't be equipped.

**Fix**: Enhanced error messages to be more helpful:
- For consumables: "You can only equip weapons or armor. Use 'use <item>' for consumables."
- For misc items: "You can only equip weapons or armor."

This is now consistent with other helpful error messages in the game.

### TALK quest objective type
**Status**: RESOLVED

**Description**: The quest system now tracks when players talk to NPCs for TALK quest objectives.

**Fix**: Added `record_talk(npc_name)` method to `Character` class and integrated it into the `talk` command handler in `main.py`. Quest progress updates automatically when talking to target NPCs. Case-insensitive matching is supported, consistent with other quest types.

### EXPLORE quest objective type
**Status**: RESOLVED

**Description**: The EXPLORE quest objective type now tracks when players visit locations.

**Fix**: Added `record_explore(location_name)` method to `Character` class and integrated it into `GameState.move()`. Quest progress updates automatically when visiting target locations. Case-insensitive matching is supported.

### Combat quit confirmation prompt doesn't consume y/n input
**Status**: RESOLVED

**Root Cause**: The quit confirmation prompt was working correctly, but there were two issues affecting user experience:
1. Stdout buffering could cause the prompt to not display immediately before the blocking `input()` call
2. No feedback was provided when the user chose 'n' to cancel the quit

**Fix**: Added `sys.stdout.flush()` before the input() call to ensure the prompt is visible, and added a "Continuing combat..." message when the user cancels the quit action. The confirmation prompt now properly consumes the y/n input and provides clear feedback.

### `complete` command not recognized
**Status**: RESOLVED

**Root Cause**: The `complete` command was missing from the `known_commands` set in `game_state.py`'s `parse_command()` function. While the command handler existed in `main.py`, the parser was returning `("unknown", [])` because it didn't recognize `complete` as a valid command.

**Fix**: Added `"complete"` to the `known_commands` set in `game_state.py` (line 67). All 27 quest-related tests now pass, including 6 tests specifically for the `complete` command.

### AI-generated content expansion
**Status**: RESOLVED

All AI-generated content features have been implemented:
- ✅ NPC conversations (AI-generated dialogue that persists to NPC greetings)
- ✅ Monsters/enemies (AI-generated with descriptions and attack flavor text)
- ✅ Item catalogue (weapons, armor, consumables) - `AIService.generate_item()` method
- ✅ Lore and world history - `AIService.generate_lore()` method

### Map misaligned and confusing
**Status**: RESOLVED

The map alignment issue with colored markers has been fixed. The player's `@` marker now aligns correctly with column headers and other location markers. Additionally, available exits are now displayed below the map legend (e.g., "Exits: east, north").


