# Tiredness Stat Implementation Summary

## What Was Implemented

The Tiredness stat system was already mostly implemented. This task completed the remaining integration for **combat tiredness increases**.

### Changes Made

#### 1. Combat Tiredness Integration (`src/cli_rpg/combat.py`)
- Added tiredness increase at the end of combat (victory only)
- Formula: `5 base + 1 per turn` of combat
- Tiredness warning messages are included in combat result if thresholds are crossed

```python
# In CombatEncounter.end_combat() after victory
tiredness_increase = 5 + self.turn_count
tiredness_msg = self.player.tiredness.increase(tiredness_increase)
if tiredness_msg:
    messages.append(tiredness_msg)
```

#### 2. New Test (`tests/test_tiredness.py`)
- Added `TestCombatTiredness` test class
- Test: `test_combat_victory_increases_tiredness` - verifies combat increases tiredness by 5 base + turn count

## Test Results

All 31 tiredness tests pass:
- 7 Tiredness model tests (defaults, clamping, thresholds)
- 3 Sleepability tests (can_sleep at various levels)
- 3 Sleep quality tests (light/normal/deep)
- 4 Penalty tests (attack and perception penalties at 80+)
- 4 Serialization tests (to_dict/from_dict)
- 1 Display test (get_display format)
- 5 Character integration tests (attribute, serialization, attack penalty)
- 1 GameState integration test (movement increases tiredness)
- 1 Combat integration test (NEW - combat increases tiredness)
- 3 Dream integration tests (blocking, tiredness-based chance)

Full test suite: **3880 tests passed**

## Pre-existing Implementations (Already in Codebase)

These were already implemented before this task:

1. **Tiredness Model** (`src/cli_rpg/models/tiredness.py`)
   - Range 0-100 with clamping
   - Threshold warnings at 60/80/100
   - Sleep availability (can_sleep at 30+)
   - Sleep quality (light/normal/deep)
   - Attack and perception penalties at 80+
   - Visual display bar
   - Serialization support

2. **Character Integration** (`src/cli_rpg/models/character.py`)
   - `tiredness` attribute on Character
   - Attack power includes tiredness penalty
   - Serialization in to_dict/from_dict with backward compatibility

3. **GameState Integration** (`src/cli_rpg/game_state.py`)
   - Movement increases tiredness by 3 per move

4. **Rest/Camp Integration** (`src/cli_rpg/main.py`, `src/cli_rpg/camping.py`)
   - Rest reduces tiredness based on sleep quality (25/50/80)
   - Camp reduces tiredness (40 base + 10 with campfire)

5. **Dream Integration** (`src/cli_rpg/dreams.py`)
   - Dreams blocked when tiredness < 30
   - Dream chance modified by tiredness level
   - Deep sleep (80+) = 40% dream chance
   - Normal sleep (60-79) = 20% dream chance
   - Light sleep (<60) = 5% dream chance

## E2E Validation Points

1. Travel multiple times to build tiredness (3 per move)
2. Verify tiredness warnings at 60, 80, 100 thresholds
3. Combat should increase tiredness (visible at end of battle)
4. Rest command should reduce tiredness based on quality
5. Camp command should reduce tiredness
6. Attack power should be reduced by 10% at 80+ tiredness
7. Dreams should only trigger when tiredness >= 30
