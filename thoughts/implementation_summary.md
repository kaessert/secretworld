# Implementation Summary: Quest Commands

## What Was Implemented

Quest viewing commands that expose the existing `models/quest.py` Quest model to users:

### Commands Added
- `quests` (alias `q`) - View quest journal with all active/completed quests
- `quest <name>` - View details of a specific quest (partial match, case-insensitive)

## Files Modified

### 1. `src/cli_rpg/models/character.py`
- Added `quests: List["Quest"] = field(default_factory=list)` attribute
- Updated `to_dict()` to serialize quests list
- Updated `from_dict()` to deserialize quests (with backward compatibility for saves without quests)

### 2. `src/cli_rpg/game_state.py`
- Added `"q": "quests"` to shorthand aliases dict
- Added `"quests"` and `"quest"` to `known_commands` set

### 3. `src/cli_rpg/main.py`
- Added `quests` command handler in `handle_exploration_command()`:
  - Shows empty message if no quests
  - Lists active quests with progress (e.g., "Kill Goblins [2/5]")
  - Shows completed quests in separate section
- Added `quest <name>` command handler:
  - Finds quest by partial name match (case-insensitive)
  - Displays full details: name, status, description, objective type, target, progress
- Updated `get_command_reference()` with quest commands help text

### 4. `tests/test_quest_commands.py` (new file)
- 13 tests covering:
  - `parse_command` recognition of quests/quest commands
  - Shorthand expansion (`q` → `quests`)
  - Empty quest journal display
  - Active quest listing with progress
  - Completed quest display
  - Quest detail view with all fields
  - Partial name matching
  - Error handling for unknown quests
  - Combat blocking (quests/quest commands blocked during combat via existing handler)

## Test Results

All 766 tests pass (13 new + 753 existing):
```
======================== 766 passed, 1 skipped in 6.76s ========================
```

## Design Decisions

1. **Partial name matching**: Quest names can be found with partial matches (e.g., "kill" finds "Kill Goblins")
2. **Case-insensitive**: Both user input and quest names compared in lowercase
3. **Combat blocking**: Quest commands correctly return error during combat (handled by existing catch-all in `handle_combat_command`)
4. **Backward compatibility**: Old save files without quests field work correctly (defaults to empty list)

## E2E Validation Checklist

- [ ] Start new game, type `quests` → should show "No active quests"
- [ ] Start new game, type `q` → should expand to `quests` and show "No active quests"
- [ ] Start new game, type `quest something` → should show "No quest found"
- [ ] Type `help` → should show quests/quest commands in help text
- [ ] Enter combat, type `quests` → should show "Can't do that during combat"

## Scope Notes

This is Phase 1 - viewing only. Future work includes:
- Quest acquisition from NPCs (talk command integration)
- Quest progress tracking from combat (kill objectives)
- Quest progress from exploration (explore objectives)
- Quest rewards on completion
