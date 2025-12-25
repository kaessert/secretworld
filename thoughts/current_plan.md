# Implementation Plan: `rest` Command

## Spec

Add a `rest` command that allows players to heal outside of combat without requiring potions. The command:
- Available only during exploration (not during combat)
- Heals 25% of max health (partial recovery, not full restore like inns)
- Requires alias `r` for quick access
- Displays message showing health restored
- Cannot rest if already at full health

## Test Plan

Create `tests/test_rest_command.py`:

1. **test_rest_heals_partial_health** - Rest heals 25% of max HP
2. **test_rest_at_full_health_fails** - Returns error message when health is already full
3. **test_rest_caps_at_max_health** - Healing doesn't exceed max_health
4. **test_rest_alias_r** - The `r` shorthand works for rest
5. **test_rest_blocked_during_combat** - Rest command unavailable in combat
6. **test_rest_displays_heal_amount** - Message shows amount healed

## Implementation Steps

### 1. Add `rest` to known commands and aliases
**File:** `src/cli_rpg/game_state.py`
- Add `"r": "rest"` to aliases dict (line 55)
- Add `"rest"` to `known_commands` set (line 66)

### 2. Implement `rest` command handler
**File:** `src/cli_rpg/main.py`
- Add handling in `handle_exploration_command()` for `command == "rest"` (after `elif command == "lore"`, around line 817)
- Calculate heal amount: `max(1, game_state.current_character.max_health // 4)`
- Check if already at full health (return error)
- Call `game_state.current_character.heal(heal_amount)`
- Return message with amount healed

### 3. Update help text
**File:** `src/cli_rpg/main.py`
- Add `"  rest (r)           - Rest to recover health (25% of max HP)"` to Exploration Commands in `get_command_reference()` (around line 42)

### 4. Block rest during combat
**File:** `src/cli_rpg/main.py`
- Add `"rest"` to blocked commands check in `handle_combat_command()` (line 819, add to the list with attack/defend/flee)
