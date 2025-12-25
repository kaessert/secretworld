# Implementation Summary: Shop Context Clearing Fix

## What was implemented

Fixed a bug where the shop context (`current_shop`) persisted after switching from a merchant NPC to a non-merchant NPC. Previously, players could still use `shop`, `buy`, and `sell` commands after talking to a non-merchant if they had previously talked to a merchant.

## Changes made

### 1. Test added: `tests/test_shop_commands.py`
- Added `test_talk_to_non_merchant_clears_shop_context` in `TestTalkCommand` class
- Test verifies: merchant talk sets shop → non-merchant talk clears shop → shop command fails

### 2. Fix applied: `src/cli_rpg/main.py` (line ~591)
- Added `else` clause to clear `game_state.current_shop = None` when NPC is not a merchant

```python
if npc.is_merchant and npc.shop:
    game_state.current_shop = npc.shop
    output += "\n\nType 'shop' to see items, 'buy <item>' to purchase, 'sell <item>' to sell."
else:
    game_state.current_shop = None  # Clear shop context for non-merchants
```

## Test results

- New test passes: `test_talk_to_non_merchant_clears_shop_context`
- All 24 shop command tests pass
- Full test suite: **1685 tests passed**

## E2E validation

To manually verify:
1. Talk to a merchant → `shop` command works
2. Talk to a non-merchant (guard, etc.) → `shop` command shows "not at a shop" error
