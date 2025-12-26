# Implementation Plan: Caravan Shop Access Fix

## Spec

When a CARAVAN world event is active at the player's current location, the `shop` command should provide access to a temporary caravan shop with exotic/rare items, instead of returning "There's no merchant here."

## Files to Modify

1. `src/cli_rpg/world_events.py` - Add caravan shop creation function
2. `src/cli_rpg/main.py` - Modify shop command to check for caravan events
3. `tests/test_world_events.py` - Add test for shop command with caravan

## Tests

### New Test: `tests/test_world_events.py`

Add to `TestCaravanEvent` class:

```python
def test_get_caravan_shop_returns_shop(self, game_state):
    """Test that caravan event provides a shop.

    Spec: Active caravan at location → shop command works
    """
    from cli_rpg.world_events import get_caravan_shop

    # Add caravan event at current location
    caravan_event = WorldEvent(
        event_id="caravan_001",
        name="Merchant Caravan",
        description="A caravan arrives",
        event_type="caravan",
        affected_locations=["Town"],
        start_hour=game_state.game_time.hour,
        duration_hours=16,
    )
    game_state.world_events.append(caravan_event)

    # Get caravan shop
    shop = get_caravan_shop(game_state)

    assert shop is not None
    assert "Caravan" in shop.name or "caravan" in shop.name.lower()
    assert len(shop.inventory) > 0  # Should have items
```

## Implementation Steps

### Step 1: Add `get_caravan_shop()` to `world_events.py`

Add function after line ~580 (after `check_and_resolve_caravan`):

```python
def get_caravan_shop(game_state: "GameState") -> Optional["Shop"]:
    """Get a temporary shop from an active caravan event at current location.

    Args:
        game_state: Current game state

    Returns:
        Shop instance if caravan active at location, None otherwise
    """
    from cli_rpg.models.shop import Shop, ShopItem
    from cli_rpg.models.item import Item, ItemType

    # Find active caravan at current location
    for event in game_state.world_events:
        if (
            event.is_active
            and event.event_type == "caravan"
            and game_state.current_location in event.affected_locations
        ):
            # Create temporary caravan shop with exotic items
            return Shop(
                name=f"{event.name}",
                inventory=[
                    ShopItem(
                        item=Item(
                            name="Exotic Spices",
                            description="Rare spices from distant lands. Restores stamina.",
                            item_type=ItemType.CONSUMABLE,
                            stamina_restore=30,
                        ),
                        buy_price=50,
                    ),
                    ShopItem(
                        item=Item(
                            name="Traveler's Map",
                            description="A detailed map revealing hidden paths.",
                            item_type=ItemType.MISC,
                        ),
                        buy_price=75,
                    ),
                    ShopItem(
                        item=Item(
                            name="Foreign Elixir",
                            description="A potent healing elixir from far away.",
                            item_type=ItemType.CONSUMABLE,
                            heal_amount=75,
                        ),
                        buy_price=100,
                    ),
                    ShopItem(
                        item=Item(
                            name="Rare Gemstone",
                            description="A valuable gemstone sought by collectors.",
                            item_type=ItemType.MISC,
                        ),
                        buy_price=200,
                    ),
                    ShopItem(
                        item=Item(
                            name="Antidote",
                            description="Cures poison and plague afflictions.",
                            item_type=ItemType.CONSUMABLE,
                            is_cure=True,
                        ),
                        buy_price=40,
                    ),
                ],
            )
    return None
```

### Step 2: Modify `shop` command in `main.py` (lines 1300-1310)

Change from:
```python
elif command == "shop":
    if game_state.current_shop is None:
        # Auto-detect merchant in current location
        location = game_state.get_current_location()
        merchant = next((npc for npc in location.npcs if npc.is_merchant and npc.shop), None)
        if merchant is None:
            return (True, "\nThere's no merchant here.")
```

To:
```python
elif command == "shop":
    if game_state.current_shop is None:
        # Auto-detect merchant in current location
        location = game_state.get_current_location()
        merchant = next((npc for npc in location.npcs if npc.is_merchant and npc.shop), None)
        if merchant is None:
            # Check for active caravan event at this location
            from cli_rpg.world_events import get_caravan_shop
            caravan_shop = get_caravan_shop(game_state)
            if caravan_shop is not None:
                game_state.current_shop = caravan_shop
            else:
                return (True, "\nThere's no merchant here.")
```

### Step 3: Run tests to verify

```bash
pytest tests/test_world_events.py -v -k "caravan"
```
