# Armor Class Restrictions - Implementation Summary

## Date: 2025-12-28

## What Was Implemented

Added armor weight categories to differentiate class equipment choices, with class-based restrictions on what armor each class can wear.

### 1. ArmorWeight Enum (`src/cli_rpg/models/item.py`)
- Added new `ArmorWeight` enum with values: `LIGHT`, `MEDIUM`, `HEAVY`
- Added optional `armor_weight: Optional[ArmorWeight] = None` field to `Item` dataclass
- Updated `to_dict()` to serialize armor_weight (only when set)
- Updated `from_dict()` to deserialize armor_weight (defaults to None for backward compatibility)
- Updated `__str__()` to display weight category for armor items (e.g., "Plate Armor [Heavy Armor]")

### 2. Class Armor Restrictions (`src/cli_rpg/models/character.py`)
- Added `CLASS_ARMOR_RESTRICTIONS` dict mapping each `CharacterClass` to allowed armor weight names:
  - **Mage**: LIGHT only
  - **Rogue**: LIGHT and MEDIUM
  - **Warrior**: LIGHT, MEDIUM, and HEAVY (only class that can use heavy armor)
  - **Ranger**: LIGHT and MEDIUM
  - **Cleric**: LIGHT and MEDIUM
- Added `can_equip_armor(armor: Item) -> bool` method that validates weight restrictions
- Added `equip_armor_with_validation(armor: Item) -> Tuple[bool, str]` method that returns success/failure with descriptive message

### 3. Main.py Equip Command Update (`src/cli_rpg/main.py`)
- Updated equip command handler to call `equip_armor_with_validation()` for armor items
- Provides descriptive error message when armor is too heavy for class (e.g., "Cannot equip Plate Armor - heavy armor is too heavy for Mage.")

### 4. Fallback Content Updates (`src/cli_rpg/fallback_content.py`)
- Added `armor_weight` field to all armor item templates:
  - **Light**: Shadow Cloak, Miner's Helm, Relic Helm, Blessed Robes, Leather Armor, Gilded Amulet, Blessed Medallion
  - **Medium**: Iron Shield, Gilded Shield, Sacred Shield, Temple Guard Armor, Chain Mail, Steel Shield
  - **Heavy**: Dungeon Guard Armor, Crystal Armor, Stone Shield, Ancient Armor

### Backward Compatibility
- Existing armor items without weight field default to `None`
- Armor with `None` weight is treated as LIGHT and can be equipped by any class
- Characters without a class (None) can equip any armor regardless of weight

## Files Modified
1. `src/cli_rpg/models/item.py` - ArmorWeight enum, armor_weight field
2. `src/cli_rpg/models/character.py` - CLASS_ARMOR_RESTRICTIONS, can_equip_armor(), equip_armor_with_validation()
3. `src/cli_rpg/main.py` - Updated equip command
4. `src/cli_rpg/fallback_content.py` - Added armor_weight to armor templates

## Files Created
1. `tests/test_armor_restrictions.py` - Test suite for armor class restrictions (19 tests)

## Test Results
- 19 new tests added in `tests/test_armor_restrictions.py`
- All 5378 tests pass (including 120 item/character/inventory tests)

## E2E Validation Suggestions
- Create a Mage character, acquire heavy armor (e.g., Dungeon Guard Armor), and verify equip command is rejected with appropriate message
- Create a Warrior character and verify they can equip all armor types
- Load an old save file and verify backward compatibility - existing armor still equips correctly

---

# Stealth Kills Bonus XP - Implementation Summary

## Date: 2025-12-28

## What Was Implemented

Added a 25% XP bonus for killing enemies with backstab (stealth) attacks.

### Files Modified

1. **`src/cli_rpg/combat.py`**:
   - Added `self.stealth_kills = 0` counter in `CombatEncounter.__init__()` (line 405)
   - Added stealth kill tracking in `player_attack()` - increments counter when enemy dies from backstab (lines 752-754)
   - Added stealth bonus XP calculation in `end_combat()` - awards 25% bonus per stealth kill (lines 1966-1970)

2. **`tests/test_sneak.py`**:
   - Added `TestSneakKillBonusXP` test class with two tests:
     - `test_stealth_kill_grants_bonus_xp`: Verifies 25% bonus XP is awarded for stealth kills
     - `test_no_bonus_for_normal_kills`: Verifies no bonus for normal (non-stealth) kills

### Implementation Details

The stealth bonus formula in `end_combat()`:
```python
stealth_bonus = int(total_xp * 0.25 * self.stealth_kills / len(self.enemies))
```

This ensures:
- 25% bonus per stealth kill relative to total enemy XP
- Scales correctly for multi-enemy encounters
- Displays "Stealth bonus: +X XP!" message when applicable

## Test Results

All tests pass:
- 15 sneak tests (including 2 new stealth kill bonus tests)
- 59 combat tests (existing functionality unaffected)

```
tests/test_sneak.py::TestSneakKillBonusXP::test_stealth_kill_grants_bonus_xp PASSED
tests/test_sneak.py::TestSneakKillBonusXP::test_no_bonus_for_normal_kills PASSED
```

## E2E Validation Points

- Rogue players should see "Stealth bonus: +X XP!" message after winning combat with stealth kills
- Non-rogue classes or normal kills should NOT see stealth bonus message
- Total XP gained should include the 25% bonus per stealth kill

---

# Add Perception Stat to Enemy Model - Implementation Summary

## Date: 2025-12-28

## What Was Implemented

Added a `perception` stat field to the Enemy model for stealth detection mechanics.

### Files Modified

1. **`src/cli_rpg/models/enemy.py`**
   - Added `perception: int = 5` field to Enemy dataclass (line 104)
   - Added `"perception": self.perception` to `to_dict()` serialization (line 262)
   - Added `perception=data.get("perception", 5)` to `from_dict()` deserialization (line 323)

2. **`tests/test_enemy.py`**
   - Updated `test_to_dict_serializes_enemy` to include perception in expected output
   - Added `assert restored.perception == original.perception` to `test_serialization_roundtrip`
   - Added new `TestEnemyPerception` test class with 4 tests:
     - `test_default_perception_is_five`: Verifies default value is 5
     - `test_custom_perception_value`: Verifies custom perception can be set
     - `test_perception_serialization_roundtrip`: Verifies perception survives save/load
     - `test_from_dict_uses_default_perception_for_legacy_data`: Verifies backward compatibility

## Test Results

- **Enemy tests**: 20 passed
- **Full test suite**: 5357 passed, 4 skipped, 1 warning

## Design Decisions

- Default perception value is 5 (baseline awareness) as per spec
- `from_dict()` uses default of 5 for backward compatibility with existing save files that don't have the perception field
- Perception field is added at the end of the dataclass to avoid breaking existing positional argument usage

## E2E Validation

The basic Enemy model functionality should be validated via existing gameplay that creates and serializes enemies. Any save/load functionality will automatically include perception in new saves and handle legacy saves gracefully.

---

# Rare Crafting Recipes as Rewards - Implementation Summary

## Date: 2025-12-28

## What Was Implemented

Added rare crafting recipes that are gated behind discovery (not available from the start). Recipes are unlocked through gameplay rewards.

### Character Model Updates (`src/cli_rpg/models/character.py`)
- Added `unlocked_recipes: Set[str]` field (default: empty set)
- Added `unlock_recipe(recipe_key: str) -> str` method to unlock rare recipes
- Added `has_recipe(recipe_key: str) -> bool` method to check if recipe is unlocked
- Updated `to_dict()` to serialize `unlocked_recipes` as a list
- Updated `from_dict()` to deserialize `unlocked_recipes` with backward compatibility

### Crafting System Updates (`src/cli_rpg/crafting.py`)
- Added `RARE_RECIPES` dict containing 3 rare recipes:
  - **Elixir of Vitality** (2 Herbs + 1 Iron Ore → 75 HP heal, requires MASTER level)
  - **Steel Blade** (3 Iron Ore + 2 Wood → +8 damage, requires EXPERT level)
  - **Fortified Armor** (4 Iron Ore + 2 Fiber → +6 defense, requires EXPERT level)
- Added `RARE_RECIPE_LEVEL` dict with crafting level requirements
- Updated `execute_craft()` to:
  - Check if recipe is in RARE_RECIPES
  - Require unlock before crafting rare recipes
  - Use appropriate level requirements for rare recipes
- Updated `get_recipes_list()` to:
  - Accept optional `character` parameter
  - Show "Discovered Rare Recipes" section when character has unlocked recipes

### Main Game Integration (`src/cli_rpg/main.py`)
- Updated `recipes` command to pass character to `get_recipes_list()` so players can see their unlocked rare recipes

## New Tests Added (`tests/test_crafting.py`)
Added 14 new tests for the rare recipe system:
- `test_rare_recipes_not_in_base_recipes` - Verifies separation of rare recipes
- `test_character_has_unlocked_recipes` - Verifies Character has unlocked_recipes field
- `test_craft_fails_for_undiscovered_rare_recipe` - Verifies gating behavior
- `test_craft_succeeds_after_unlocking_recipe` - Verifies unlock enables crafting
- `test_unlock_recipe_adds_to_set` - Tests unlock_recipe method
- `test_unlock_recipe_returns_message_for_already_unlocked` - Tests duplicate unlock
- `test_has_recipe_method` - Tests has_recipe method
- `test_recipes_list_shows_rare_section` - Tests UI with unlocked recipes
- `test_recipes_list_without_rare_recipes` - Tests UI without unlocked recipes
- `test_rare_recipe_serialization` - Tests save/load of unlocked_recipes
- `test_rare_recipes_require_expert_level` - Verifies level requirements
- `test_elixir_of_vitality_requires_master_level` - Verifies master requirement
- `test_rare_recipe_requires_crafting_level` - Tests level gating in practice
- `test_backward_compat_character_without_unlocked_recipes` - Tests old save compatibility

## Test Results
- All 50 crafting tests pass
- All 5128 unit tests pass (no regressions)

## E2E Test Considerations
E2E tests should validate:
1. Using `recipes` command shows both base and discovered rare recipes
2. Crafting a rare recipe without unlocking shows appropriate error message
3. After calling `character.unlock_recipe()`, the recipe becomes craftable
4. Saved games preserve unlocked recipes

---

# Previous Implementation: Crafting Skill Progression - Implementation Summary

## Date: 2025-12-28

## What Was Implemented

Added a crafting skill progression system that tracks player skill in crafting and gates advanced recipes.

### New Files Created

1. **`src/cli_rpg/models/crafting_proficiency.py`**
   - `CraftingLevel` enum: NOVICE, APPRENTICE, JOURNEYMAN, EXPERT, MASTER
   - `CraftingProficiency` dataclass with `xp: int = 0`
   - Methods: `get_level()`, `get_success_bonus()`, `gain_xp()`, `to_dict()`, `from_dict()`
   - Level thresholds: 0/25/50/75/100 XP
   - Success bonuses: 0%/5%/10%/15%/20% per level

### Files Modified

1. **`src/cli_rpg/models/character.py`**
   - Added import for `CraftingProficiency`
   - Added field: `crafting_proficiency: CraftingProficiency = field(default_factory=CraftingProficiency)`
   - Updated `to_dict()` to serialize crafting proficiency
   - Updated `from_dict()` to restore crafting proficiency with backward compatibility

2. **`src/cli_rpg/crafting.py`**
   - Added import for `CraftingLevel`
   - Added `RECIPE_MIN_LEVEL` dict mapping recipes to required level (iron sword/armor require JOURNEYMAN)
   - Added `CRAFT_XP_GAIN = 5` constant
   - Updated `execute_craft()` to:
     - Check crafting level requirement before allowing craft
     - Grant +5 XP on successful craft
     - Include level-up message in result when threshold crossed

3. **`tests/test_crafting.py`**
   - Added 11 new tests for crafting skill progression:
     - `test_character_has_crafting_proficiency`
     - `test_crafting_proficiency_levels_up`
     - `test_craft_success_grants_xp`
     - `test_crafting_level_affects_success_rate`
     - `test_advanced_recipes_require_journeyman`
     - `test_crafting_proficiency_serialization`
     - `test_character_crafting_proficiency_serialization`
     - `test_crafting_proficiency_gain_xp_returns_levelup_message`
     - `test_crafting_proficiency_xp_capped_at_100`
     - `test_craft_shows_levelup_message`
     - `test_backward_compat_character_without_crafting_proficiency`

## Test Results

- All 36 crafting tests pass
- Full test suite: 5339 tests pass
- No regressions

## Key Design Decisions

1. **Followed WeaponProficiency pattern**: The implementation mirrors the existing weapon proficiency system for consistency.

2. **XP thresholds match weapon proficiency**: 0/25/50/75/100 for familiarity.

3. **Backward compatibility**: Old saves without `crafting_proficiency` key load with default (0 XP, NOVICE level).

4. **Recipe gating**: Only iron sword and iron armor require JOURNEYMAN level. All other recipes are available at NOVICE.

5. **Success bonus stored as float**: 0.0 to 0.20 (ready for future random crafting success mechanics).

## E2E Test Considerations

E2E tests should validate:
- New characters start with NOVICE crafting level
- Crafting basic recipes (torch, bandage) grants XP
- After 5 basic crafts (25 XP), character reaches APPRENTICE
- Iron sword/armor cannot be crafted until JOURNEYMAN (50 XP, 10 basic crafts)
- Save/load preserves crafting proficiency XP

---

# Previous Implementation Summary: Branching Quest Paths

## Date: 2025-12-28

## Overview

Verified that the branching quest system is fully implemented. All components were found to be in place and all tests pass.

## Components Verified

### 1. Quest Model (src/cli_rpg/models/quest.py)
- `QuestBranch` dataclass with id, name, objective_type, target, progress tracking
- `Quest.alternative_branches` list field
- `Quest.completed_branch_id` field
- `Quest.get_branches_display()` method for UI
- Full serialization support via `to_dict()`/`from_dict()`

### 2. Quest Accept (src/cli_rpg/main.py lines 1774-1797)
- Clones `alternative_branches` with deep copy of faction_effects
- Clones `world_effects` with deep copy of metadata
- Resets `current_count` to 0 on each branch

### 3. Quest Details Display (src/cli_rpg/main.py lines 2025-2032)
- Shows "Alternative Paths:" section when quest has branches
- Displays branch name, objective, progress, and completion status

### 4. Procedural Quest Generation (src/cli_rpg/procedural_quests.py)
- `BranchTemplate` dataclass (lines 71-89)
- `BRANCHING_QUEST_TEMPLATES` dict mapping template types to branch sets
  - KILL_BOSS: kill/persuade and kill/betray sets
  - KILL_MOBS: kill/lure set
  - COLLECT_ITEMS: collect/buy set
  - TALK_NPC: talk/intimidate set
- `generate_branches_for_template()` function

### 5. Fallback Content (src/cli_rpg/fallback_content.py)
- `BRANCH_NAME_TEMPLATES` dict
- `BRANCH_DESCRIPTION_TEMPLATES` dict
- `FallbackContentProvider.get_branch_content()` method

### 6. ContentLayer Integration (src/cli_rpg/content_layer.py)
- `generate_quest_from_template()` calls `generate_branches_for_template()`
- Attaches generated branches to Quest

### 7. Branch Completion (src/cli_rpg/models/character.py)
- `record_kill()` checks and completes KILL branches
- `record_talk()` checks and completes TALK branches
- Sets `completed_branch_id` when branch completes
- Sets quest status to READY_TO_TURN_IN

### 8. Branch Rewards (src/cli_rpg/models/character.py)
- `claim_quest_rewards()` applies branch modifiers:
  - `gold_modifier` scales gold reward
  - `xp_modifier` scales XP reward
  - `faction_effects` applied to factions

## Test Results

All tests pass:
- `tests/test_quest_branching.py`: 11 passed
- `tests/test_branching_quests_integration.py`: 15 passed
- `tests/test_quest_branch_validation.py`: 6 passed
- `tests/test_quest.py`: 48 passed
- `tests/test_procedural_quests.py`: 31 passed
- All 39 branch-related tests: passed

## Files Modified
No files were modified - the implementation was already complete.

## Verification Commands
```bash
pytest tests/test_quest_branching.py -v
pytest tests/test_branching_quests_integration.py -v
pytest tests/test_quest.py -v
pytest -k "branch" -v
```

---

# Previous Implementation: World State Changes from Quest Completion

## Date: 2025-12-28

## Overview

Connected quest completion to WorldStateManager to record permanent world changes (e.g., cleared dungeons, defeated bosses, transformed locations).

## Files Modified

### Core Implementation

1. **`src/cli_rpg/models/quest.py`**
   - Added `WorldEffect` dataclass with fields:
     - `effect_type: str` - Type of effect (area_cleared, location_transformed, boss_defeated, npc_moved, etc.)
     - `target: str` - Location/NPC name affected
     - `description: str` - Human-readable description
     - `metadata: dict` - Extra data (new_category, etc.)
   - Added validation: target cannot be empty
   - Added `to_dict()` and `from_dict()` for serialization
   - Added `world_effects: List[WorldEffect]` field to `Quest` dataclass
   - Updated Quest's `to_dict()` and `from_dict()` to include world_effects

2. **`src/cli_rpg/models/world_state.py`**
   - Added `record_quest_world_effect()` method to `WorldStateManager` that:
     - Records a `QUEST_WORLD_EFFECT` change type with the effect's metadata
     - For `area_cleared` effects, also records an `AREA_CLEARED` change for backwards compatibility with `is_area_cleared()` queries
   - Added TYPE_CHECKING import for WorldEffect

3. **`src/cli_rpg/main.py`** (line ~1838)
   - Added integration point after quest completion to apply world effects:
     ```python
     for effect in matching_quest.world_effects:
         game_state.world_state_manager.record_quest_world_effect(
             effect=effect,
             quest_name=matching_quest.name,
             timestamp=game_state.game_time.total_hours,
         )
     ```

### Test Files

4. **`tests/test_quest_world_effects.py`** (new file)
   - 16 tests covering:
     - WorldEffect dataclass creation and validation
     - Serialization round-trip for WorldEffect
     - Quest with world_effects field
     - WorldStateManager.record_quest_world_effect() method
     - Integration: is_area_cleared() after quest completion

5. **`tests/test_quest.py`**
   - Updated `test_to_dict` to include `world_effects` in expected output

## Test Results

All tests pass:
- 16 new tests in `tests/test_quest_world_effects.py`
- 5313 total tests pass across the project

## E2E Validation

The feature should be validated by:
1. Creating a quest with world_effects set
2. Completing the quest via the "turn in" command
3. Verifying world state changes are recorded
4. Checking that `is_area_cleared()` returns True for cleared locations

## Design Decisions

1. **Dual Recording for area_cleared**: When a quest has an `area_cleared` effect, we record both a `QUEST_WORLD_EFFECT` (for tracking quest-triggered changes) and an `AREA_CLEARED` change (for backwards compatibility with existing `is_area_cleared()` queries).

2. **Metadata Preservation**: The original `effect_type` from WorldEffect is stored in the WorldStateChange's metadata, allowing future queries to distinguish between different types of quest world effects.

3. **Forward Compatibility**: WorldEffect uses a string `effect_type` rather than an enum to allow AI-generated quests to specify custom effect types without code changes.
