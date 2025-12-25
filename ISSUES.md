## Active Issues

### EXPLORE and TALK quest objective types are not implemented
**Status**: ACTIVE

**Description**: The quest system defines `ObjectiveType.EXPLORE` and `ObjectiveType.TALK` enum values, and the AI configuration documents them (e.g., "explore: Visit location (target = location name, target_count = 1)"). However, there is no code that tracks when a player visits a location or talks to an NPC for these quest types.

**Steps to Reproduce**:
1. Create a quest with `objective_type=ObjectiveType.EXPLORE` and `target='Forest'`
2. Accept the quest
3. Move to the Forest location
4. Check quest progress - it remains at 0/1 despite visiting the target location

**Expected Behavior**: Quest progress should update to 1/1 when the player visits the target location (for EXPLORE) or talks to the target NPC (for TALK).

**Actual Behavior**: Quest progress stays at 0/1 forever because no code handles these objective types.

**Impact**: If AI generates quests with EXPLORE or TALK objectives, players will be stuck with uncompletable quests.

**Root Cause**: The `Character` class has `record_kill()`, `record_collection()`, and `record_drop()` methods, but no corresponding `record_explore()` or `record_talk()` methods. The `GameState.move()` and talk command handler don't call any quest tracking for these objectives.

## Resolved Issues

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


