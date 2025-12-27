# Implementation Summary: Hidden Rooms via Secret Doors

## What Was Implemented

This feature makes discovered hidden doors lead to actual navigable hidden rooms within SubGrid locations, rather than just cosmetic temporary exits.

### Core Changes

1. **`src/cli_rpg/secrets.py`**
   - Added `HIDDEN_ROOM_TEMPLATES` dictionary with category-specific room templates:
     - `dungeon`: Hidden Chamber, Secret Vault, Forgotten Cell
     - `cave`: Crystal Grotto, Hidden Cavern, Secret Pool
     - `forest`: Hidden Glade, Secret Hollow, Fairy Circle
     - `temple`: Hidden Shrine, Secret Crypt, Sacred Chamber
     - `default`: Hidden Room, Secret Alcove, Concealed Chamber

   - Added `generate_hidden_room()` function that:
     - Takes current location, SubGrid, direction, and parent category
     - Calculates target 3D coordinates using `SUBGRID_DIRECTION_OFFSETS`
     - Validates target is within bounds and unoccupied
     - Creates a themed Location using templates
     - Adds 50% chance of hidden treasure secret in the new room
     - Returns the new Location (or None if creation failed)

   - Updated `perform_active_search()` to accept optional `sub_grid` parameter
   - Updated `apply_secret_rewards()` to accept optional `sub_grid` parameter
   - Updated `_apply_hidden_door()` to:
     - Attempt room generation when SubGrid is provided
     - Fall back to temporary_exits when no SubGrid or room creation fails
     - Return descriptive message including new room name

2. **`src/cli_rpg/main.py`**
   - Updated search command handler to pass `game_state.current_sub_grid` to `perform_active_search()`

### New Tests

3. **`tests/test_hidden_rooms.py`** (12 tests)
   - `TestHiddenRoomGeneration`: Tests room creation, bounds checking, occupation detection, template selection, vertical directions, and treasure generation
   - `TestHiddenDoorCreatesRoom`: Tests integration with search command, SubGrid room creation, and fallback to temporary exits
   - `TestHiddenRoomNavigation`: Tests that hidden rooms are navigable and have correct parent set

## Test Results

- All 12 new tests pass
- All 33 existing secret/perception tests pass (no regression)
- Full test suite: **4138 passed** in 110.86s

## Technical Details

### Navigation Flow
1. Player uses `search` command in SubGrid location
2. If hidden_door secret found and passes PER check, `generate_hidden_room()` is called
3. New room is placed at adjacent 3D coordinate in SubGrid
4. Player can now use `go <direction>` to enter the hidden room
5. Room has parent_location set correctly for exit navigation

### Backward Compatibility
- Functions with new `sub_grid` parameter default to `None`
- When `sub_grid=None`, falls back to temporary_exits behavior
- Overworld hidden doors still use cosmetic temporary_exits

### Room Content
- Hidden rooms are themed by parent location category
- 50% chance to contain treasure secret (easy threshold of 8, 20-50 gold)
- Category set to "hidden_room" for potential future differentiation

## E2E Validation

To validate end-to-end:
1. Enter a SubGrid location (dungeon, cave, etc.)
2. Use `search` command in a room with hidden_door secret
3. Verify "A hidden passage to the X reveals <Room Name>!" message
4. Use `go <direction>` to enter the new room
5. Verify room has themed name/description matching parent category
6. Use `search` again to find potential treasure in hidden room
