# Implementation Plan: Boss Encounter in Boss Chamber

## Summary
Add a boss encounter to the Boss Chamber sub-location in Abandoned Mines, completing the dungeon experience with a unique mine boss, thematic flavor, and special loot.

## Spec
- Boss Chamber triggers a guaranteed boss fight on first entry (not random 30% chance)
- New mine-themed boss: "The Stone Sentinel" (ancient guardian awakened by miners)
- Location tracks if boss has been defeated (prevents respawn)
- Boss has appropriate stats for dungeon difficulty and thematic abilities
- Victory unlocks the chamber for safe exploration afterward

## Test Plan (TDD)

### File: `tests/test_boss_chamber.py`

1. **test_boss_chamber_triggers_boss_on_first_entry**: Enter Boss Chamber triggers combat with a boss enemy
2. **test_boss_chamber_boss_is_stone_sentinel**: Verify boss name and is_boss=True
3. **test_boss_chamber_boss_has_dungeon_stats**: Boss has 2x dungeon category stats
4. **test_boss_chamber_no_respawn_after_defeat**: After defeating boss, entering doesn't trigger combat
5. **test_boss_chamber_boss_defeat_persists_in_save**: boss_defeated flag serializes correctly
6. **test_boss_chamber_safe_after_defeat**: Location becomes safe zone after boss defeated

## Implementation Steps

### Step 1: Extend Location Model
**File**: `src/cli_rpg/models/location.py`
- Add `boss_enemy: Optional[str] = None` field (boss template name)
- Add `boss_defeated: bool = False` field
- Update `to_dict()` and `from_dict()` for serialization

### Step 2: Create Stone Sentinel Boss Template
**File**: `src/cli_rpg/combat.py`
- Add boss template for "stone_sentinel" in `spawn_boss()`:
  - Name: "The Stone Sentinel"
  - Category: dungeon
  - Special abilities: stun_chance (heavy stone fist)
  - Flavor text: awakened by miners' greed
- Add ASCII art for stone/golem boss type

### Step 3: Add Boss Encounter Trigger in GameState.enter()
**File**: `src/cli_rpg/game_state.py`
- In `enter()` method, after moving to sub-location:
  - Check if location has `boss_enemy` and `not boss_defeated`
  - If so, spawn boss using `spawn_boss()` with location's category
  - Start combat encounter
  - Return combat intro message

### Step 4: Mark Boss Defeated on Victory
**File**: `src/cli_rpg/game_state.py`
- After combat ends with victory, check if defeated enemy was location's boss
- Set `location.boss_defeated = True`
- Optionally set `location.is_safe_zone = True`

### Step 5: Configure Boss Chamber in World Creation
**File**: `src/cli_rpg/world.py`
- Update `boss_chamber` location in `create_default_world()`:
  - Set `boss_enemy = "stone_sentinel"`
  - Keep `is_safe_zone = False` (boss makes it dangerous)
  - Add thematic description mentioning the guardian
