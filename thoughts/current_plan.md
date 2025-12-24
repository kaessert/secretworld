# Plan: Shop Buy Command Partial Name Matching

## Spec
When user types `buy sword` but shop has "Iron Sword":
1. Match partial names (case-insensitive) - "sword" matches "Iron Sword"
2. If multiple matches, show all matching items as suggestions
3. If no matches, show "Did you mean...?" with similar items

## Implementation

### 1. Add `find_items_by_partial_name()` to `Shop` class in `src/cli_rpg/models/shop.py`

```python
def find_items_by_partial_name(self, partial_name: str) -> List[ShopItem]:
    """Find shop items where name contains partial_name (case-insensitive)."""
    partial_lower = partial_name.lower()
    return [si for si in self.inventory if partial_lower in si.item.name.lower()]
```

### 2. Update buy command in `src/cli_rpg/main.py` (lines 416-418)

**Current:**
```python
shop_item = game_state.current_shop.find_item_by_name(item_name)
if shop_item is None:
    return (True, f"\nThe shop doesn't have '{item_name}'.")
```

**New:**
```python
shop_item = game_state.current_shop.find_item_by_name(item_name)
if shop_item is None:
    # Try partial match
    matches = game_state.current_shop.find_items_by_partial_name(item_name)
    if len(matches) == 1:
        shop_item = matches[0]  # Unique partial match - use it
    elif len(matches) > 1:
        names = ", ".join(f"'{m.item.name}'" for m in matches)
        return (True, f"\nMultiple items match '{item_name}': {names}. Please be more specific.")
    else:
        # No matches - list available items
        available = ", ".join(f"'{si.item.name}'" for si in game_state.current_shop.inventory)
        return (True, f"\nThe shop doesn't have '{item_name}'. Available: {available}")
```

## Tests (add to `tests/test_shop_commands.py`)

### 3. Test partial match success
```python
def test_buy_partial_name_match(self, game_with_shop):
    """Buy command matches partial item name."""
    handle_exploration_command(game_with_shop, "talk", ["merchant"])
    cont, msg = handle_exploration_command(game_with_shop, "buy", ["sword"])
    assert "bought" in msg.lower()
    assert "Iron Sword" in msg
```

### 4. Test multiple matches shows options
```python
def test_buy_partial_name_multiple_matches(self, game_with_shop):
    """Buy command shows options when multiple items match."""
    # Add another item with "potion" in name
    from cli_rpg.models.item import Item, ItemType
    from cli_rpg.models.shop import ShopItem
    mana_potion = Item(name="Mana Potion", description="Restores mana", item_type=ItemType.CONSUMABLE)
    game_with_shop.current_shop.inventory.append(ShopItem(item=mana_potion, buy_price=75))

    handle_exploration_command(game_with_shop, "talk", ["merchant"])
    cont, msg = handle_exploration_command(game_with_shop, "buy", ["potion"])
    assert "multiple" in msg.lower()
    assert "Health Potion" in msg
    assert "Mana Potion" in msg
```

### 5. Test no match shows available items
```python
def test_buy_no_match_shows_available(self, game_with_shop):
    """Buy command shows available items when no match found."""
    handle_exploration_command(game_with_shop, "talk", ["merchant"])
    cont, msg = handle_exploration_command(game_with_shop, "buy", ["wand"])
    assert "doesn't have" in msg.lower()
    assert "available" in msg.lower()
    assert "Iron Sword" in msg
```

### 6. Add unit test for `find_items_by_partial_name()` in `tests/test_shop.py`
```python
def test_find_items_by_partial_name(self):
    """find_items_by_partial_name returns matching items."""
    # Setup shop with multiple items
    # Test partial match returns correct items
    # Test case-insensitive matching
    # Test no matches returns empty list
```
