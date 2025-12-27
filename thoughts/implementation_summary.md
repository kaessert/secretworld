# Issue 21: Location-Specific Random Encounters - Implementation Summary

## What Was Implemented

### New Module: `src/cli_rpg/encounter_tables.py`

Created a new module with category-specific encounter configuration:

1. **CATEGORY_ENEMIES** - Enemy pools by location type:
   - `dungeon`: Skeleton Warrior, Zombie, Stone Construct, Cultist, Bone Golem, Dark Acolyte
   - `cave`: Giant Spider, Cave Bear, Giant Bat, Goblin, Troll, Cave Beetle
   - `ruins`: Restless Ghost, Stone Golem, Treasure Hunter, Phantom, Ancient Guardian, Ruin Lurker
   - `forest`: Wolf, Bandit, Wild Boar, Dryad, Forest Spirit, Giant Spider
   - `temple`: Dark Priest, Animated Statue, Temple Guardian, Cultist Zealot, Stone Sentinel, Shadow Monk

2. **CATEGORY_ENCOUNTER_RATES** - Variable encounter rates:
   - `dungeon`: 0.25 (higher danger)
   - `cave`, `ruins`, `temple`: 0.20
   - `forest`: 0.15 (default)
   - `town`, `village`, `city`: 0.05 (safe zones)

3. **CATEGORY_MERCHANT_ITEMS** - Location-appropriate merchant inventories:
   - `dungeon`: healing_potion, antidote, torch
   - `cave`: torch, rope, healing_potion
   - `ruins`: lockpick, healing_potion, antidote
   - `temple`: holy_water, healing_potion, blessed_charm
   - `forest`: rations, healing_potion, rope

4. **Helper Functions**:
   - `get_enemies_for_category(category)` - Returns enemy list or DEFAULT_ENEMIES
   - `get_encounter_rate(category)` - Returns rate or DEFAULT_ENCOUNTER_RATE (0.15)
   - `get_merchant_items(category)` - Returns item templates or DEFAULT_MERCHANT_ITEMS

### Modified: `src/cli_rpg/random_encounters.py`

- Added import of `get_encounter_rate` and `get_merchant_items` from encounter_tables
- Updated `check_for_random_encounter()` to use category-specific encounter rate instead of global `RANDOM_ENCOUNTER_CHANCE`
- Logic: `encounter_rate = get_encounter_rate(location.category) if location.category else RANDOM_ENCOUNTER_CHANCE`

### New Tests: `tests/test_encounter_tables.py`

18 tests covering:
- Category enemy table existence and content
- Minimum enemy counts per category
- Category encounter rate configuration
- Safe zone lower rates
- Merchant item templates
- Helper function behavior and fallbacks

### Extended Tests: `tests/test_random_encounters.py`

4 new integration tests in `TestCategorySpecificEncounters` class:
- `test_encounter_rate_uses_category` - Verifies dungeon rate > forest rate
- `test_dungeon_triggers_more_encounters` - Verifies rate values
- `test_check_for_random_encounter_uses_category_rate` - Verifies category rate is used
- `test_no_encounter_when_roll_exceeds_category_rate` - Verifies rate comparison logic

## Test Results

- **encounter_tables tests**: 18 passed
- **random_encounters tests**: 54 passed (including 4 new)
- **Full test suite**: 4550 passed

## E2E Validation

To validate in-game:
1. Enter a dungeon location and move around - should see encounters ~25% of moves
2. Move in forest areas - should see encounters ~15% of moves
3. Move in town/village - should see encounters ~5% of moves
4. Verify hostile encounter enemies match the location category

## Design Decisions

1. **Fallback behavior**: Unknown categories use `DEFAULT_ENCOUNTER_RATE` (0.15) and `DEFAULT_ENEMIES` for graceful degradation
2. **Category check**: Uses `location.category` attribute; falls back to global rate if category is None
3. **Merchant items**: Stored as string templates for future integration with item generation system
4. **Enemy tables separate from combat.py**: Kept `CATEGORY_ENEMIES` in encounter_tables.py as specified, existing `ENEMY_TEMPLATES` in combat.py remains for terrain-based spawns
