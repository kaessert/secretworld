# Dread Hallucinations System - Implementation Summary

## What Was Implemented

### New Module: `src/cli_rpg/hallucinations.py`
- Created hallucination spawning and trigger logic
- **Constants**:
  - `HALLUCINATION_DREAD_THRESHOLD = 75` (triggers at 75-99% dread)
  - `HALLUCINATION_CHANCE = 0.30` (30% chance per movement)
  - `DREAD_REDUCTION_ON_DISPEL = 5` (catharsis on dispel)
- **Functions**:
  - `spawn_hallucination(level)`: Creates a hallucination enemy scaled to player level
  - `check_for_hallucination(game_state)`: Checks and triggers hallucination encounter
- **Templates**: Shadow Mimic, Phantom Shade, Nightmare Echo with unique descriptions and ASCII art

### Modified: `src/cli_rpg/models/enemy.py`
- Added `is_hallucination: bool = False` field to Enemy dataclass
- Updated `to_dict()` to serialize the new field
- Updated `from_dict()` to deserialize with backward compatibility (defaults to False)

### Modified: `src/cli_rpg/combat.py`
- Added hallucination check in `player_attack()` method
- When attacking a hallucination:
  - The creature dissipates (removed from enemies list)
  - Special message displayed: "Your attack passes through... it was never real"
  - Combat ends if no other enemies remain
  - No damage calculation occurs

### Modified: `src/cli_rpg/game_state.py`
- Added import for hallucination module
- Integrated hallucination check in `move()` after shadow creature check
- Hallucinations only trigger if:
  - No shadow attack (100% dread priority)
  - Not already in combat
  - Dread is 75-99%
  - 30% random chance succeeds

### Modified: `src/cli_rpg/main.py`
- Updated `handle_combat_command()` for both attack and cast commands
- Added special handling for hallucination-only fights:
  - Skips bestiary recording
  - Skips XP/loot/gold rewards
  - Skips quest progress tracking
  - Reduces dread by 5 with "Your mind clears slightly" message

## Test Results

All 17 new tests pass + 2239 existing tests (2256 total):
- `tests/test_hallucinations.py`: Full coverage of new functionality
  - Spawn tests: enemy creation, flag, names, level scaling, description, ASCII art
  - Trigger tests: 75% threshold, below threshold, at 100%, in combat, chance check
  - Combat tests: dispel on attack, combat ends
  - Enemy model tests: default flag, serialization roundtrip, backward compatibility
  - Constants test: dread reduction value

## Test Files Modified

- `tests/test_enemy.py`: Added `is_hallucination: False` to expected serialization dict
- `tests/test_companion_banter_integration.py`: Changed dread level from 75 to 60 to avoid hallucination trigger interference

## E2E Validation Suggestions

1. Create a new game and enter a dungeon/cave
2. Increase dread to 75%+ (can be done by exploring dark areas)
3. Move around - with 30% chance, hallucinations should appear
4. Attack the hallucination - should dispel with special message
5. Verify dread is reduced by 5
6. Verify no XP/gold/loot awarded
7. Verify hallucination not added to bestiary
