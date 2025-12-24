# Implementation Summary: Fix No NPCs in AI-Generated Worlds

## What Was Implemented

Added a default merchant NPC to the starting location in AI-generated worlds, ensuring players always have access to a shop.

## Files Modified

### `src/cli_rpg/ai_world.py`
- Added imports for `NPC`, `Shop`, `ShopItem`, `Item`, and `ItemType` models
- After creating the starting location in `create_ai_world()`, added code to:
  - Create three shop items: Health Potion (50g), Iron Sword (100g), Leather Armor (80g)
  - Create a Shop named "General Store" with these items
  - Create a merchant NPC with dialogue and the shop attached
  - Append the merchant to the starting location's `npcs` list

### `tests/test_ai_world_generation.py`
- Added new test `test_create_ai_world_starting_location_has_merchant_npc()` that verifies:
  - Starting location has at least one NPC
  - At least one NPC is a merchant (`is_merchant=True`)
  - The merchant has a shop attached (`shop is not None`)

## Test Results

All 805 tests pass (1 skipped).

## Design Decisions

- The merchant NPC is added directly to the starting location object after it's created
- Shop inventory matches the default world's merchant (consistent player experience)
- The fix is minimal and surgical - only affects the starting location in AI-generated worlds

## E2E Validation

Players should be able to:
1. Start a new game with AI world generation
2. Use the `talk` command to interact with the merchant
3. Use `shop` or `buy`/`sell` commands to access the store
4. Purchase items like Health Potion, Iron Sword, and Leather Armor
