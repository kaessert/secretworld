# Plan: Fix shop context persisting after switching to non-merchant NPC

## Spec

When player talks to a non-merchant NPC after previously talking to a merchant, the shop context (`current_shop`) must be cleared. This prevents `shop`, `buy`, and `sell` commands from working while appearing to converse with a non-merchant.

**Expected behavior:**
- `talk Merchant` → sets `current_shop` to merchant's shop
- `talk Guard` (non-merchant) → clears `current_shop` to `None`
- `shop` after talking to Guard → "You're not at a shop. Talk to a merchant first."

## Test

Add test to `tests/test_shop_commands.py` in `TestTalkCommand` class:

```python
def test_talk_to_non_merchant_clears_shop_context(self, game_with_shop):
    """Talking to non-merchant NPC clears any active shop context."""
    guard = NPC(name="Guard", description="A town guard", dialogue="Move along.", is_merchant=False)
    game_with_shop.get_current_location().npcs.append(guard)

    # Talk to merchant first - sets current_shop
    handle_exploration_command(game_with_shop, "talk", ["merchant"])
    assert game_with_shop.current_shop is not None

    # Talk to non-merchant - should clear current_shop
    handle_exploration_command(game_with_shop, "talk", ["guard"])
    assert game_with_shop.current_shop is None

    # Shop command should now fail
    cont, msg = handle_exploration_command(game_with_shop, "shop", [])
    assert "not at a shop" in msg.lower() or "talk" in msg.lower()
```

## Implementation

**File:** `src/cli_rpg/main.py`, line ~588-590

**Change:** Add `else` clause to clear shop when NPC is not a merchant:

```python
if npc.is_merchant and npc.shop:
    game_state.current_shop = npc.shop
    output += "\n\nType 'shop' to see items, 'buy <item>' to purchase, 'sell <item>' to sell."
else:
    game_state.current_shop = None  # Clear shop context for non-merchants
```

## Verification

```bash
pytest tests/test_shop_commands.py::TestTalkCommand -v
pytest  # Full suite
```
