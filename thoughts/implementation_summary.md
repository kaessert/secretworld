# Issue 18: AI-Generated Hidden Secrets Implementation Summary

## What Was Implemented

### 1. Secret Generation Constants and Function (`src/cli_rpg/ai_world.py`)

**Added constants:**
- `SECRET_CATEGORIES`: frozenset of categories that should have secrets (`dungeon`, `cave`, `ruins`, `temple`, `forest`)
- `SECRET_TEMPLATES`: dict mapping each category to a list of secret templates, each containing (type, description, base_threshold)

**Added function:**
- `_generate_secrets_for_location(category: str, distance: int = 0) -> list[dict]`
  - Generates 1-2 hidden secrets for locations with appropriate categories
  - Scales threshold based on distance from entry (deeper = harder to detect)
  - Adds type-specific fields:
    - `hidden_treasure`: adds `reward_gold` (10-30 + distance*5)
    - `trap`: adds `trap_damage` (5 + distance*2)
    - `hidden_door`: adds `exit_direction` (random cardinal direction)

### 2. Secret Wiring into Location Generation

**`generate_subgrid_for_location()` (~line 775):**
- Adds secrets to non-entry rooms (skips entry/exit point)
- Uses Manhattan distance from (0,0) for threshold scaling

**`expand_area()` (~line 1433):**
- Adds secrets to non-entry locations in area expansions
- Uses relative coordinates for distance calculation

**`expand_world()` (~line 1241):**
- Adds secrets to named overworld locations with secret categories
- Uses distance=0 since these are standalone locations

### 3. Passive Detection Wiring (`src/cli_rpg/game_state.py`)

**Added import:**
- `from cli_rpg.secrets import check_passive_detection`

**Added helper method:**
- `_check_and_report_passive_secrets(location: Location) -> Optional[str]`
  - Calls `check_passive_detection()` with player character and location
  - Returns formatted message if secrets were detected, None otherwise

**Wired into movement:**
- `move()` (~line 778): Checks for secrets after updating dread
- `_move_in_sub_grid()` (~line 919): Checks for secrets before returning success message
- `enter()` (~line 1050): Checks for secrets after building look message

### 4. Test File (`tests/test_ai_secrets.py`)

Created comprehensive tests:
- `TestSecretConstants`: Verifies constants are defined correctly
- `TestGenerateSecretsForLocation`: Tests secret generation logic
  - Output count validation (1-2 secrets)
  - Schema validation (required fields)
  - Type-specific field validation (gold, damage, direction)
  - Distance scaling validation
  - Non-secret category handling

## Test Results

```
tests/test_ai_secrets.py: 10 passed
tests/test_perception.py: 22 passed
Full suite: 4322 passed in 95.77s
```

## Files Modified

1. `src/cli_rpg/ai_world.py` - Added SECRET_CATEGORIES, SECRET_TEMPLATES, _generate_secrets_for_location(), and wiring in 3 locations
2. `src/cli_rpg/game_state.py` - Added import, helper method, and calls in move(), _move_in_sub_grid(), enter()

## Files Created

1. `tests/test_ai_secrets.py` - Test file for secret generation

## E2E Validation Points

Players should now:
1. See "You notice: [secret description]" messages when entering locations with secrets (if PER meets threshold)
2. Find secrets in dungeon, cave, ruins, temple, and forest locations
3. Have harder-to-detect secrets in deeper dungeon rooms
4. Be able to discover secrets via active `search` command even if passive detection fails
