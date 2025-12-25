## Active Issues

### Misleading error message when trying to 'use' an equipped item
**Status**: ACTIVE

**Description**: When a user tries to use the `use` command on an item that is currently equipped (e.g., `use Steel Spear` when Steel Spear is equipped as their weapon), the game shows the error message "You don't have 'steel spear' in your inventory." This message is misleading because the user DOES have the item - it's equipped, not missing.

**Steps to Reproduce**:
1. Load a character with a weapon (e.g., Steel Spear) in their inventory
2. Use `equip Steel Spear` to equip the weapon
3. Verify with `i` (inventory) that the weapon is shown as `[Weapon] Steel Spear`
4. Try `use Steel Spear`
5. Observe the message: "You don't have 'steel spear' in your inventory."

**Expected Behavior**: The error message should indicate that the item is equipped, not missing. For example: "Steel Spear is currently equipped as your weapon and cannot be used." or "You can't use Steel Spear - it's equipped as your weapon. Use 'unequip weapon' first."

**Actual Behavior**: The message "You don't have 'steel spear' in your inventory." implies the item doesn't exist, when it's actually just equipped.

**Impact**: Minor UX issue. Could confuse users who know they have the item but see a message suggesting it's missing.

## Resolved Issues

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


