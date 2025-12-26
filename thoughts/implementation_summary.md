# Implementation Summary: Fix Shop Price Display Inconsistency

## What Was Implemented

Fixed a bug where the `shop` command displayed base prices while the `buy` command used adjusted prices (factoring in CHA modifier, faction reputation, persuade discount, and haggle bonus). This caused player confusion when the displayed price didn't match the actual purchase price.

## Files Modified

1. **`tests/test_faction_shop_prices.py`**
   - Added `test_shop_displays_faction_adjusted_prices` to `TestShopCommandWithFactionReputation` class
   - Test verifies that displayed prices match faction-adjusted prices (80 gold instead of 100 for HONORED)

2. **`src/cli_rpg/main.py`** (lines 1331-1343)
   - Updated shop display logic to calculate prices with all modifiers:
     - CHA modifier (from `get_cha_price_modifier`)
     - Faction reputation modifier (via `faction_buy_mod`)
     - Persuade discount (20% if NPC persuaded)
     - Haggle bonus (if active)
   - This matches the exact price calculation used in the `buy` command

## Technical Details

The fix imports `get_cha_price_modifier` from `social_skills` module and applies the same chain of price modifiers used in the buy command:

```python
display_price = int(si.buy_price * cha_modifier)
if faction_buy_mod is not None:
    display_price = int(display_price * faction_buy_mod)
if game_state.current_npc and game_state.current_npc.persuaded:
    display_price = int(display_price * 0.8)
if game_state.haggle_bonus > 0:
    display_price = int(display_price * (1 - game_state.haggle_bonus))
```

## Test Results

- New test: `test_shop_displays_faction_adjusted_prices` - PASSED
- Related tests (118 shop/charisma/haggle/faction tests) - ALL PASSED
- Full test suite (3454 tests) - ALL PASSED

## E2E Validation

To manually validate:
1. Start game with a merchant NPC
2. Build faction reputation to HONORED (80+)
3. Run `shop` command - prices should show discounted values
4. Run `buy <item>` - charged price should match displayed price
