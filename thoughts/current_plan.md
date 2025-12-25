# Implementation Plan: Improve Test Coverage for Remaining Uncovered Lines

## Summary
Add targeted tests to cover the 18 uncovered lines across `main.py`, `models/character.py`, and `ai_service.py`.

---

## 1. main.py Lines 361, 363 (Lowest Hanging Fruit)

**Uncovered code**: Using an equipped weapon/armor during combat shows "equipped" message instead of "not found"

**Location**: `handle_combat_command()` in `src/cli_rpg/main.py`, lines 351-363

**Tests to add** in `tests/test_main_combat_integration.py`:

```python
class TestUseEquippedItemDuringCombat:
    """Tests for 'use' on equipped items during combat."""

    def test_use_equipped_weapon_during_combat_shows_equipped_message(self):
        """Spec: 'use' on equipped weapon during combat shows equipped message."""
        # Setup: Equip weapon, enter combat, try to use it
        # Assert: "equipped as your weapon" in message

    def test_use_equipped_armor_during_combat_shows_equipped_message(self):
        """Spec: 'use' on equipped armor during combat shows equipped message."""
        # Setup: Equip armor, enter combat, try to use it
        # Assert: "equipped as your armor" in message
```

---

## 2. models/character.py Lines 8-11, 71, 97, 113 (7 lines)

**Uncovered lines**:
- Lines 8-11: `TYPE_CHECKING` imports (runtime never executed - skip, standard Python pattern)
- Line 71: `if not isinstance(stat_value, int)` validation error
- Line 97: `if amount < 0` in `add_gold()`
- Line 113: `if amount < 0` in `remove_gold()`

**Tests to add** in `tests/test_character.py`:

```python
def test_character_stat_non_integer_raises_error():
    """Spec: Non-integer stat values raise ValueError."""
    # Pass float/string as strength/dexterity/intelligence

def test_add_gold_negative_amount_raises_error():
    """Spec: Adding negative gold raises ValueError."""

def test_remove_gold_negative_amount_raises_error():
    """Spec: Removing negative gold raises ValueError."""
```

---

## 3. ai_service.py Lines 9, 18-21, 252, 309, 423, 455 (9 lines)

**Uncovered lines**:
- Line 9: `TYPE_CHECKING` import (skip - standard pattern)
- Lines 18-21: `except ImportError` block for Anthropic (requires uninstalling anthropic package)
- Line 252: Final fallback `raise AIServiceError` in `_call_openai()` - unreachable defensive code
- Line 309: Final fallback `raise AIServiceError` in `_call_anthropic()` - unreachable defensive code
- Line 423: Cache load handles expired entries (edge case, already tested implicitly)
- Line 455: Cache save to file with no parent directory

**Practical tests to add** (skipping unreachable defensive code):

```python
# In tests/test_ai_service.py - test cache save with no parent dir
def test_save_cache_handles_no_parent_directory():
    """Spec: Cache saves when file has no parent directory (e.g., 'cache.json')."""
```

Note: Lines 18-21, 252, 309 are defensive fallbacks that are intentionally difficult to reach. Covering them would require:
- Uninstalling anthropic package (lines 18-21)
- Creating impossible retry loop conditions (lines 252, 309)

These are acceptable to leave uncovered as they represent defensive programming.

---

## Implementation Order

1. **tests/test_main_combat_integration.py** - Add `TestUseEquippedItemDuringCombat` class (covers lines 361, 363)
2. **tests/test_character.py** - Add negative/invalid input tests (covers lines 71, 97, 113)
3. Optionally: Add cache edge case test if time permits

## Expected Coverage Improvement

- main.py: 99% → 100% (+2 lines)
- models/character.py: 97% → 99% (+3 lines, 4 TYPE_CHECKING lines remain)
- Overall: ~98.81% → ~99.0%
