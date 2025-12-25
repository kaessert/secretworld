"""Tests for Shop model.

Tests the Shop and ShopItem models including pricing and serialization.
"""
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType


class TestShopItem:
    """Tests for ShopItem - tests spec: ShopItem (Item + price)."""

    def test_create_shop_item(self):
        """ShopItem can be created with item and buy price."""
        item = Item(name="Health Potion", description="Heals 25 HP", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        assert shop_item.item.name == "Health Potion"
        assert shop_item.buy_price == 50

    def test_sell_price_is_half_buy_price(self):
        """Sell price is 50% of buy price (integer division)."""
        item = Item(name="Health Potion", description="Heals 25 HP", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        assert shop_item.sell_price == 25  # 50% of buy price

    def test_sell_price_rounds_down(self):
        """Sell price rounds down on odd buy prices."""
        item = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        shop_item = ShopItem(item=item, buy_price=99)
        assert shop_item.sell_price == 49  # 99 // 2 = 49

    def test_shop_item_serialization(self):
        """ShopItem can be serialized to dict."""
        item = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        shop_item = ShopItem(item=item, buy_price=100)
        data = shop_item.to_dict()
        assert data["buy_price"] == 100
        assert data["item"]["name"] == "Sword"

    def test_shop_item_deserialization(self):
        """ShopItem can be deserialized from dict."""
        item = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        shop_item = ShopItem(item=item, buy_price=100)
        data = shop_item.to_dict()
        restored = ShopItem.from_dict(data)
        assert restored.item.name == shop_item.item.name
        assert restored.buy_price == shop_item.buy_price


class TestShop:
    """Tests for Shop - tests spec: Shop Model."""

    def test_create_shop(self):
        """Shop can be created with name and inventory."""
        item = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        shop = Shop(name="Potion Shop", inventory=[shop_item])
        assert shop.name == "Potion Shop"
        assert len(shop.inventory) == 1

    def test_create_empty_shop(self):
        """Shop can be created with empty inventory."""
        shop = Shop(name="Empty Shop")
        assert len(shop.inventory) == 0

    def test_find_item_by_name_exact(self):
        """find_item_by_name finds item with exact name match."""
        item = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        shop = Shop(name="Potion Shop", inventory=[shop_item])
        found = shop.find_item_by_name("Health Potion")
        assert found is not None
        assert found.item.name == "Health Potion"

    def test_find_item_by_name_case_insensitive(self):
        """find_item_by_name is case insensitive."""
        item = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        shop = Shop(name="Potion Shop", inventory=[shop_item])
        found = shop.find_item_by_name("health potion")
        assert found is not None
        assert found.item.name == "Health Potion"

    def test_find_item_by_name_not_found(self):
        """find_item_by_name returns None when item not found."""
        item = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        shop = Shop(name="Potion Shop", inventory=[shop_item])
        found = shop.find_item_by_name("Sword")
        assert found is None

    def test_shop_serialization(self):
        """Shop can be serialized to dict."""
        item = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        shop_item = ShopItem(item=item, buy_price=100)
        shop = Shop(name="Armory", inventory=[shop_item])
        data = shop.to_dict()
        assert data["name"] == "Armory"
        assert len(data["inventory"]) == 1

    def test_shop_deserialization(self):
        """Shop can be deserialized from dict."""
        item = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        shop_item = ShopItem(item=item, buy_price=100)
        shop = Shop(name="Armory", inventory=[shop_item])
        data = shop.to_dict()
        restored = Shop.from_dict(data)
        assert restored.name == shop.name
        assert len(restored.inventory) == 1
        assert restored.inventory[0].item.name == "Sword"

    def test_find_items_by_partial_name_single_match(self):
        """find_items_by_partial_name returns matching items."""
        # Tests spec: Partial name matching for shop buy command
        potion = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE)
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        shop = Shop(name="Store", inventory=[
            ShopItem(item=potion, buy_price=50),
            ShopItem(item=sword, buy_price=100)
        ])
        matches = shop.find_items_by_partial_name("sword")
        assert len(matches) == 1
        assert matches[0].item.name == "Iron Sword"

    def test_find_items_by_partial_name_multiple_matches(self):
        """find_items_by_partial_name returns multiple matching items."""
        # Tests spec: Partial name matching - multiple matches
        health_pot = Item(name="Health Potion", description="Heals HP", item_type=ItemType.CONSUMABLE)
        mana_pot = Item(name="Mana Potion", description="Heals MP", item_type=ItemType.CONSUMABLE)
        shop = Shop(name="Store", inventory=[
            ShopItem(item=health_pot, buy_price=50),
            ShopItem(item=mana_pot, buy_price=75)
        ])
        matches = shop.find_items_by_partial_name("potion")
        assert len(matches) == 2
        names = [m.item.name for m in matches]
        assert "Health Potion" in names
        assert "Mana Potion" in names

    def test_find_items_by_partial_name_case_insensitive(self):
        """find_items_by_partial_name is case insensitive."""
        # Tests spec: Case-insensitive matching
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        shop = Shop(name="Store", inventory=[ShopItem(item=sword, buy_price=100)])
        matches = shop.find_items_by_partial_name("SWORD")
        assert len(matches) == 1
        assert matches[0].item.name == "Iron Sword"

    def test_find_items_by_partial_name_no_match(self):
        """find_items_by_partial_name returns empty list when no match."""
        # Tests spec: No matches returns empty list
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        shop = Shop(name="Store", inventory=[ShopItem(item=sword, buy_price=100)])
        matches = shop.find_items_by_partial_name("wand")
        assert len(matches) == 0
