# Implementation Summary: Ranger Class Abilities

## Status: Complete

Implemented Ranger class abilities (track command and wilderness bonus) to bring parity with Warrior (bash), Mage (fireball/ice_bolt/heal), and Rogue (sneak).

## What Was Implemented

### 1. Track Command (`track` / `tr`)
A new exploration command that allows Rangers to detect enemies in adjacent locations:
- **Cost**: 10 stamina per use
- **Success Rate**: Base 50% + 3% per PER point (e.g., PER 10 = 80%, PER 15 = 95%)
- **Restrictions**: Rangers only, cannot be used in combat
- **Output**: Lists detected enemy types and counts in each connected location

### 2. Wilderness Damage Bonus
Rangers receive +15% attack damage when fighting in wilderness or forest locations:
- Applied automatically during combat in `CombatEncounter.player_attack()`
- Affects only Rangers (other classes don't receive the bonus)
- Applies to "forest" and "wilderness" category locations only

## Files Created
| File | Description |
|------|-------------|
| `src/cli_rpg/ranger.py` | New module with Ranger abilities (execute_track, calculate_wilderness_bonus) |
| `tests/test_ranger.py` | TDD test suite with 12 test cases covering both features |

## Files Modified
| File | Changes |
|------|---------|
| `src/cli_rpg/game_state.py` | Added "track" to KNOWN_COMMANDS, added "tr" alias |
| `src/cli_rpg/main.py` | Added track command handler in handle_exploration_command(), updated help text |
| `src/cli_rpg/combat.py` | Added location_category param to CombatEncounter, integrated wilderness bonus |
| `src/cli_rpg/hallucinations.py` | Updated CombatEncounter call with location_category |
| `src/cli_rpg/world_events.py` | Updated CombatEncounter call with location_category |
| `src/cli_rpg/random_encounters.py` | Updated CombatEncounter call with location_category |
| `src/cli_rpg/shadow_creature.py` | Updated CombatEncounter call with location_category |

## Test Results
All tests pass:
- **Ranger tests**: 12/12 passed
- **Full test suite**: 2919/2919 passed

## Constants Defined in ranger.py
```python
TRACK_STAMINA_COST = 10
TRACK_BASE_CHANCE = 50
TRACK_PER_BONUS = 3
WILDERNESS_DAMAGE_BONUS = 0.15
WILDERNESS_CATEGORIES = {"forest", "wilderness"}
```

## E2E Tests Should Validate
1. Create a Ranger character
2. Use `track` command to detect enemies in adjacent locations
3. Enter a forest or wilderness area and engage in combat
4. Verify damage output is 15% higher than with other classes in wilderness/forest
5. Verify non-Rangers cannot use track command
6. Verify track fails with insufficient stamina (<10)

## Design Notes
- The `location_category` is now passed to all CombatEncounter instances for consistency
- The wilderness bonus is applied after companion bonus but before critical hit calculation
- Track command uses a simulated enemy detection based on location category
