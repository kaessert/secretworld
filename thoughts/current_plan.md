# Implementation Plan: Add Boss Encounters to Forest Sub-Locations

## Summary
Add boss encounters to the Forest's "Ancient Grove" location, following the pattern established by the Abandoned Mines' Boss Chamber. This creates progression goals and combat variety in the forest area.

## Spec
- **Ancient Grove**: Add a forest-themed boss ("elder_treant" - an ancient tree spirit guardian)
- **Boss template**: Has poison ability (nature's corruption theme)
- **Behavior**: Same as Boss Chamber - triggers on first entry, no respawn after defeat, location becomes safe zone

## Implementation Steps

### Step 1: Add Forest Boss ASCII Art Template
**File**: `src/cli_rpg/combat.py` (after line ~247)
```python
_ASCII_ART_BOSS_TREANT = r"""
     /\  ||  /\
    /  \ || /  \
   /    \||/    \
  |  O   ||   O  |
  |______||______|
      |  ||  |
     /|  ||  |\
    / |__||__| \
"""
```

### Step 2: Add Forest Boss Category to Templates
**File**: `src/cli_rpg/combat.py` (line ~1394-1399)
- Add `"forest": ["Elder Treant", "Grove Guardian", "Ancient Dryad"]` to `boss_templates` dict

### Step 3: Add Elder Treant Boss Type Handler
**File**: `src/cli_rpg/combat.py` in `spawn_boss()` function (after stone_sentinel handler, ~line 1391)
- Add `elif boss_type == "elder_treant":` handler
- Stats: 2x base like other bosses
- Special ability: poison_chance=0.25, poison_damage=5, poison_duration=3 (nature's corruption)
- ASCII art: use new treant template

### Step 4: Update get_boss_ascii_art() for Treant
**File**: `src/cli_rpg/combat.py` (in `get_boss_ascii_art()` function, ~line 1311-1339)
- Add check for treant/tree/forest/dryad/grove keywords to return `_ASCII_ART_BOSS_TREANT`

### Step 5: Configure Ancient Grove with Boss
**File**: `src/cli_rpg/world.py` (line ~326-333)
- Update `ancient_grove` Location to add:
  - `boss_enemy="elder_treant"`
  - Update description to hint at guardian presence

### Step 6: Add Tests
**File**: `tests/test_forest_boss.py` (new file)
- Test Ancient Grove has boss_enemy = "elder_treant"
- Test entering Ancient Grove triggers boss combat
- Test boss has is_boss=True and forest-themed abilities (poison)
- Test boss doesn't respawn after defeat
- Test boss_defeated persists in save/load
- Test spawn_boss with elder_treant returns correct enemy
