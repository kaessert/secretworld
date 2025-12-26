# Implementation Summary: NPCs Visible at Current Location in Fog

## What Was Implemented

Fixed bug #3 (HIGH PRIORITY): NPCs were incorrectly shown as "???" at the player's current location during fog weather conditions.

### The Fix
NPCs at the player's current location are now always visible regardless of fog. The fog "obscured" visibility effect now only hides some exits (50% chance each), not NPCs.

## Files Modified

1. **`src/cli_rpg/models/location.py`** (lines 202-205)
   - Removed the conditional logic that obscured NPC names with "???" in fog
   - NPCs are now always shown with their actual names at the player's location
   - Updated docstring to reflect that "obscured" visibility only affects exits

2. **`src/cli_rpg/game_state.py`** (line 335)
   - Updated docstring in `look()` method to remove reference to NPC names being obscured

3. **`src/cli_rpg/models/weather.py`** (line 53)
   - Updated visibility levels comment to remove reference to NPC name obscuring

4. **`tests/test_weather.py`** (lines 472-493, 554-580)
   - Updated `test_location_obscured_visibility_shows_npc_names` to verify NPCs ARE visible in fog
   - Updated `test_look_in_fog_shows_npcs_at_current_location` to verify NPCs ARE visible via GameState.look()

## Test Results

- All 39 weather tests pass
- Full test suite: 3453 tests pass

## Design Decision

The fog weather effect is intended to reduce visibility of distant locations (hidden exits), not obscure things the player is standing directly next to. Players should always be able to see NPCs at their current location.
