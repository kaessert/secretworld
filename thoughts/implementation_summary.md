# Shop Command Auto-Detect Merchant Fix - Implementation Summary

## What Was Implemented

Modified the `shop` command handler in `main.py` to automatically detect and open a merchant's shop when the player is in a location with a merchant NPC, eliminating the need to first run `talk Merchant`.

### Files Modified

1. **`src/cli_rpg/main.py`** (lines 652-659)
   - Changed the `shop` command to auto-detect merchants instead of requiring prior `talk` command
   - When `current_shop` is None, searches location NPCs for first merchant with a shop
   - Shows "There's no merchant here." if no merchant found

2. **`tests/test_shop_commands.py`**
   - Added `test_shop_auto_detects_merchant`: Verifies shop opens without talking to merchant first
   - Added `test_shop_with_multiple_merchants_uses_first`: Verifies first merchant is used when multiple present
   - Added `test_shop_no_merchant_shows_error`: Verifies error when no merchant in location
   - Updated `test_talk_to_non_merchant_clears_shop_context`: Removed outdated assertion about shop failing after talking to non-merchant

## Test Results

- All 26 shop command tests pass
- Full test suite: 1782 passed in 38.50s

## Technical Details

The fix uses a generator expression with `next()` to find the first NPC that is both:
- Marked as a merchant (`npc.is_merchant == True`)
- Has an associated shop (`npc.shop is not None`)

```python
merchant = next((npc for npc in location.npcs if npc.is_merchant and npc.shop), None)
```

## E2E Validation

To validate manually:
1. Start game and navigate to a location with a merchant
2. Run `shop` command without first talking to the merchant
3. Verify shop inventory is displayed
