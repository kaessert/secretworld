# Implementation Summary: Caravan Shop Access Fix

## What was Implemented

When a CARAVAN world event is active at the player's current location, the `shop` command now provides access to a temporary caravan shop with exotic/rare items, instead of returning "There's no merchant here."

### Files Modified

1. **`src/cli_rpg/world_events.py`**
   - Added type import for `Shop` in `TYPE_CHECKING` block (line 16)
   - Added new function `get_caravan_shop(game_state)` (lines 582-650) that:
     - Finds active caravan events at the player's current location
     - Returns a `Shop` instance with exotic items:
       - Exotic Spices (50 gold) - stamina restore
       - Traveler's Map (75 gold) - misc item
       - Foreign Elixir (100 gold) - healing potion
       - Rare Gemstone (200 gold) - valuable misc
       - Antidote (40 gold) - cure item for plagues

2. **`src/cli_rpg/main.py`**
   - Modified the `shop` command handler (lines 1305-1317) to:
     - Check for caravan shop when no merchant NPC is found
     - Set `game_state.current_shop` to the caravan shop if one exists
     - Only return "There's no merchant here." if no merchant AND no caravan

3. **`tests/test_world_events.py`**
   - Added test `test_get_caravan_shop_returns_shop` in `TestCaravanEvent` class (lines 394-418) that verifies:
     - Caravan shop is returned when active caravan event exists at location
     - Shop name contains "Caravan"
     - Shop has items in inventory

### Test Results

- All 32 world events tests pass
- All 42 shop-related tests pass
- Full test suite: 3455 tests pass

### Design Decisions

1. **Caravan shop is temporary** - The shop is created on-the-fly when `get_caravan_shop()` is called, not stored persistently. This aligns with the event-based nature of caravans.

2. **Exotic items theme** - Items are designed to feel rare/exotic (spices, foreign elixir, gemstones) fitting the traveling caravan concept.

3. **Includes cure item** - The Antidote in caravan stock provides a way for players to prepare for plague events.

4. **No night restriction** - Caravans don't have the `available_at_night` check that regular merchants have (code structure ensures this).

### E2E Test Validation

The following scenarios should work:
1. Player at location with no NPCs but active caravan event → `shop` shows caravan inventory
2. Player buys from caravan shop → normal buy flow works
3. Caravan event expires → `shop` returns to showing "no merchant here"
