# Implementation Summary: `hide` Command in Combat

## What was implemented

Added a new `hide` combat command that makes the player untargetable for 1 turn. Enemies skip attacking hidden players, making it a defensive tactical option available to all classes.

### Features implemented:
- **Command**: `hide` (alias: `hd`)
- **Effect**: Applies "Hidden" status effect for 1 turn
- **Cost**: 10 stamina (same as sneak)
- **Availability**: All classes (unlike sneak which is Rogue-only)
- **Duration**: Expires after enemy turn

### Files Modified

1. **`src/cli_rpg/models/character.py`**
   - Added `is_hidden()` method to check if character has active hidden effect

2. **`src/cli_rpg/combat.py`**
   - Added `player_hide()` method that costs 10 stamina and applies hidden effect
   - Modified `enemy_turn()` to skip attacking hidden players (with proper status effect ticking and stamina regeneration)

3. **`src/cli_rpg/game_state.py`**
   - Added "hide" to `KNOWN_COMMANDS` set
   - Added "hd" alias to command aliases dict

4. **`src/cli_rpg/main.py`**
   - Wired up `hide` command handler in combat loop
   - Added "hide" to `combat_commands` set
   - Updated error messages to include "hide" option
   - Added help text for hide command

5. **`tests/test_hide.py`** (new file)
   - 13 tests covering all spec requirements

## Test Results

All 13 new tests pass:
- `test_hide_applies_hidden_effect` - Hide applies hidden status effect
- `test_hide_works_for_all_classes` (5 parametrized tests) - All classes can use hide
- `test_hide_costs_10_stamina` - Stamina cost verified
- `test_hide_fails_without_stamina` - Proper error when insufficient stamina
- `test_hidden_player_not_attacked` - Enemies skip attacking hidden player
- `test_hidden_expires_after_enemy_turn` - Hidden effect expires after 1 turn
- `test_hide_blocked_when_stunned` - Cannot hide while stunned
- `test_is_hidden_returns_true_when_hidden` - Character.is_hidden() works correctly
- `test_is_hidden_returns_false_when_not_hidden` - is_hidden() returns False when not hidden

Full test suite: **3016 passed** in 64.46s

## Technical Details

- The hidden effect uses `effect_type="hidden"` with duration 1
- When hidden, `enemy_turn()` short-circuits before enemy attacks, but still:
  - Ticks player status effects (so hidden expires)
  - Ticks enemy status effects (DoTs, etc.)
  - Regenerates player stamina
- The command follows the same pattern as sneak/bash for stun checking and stamina handling
- Help text includes `hide (hd)` in the Combat Commands section

## E2E Validation Points

1. Start combat and use `hide` command - verify "hidden" message appears
2. Verify enemy doesn't attack during their turn while hidden
3. Verify hidden effect expires after one enemy turn
4. Test with insufficient stamina (<10) - should fail with error message
5. Use `help` command during combat - verify `hide` is listed
