# Implementation Plan: Fix Save/Load Validation for Leveled-Up Characters

## Problem
Saved games fail to load after a character levels up because `Character.__post_init__()` enforces the 1-20 stat limit during deserialization. When `from_dict()` creates a character with stats > 20 (from level-ups), validation rejects it with "strength must be at most 20".

## Root Cause
- `Character.__post_init__()` (lines 56-68 in `models/character.py`) validates stats against `MAX_STAT = 20`
- `Character.from_dict()` creates a new Character instance, triggering `__post_init__` validation
- `level_up()` increases stats by +1 each, so a level 2 character with starting STR 20 has STR 21
- This breaks all saves for leveled-up characters

## Solution
Add a `_skip_validation` parameter to `Character.__init__` that bypasses the MAX_STAT check when loading saved data. The 1-20 limit is a **character creation** rule, not a game state rule.

## Implementation Steps

### 1. Add test for loading leveled-up character (TDD)
**File:** `tests/test_character_leveling.py`

Add test in `TestXPSerialization` class:
```python
def test_from_dict_allows_stats_above_20_from_level_ups(self):
    """Spec: from_dict() should allow stats > 20 from leveled-up characters."""
    # Simulate a level 2 character who started with 20 STR and leveled up
    data = {
        "name": "Hero",
        "strength": 21,  # 20 + 1 from level up
        "dexterity": 21,
        "intelligence": 21,
        "level": 2,
        "health": 200,
        "max_health": 205,
        "xp": 50
    }
    character = Character.from_dict(data)
    assert character.strength == 21
    assert character.dexterity == 21
    assert character.intelligence == 21
    assert character.level == 2
```

### 2. Add test for character creation still enforcing limit
**File:** `tests/test_character.py`

Verify existing test `test_character_stat_validation_above_max` still passes - character creation must still reject stats > 20.

### 3. Modify Character class to skip validation on load
**File:** `src/cli_rpg/models/character.py`

Add `_skip_stat_validation: bool = False` parameter to dataclass (excluded from `__init__` via `field(init=False, default=False)`).

Modify `__post_init__` (lines 66-68) to conditionally skip MAX_STAT validation:
```python
if stat_name != "level" and stat_value > self.MAX_STAT:
    if not self._skip_stat_validation:
        raise ValueError(f"{stat_name} must be at most {self.MAX_STAT}")
```

Modify `from_dict()` to set `_skip_stat_validation = True` before construction, or use `object.__setattr__` after construction.

**Alternative approach (simpler):** Create character first with validation, then directly set stats via `object.__setattr__`:
```python
@classmethod
def from_dict(cls, data: dict) -> "Character":
    # Create with capped stats to pass validation
    capped_strength = min(data["strength"], cls.MAX_STAT)
    capped_dexterity = min(data["dexterity"], cls.MAX_STAT)
    capped_intelligence = min(data["intelligence"], cls.MAX_STAT)

    character = cls(
        name=data["name"],
        strength=capped_strength,
        dexterity=capped_dexterity,
        intelligence=capped_intelligence,
        level=data.get("level", 1)
    )

    # Override with actual stats from save (may be > 20)
    character.strength = data["strength"]
    character.dexterity = data["dexterity"]
    character.intelligence = data["intelligence"]
    # Recalculate derived stats
    character.max_health = cls.BASE_HEALTH + character.strength * cls.HEALTH_PER_STRENGTH
    character.constitution = character.strength
    ...
```

### 4. Add roundtrip test for highly leveled character
**File:** `tests/test_character_leveling.py`

```python
def test_serialization_roundtrip_preserves_high_stats(self):
    """Spec: Stats > 20 should survive serialization roundtrip."""
    original = Character(name="Hero", strength=15, dexterity=15, intelligence=15, level=1)
    # Level up 10 times
    for _ in range(10):
        original.level_up()

    assert original.strength == 25  # 15 + 10

    data = original.to_dict()
    restored = Character.from_dict(data)

    assert restored.strength == 25
    assert restored.level == 11
```

## Files to Modify
- `src/cli_rpg/models/character.py` - Modify `from_dict()` to allow stats > 20
- `tests/test_character_leveling.py` - Add tests for loading leveled-up characters

## Verification
1. Run `pytest tests/test_character_leveling.py -v` - new tests pass
2. Run `pytest tests/test_character.py -v` - creation validation still enforced
3. Run `pytest` - full suite passes (713+ tests)
4. Manual test: Create character with 20 STR, level up, save, quit, load - should succeed
