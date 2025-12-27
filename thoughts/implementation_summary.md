# Implementation Summary: Terrain-Aware Random Encounters

## What Was Implemented

Made random encounters respect the current location's terrain type (from WFC generation), with category as fallback.

### Changes Made

#### 1. Extended ENEMY_TEMPLATES (combat.py, line ~33)
Added enemy templates for new terrain types:
- `plains`: Wild Dog, Highwayman, Giant Rat, Roaming Boar
- `desert`: Scorpion, Sand Serpent, Vulture, Dust Bandit
- `swamp`: Swamp Leech, Marsh Troll, Bog Hag, Giant Frog
- `hills`: Hill Giant, Bandit Scout, Wild Goat, Hawk
- `beach`: Giant Crab, Sea Serpent, Coastal Raider, Seagull Swarm
- `foothills`: Mountain Cat, Rock Troll, Foothill Bandit, Wild Ram

#### 2. Updated spawn_enemy function (combat.py, line ~2163)
- Added `terrain_type: Optional[str] = None` parameter
- Updated priority logic: `terrain_type > location_category > name matching`
- Added terrain type mappings in `category_mappings` dict
- Added water->beach fallback for edge cases

#### 3. Updated _handle_hostile_encounter (random_encounters.py, line ~280)
- Now passes `terrain_type=location.terrain` to `spawn_enemy()`

### Files Modified
- `src/cli_rpg/combat.py` - Extended ENEMY_TEMPLATES, updated spawn_enemy signature and logic
- `src/cli_rpg/random_encounters.py` - Pass terrain to spawn_enemy
- `tests/test_random_encounters.py` - Added TestTerrainAwareEncounters class with 4 tests, updated existing mock

## Test Results

All tests pass:
- `tests/test_random_encounters.py`: 32 passed
- `tests/test_combat.py`: 59 passed

### New Tests Added (TestTerrainAwareEncounters)
1. `test_hostile_encounter_uses_terrain_for_enemy` - Verifies terrain_type is passed to spawn_enemy
2. `test_terrain_takes_priority_over_category` - Verifies terrain > category priority
3. `test_category_used_when_no_terrain` - Verifies category fallback works
4. `test_new_terrain_types_have_templates` - Verifies all new terrains have enemy lists

## E2E Validation
- Travel to locations with WFC-generated terrain and encounter hostiles
- Verify enemy types match the terrain (e.g., Scorpion in desert, Giant Crab on beach)
- Verify fallback to category still works for non-terrain locations
