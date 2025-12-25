# Multi-Enemy Combat Implementation Plan

## Feature Spec
Extend combat to support 2+ enemies per encounter, allowing player to target specific foes.

**Player Experience:**
- Encounters can spawn 1-3 enemies
- `attack [enemy]` targets a specific enemy (default: first living enemy)
- `cast [enemy]` similarly allows targeting
- Combat status shows all enemies with health bars
- Victory requires defeating all enemies
- All living enemies attack player each turn

## Test Cases (tests/test_multi_enemy_combat.py)

### CombatEncounter with multiple enemies
1. `test_combat_with_multiple_enemies_init` - Combat initializes with list of enemies
2. `test_attack_targets_first_enemy_by_default` - No target = first living enemy
3. `test_attack_specific_enemy_by_name` - Can target by partial/full name
4. `test_attack_invalid_target_shows_error` - Unknown target gives helpful error listing valid targets
5. `test_all_enemies_attack_player_each_turn` - Enemy turn damages player from all living enemies
6. `test_victory_requires_all_enemies_dead` - Combat ends only when all enemies defeated
7. `test_get_status_shows_all_enemies` - Status displays all enemies with HP
8. `test_cast_targets_specific_enemy` - Cast command supports targeting
9. `test_flee_from_multiple_enemies` - Flee works (same mechanics)
10. `test_xp_and_loot_from_multiple_enemies` - Victory awards sum of all enemy XP, loot from each

### spawn_enemies (new function)
11. `test_spawn_enemies_returns_1_to_3_enemies` - Spawns appropriate count
12. `test_spawn_enemies_scales_with_level` - Enemy count increases at higher levels

## Implementation Steps

### 1. Update Enemy Model (models/enemy.py)
- No changes needed - Enemy is already a standalone dataclass

### 2. Update CombatEncounter (combat.py)
```python
class CombatEncounter:
    def __init__(self, player: Character, enemies: list[Enemy]):
        self.enemies = enemies  # Changed from single enemy
        self.enemy = enemies[0]  # Backward compat property (deprecate later)
```

**Methods to update:**
- `__init__`: Accept `enemies: list[Enemy]` (support single Enemy for backward compat)
- `start()`: Announce all enemies
- `player_attack(target: str = "")`: Target specific or first living enemy
- `player_cast(target: str = "")`: Same targeting logic
- `enemy_turn()`: All living enemies attack, return combined message
- `end_combat(victory)`: Sum XP, generate loot from each enemy
- `get_status()`: Show all enemies with HP
- Add `get_living_enemies()` -> list[Enemy]
- Add `find_enemy_by_name(name: str)` -> Optional[Enemy]

### 3. Update spawn functions (combat.py)
- Add `spawn_enemies(location_name, level, count=None)` -> list[Enemy]
- Count defaults to: level 1-3: 1-2 enemies, level 4+: 1-3 enemies
- Existing `spawn_enemy` unchanged (backward compat)

### 4. Update GameState (game_state.py)
- `trigger_encounter()`: Use `spawn_enemies()` instead of single spawn

### 5. Update Combat Command Handlers (main.py)
- `handle_combat_command()`: Pass target arg to attack/cast
- Parse `attack goblin` -> target="goblin"
- Update quest kill tracking for each defeated enemy

### 6. Update Tab Completion (completer.py)
- Add `_complete_attack(text)` for enemy targeting during combat

### 7. Update Persistence (persistence.py, game_state.py)
- `CombatEncounter.to_dict()` / `from_dict()` for multi-enemy serialization
- `GameState.to_dict()` includes active combat state

### 8. Update JSON Output (json_output.py)
- `emit_combat()`: Show all enemies with health

## File Changes Summary
| File | Changes |
|------|---------|
| combat.py | Multi-enemy CombatEncounter, spawn_enemies() |
| game_state.py | trigger_encounter uses list |
| main.py | Target parsing for attack/cast |
| completer.py | Attack target completion |
| persistence.py | Combat serialization (if saving mid-combat) |
| json_output.py | Multi-enemy combat state |
| tests/test_multi_enemy_combat.py | New test file |
| tests/test_combat.py | Update existing tests for backward compat |
