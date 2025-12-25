# Implementation Summary: Bestiary Command

## What Was Implemented

A **bestiary** feature that allows players to track all enemies they have defeated, with kill counts and enemy stats.

### New Command: `bestiary` (alias: `b`)
Displays a formatted list of defeated enemies with their stats:
```
=== Bestiary ===

Goblin Scout (x3)
  Level 2 | ATK: 8 | DEF: 3
  "A small, green-skinned creature with beady eyes"

Shadow Wolf (x1)
  Level 4 | ATK: 12 | DEF: 5
  "A spectral wolf that prowls the darkness"

Total enemies defeated: 4
```

When no enemies have been defeated:
```
=== Bestiary ===
No enemies defeated yet.
```

## Files Modified

### 1. `src/cli_rpg/models/character.py`
- Added `bestiary: Dict[str, dict]` field to Character dataclass
- Added `record_enemy_defeat(enemy: Enemy)` method to track kills
- Updated `to_dict()` to serialize bestiary
- Updated `from_dict()` to restore bestiary (with backward compatibility for old saves)

### 2. `src/cli_rpg/game_state.py`
- Added "b" → "bestiary" alias to command parsing
- Added "bestiary" to the set of known commands

### 3. `src/cli_rpg/main.py`
- Added `record_enemy_defeat()` calls in combat victory handlers (attack and cast commands)
- Added bestiary command handler to `handle_exploration_command()`
- Added "bestiary (b) - View defeated enemies" to help text

## Tests Created

### `tests/test_bestiary.py` (11 tests)

**TestRecordEnemyDefeat:**
- `test_record_first_enemy_defeat` - First kill stores enemy data with count=1
- `test_record_repeated_enemy_defeat` - Repeated kills increment count
- `test_record_different_enemies` - Multiple enemy types tracked separately

**TestBestiarySerialization:**
- `test_bestiary_serialization` - to_dict/from_dict preserves bestiary
- `test_bestiary_empty_serialization` - Empty bestiary is preserved
- `test_bestiary_backward_compatibility` - Old saves without bestiary work

**TestBestiaryCommand:**
- `test_bestiary_command_empty` - Shows "No enemies defeated yet" when empty
- `test_bestiary_command_with_kills` - Shows formatted enemy list
- `test_bestiary_alias` - "b" works as alias for "bestiary"

**TestCombatBestiaryIntegration:**
- `test_combat_victory_records_enemy` - Attack victory records enemy
- `test_cast_victory_records_enemy` - Cast victory also records enemy

## Test Results

```
tests/test_bestiary.py: 11 passed
Full test suite: 1338 passed, 1 skipped
```

## Design Decisions

1. **Key format**: Enemy names are stored as lowercase keys for case-insensitive lookup
2. **First-seen stats**: The bestiary stores the first-seen stats for each enemy type (level, attack, defense, description)
3. **Sorted output**: Enemies are displayed in alphabetical order by name
4. **Backward compatibility**: Old saves without the bestiary field default to an empty dict

## E2E Validation

To validate in-game:
1. Start a new game or load a save
2. Enter combat and defeat an enemy
3. Type `bestiary` or `b` to view the bestiary
4. Verify the defeated enemy appears with correct stats
5. Defeat the same enemy type again and verify count increments
6. Save and reload the game, verify bestiary persists
