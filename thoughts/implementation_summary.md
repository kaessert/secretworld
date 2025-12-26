# Implementation Summary: AI Merchant Detection Fix

## What Was Implemented

### Problem
AI-generated NPCs with merchant-related names (e.g., "Tech Merchant", "Desert Trader") were not working with the `shop` command because:
1. The AI might return `role: "villager"` instead of `role: "merchant"`
2. Even with `is_merchant=True`, no `Shop` object was being created

### Solution

Modified `/src/cli_rpg/ai_world.py` with two changes:

1. **Added `_create_default_merchant_shop()` function** (lines 39-70)
   - Creates a basic shop with three consumable items:
     - Health Potion (50 gold, heals 25 HP)
     - Antidote (40 gold, cures poison)
     - Travel Rations (20 gold, heals 10 HP)
   - Returns a `Shop` object with name "Traveling Wares"

2. **Updated `_create_npcs_from_data()` function** (lines 77-117)
   - Added merchant keyword detection via `MERCHANT_KEYWORDS` set containing: merchant, trader, vendor, shopkeeper, seller, dealer
   - If NPC has `role="villager"` (default) but name contains any merchant keyword (case-insensitive), override role to "merchant"
   - When `is_merchant=True`, automatically create a default shop using `_create_default_merchant_shop()`
   - Shop is now passed to NPC constructor

### Files Modified
| File | Change |
|------|--------|
| `src/cli_rpg/ai_world.py` | Added `_create_default_merchant_shop()`, `MERCHANT_KEYWORDS`, updated `_create_npcs_from_data()` |
| `tests/test_ai_merchant_detection.py` | NEW - 18 test cases covering merchant detection and shop creation |

## Test Results

All 18 new tests pass:
- 9 tests for merchant role inference from names
- 4 tests for merchant shop creation
- 5 tests for default shop contents

Related test suites verified:
- `tests/test_ai_world*.py`: 92 tests pass
- `tests/test_npc.py`: 12 tests pass
- `tests/test_shop.py`: 16 tests pass

## E2E Validation

To validate this fix in gameplay:
1. Start game and travel to a location with AI-generated NPCs
2. Find an NPC with a merchant-related name (Merchant, Trader, Vendor, etc.)
3. Use the `shop` command
4. Verify the shop interface appears with items available
