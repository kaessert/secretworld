# Plan: Add NPC Shop System

## Summary
Add a basic NPC shop system where players can buy/sell items using gold. This leverages the existing gold (misc loot), inventory, and item infrastructure.

## Spec

### Gold System (Character Enhancement)
- Add `gold: int = 0` attribute to Character
- Add `add_gold(amount)` and `remove_gold(amount)` methods
- Display gold in `status` command output
- Award gold on combat victory (random amount based on enemy level)

### NPC Model
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | NPC identifier (2-30 chars) |
| `description` | str | What player sees (1-200 chars) |
| `dialogue` | str | What NPC says when talked to |
| `is_merchant` | bool | Whether NPC runs a shop |

### Shop Model
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Shop name |
| `inventory` | List[ShopItem] | Items for sale with prices |

### ShopItem (Item + price)
| Field | Type | Description |
|-------|------|-------------|
| `item` | Item | The item being sold |
| `buy_price` | int | Cost to buy from shop |
| `sell_price` | int | Gold received when selling (50% of buy price) |

### Commands
| Command | Syntax | Behavior |
|---------|--------|----------|
| `talk` | `talk <npc name>` | Show NPC dialogue; if merchant, show shop options |
| `buy` | `buy <item name>` | Purchase item if enough gold and inventory space |
| `sell` | `sell <item name>` | Sell item from inventory for gold |
| `shop` | `shop` | List shop inventory and prices (when talking to merchant) |

### Location Enhancement
- Add `npcs: List[NPC]` to Location model
- NPCs persist with world save/load

## Tests First

**File:** `tests/test_npc.py`
```python
"""Tests for NPC model."""
import pytest
from cli_rpg.models.npc import NPC

class TestNPC:
    def test_create_npc(self):
        npc = NPC(name="Merchant", description="A friendly shopkeeper", dialogue="Welcome!", is_merchant=True)
        assert npc.name == "Merchant"
        assert npc.is_merchant is True

    def test_npc_name_validation(self):
        with pytest.raises(ValueError):
            NPC(name="X", description="Too short name", dialogue="Hi")

    def test_npc_serialization(self):
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello!", is_merchant=True)
        data = npc.to_dict()
        restored = NPC.from_dict(data)
        assert restored.name == npc.name
        assert restored.is_merchant == npc.is_merchant
```

**File:** `tests/test_shop.py`
```python
"""Tests for Shop model."""
import pytest
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType

class TestShopItem:
    def test_create_shop_item(self):
        item = Item(name="Health Potion", description="Heals 25 HP", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        assert shop_item.buy_price == 50
        assert shop_item.sell_price == 25  # 50% of buy price

class TestShop:
    def test_create_shop(self):
        item = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        shop = Shop(name="Potion Shop", inventory=[shop_item])
        assert len(shop.inventory) == 1

    def test_shop_serialization(self):
        item = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        shop_item = ShopItem(item=item, buy_price=100)
        shop = Shop(name="Armory", inventory=[shop_item])
        data = shop.to_dict()
        restored = Shop.from_dict(data)
        assert restored.name == shop.name
        assert len(restored.inventory) == 1
```

**File:** `tests/test_gold.py`
```python
"""Tests for gold system."""
import pytest
from cli_rpg.models.character import Character

class TestGold:
    def test_character_starts_with_zero_gold(self):
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        assert char.gold == 0

    def test_add_gold(self):
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(100)
        assert char.gold == 100

    def test_remove_gold_success(self):
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(100)
        success = char.remove_gold(50)
        assert success is True
        assert char.gold == 50

    def test_remove_gold_insufficient(self):
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(30)
        success = char.remove_gold(50)
        assert success is False
        assert char.gold == 30  # Unchanged

    def test_gold_serialization(self):
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(250)
        data = char.to_dict()
        assert data["gold"] == 250
```

**File:** `tests/test_shop_commands.py`
```python
"""Tests for shop commands in main game loop."""
import pytest
from cli_rpg.main import handle_exploration_command
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType

@pytest.fixture
def game_with_shop():
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    char.add_gold(200)

    potion = Item(name="Health Potion", description="Heals 25 HP", item_type=ItemType.CONSUMABLE, heal_amount=25)
    sword = Item(name="Iron Sword", description="A blade", item_type=ItemType.WEAPON, damage_bonus=5)
    shop_items = [ShopItem(item=potion, buy_price=50), ShopItem(item=sword, buy_price=150)]
    shop = Shop(name="General Store", inventory=shop_items)

    merchant = NPC(name="Merchant", description="A friendly shopkeeper", dialogue="Welcome to my shop!", is_merchant=True, shop=shop)

    town = Location(name="Town", description="A quiet town", npcs=[merchant])
    world = {"Town": town}
    return GameState(char, world, starting_location="Town")

class TestTalkCommand:
    def test_talk_to_merchant(self, game_with_shop):
        cont, msg = handle_exploration_command(game_with_shop, "talk", ["merchant"])
        assert cont is True
        assert "Welcome to my shop" in msg
        assert game_with_shop.current_shop is not None

    def test_talk_npc_not_found(self, game_with_shop):
        cont, msg = handle_exploration_command(game_with_shop, "talk", ["nobody"])
        assert cont is True
        assert "don't see" in msg.lower() or "not here" in msg.lower()

    def test_talk_no_args(self, game_with_shop):
        cont, msg = handle_exploration_command(game_with_shop, "talk", [])
        assert cont is True
        assert "who" in msg.lower() or "specify" in msg.lower()

class TestBuyCommand:
    def test_buy_item_success(self, game_with_shop):
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["health", "potion"])
        assert cont is True
        assert "bought" in msg.lower() or "purchased" in msg.lower()
        assert game_with_shop.current_character.gold == 150  # 200 - 50
        assert game_with_shop.current_character.inventory.find_item_by_name("Health Potion") is not None

    def test_buy_insufficient_gold(self, game_with_shop):
        game_with_shop.current_character.gold = 10
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["iron", "sword"])
        assert cont is True
        assert "afford" in msg.lower() or "gold" in msg.lower()

    def test_buy_not_in_shop(self, game_with_shop):
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["health", "potion"])
        assert cont is True
        assert "shop" in msg.lower() or "talk" in msg.lower()

class TestSellCommand:
    def test_sell_item_success(self, game_with_shop):
        item = Item(name="Old Sword", description="Rusty", item_type=ItemType.WEAPON, damage_bonus=2)
        game_with_shop.current_character.inventory.add_item(item)
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        old_gold = game_with_shop.current_character.gold
        cont, msg = handle_exploration_command(game_with_shop, "sell", ["old", "sword"])
        assert cont is True
        assert "sold" in msg.lower()
        assert game_with_shop.current_character.gold > old_gold
        assert game_with_shop.current_character.inventory.find_item_by_name("Old Sword") is None

    def test_sell_item_not_in_inventory(self, game_with_shop):
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "sell", ["nonexistent"])
        assert cont is True
        assert "don't have" in msg.lower()

class TestShopCommand:
    def test_shop_lists_items(self, game_with_shop):
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "shop", [])
        assert cont is True
        assert "Health Potion" in msg
        assert "50" in msg  # Price
        assert "Iron Sword" in msg

class TestParseShopCommands:
    def test_parse_talk(self):
        cmd, args = parse_command("talk merchant")
        assert cmd == "talk"
        assert args == ["merchant"]

    def test_parse_buy(self):
        cmd, args = parse_command("buy health potion")
        assert cmd == "buy"
        assert args == ["health", "potion"]

    def test_parse_sell(self):
        cmd, args = parse_command("sell old sword")
        assert cmd == "sell"
        assert args == ["old", "sword"]

    def test_parse_shop(self):
        cmd, args = parse_command("shop")
        assert cmd == "shop"
```

## Implementation Steps

### Phase 1: Gold System

#### 1.1 Update `src/cli_rpg/models/character.py`

Add gold attribute and methods:
```python
# Add to Character dataclass fields (after xp_to_next_level)
gold: int = 0

# Add methods
def add_gold(self, amount: int) -> None:
    """Add gold to character."""
    if amount < 0:
        raise ValueError("Amount must be non-negative")
    self.gold += amount

def remove_gold(self, amount: int) -> bool:
    """Remove gold from character. Returns False if insufficient."""
    if amount < 0:
        raise ValueError("Amount must be non-negative")
    if self.gold < amount:
        return False
    self.gold -= amount
    return True
```

Update `to_dict()` to include `"gold": self.gold`
Update `from_dict()` to restore `gold=data.get("gold", 0)`

#### 1.2 Update `src/cli_rpg/combat.py` - `end_combat()` method

Add gold reward on victory:
```python
# In end_combat(), after XP reward:
gold_reward = random.randint(5, 15) * self.enemy.level
self.player.add_gold(gold_reward)
# Update return message to include gold
```

#### 1.3 Update status command in `src/cli_rpg/main.py`

Show gold in status output alongside other stats.

### Phase 2: NPC Model

#### 2.1 Create `src/cli_rpg/models/npc.py`

```python
"""NPC model for non-hostile characters."""
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.shop import Shop

@dataclass
class NPC:
    name: str
    description: str
    dialogue: str
    is_merchant: bool = False
    shop: Optional["Shop"] = None

    def __post_init__(self):
        if not 2 <= len(self.name) <= 30:
            raise ValueError("NPC name must be 2-30 characters")
        if not 1 <= len(self.description) <= 200:
            raise ValueError("Description must be 1-200 characters")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "dialogue": self.dialogue,
            "is_merchant": self.is_merchant,
            "shop": self.shop.to_dict() if self.shop else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        from cli_rpg.models.shop import Shop
        shop = Shop.from_dict(data["shop"]) if data.get("shop") else None
        return cls(
            name=data["name"],
            description=data["description"],
            dialogue=data["dialogue"],
            is_merchant=data.get("is_merchant", False),
            shop=shop
        )
```

### Phase 3: Shop Model

#### 3.1 Create `src/cli_rpg/models/shop.py`

```python
"""Shop model for merchant NPCs."""
from dataclasses import dataclass, field
from typing import List
from cli_rpg.models.item import Item

@dataclass
class ShopItem:
    item: Item
    buy_price: int

    @property
    def sell_price(self) -> int:
        """Sell price is 50% of buy price."""
        return self.buy_price // 2

    def to_dict(self) -> dict:
        return {
            "item": self.item.to_dict(),
            "buy_price": self.buy_price
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShopItem":
        return cls(
            item=Item.from_dict(data["item"]),
            buy_price=data["buy_price"]
        )

@dataclass
class Shop:
    name: str
    inventory: List[ShopItem] = field(default_factory=list)

    def find_item_by_name(self, name: str) -> Optional[ShopItem]:
        """Case-insensitive item search."""
        name_lower = name.lower()
        for shop_item in self.inventory:
            if shop_item.item.name.lower() == name_lower:
                return shop_item
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "inventory": [si.to_dict() for si in self.inventory]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Shop":
        return cls(
            name=data["name"],
            inventory=[ShopItem.from_dict(si) for si in data.get("inventory", [])]
        )
```

### Phase 4: Location Enhancement

#### 4.1 Update `src/cli_rpg/models/location.py`

Add NPCs field:
```python
# Add to imports
from typing import List, Optional
from cli_rpg.models.npc import NPC

# Add to Location dataclass
npcs: List[NPC] = field(default_factory=list)

# Add method
def find_npc_by_name(self, name: str) -> Optional[NPC]:
    """Case-insensitive NPC search."""
    name_lower = name.lower()
    for npc in self.npcs:
        if npc.name.lower() == name_lower:
            return npc
    return None
```

Update `to_dict()` to include `"npcs": [npc.to_dict() for npc in self.npcs]`
Update `from_dict()` to restore NPCs
Update `__str__()` to show NPCs present: "NPCs: Merchant, Guard"

### Phase 5: GameState Enhancement

#### 5.1 Update `src/cli_rpg/game_state.py`

Add shop state tracking:
```python
# Add to GameState class
current_shop: Optional[Shop] = None  # Active shop interaction

# Add to known_commands in parse_command()
known_commands = {..., "talk", "buy", "sell", "shop"}

# Add helper method
def get_current_location_npcs(self) -> List[NPC]:
    """Get NPCs at current location."""
    location = self.world.get(self.current_location)
    return location.npcs if location else []
```

### Phase 6: Command Handlers

#### 6.1 Update `src/cli_rpg/main.py` - `handle_exploration_command()`

Add new command handlers:

```python
elif command == "talk":
    if not args:
        return (True, "\nTalk to whom? Specify an NPC name.")
    npc_name = " ".join(args)
    location = game_state.world.get(game_state.current_location)
    npc = location.find_npc_by_name(npc_name) if location else None
    if npc is None:
        return (True, f"\nYou don't see '{npc_name}' here.")
    output = f"\n{npc.name}: \"{npc.dialogue}\""
    if npc.is_merchant and npc.shop:
        game_state.current_shop = npc.shop
        output += f"\n\nType 'shop' to see items, 'buy <item>' to purchase, 'sell <item>' to sell."
    return (True, output)

elif command == "shop":
    if game_state.current_shop is None:
        return (True, "\nYou're not at a shop. Talk to a merchant first.")
    shop = game_state.current_shop
    lines = [f"\n=== {shop.name} ===", f"Your gold: {game_state.current_character.gold}", ""]
    for si in shop.inventory:
        lines.append(f"  {si.item.name} - {si.buy_price} gold")
    return (True, "\n".join(lines))

elif command == "buy":
    if game_state.current_shop is None:
        return (True, "\nYou're not at a shop. Talk to a merchant first.")
    if not args:
        return (True, "\nBuy what? Specify an item name.")
    item_name = " ".join(args)
    shop_item = game_state.current_shop.find_item_by_name(item_name)
    if shop_item is None:
        return (True, f"\nThe shop doesn't have '{item_name}'.")
    if game_state.current_character.gold < shop_item.buy_price:
        return (True, f"\nYou can't afford {shop_item.item.name} ({shop_item.buy_price} gold). You have {game_state.current_character.gold} gold.")
    if game_state.current_character.inventory.is_full():
        return (True, "\nYour inventory is full!")
    # Create a copy of the item for the player
    new_item = Item(
        name=shop_item.item.name,
        description=shop_item.item.description,
        item_type=shop_item.item.item_type,
        damage_bonus=shop_item.item.damage_bonus,
        defense_bonus=shop_item.item.defense_bonus,
        heal_amount=shop_item.item.heal_amount
    )
    game_state.current_character.remove_gold(shop_item.buy_price)
    game_state.current_character.inventory.add_item(new_item)
    autosave(game_state)
    return (True, f"\nYou bought {new_item.name} for {shop_item.buy_price} gold.")

elif command == "sell":
    if game_state.current_shop is None:
        return (True, "\nYou're not at a shop. Talk to a merchant first.")
    if not args:
        return (True, "\nSell what? Specify an item name.")
    item_name = " ".join(args)
    item = game_state.current_character.inventory.find_item_by_name(item_name)
    if item is None:
        return (True, f"\nYou don't have '{item_name}' in your inventory.")
    # Base sell price calculation (could be enhanced later)
    sell_price = 10 + (item.damage_bonus + item.defense_bonus + item.heal_amount) * 2
    game_state.current_character.inventory.remove_item(item)
    game_state.current_character.add_gold(sell_price)
    autosave(game_state)
    return (True, f"\nYou sold {item.name} for {sell_price} gold.")
```

### Phase 7: World Generation

#### 7.1 Update `src/cli_rpg/world.py` - `create_default_world()`

Add a merchant NPC to the starting town:
```python
# Create default merchant shop
potion = Item(name="Health Potion", description="Restores 25 HP", item_type=ItemType.CONSUMABLE, heal_amount=25)
sword = Item(name="Iron Sword", description="A sturdy blade", item_type=ItemType.WEAPON, damage_bonus=5)
armor = Item(name="Leather Armor", description="Light protection", item_type=ItemType.ARMOR, defense_bonus=3)

shop_items = [
    ShopItem(item=potion, buy_price=50),
    ShopItem(item=sword, buy_price=100),
    ShopItem(item=armor, buy_price=80)
]
shop = Shop(name="General Store", inventory=shop_items)
merchant = NPC(name="Merchant", description="A friendly shopkeeper with various wares", dialogue="Welcome, traveler! Take a look at my goods.", is_merchant=True, shop=shop)

# Add to Town location
town.npcs.append(merchant)
```

### Phase 8: Help Text Updates

#### 8.1 Update help text in `src/cli_rpg/main.py`

Add NPC/shop commands to exploration help:
```python
print("  talk <npc>     - Talk to an NPC")
print("  shop           - View shop inventory (when at a shop)")
print("  buy <item>     - Buy an item from the shop")
print("  sell <item>    - Sell an item to the shop")
```

## Verification

```bash
# Run new tests first
pytest tests/test_gold.py -v
pytest tests/test_npc.py -v
pytest tests/test_shop.py -v
pytest tests/test_shop_commands.py -v

# Full test suite
pytest tests/ -v

# Manual verification
python -m cli_rpg.main
# Create character, go to town, talk merchant, buy/sell items
```
