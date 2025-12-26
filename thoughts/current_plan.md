# Implementation Plan: NPCs shown as "???" in fog weather (HIGH PRIORITY BUG #3)

## Bug Summary
NPC names display as "???" at the player's current location during fog conditions. Players should be able to see NPCs they're standing next to - fog should only obscure NPCs at distant locations, not at the player's current position.

## Root Cause
In `models/location.py` line 204-207, when `visibility == "obscured"`, ALL NPC names are replaced with "???". This applies even to the player's current location via `game_state.look()`.

## Design Decision
**NPC names should always be visible at the player's current location regardless of fog.** The fog "obscured" effect should NOT hide NPC names at the player's position - only exits should be partially hidden in fog.

## Implementation Steps

### 1. Update test to reflect correct behavior
**File:** `tests/test_weather.py`

Modify `test_location_obscured_visibility_obscures_npc_names` (line 472-493) to assert that NPC names ARE visible even in obscured visibility, since `get_layered_description` is used for the player's current location.

### 2. Update test `test_look_in_fog_obscures_visibility`
**File:** `tests/test_weather.py`

Modify the test at line 554-579 to assert that NPC names ARE visible in fog at the player's current location.

### 3. Fix NPC visibility in fog
**File:** `src/cli_rpg/models/location.py`

Change lines 202-210 to always show NPC names, removing the "obscured" special case for NPCs:

```python
# Before (line 202-210):
if self.npcs:
    if visibility == "obscured":
        # Show "???" for each NPC instead of their names
        obscured_names = [colors.npc("???") for _ in self.npcs]
        result += f"NPCs: {', '.join(obscured_names)}\n"
    else:
        npc_names = [colors.npc(npc.name) for npc in self.npcs]
        result += f"NPCs: {', '.join(npc_names)}\n"

# After:
if self.npcs:
    # NPCs are always visible at the player's current location
    npc_names = [colors.npc(npc.name) for npc in self.npcs]
    result += f"NPCs: {', '.join(npc_names)}\n"
```

### 4. Update docstrings
Update the visibility docstring in `models/location.py` line 181 to remove reference to NPC names being obscured.

Update the docstring in `game_state.py` line 335 to remove reference to NPC names.

Update the comment in `models/weather.py` line 53 to remove reference to NPC names.

### 5. Run tests
```bash
pytest tests/test_weather.py -v
pytest -x
```

## Files to Modify
1. `tests/test_weather.py` - Update 2 tests
2. `src/cli_rpg/models/location.py` - Remove NPC obscuring logic, update docstring
3. `src/cli_rpg/game_state.py` - Update docstring comment
4. `src/cli_rpg/models/weather.py` - Update visibility level comment
