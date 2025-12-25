## Active Issues

### Unclear error message when trying to equip non-equippable items
**Status**: ACTIVE

**Description**: When a user tries to equip a consumable item (like "Life Draught" or "Healing Elixir"), the error message is simply "You can't equip Life Draught." This message doesn't explain *why* the item can't be equipped, leaving users confused about whether the item is broken, the command syntax is wrong, or something else is happening.

**Steps to Reproduce**:
1. Load a game with a consumable item in inventory (e.g., Health Potion, Life Draught)
2. Type `equip Life Draught` (or any consumable name)
3. Observe error message: "You can't equip Life Draught."

**Expected Behavior**: The error message should explain that only weapons and armor can be equipped, and suggest using the `use` command for consumables. For example: "You can only equip weapons or armor. Use 'use Life Draught' for consumables."

**Actual Behavior**: Generic "You can't equip [item name]." message with no explanation.

**Comparison**: Other error messages in the game are more helpful:
- `complete` without NPC → "You need to talk to an NPC first to turn in a quest."
- `unequip helmet` → "You can only unequip 'weapon' or 'armor'."
- `use` without args → "Use what? Specify an item name."

The `equip` error message is inconsistent with these more detailed messages.

## Resolved Issues

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


