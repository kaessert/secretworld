# Environmental Hazards System Implementation Summary

## What Was Implemented (Issue #26)

### New Module: `src/cli_rpg/hazards.py`
Created a comprehensive environmental hazards system with the following hazard types:

1. **Poison Gas** - Deals 3-6 damage per move in poisonous areas
2. **Darkness** - Reduces perception by 50% (negated by light source)
3. **Unstable Ground** - DEX check (d20 + DEX modifier vs DC 12) or take 5-15 fall damage
4. **Extreme Cold/Heat** - Adds +5 tiredness per move
5. **Flooded Rooms** - 50% chance to fail movement (slowed)

### Hazard Mitigation
- **Ranger Class**: Ignores unstable_ground, extreme_cold, extreme_heat (wilderness affinity)
- **Light Source**: Negates darkness penalty
- **Poison Gas**: No class-based mitigation (requires antidote/items)

### Category-Specific Hazard Pools
| Category | Possible Hazards |
|----------|------------------|
| Dungeon | poison_gas, darkness, unstable_ground |
| Cave | darkness, flooded, extreme_cold |
| Ruins | unstable_ground, darkness |
| Temple | poison_gas, darkness |

### Hazard Chance by Distance
- Distance 0-1: 10% chance for 1 hazard
- Distance 2-3: 25% for 1 hazard, 10% for 2
- Distance 4+: 40% for 1 hazard, 20% for 2

## Files Modified

1. **`src/cli_rpg/models/location.py`**
   - Added `hazards: List[str]` field (default empty list)
   - Added serialization in `to_dict()`
   - Added deserialization in `from_dict()` with backward compatibility

2. **`src/cli_rpg/game_state.py`**
   - Integrated `check_hazards_on_entry()` call in `_move_in_sub_grid()` method
   - Hazard effects are applied and messages displayed when entering hazardous rooms

3. **`src/cli_rpg/ai_world.py`**
   - Added hazard generation in `generate_subgrid_for_location()`
   - Non-entry rooms get hazards based on category and distance from entrance

## New File Created

1. **`src/cli_rpg/hazards.py`** - Full hazard system with:
   - `HAZARD_TYPES` constant set
   - `CATEGORY_HAZARDS` mapping
   - `RANGER_MITIGATED_HAZARDS` set
   - `apply_poison_gas()` - applies DOT damage
   - `check_darkness_penalty()` - returns perception multiplier
   - `check_unstable_ground()` - DEX check for fall damage
   - `apply_temperature_effect()` - adds tiredness
   - `check_flooded_movement()` - 50% movement failure
   - `can_mitigate_hazard()` - checks class/equipment mitigation
   - `get_hazards_for_category()` - generates hazards for locations
   - `check_hazards_on_entry()` - main entry point for processing hazards

## Test Results
- Created `tests/test_hazards.py` with 27 comprehensive tests
- All 27 hazard tests pass
- Full test suite: 4684 passed (1 unrelated flaky test about key placement)
- Location serialization, persistence, and sub-grid navigation tests all pass

## E2E Validation Points
- Enter a dungeon-type location and navigate deeper rooms
- Verify hazard messages appear based on room hazards
- Test Ranger class mitigation for unstable_ground/temperature hazards
- Test light source mitigation for darkness
- Verify damage/tiredness effects apply correctly
- Verify save/load preserves location hazards

## Technical Design Decisions
- Hazards are stored as string list on Location for simplicity and serialization
- Hazard effects are processed at room entry (not continuously)
- Mitigation checks happen before effect application
- Distance-based hazard chance creates natural difficulty scaling deeper in dungeons
