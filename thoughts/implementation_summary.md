# Implementation Summary: Fix KILL Quest Target Spawn Mismatch

## What Was Implemented

Fixed KILL quests that generate enemy targets (e.g., "Giant Spider") that never spawn in the game world, making quests impossible to complete.

### Changes Made

#### 1. `src/cli_rpg/combat.py`
- Moved `enemy_templates` dict from inside `spawn_enemy()` to module level as `ENEMY_TEMPLATES`
- Added `VALID_ENEMY_TYPES: frozenset[str]` - a set of all spawnable enemy names (lowercase) for O(1) validation lookups
- Updated `spawn_enemy()` to reference the module-level `ENEMY_TEMPLATES` instead of local variable

#### 2. `src/cli_rpg/ai_service.py`
- Added KILL quest target validation in `_parse_quest_response()` (after line 1867)
- When `objective_type == "kill"`, validates that `target.lower()` is in `VALID_ENEMY_TYPES`
- Raises `AIGenerationError` with descriptive message for invalid targets

#### 3. `tests/test_quest_validation.py` (new file)
- 8 tests for `VALID_ENEMY_TYPES` constant (validates all enemy categories are present, lowercase)
- 7 tests for KILL quest target validation (valid targets accepted, invalid rejected, case-insensitive, non-kill quests not validated)

#### 4. Test Fixes
Updated existing tests that used invalid enemy types as KILL targets:
- `tests/test_ai_quest_generation.py`: Changed "Enemy" to "Goblin" in 3 tests
- `tests/test_coverage_gaps.py`: Changed "Dragon" to "Troll"/"Goblin" in 2 tests

## Valid Enemy Types (Spawnable)

| Location | Enemies |
|----------|---------|
| Forest | Wolf, Bear, Wild Boar, Giant Spider |
| Cave | Bat, Goblin, Troll, Cave Dweller |
| Dungeon | Skeleton, Zombie, Ghost, Dark Knight |
| Mountain | Eagle, Goat, Mountain Lion, Yeti |
| Village | Bandit, Thief, Ruffian, Outlaw |
| Default | Monster, Creature, Beast, Fiend |

## Test Results

```
pytest - 3473 passed in 104.63s
pytest tests/test_quest_validation.py - 15 passed in 0.53s
```

## Technical Details

- `VALID_ENEMY_TYPES` is a `frozenset` for immutability and O(1) lookups
- Validation is case-insensitive (target is lowercased before checking)
- Original target case is preserved in quest data
- Only KILL quests are validated; EXPLORE, COLLECT, TALK, DROP quests are not affected

## E2E Validation

With seed 999, KILL quests should now only generate targets that can actually spawn:
- AI generates "Hunt Goblins" → player can find goblins in caves
- AI generates "Kill Wild Boar" → player can find wild boars in forests
- AI cannot generate "Slay Dragons" → dragons are not spawnable enemies
