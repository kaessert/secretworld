# Lockpicking & Treasure Chests Implementation Summary

## What Was Implemented

### Feature: Lockpicking System
- **Rogue-only `pick` command** to attempt unlocking locked treasure chests
- **DEX-based success formula**: `20% base + (DEX * 2%)`, capped at 80%
- **Difficulty modifiers**: Levels 1-5 modify chance by +20%/+10%/0%/-10%/-20%
- **Lockpick consumable**: Always consumed on attempt (success or fail)
- **`open` command**: Anyone can open unlocked chests
- **One-time loot**: Chests contain items, can only be opened once

### Files Modified

1. **`src/cli_rpg/models/location.py`**
   - Added `treasures: List[dict]` field to Location dataclass
   - Updated `to_dict()` to serialize treasures
   - Updated `from_dict()` to deserialize treasures

2. **`src/cli_rpg/game_state.py`**
   - Added `"pick"` and `"open"` to `KNOWN_COMMANDS`
   - Added aliases: `"lp": "pick"`, `"o": "open"`

3. **`src/cli_rpg/main.py`**
   - Added `pick` command handler (Rogue class check, lockpick consumption, DEX-based roll)
   - Added `open` command handler (locked check, item transfer, opened state tracking)
   - Updated help text with new commands

4. **`src/cli_rpg/world.py`**
   - Added Lockpick item to Market District shop (30 gold)
   - Added "Mossy Chest" to Ancient Grove (difficulty 2, contains Forest Gem + Health Potion)
   - Added "Rusted Strongbox" to Mine Entrance (difficulty 3, contains Mining Pick + Miner's Lantern)

5. **`src/cli_rpg/completer.py`**
   - Added `_complete_treasure()` method for tab completion
   - Hooked into `pick` and `open` commands

### Files Created

1. **`tests/test_lockpicking.py`**
   - 14 tests covering all spec requirements:
     - Rogue can pick locked chest (mock random)
     - Non-Rogue (Warrior/Mage) gets rejection
     - Lockpick consumed on attempt (success and fail)
     - Error when no lockpick in inventory
     - DEX affects success chance
     - Difficulty modifies chance (levels 1-5)
     - Anyone can open unlocked chest
     - Items transfer to inventory on open
     - Cannot reopen already-opened chest
     - Chest state persists through save/load

## Test Results

```
tests/test_lockpicking.py - 14 passed
Full test suite - 2665 passed
```

## Technical Details

### Treasure Chest Data Structure
```python
{
    "name": str,           # Display name
    "description": str,    # Flavor text
    "locked": bool,        # Whether lock needs to be picked
    "difficulty": int,     # 1-5, affects pick success chance
    "opened": bool,        # Whether items have been looted
    "items": List[dict],   # Items to give when opened
    "requires_key": None   # Reserved for future key-based locks
}
```

### Success Chance Formula
```
base_chance = 20 + (DEX * 2)
difficulty_mod = {1: +20, 2: +10, 3: 0, 4: -10, 5: -20}
success_chance = min(80, base_chance + difficulty_mod)
```

### Command Aliases
- `pick` or `lp` for lockpicking
- `open` or `o` for opening chests

## E2E Test Validation
The following scenarios should be validated manually or via E2E tests:
1. Create Rogue character → Buy lockpick → Travel to Ancient Grove → Pick Mossy Chest → Open chest → Get items
2. Create Warrior → Attempt to pick lock → Get "Only Rogues" message
3. Pick lock without lockpick → Get "need Lockpick" message
4. Open already-opened chest → Get "already opened" message
5. Save game with opened chest → Load game → Verify chest still marked opened
