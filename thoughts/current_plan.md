# Lockpicking & Treasure Chests Implementation Plan

## Spec
- Rogue-only `pick` command to attempt unlocking locked chests
- DEX-based success: `20% base + (DEX * 2%)`, capped at 80%
- Difficulty levels 1-5 modify chance by +20%/+10%/0%/-10%/-20%
- Lockpick consumable items (consumed on attempt, success or fail)
- `open` command for unlocked chests (anyone can use)
- Chests contain items, can only be opened once

## Tests (tests/test_lockpicking.py)

1. `test_rogue_can_pick_locked_chest` - Rogue with lockpick succeeds (mock random)
2. `test_non_rogue_cannot_pick` - Warrior/Mage get rejection message
3. `test_lockpick_consumed_on_attempt` - Lockpick removed from inventory
4. `test_no_lockpick_fails` - Error if no lockpick in inventory
5. `test_dex_affects_success_chance` - Higher DEX = higher success rate
6. `test_difficulty_modifies_chance` - Difficulty 1-5 adjustments
7. `test_open_unlocked_chest` - Anyone can open unlocked chest
8. `test_chest_items_added_to_inventory` - Items transfer on open
9. `test_chest_cannot_reopen` - Already-opened chest returns message
10. `test_chest_persistence` - Opened state survives save/load

## Implementation Steps

### 1. Add Treasure model to Location
**File**: `src/cli_rpg/models/location.py`
- Add `treasures: List[dict] = field(default_factory=list)` to Location dataclass (~line 35)
- Treasure dict structure: `{"name", "description", "locked", "difficulty", "opened", "items", "requires_key"}`
- Update `to_dict()` (~line 290) to serialize treasures
- Update `from_dict()` (~line 340) to deserialize treasures

### 2. Create lockpick item template
**File**: `src/cli_rpg/world.py`
- Add lockpick item creation in shop setup (~line 230):
  ```python
  lockpick = Item(name="Lockpick", description="A thin metal tool for bypassing locks", item_type=ItemType.CONSUMABLE, heal_amount=0)
  ```
- Add to Market District merchant inventory with ShopItem wrapper, price ~30 gold

### 3. Add commands to parser
**File**: `src/cli_rpg/game_state.py`
- Add `"pick"`, `"open"` to `KNOWN_COMMANDS` set (~line 51)
- Add alias `"lp": "pick"` in `COMMAND_ALIASES` (~line 60)

### 4. Implement pick command handler
**File**: `src/cli_rpg/main.py`
- Add handler in non-combat command section (~line 500):
  - Check `player.character_class == CharacterClass.ROGUE`
  - Check lockpick in inventory
  - Find target chest in `location.treasures`
  - Calculate success: `min(80, 20 + player.dexterity * 2 + difficulty_mod)`
  - On success: set `chest["locked"] = False`
  - Always consume lockpick from inventory
  - Return appropriate message

### 5. Implement open command handler
**File**: `src/cli_rpg/main.py`
- Add handler after pick:
  - Find chest in `location.treasures`
  - Check `not chest["locked"]` or player has required key
  - Check `not chest["opened"]`
  - Add items to player inventory
  - Set `chest["opened"] = True`

### 6. Add sample chests to locations
**File**: `src/cli_rpg/world.py`
- Add locked chest to Ancient Grove (~difficulty 2)
- Add locked chest to Mine entrance (~difficulty 3)
- Each contains 1-2 items (gold, potions, or equipment)

### 7. Add tab completion
**File**: `src/cli_rpg/completer.py`
- Add `"pick"` and `"open"` to completions
- Add chest names as arguments for both commands

### 8. Update help text
**File**: `src/cli_rpg/main.py`
- Add to EXPLORATION_HELP: `"  pick <chest>  - Attempt to pick a lock (Rogue only)"`
- Add to EXPLORATION_HELP: `"  open <chest>  - Open an unlocked chest"`
