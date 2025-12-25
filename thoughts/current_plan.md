# Implementation Plan: Bestiary Command

**Note**: The quest log feature (`quests` and `quest <name>` commands) already exists in the codebase. This plan proposes a **bestiary** feature instead - a monster log tracking defeated enemies.

## Spec

Add a `bestiary` command that displays all enemies the player has defeated, with kill counts and enemy details. This enhances gameplay by:
- Providing a sense of progression/achievement
- Helping players remember enemy stats for combat strategy
- Complementing the existing quest system (KILL objectives)

### Command: `bestiary` (alias: `b`)
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

## Implementation Steps

### 1. Add bestiary field to Character model
**File**: `src/cli_rpg/models/character.py`
- Add `bestiary: Dict[str, dict]` field (default empty dict)
- Keys: enemy name (lowercase), Values: `{"count": int, "enemy_data": dict}`

### 2. Add record_enemy_defeat method to Character
**File**: `src/cli_rpg/models/character.py`
- Method: `record_enemy_defeat(enemy: Enemy) -> None`
- Stores enemy name, count, and first-seen stats (level, attack, defense, description)

### 3. Update Character serialization
**File**: `src/cli_rpg/models/character.py`
- Update `to_dict()` to include bestiary
- Update `from_dict()` to restore bestiary

### 4. Call record_enemy_defeat in combat victory
**File**: `src/cli_rpg/combat.py`
- In `process_enemy_death()` or equivalent, call `character.record_enemy_defeat(enemy)`

### 5. Add bestiary command handler
**File**: `src/cli_rpg/main.py`
- Add "bestiary" to `known_commands` set in `game_state.py`
- Add alias "b" -> "bestiary" in `parse_command()`
- Add command handler in `handle_exploration_command()`

### 6. Add to help text
**File**: `src/cli_rpg/main.py`
- Add `bestiary (b) - View defeated enemies` to `get_command_reference()`

## Tests

### File: `tests/test_bestiary.py`

```python
# Test Character.record_enemy_defeat()
- test_record_first_enemy_defeat: First kill stores enemy data with count=1
- test_record_repeated_enemy_defeat: Repeated kills increment count
- test_record_different_enemies: Multiple enemy types tracked separately
- test_bestiary_serialization: to_dict/from_dict preserves bestiary

# Test bestiary command
- test_bestiary_command_empty: Shows "No enemies defeated yet" when empty
- test_bestiary_command_with_kills: Shows formatted enemy list
- test_bestiary_alias: "b" works as alias for "bestiary"
```

### Integration in existing tests
- Verify combat victory calls `record_enemy_defeat`
