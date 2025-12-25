# Brave Player Rewards - Implementation Summary

## What Was Implemented

Added a "Dread Treasure" system that rewards players who venture into high-dread areas (75%+) rather than always managing their dread down.

### New Files

**`src/cli_rpg/brave_rewards.py`** - New module containing:
- `BRAVE_REWARD_DREAD_THRESHOLD` constant (75%)
- `DREAD_TREASURE_CHANCE` constant (30%)
- `DREAD_TREASURES` list with 4 powerful themed items:
  - Shadow Essence (consumable, heals 50 HP)
  - Veil of Courage (armor, +8 defense)
  - Dread Blade (weapon, +10 damage)
  - Darklight Torch (consumable, 20 moves of light)
- `check_for_dread_treasure()` function - Checks if player discovers treasure
- `get_discovery_message()` function - Returns thematic discovery message

**`tests/test_brave_rewards.py`** - Comprehensive test suite with:
- 5 tests for treasure discovery conditions
- 3 tests for treasure item definitions
- 2 integration tests with GameState.look()
- 2 tests for discovery message formatting

### Modified Files

**`src/cli_rpg/game_state.py`** - Updated `look()` method (lines 245-284):
- Added dread treasure check after location description
- Treasure is automatically added to inventory if found
- Handles full inventory case with warning message
- Updated docstring to document the new behavior

## Test Results

All tests pass:
- 12/12 brave_rewards tests pass
- 2343/2343 full test suite passes

## Technical Details

### How It Works
1. When player uses `look` command, the `GameState.look()` method is called
2. After getting the layered description, it calls `check_for_dread_treasure()`
3. If player has 75%+ dread, is on their 3rd+ look, AND the 30% chance succeeds:
   - A random dread treasure is created and added to inventory
   - A thematic discovery message is appended to the look result
4. If inventory is full, a warning message is shown instead

### Thematic Tie-in
The system rewards brave players who embrace the darkness rather than fleeing from it. The flavor text emphasizes that "the darkness reveals its secrets to those who dare face it" - making high dread a risk/reward tradeoff rather than purely negative.

## E2E Test Validation

To manually verify:
1. Start game and travel to a dungeon/cave
2. Build dread to 75%+ (travel at night, enter dungeons)
3. Use `look` command 3+ times in the same location
4. With 30% chance, you should see the discovery message and find a dread treasure in inventory
