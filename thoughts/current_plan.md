# Crafting Skill Progression Implementation Plan

## Spec

Add a crafting skill level to the character model that:
1. Starts at level 1 (Novice)
2. Gains XP on successful crafts (+5 XP per craft)
3. Levels up at thresholds: Apprentice (25), Journeyman (50), Expert (75), Master (100)
4. Provides success rate bonus per level (+5% per level above Novice)
5. Unlocks advanced recipes at higher levels (Journeyman+ for iron items)

## Model: CraftingProficiency

Create `src/cli_rpg/models/crafting_proficiency.py` following the `WeaponProficiency` pattern:
- `CraftingLevel` enum: NOVICE, APPRENTICE, JOURNEYMAN, EXPERT, MASTER
- `CraftingProficiency` dataclass with `xp: int = 0`
- Methods: `get_level()`, `get_success_bonus()`, `gain_xp()`, `to_dict()`, `from_dict()`
- Level thresholds mirror weapon proficiency: 0/25/50/75/100

## Tests First

Add to `tests/test_crafting.py`:

```python
# Crafting skill progression tests
def test_character_has_crafting_proficiency():
    """Character should have crafting_proficiency field defaulting to level 1."""

def test_crafting_proficiency_levels_up():
    """Crafting XP should level up at thresholds (25/50/75/100)."""

def test_craft_success_grants_xp():
    """Successful craft should grant +5 crafting XP."""

def test_crafting_level_affects_success_rate():
    """Higher crafting level should increase success chance (base 100% for basic recipes)."""

def test_advanced_recipes_require_journeyman():
    """Iron sword/armor require Journeyman (level 3) to craft."""

def test_crafting_proficiency_serialization():
    """Proficiency should serialize/deserialize correctly."""
```

## Implementation Steps

1. **Create `src/cli_rpg/models/crafting_proficiency.py`**:
   - `CraftingLevel` enum with 5 levels
   - `LEVEL_THRESHOLDS` dict (0/25/50/75/100)
   - `LEVEL_SUCCESS_BONUS` dict (0%/5%/10%/15%/20%)
   - `CraftingProficiency` dataclass with xp field
   - `get_level()`, `get_success_bonus()`, `gain_xp()` methods
   - `to_dict()` and `from_dict()` for serialization

2. **Update `src/cli_rpg/models/character.py`**:
   - Import `CraftingProficiency`
   - Add field: `crafting_proficiency: CraftingProficiency = field(default_factory=CraftingProficiency)`
   - Update `to_dict()`: add `"crafting_proficiency": self.crafting_proficiency.to_dict()`
   - Update `from_dict()`: restore with backward compat default

3. **Update `src/cli_rpg/crafting.py`**:
   - Add `RECIPE_MIN_LEVEL` dict mapping recipe keys to minimum `CraftingLevel` required
   - Add recipe level requirements: basic recipes (torch, rope, bandage) = NOVICE, iron items = JOURNEYMAN
   - Modify `execute_craft()`:
     - Check crafting level vs recipe requirement
     - On success: call `character.crafting_proficiency.gain_xp(5)`
     - Return level-up message if applicable
   - Update `get_recipes_list()` to optionally show level requirements

4. **Update tests**:
   - Add all tests from spec above to `tests/test_crafting.py`
   - Verify backward compatibility with old saves (no crafting_proficiency field)
