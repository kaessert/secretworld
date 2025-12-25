# Random Travel Encounters - Implementation Summary

## What Was Implemented

The random encounter system is fully implemented and tested. This feature adds urgency and emergent gameplay by triggering occasional events when players move between locations.

### Files Created

1. **`src/cli_rpg/models/random_encounter.py`**
   - `RandomEncounter` dataclass with fields: `encounter_type`, `entity`, `description`
   - Validation ensures proper entity types (Enemy for hostile, NPC for merchant/wanderer)
   - Serialization via `to_dict()` / `from_dict()` for persistence

2. **`src/cli_rpg/random_encounters.py`**
   - `RANDOM_ENCOUNTER_CHANCE = 0.15` (15% trigger chance per move)
   - `ENCOUNTER_WEIGHTS` (hostile: 60%, merchant: 25%, wanderer: 15%)
   - `check_for_random_encounter(game_state)` - main trigger function
   - `spawn_wandering_merchant(level)` - creates merchant NPC with shop (2-3 items)
   - `spawn_wanderer(theme)` - creates atmospheric NPC with lore dialogue
   - `format_encounter_message()` - formats output with `[Random Encounter!]` marker

3. **`tests/test_random_encounters.py`**
   - 26 comprehensive tests covering all spec requirements
   - Model creation and validation tests
   - Serialization roundtrip tests
   - Integration tests with GameState.move()
   - Combat, merchant, and wanderer encounter tests
   - Message formatting tests

### Files Modified

- **`src/cli_rpg/game_state.py`**
   - Imported `check_for_random_encounter` from new module
   - Called in `move()` after successful movement (line 480-482)

## Test Results

All tests pass:
- 26 random encounter tests
- 1987 total tests in suite

## Key Design Decisions

1. **Encounter types respect existing patterns**: Hostile encounters reuse `spawn_enemy()` from combat.py
2. **NPCs are temporary**: Wanderers and merchants are added to the current location's NPC list
3. **Location category awareness**: Hostile encounters use location category for appropriate enemy spawning
4. **Combat integration**: Hostile encounters properly start combat using existing `CombatEncounter`
5. **Clear messaging**: All encounters show `[Random Encounter!]` marker and interaction hints

## E2E Validation

To validate in-game:
1. Move between locations multiple times (15% trigger rate)
2. Hostile encounters should start combat immediately
3. Merchant encounters should add talkable NPC with shop (use `talk` command)
4. Wanderer encounters should add atmospheric NPC with dialogue
