# Shop Command Auto-Detect Merchant Fix

## Problem
Running `shop` command without first doing `talk Merchant` fails with "You're not at a shop", even when standing in a location with a visible Merchant NPC.

## Solution
Modify the `shop` command handler in `main.py` to auto-detect a merchant NPC in the current location when `current_shop` is None.

## Implementation Steps

### 1. Write Tests
**File:** `tests/test_shop_commands.py`

Add test to `TestShopCommand` class:
```python
def test_shop_auto_detects_merchant(self, game_with_shop):
    """Shop command auto-detects merchant when not in active shop conversation."""
    # Don't talk to merchant first - just use shop directly
    cont, msg = handle_exploration_command(game_with_shop, "shop", [])
    assert cont is True
    assert "Health Potion" in msg
    assert "Iron Sword" in msg
    # Verify shop context was set
    assert game_with_shop.current_shop is not None
```

Add test for multiple merchants (optional - clarifies behavior):
```python
def test_shop_with_multiple_merchants_uses_first(self, game_with_shop):
    """Shop command uses first available merchant when multiple present."""
    # Add second merchant
    from cli_rpg.models.item import Item, ItemType
    from cli_rpg.models.shop import Shop, ShopItem
    potion2 = Item(name="Stamina Potion", description="Restores stamina", item_type=ItemType.CONSUMABLE)
    shop2 = Shop(name="Alchemy Shop", inventory=[ShopItem(item=potion2, buy_price=60)])
    merchant2 = NPC(name="Alchemist", description="A potion maker", dialogue="Need potions?", is_merchant=True, shop=shop2)
    game_with_shop.get_current_location().npcs.append(merchant2)

    cont, msg = handle_exploration_command(game_with_shop, "shop", [])
    assert cont is True
    # Should open first merchant's shop (General Store)
    assert "General Store" in msg or "Health Potion" in msg
```

Add test for no merchant present:
```python
def test_shop_no_merchant_shows_error(self):
    """Shop command shows error when no merchant in location."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    guard = NPC(name="Guard", description="A guard", dialogue="Move along", is_merchant=False)
    town = Location(name="Barracks", description="Guard station", npcs=[guard])
    game = GameState(char, {"Barracks": town}, starting_location="Barracks")

    cont, msg = handle_exploration_command(game, "shop", [])
    assert cont is True
    assert "no merchant" in msg.lower() or "no shop" in msg.lower()
```

### 2. Implement Fix
**File:** `src/cli_rpg/main.py` (line ~652)

Replace:
```python
elif command == "shop":
    if game_state.current_shop is None:
        return (True, "\nYou're not at a shop. Talk to a merchant first.")
```

With:
```python
elif command == "shop":
    if game_state.current_shop is None:
        # Auto-detect merchant in current location
        location = game_state.get_current_location()
        merchant = next((npc for npc in location.npcs if npc.is_merchant and npc.shop), None)
        if merchant is None:
            return (True, "\nThere's no merchant here.")
        game_state.current_shop = merchant.shop
```

### 3. Run Tests
```bash
pytest tests/test_shop_commands.py -v
pytest --cov=src/cli_rpg tests/
```

## Files Changed
- `src/cli_rpg/main.py` - Shop command handler (~3 lines added)
- `tests/test_shop_commands.py` - New test cases (~20 lines)
