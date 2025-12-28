# Implementation Summary: class_behaviors.py

## What Was Implemented

Created `scripts/agent/class_behaviors.py` with class-specific combat and exploration strategies for all 5 character classes (Warrior, Mage, Rogue, Ranger, Cleric) to make the AI agent behave differently based on character class.

### Files Created/Modified

1. **`scripts/agent/class_behaviors.py`** (new - 347 lines)
   - `CharacterClassName` enum - mirrors game's CharacterClass (WARRIOR, MAGE, ROGUE, RANGER, CLERIC)
   - `ClassBehaviorConfig` dataclass - thresholds and cooldowns with `to_dict`/`from_dict` serialization
   - `ClassBehavior` Protocol - defines interface with `get_combat_command`, `get_exploration_command`, `should_flee`
   - 5 concrete behavior classes:
     - `WarriorBehavior` - bash, stance switching (aggressive/berserker), 15% flee threshold
     - `MageBehavior` - fireball/ice_bolt, self-heal, mana conservation, 25% flee threshold
     - `RogueBehavior` - hide/sneak attack cycle, dungeon secret searching (30% chance), 20% flee
     - `RangerBehavior` - companion summoning, tracking, feeding wounded companion, wilderness comfort
     - `ClericBehavior` - smite undead, bless at combat start, heal, holy symbol equipped
   - `BEHAVIOR_REGISTRY` dict - maps CharacterClassName to behavior instances
   - `get_class_behavior()` helper function

2. **`scripts/agent/__init__.py`** (updated)
   - Added exports for all new classes and functions

3. **`tests/test_agent_class_behaviors.py`** (new - 47 tests)
   - Tests for CharacterClassName enum
   - Tests for ClassBehaviorConfig dataclass
   - Tests for registry and get_class_behavior
   - Tests for each behavior class (Warrior, Mage, Rogue, Ranger, Cleric)
   - Serialization tests for ClassBehaviorConfig

### Class Behavior Details

| Class   | Combat                              | Exploration              | Flee Threshold |
|---------|-------------------------------------|--------------------------|----------------|
| Warrior | bash, stance aggressive/berserker   | Direct approach          | 15% (brave)    |
| Mage    | fireball/ice_bolt, self-heal        | Conserve mana            | 25% (fragile)  |
| Rogue   | sneak attacks, hide                 | Search secrets (30%)     | 20%            |
| Ranger  | companion fights alongside          | summon, track, feed      | 20% (15% wild) |
| Cleric  | smite undead, bless, heal           | Equip holy symbol        | 20%            |

## Test Results

```
============================= test session starts ==============================
tests/test_agent_class_behaviors.py ... 47 passed in 0.15s
tests/test_agent_*.py ... 116 passed in 0.25s
```

All tests pass including:
- 47 new class behavior tests
- 69 existing agent tests (personality, memory, checkpoint)

## Technical Notes

- Uses Protocol for duck-typing (class behaviors don't need to inherit from a base class)
- Each behavior class maintains internal state (e.g., `_is_hidden` for Rogue, `_mana_percent` for Mage)
- Behaviors return `None` to signal "use default attack" - caller handles fallback
- Mage's `_mana_percent` is set externally (could be parsed from game state in future)
- Random elements for variety (Mage spell choice, Rogue search probability, Ranger track probability)

## E2E Test Validation

The class behaviors integrate with the AI agent system and can be validated by:
1. Running simulation with different character classes
2. Verifying class-specific commands are issued in combat/exploration
3. Checking flee behavior matches class thresholds
