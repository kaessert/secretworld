# Implementation Plan: Fix Confusing Error Message When Selling Equipped Items

## Spec

When a player tries to sell an equipped item, the game should:
1. Detect that the item is equipped (as weapon or armor)
2. Return a helpful message explaining why the sell failed
3. Provide guidance on how to unequip the item first

**Current behavior**: `"You don't have '{item_name}' in your inventory."`

**Target behavior**: `"You can't sell {item.name} because it's currently equipped. Unequip it first with 'unequip weapon'."`
(or `'unequip armor'` if it's armor)

## Tests

Add to `tests/test_shop_commands.py` in the `TestSellCommand` class:

```python
def test_sell_equipped_weapon_shows_helpful_message(self, game_with_shop):
    """Sell command shows helpful message when trying to sell equipped weapon."""
    item = Item(name="Battle Axe", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
    game_with_shop.current_character.inventory.add_item(item)
    game_with_shop.current_character.inventory.equip(item)
    handle_exploration_command(game_with_shop, "talk", ["merchant"])
    cont, msg = handle_exploration_command(game_with_shop, "sell", ["battle", "axe"])
    assert cont is True
    assert "equipped" in msg.lower()
    assert "unequip weapon" in msg.lower()

def test_sell_equipped_armor_shows_helpful_message(self, game_with_shop):
    """Sell command shows helpful message when trying to sell equipped armor."""
    item = Item(name="Steel Plate", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=5)
    game_with_shop.current_character.inventory.add_item(item)
    game_with_shop.current_character.inventory.equip(item)
    handle_exploration_command(game_with_shop, "talk", ["merchant"])
    cont, msg = handle_exploration_command(game_with_shop, "sell", ["steel", "plate"])
    assert cont is True
    assert "equipped" in msg.lower()
    assert "unequip armor" in msg.lower()
```

## Implementation

**File**: `src/cli_rpg/main.py`
**Location**: Lines 364-378 (the `sell` command handler)

**Change**: After checking `find_item_by_name` returns `None`, add a check for equipped items before returning the "don't have" message:

```python
elif command == "sell":
    if game_state.current_shop is None:
        return (True, "\nYou're not at a shop. Talk to a merchant first.")
    if not args:
        return (True, "\nSell what? Specify an item name.")
    item_name = " ".join(args)
    item = game_state.current_character.inventory.find_item_by_name(item_name)
    if item is None:
        # Check if item is equipped
        inv = game_state.current_character.inventory
        item_name_lower = item_name.lower()
        if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
            return (True, f"\nYou can't sell {inv.equipped_weapon.name} because it's currently equipped. Unequip it first with 'unequip weapon'.")
        if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
            return (True, f"\nYou can't sell {inv.equipped_armor.name} because it's currently equipped. Unequip it first with 'unequip armor'.")
        return (True, f"\nYou don't have '{item_name}' in your inventory.")
    # Base sell price calculation
    sell_price = 10 + (item.damage_bonus + item.defense_bonus + item.heal_amount) * 2
    game_state.current_character.inventory.remove_item(item)
    game_state.current_character.add_gold(sell_price)
    autosave(game_state)
    return (True, f"\nYou sold {item.name} for {sell_price} gold.")
```

## Verification

1. Run `pytest tests/test_shop_commands.py -v` to verify new tests pass
2. Run full suite `pytest` to ensure no regressions
