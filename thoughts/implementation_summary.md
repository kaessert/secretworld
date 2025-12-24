# Implementation Summary: Quest Acquisition from NPCs

## What Was Implemented

Players can now acquire quests by talking to NPCs. The feature adds a parallel pattern to the existing merchant/shop system.

### New Functionality

1. **NPC Quest-Giver Capability** (`src/cli_rpg/models/npc.py`)
   - Added `is_quest_giver: bool = False` field
   - Added `offered_quests: List[Quest] = []` field
   - Updated `to_dict()` to serialize quest data
   - Updated `from_dict()` to deserialize quest data with backward compatibility

2. **Character Quest Check** (`src/cli_rpg/models/character.py`)
   - Added `has_quest(quest_name: str) -> bool` method
   - Case-insensitive matching

3. **GameState NPC Context** (`src/cli_rpg/game_state.py`)
   - Added `current_npc: Optional[NPC] = None` field
   - Added "accept" to known commands set

4. **Talk Command Updates** (`src/cli_rpg/main.py`)
   - Sets `game_state.current_npc` when talking to an NPC
   - Shows "Available Quests:" section for quest-giver NPCs
   - Filters out quests the player already has
   - Shows "accept <quest>" hint

5. **Accept Command** (`src/cli_rpg/main.py`)
   - New command handler for `accept <quest_name>`
   - Requires NPC context (must talk first)
   - Case-insensitive quest name matching
   - Clones quest with ACTIVE status
   - Prevents accepting duplicate quests
   - Autosaves after accepting

## Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/models/npc.py` | Added `is_quest_giver`, `offered_quests`, updated serialization |
| `src/cli_rpg/models/character.py` | Added `has_quest()` method |
| `src/cli_rpg/game_state.py` | Added `current_npc` field, added "accept" to known commands |
| `src/cli_rpg/main.py` | Updated talk command, added accept command, updated help text |
| `tests/test_npc_quests.py` | New test file with 20 tests covering all functionality |

## Test Results

- **New Tests**: 20 tests in `tests/test_npc_quests.py`
- **Full Suite**: 857 passed, 1 skipped
- **No regressions** in existing functionality

## Test Coverage

The tests cover:
- NPC quest-giver default values
- NPC creation with offered quests
- NPC serialization/deserialization with quests
- Backward compatibility for old NPC data
- Character `has_quest()` method (case-insensitive)
- GameState `current_npc` field
- Talk command showing available quests
- Talk command filtering already-acquired quests
- Talk command setting current NPC context
- Accept command parsing
- Accept command requiring NPC context
- Accept command requiring quest name
- Accept command adding quest to character
- Accept command rejecting duplicates
- Accept command rejecting non-offered quests
- Accept command case-insensitive matching

## E2E Tests Should Validate

1. Talk to a quest-giver NPC and see available quests
2. Accept a quest and verify it appears in quest journal
3. Talk to NPC again and verify accepted quest is no longer shown as available
4. Try to accept the same quest twice and see rejection message
5. Save game with quest-giver NPCs and load successfully
