# Multi-Enemy Combat Implementation Summary

## What Was Implemented

### Core Features
- **Multi-enemy encounters**: Combat can now spawn and handle 1-3 enemies per encounter
- **Target-based attacks**: Players can target specific enemies with `attack [enemy]` or `cast [enemy]`
- **Default targeting**: When no target specified, attacks/spells hit the first living enemy
- **All enemies attack**: Each living enemy attacks the player on the enemy turn
- **Victory condition**: Combat ends only when ALL enemies are defeated
- **Multi-enemy rewards**: XP is summed from all enemies, loot rolls for each enemy

### Files Modified

1. **src/cli_rpg/combat.py**
   - `CombatEncounter.__init__()`: Now accepts `enemies: list[Enemy]` or single `enemy: Enemy` (backward compatible)
   - `CombatEncounter.enemy` property: Returns first enemy for backward compatibility
   - `CombatEncounter.get_living_enemies()`: New method returning alive enemies
   - `CombatEncounter.find_enemy_by_name()`: New method for partial/full name matching (case-insensitive)
   - `CombatEncounter._get_target()`: Private method for target resolution with error messaging
   - `CombatEncounter.player_attack(target="")`: Updated to accept target parameter
   - `CombatEncounter.player_cast(target="")`: Updated to accept target parameter
   - `CombatEncounter.enemy_turn()`: Now loops through all living enemies, each attacks
   - `CombatEncounter.start()`: Announces all enemies when multiple
   - `CombatEncounter.end_combat()`: Sums XP from all enemies, rolls loot for each
   - `CombatEncounter.get_status()`: Shows all enemies with HP status
   - `spawn_enemies()`: New function spawning 1-2 enemies (level 1-3) or 1-3 (level 4+)

2. **src/cli_rpg/game_state.py**
   - `trigger_encounter()`: Uses `spawn_enemies()` for non-AI spawns, wraps AI enemy in list

3. **src/cli_rpg/main.py**
   - `handle_combat_command()`: Passes target arg from `attack [target]` and `cast [target]`
   - Records bestiary kills and quest progress for each enemy on victory
   - Help text updated to show `[target]` argument

4. **tests/test_multi_enemy_combat.py** (New file, 24 tests)
   - Tests for multi-enemy initialization
   - Tests for attack/cast targeting (default, by name, partial name, invalid target)
   - Tests for all-enemies-attack behavior
   - Tests for victory requiring all enemies dead
   - Tests for status display showing all enemies
   - Tests for spawn_enemies function

## Test Results
- All 1558 tests pass
- 24 new tests added for multi-enemy combat
- 22 existing combat tests pass (backward compatibility verified)

## Design Decisions

1. **Backward Compatibility**: Legacy code using `CombatEncounter(player, enemy)` continues to work. The constructor detects if a single Enemy is passed and wraps it in a list.

2. **Target Matching**: Uses case-insensitive partial name matching. `attack gob` targets "Goblin".

3. **Invalid Target Handling**: Returns helpful error message listing valid targets, doesn't consume the player's turn.

4. **AI Integration**: When AI service is available, currently spawns single AI enemy (wrapped in list). Multi-AI spawning could be added later.

5. **Defensive Stance**: Applies damage reduction to ALL enemy attacks in the turn, then resets.

## E2E Test Validation Points

- Entering combat with multiple enemies shows all enemy names
- `attack orc` targets specific enemy when multiple present
- `attack` with no target hits first living enemy
- `status` shows all enemies with their HP
- Defeating one enemy doesn't end combat until all are dead
- Victory message shows all defeated enemies
- XP reward is sum of all enemy rewards
