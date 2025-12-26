# Implementation Plan: Add Boss Encounter to Flooded Level

## Summary
Add a water/mine-themed boss encounter to the "Flooded Level" sub-location in Abandoned Mines. This creates a mid-dungeon challenge before the final Boss Chamber, following the established boss encounter pattern.

## Spec
- **Flooded Level**: Add a mine-themed water boss ("drowned_overseer" - an undead former mine foreman)
- **Boss template**: Has bleed ability (rusted mining tools) + freeze chance (icy water)
- **Behavior**: Triggers on first entry, no respawn after defeat, location becomes safe zone
- **Thematic fit**: An overseer who drowned when the mines flooded, now risen as undead guardian

## Implementation Steps

### Step 1: Add Drowned Overseer ASCII Art Template
**File**: `src/cli_rpg/combat.py` (after `_ASCII_ART_BOSS_TREANT`, ~line 258)
```python
_ASCII_ART_BOSS_DROWNED_OVERSEER = r"""
     .-~~~-.
    ( ~   ~ )
    /|  <>  |\
   / | ~~~~ | \
  |  | |==| |  |
  |  | |  | |  |
  /__| |__| |__\
"""
```

### Step 2: Update get_boss_ascii_art() for Drowned Overseer
**File**: `src/cli_rpg/combat.py` (in `get_boss_ascii_art()` function, ~line 1350)
- Add check for drowned/overseer/flooded keywords to return `_ASCII_ART_BOSS_DROWNED_OVERSEER`

### Step 3: Add Drowned Overseer Boss Type Handler
**File**: `src/cli_rpg/combat.py` in `spawn_boss()` function (after elder_treant handler, ~line 1435)
- Add `if boss_type == "drowned_overseer":` handler
- Stats: 2x base like other bosses
- Special abilities:
  - bleed_chance=0.20, bleed_damage=4, bleed_duration=3 (rusted pickaxe)
  - freeze_chance=0.15, freeze_duration=2 (icy water touch)
- Description: "The former overseer of these mines, drowned when the waters rose. Now he guards the depths with rusted tools and icy hatred."
- attack_flavor: "swings a corroded pickaxe"

### Step 4: Configure Flooded Level with Boss
**File**: `src/cli_rpg/world.py` (line ~479, flooded_level location)
- Update `flooded_level` Location to add:
  - `boss_enemy="drowned_overseer"`
  - Keep existing description (already thematic)

### Step 5: Add Tests
**File**: `tests/test_flooded_level_boss.py` (new file)
- Test Flooded Level has boss_enemy = "drowned_overseer"
- Test entering Flooded Level triggers boss combat
- Test boss has is_boss=True
- Test boss has bleed and freeze abilities
- Test boss doesn't respawn after defeat
- Test boss_defeated persists in save/load
- Test spawn_boss with drowned_overseer returns correct enemy

## Test Command
```bash
pytest tests/test_flooded_level_boss.py -v
```
