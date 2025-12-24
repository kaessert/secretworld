# Implementation Summary: Add "use item" support during combat

## What was implemented

Added the ability for players to use consumable items (like health potions) during combat encounters.

### Changes made:

1. **`src/cli_rpg/main.py`**:
   - Added `use` command handler in `handle_combat_command()` (lines 271-293)
   - Command logic:
     - Validates that an item name is provided
     - Looks up item in player's inventory
     - Delegates to `Character.use_item()` for item consumption
     - On success, triggers enemy turn (item usage counts as a turn)
     - Handles player death if enemy kills them after using item
   - Updated help text to list `use <item>` in Combat Commands section (line 44)
   - Updated error message for unknown combat commands to include `use` (line 314)

2. **`tests/test_main_combat_integration.py`**:
   - Added new test class `TestUseItemDuringCombat` with 6 tests:
     - `test_use_health_potion_during_combat_heals_player` - Verifies healing works
     - `test_use_item_during_combat_triggers_enemy_turn` - Verifies enemy attacks after item use
     - `test_use_item_not_found_during_combat` - Error when item doesn't exist
     - `test_use_no_args_during_combat` - Error when no item specified
     - `test_use_non_consumable_during_combat` - Can't use weapons/armor
     - `test_use_potion_at_full_health_during_combat` - Reject when at full health

## Test Results

- All 6 new tests pass
- Full test suite: 723 passed, 1 skipped
- No regressions

## E2E Validation

To manually test this feature:
1. Start a game and enter combat (move to a location with enemies)
2. Take some damage from the enemy
3. Have a health potion in inventory (or buy one from a shop)
4. During combat, type: `use health potion`
5. Verify: Player heals, potion is consumed, enemy attacks

## Technical Notes

- The implementation reuses the existing `Character.use_item()` method which already handles:
  - Consumable validation (only consumables can be used)
  - Full health check (can't use healing items at full health)
  - Item removal from inventory on success
- Using an item counts as the player's turn, triggering enemy retaliation
- Failed item usage (wrong item type, full health, etc.) does NOT trigger enemy turn
