# Implementation Summary: NPC Dialogue Variety (Greeting Text)

## What Was Implemented

Added a `greetings` field to NPCs that allows varied, randomly-selected greeting text for more immersive interactions.

### Files Modified

1. **`src/cli_rpg/models/npc.py`**
   - Added `import random` at top
   - Added `greetings: List[str]` field (default: empty list)
   - Added `get_greeting()` method that returns random greeting or falls back to `dialogue`
   - Updated `to_dict()` to serialize greetings
   - Updated `from_dict()` to deserialize greetings (with backward compatibility)

2. **`src/cli_rpg/main.py`**
   - Changed line 416 from `npc.dialogue` to `npc.get_greeting()`

3. **`src/cli_rpg/world.py`**
   - Added sample greetings list to the default Merchant NPC

### Tests Created

- **`tests/test_npc_greetings.py`** - 7 tests covering:
  - Default empty greetings list
  - Creating NPC with greetings
  - `get_greeting()` returns from list when available
  - `get_greeting()` falls back to dialogue when list empty
  - Serialization includes greetings
  - Deserialization restores greetings
  - Missing greetings in dict defaults to empty (backward compatibility)

## Test Results

- All 7 new tests pass
- Full test suite: **946 passed, 1 skipped**
- No regressions

## Design Decisions

- **Backward compatible**: Old save files without `greetings` work (defaults to empty list)
- **Random selection**: Uses `random.choice()` for variety
- **Fallback behavior**: If greetings empty, uses existing `dialogue` field
- **Optional enhancement**: Default Merchant NPC now has 3 varied greetings

## E2E Validation

- Start game, navigate to Town Square
- Talk to Merchant multiple times
- Verify different greetings appear
