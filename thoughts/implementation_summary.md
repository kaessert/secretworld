# Implementation Summary: Spreading Hazard System (Issue 25)

## Status: COMPLETE

All 4992 tests pass. The spreading hazard system is fully implemented and integrated.

## What Was Implemented

The spreading hazard system for fire and flooding was fully implemented as part of the Dynamic Interior Events feature.

### Files Modified

1. **`src/cli_rpg/interior_events.py`** - Core implementation:
   - Extended `InteriorEvent` dataclass with:
     - `hazard_type: Optional[str]` - "fire" or "flooding"
     - `spread_rooms: Optional[dict]` - Maps `(x,y,z)` -> hour added
     - `max_spread_radius: int` - Maximum rooms from origin (default 3)
   - Added constants:
     - `SPREADING_HAZARD_SPAWN_CHANCE = 0.05`
     - `SPREADING_HAZARD_DURATION_RANGE = (8, 16)`
     - `FIRE_DAMAGE_RANGE = (4, 8)`
     - `FLOODING_TIREDNESS = 3`
     - `MAX_SPREAD_RADIUS = 3`
   - Added functions:
     - `check_for_spreading_hazard()` - 5% spawn on SubGrid entry
     - `spread_hazard()` - Spreads to adjacent rooms each hour
     - `get_active_spreading_hazard_event()` - Get active hazard
     - `clear_spreading_hazard()` - Remove hazard from all rooms on expiry
   - Updated `progress_interior_events()` to handle spreading and expiry

2. **`src/cli_rpg/hazards.py`** - Effect handlers:
   - Added hazard types: `"spreading_fire"`, `"spreading_flood"`
   - `apply_spreading_fire()` - Deals 4-8 damage
   - `apply_spreading_flood()` - 50% movement fail + 3 tiredness
   - Updated `check_hazards_on_entry()` to process new hazard types

3. **`src/cli_rpg/game_state.py`** - Integration:
   - Imported `check_for_spreading_hazard`
   - Called spawn check in `enter()` method alongside rival/ritual spawns

4. **`tests/test_spreading_hazard.py`** - Comprehensive test coverage (21 tests):
   - Model field tests (hazard_type, spread_rooms, max_spread_radius)
   - Spawn mechanics (5% chance, 50/50 fire/flooding, valid categories)
   - Spread mechanics (adjacent rooms, max radius limit, hazard updates)
   - Effect tests (fire damage range, flooding movement penalty + tiredness)
   - Expiry tests (clears after duration, removes from all rooms)
   - Serialization tests (spread_rooms dict round-trip)
   - Integration tests (progress_interior_events spreads hazard)

## Test Results

```
tests/test_spreading_hazard.py: 21 passed
Full suite: 4992 passed
```

## Behavior Summary

- **Fire hazard**: Spawns at random room, spreads to adjacent rooms over time, deals 4-8 damage per turn
- **Flooding hazard**: Spawns at random room, spreads to adjacent rooms, causes 50% movement failure + 3 tiredness per turn
- Both spread 1 room per hour (integrated with `progress_interior_events`)
- Max spread radius of 3 rooms from origin
- Duration: 8-16 hours before dissipating
- Spawn chance: 5% on SubGrid entry (same as cave-ins)
- Valid categories: dungeon, cave, ruins, temple

## E2E Validation Points

- Enter a dungeon/cave/ruins/temple and verify 5% chance of seeing "fire has broken out" or "flooding has begun" message
- Wait in affected SubGrid and observe hazard spreading to adjacent rooms
- Verify fire damage (4-8) and flooding effects (tiredness + movement failure) when in affected rooms
- Wait for duration to expire and verify hazard clears from all rooms
