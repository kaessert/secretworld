# Implementation Summary: Auto-accept Single Quest

## What Was Implemented

Added auto-accept functionality for the bare `accept` command in `src/cli_rpg/main.py` (lines 1595-1615).

**Behavior:**
- **1 available quest**: Auto-accepts it (sets `args` and continues to normal accept flow)
- **0 available quests**: Shows "X doesn't offer any quests."
- **2+ available quests**: Shows "Accept what? Available: Quest1, Quest2, ..."

Available quests = quests the NPC offers that the player doesn't already have.

## Files Modified

1. **`src/cli_rpg/main.py`** (lines 1586-1618): Added logic in the `accept` command handler to:
   - Check if NPC is a quest giver with offered quests
   - Filter available quests (exclude already-acquired quests)
   - Auto-accept if exactly 1 available, list names if 2+, show "no quests" if 0

2. **`tests/test_npc_quests.py`**: Replaced `test_accept_requires_quest_name` with 4 new tests:
   - `test_accept_auto_accepts_single_quest` - NPC with 1 quest, bare "accept" works
   - `test_accept_lists_quests_when_multiple` - NPC with 2+ quests, shows list
   - `test_accept_no_quests_shows_none` - Non-quest-giver NPC shows "doesn't offer"
   - `test_accept_auto_accepts_only_available_quest` - Player has 1 of 2 quests, auto-accepts remaining

## Test Results

All 23 tests in `tests/test_npc_quests.py` pass, including the 4 new tests and all existing tests (no regressions).

## E2E Validation

To test manually:
1. Start game, find an NPC quest giver with 1 quest
2. `talk <npc_name>` to start conversation
3. Type `accept` (no args) - quest should be accepted automatically
4. Find NPC with 2+ quests, type bare `accept` - should list available quest names
