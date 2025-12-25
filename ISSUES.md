## Active Issues

### Combat quit confirmation prompt doesn't consume y/n input
**Status**: OPEN

**Description**: When a player types `quit` during combat, the warning prompt "Quit without saving? (y/n):" is displayed, but the code does not actually wait for and consume the y/n response. Instead, combat continues immediately and the user's next input (intended to be 'y' or 'n' for the confirmation) is treated as a combat command.

**Steps to Reproduce**:
1. Start a new game and create a character
2. Move around until a combat encounter is triggered (e.g., `go east` repeatedly)
3. During combat, type `quit`
4. Type `n` (intending to cancel the quit and continue combat)
5. Observe that `n` is not consumed as the confirmation response; combat displays status again and 'n' is silently ignored or treated as invalid command

**Expected Behavior**:
- After typing `quit`, the prompt should wait for and consume either 'y' or 'n'
- If 'n', combat should continue with a clear message like "Continuing combat..."
- If 'y', player should return to main menu

**Actual Behavior**:
- The prompt displays but immediately continues to the combat loop
- The 'n' input is treated as a combat command (ignored as invalid)
- User has to type `quit` again and then 'y' to actually quit

**Impact**: Confusing user experience - players may think their input was acknowledged when it wasn't

## Resolved Issues

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


