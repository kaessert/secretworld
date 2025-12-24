# Bug Fix: User finds no NPCs

## Root Cause
AI-generated locations never include NPCs. In `ai_world.py`:
- `create_ai_world()` creates locations with only `name`, `description`, `connections` - no `npcs`
- `expand_world()` same issue - creates locations without NPCs
- The AI prompt in `ai_config.py` doesn't request NPC generation
- The AI service `_parse_location_response()` doesn't parse NPCs

Meanwhile, `world.py:create_default_world()` correctly adds a merchant NPC to Town Square.

## Solution
Add a default merchant NPC to the starting location in AI-generated worlds. This ensures players always have access to a shop.

## Implementation

### 1. Add tests (`tests/test_ai_world_generation.py`)

Add test case:
```python
def test_create_ai_world_starting_location_has_merchant_npc(mock_ai_service):
    """Test starting location has a merchant NPC for shop access."""
    mock_ai_service.generate_location.return_value = {
        "name": "Town Square",
        "description": "A bustling town square.",
        "connections": {}
    }

    world, starting_location = create_ai_world(mock_ai_service, theme="fantasy")

    start_loc = world[starting_location]
    assert len(start_loc.npcs) >= 1
    merchants = [npc for npc in start_loc.npcs if npc.is_merchant]
    assert len(merchants) >= 1
    assert merchants[0].shop is not None
```

### 2. Update `ai_world.py:create_ai_world()`

After creating starting location (around line 84), add merchant NPC:

```python
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType

# Add default merchant to starting location
potion = Item(name="Health Potion", description="Restores 25 HP",
              item_type=ItemType.CONSUMABLE, heal_amount=25)
sword = Item(name="Iron Sword", description="A sturdy blade",
             item_type=ItemType.WEAPON, damage_bonus=5)
armor = Item(name="Leather Armor", description="Light protection",
             item_type=ItemType.ARMOR, defense_bonus=3)
shop_items = [
    ShopItem(item=potion, buy_price=50),
    ShopItem(item=sword, buy_price=100),
    ShopItem(item=armor, buy_price=80)
]
shop = Shop(name="General Store", inventory=shop_items)
merchant = NPC(name="Merchant", description="A friendly shopkeeper with various wares",
               dialogue="Welcome, traveler! Take a look at my goods.",
               is_merchant=True, shop=shop)
starting_location.npcs.append(merchant)
```

### 3. Run tests
```bash
pytest tests/test_ai_world_generation.py::test_create_ai_world_starting_location_has_merchant_npc -v
pytest tests/test_shop_commands.py -v
pytest -x
```

## Files to Modify
- `tests/test_ai_world_generation.py` - Add NPC generation test
- `src/cli_rpg/ai_world.py` - Add merchant NPC to starting location
