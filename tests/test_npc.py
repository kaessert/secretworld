"""Tests for NPC model.

Tests the NPC model including validation and serialization.
"""
import pytest
from cli_rpg.models.npc import NPC


class TestNPC:
    """Tests for NPC model - tests spec: NPC Model."""

    def test_create_npc(self):
        """NPC can be created with basic attributes."""
        npc = NPC(name="Merchant", description="A friendly shopkeeper", dialogue="Welcome!", is_merchant=True)
        assert npc.name == "Merchant"
        assert npc.description == "A friendly shopkeeper"
        assert npc.dialogue == "Welcome!"
        assert npc.is_merchant is True

    def test_create_npc_not_merchant(self):
        """NPC defaults to not being a merchant."""
        npc = NPC(name="Guard", description="A town guard", dialogue="Move along, citizen.")
        assert npc.is_merchant is False

    def test_npc_name_validation_too_short(self):
        """NPC name must be at least 2 characters."""
        with pytest.raises(ValueError, match="2-30 characters"):
            NPC(name="X", description="Too short name", dialogue="Hi")

    def test_npc_name_validation_too_long(self):
        """NPC name must be at most 30 characters."""
        with pytest.raises(ValueError, match="2-30 characters"):
            NPC(name="X" * 31, description="Too long name", dialogue="Hi")

    def test_npc_description_validation_empty(self):
        """NPC description cannot be empty."""
        with pytest.raises(ValueError, match="1-200 characters"):
            NPC(name="Merchant", description="", dialogue="Hi")

    def test_npc_description_validation_too_long(self):
        """NPC description must be at most 200 characters."""
        with pytest.raises(ValueError, match="1-200 characters"):
            NPC(name="Merchant", description="X" * 201, dialogue="Hi")

    def test_npc_serialization(self):
        """NPC can be serialized to dict."""
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello!", is_merchant=True)
        data = npc.to_dict()
        assert data["name"] == "Merchant"
        assert data["description"] == "A shopkeeper"
        assert data["dialogue"] == "Hello!"
        assert data["is_merchant"] is True

    def test_npc_deserialization(self):
        """NPC can be deserialized from dict."""
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello!", is_merchant=True)
        data = npc.to_dict()
        restored = NPC.from_dict(data)
        assert restored.name == npc.name
        assert restored.description == npc.description
        assert restored.dialogue == npc.dialogue
        assert restored.is_merchant == npc.is_merchant

    def test_npc_with_shop_serialization(self):
        """NPC with shop can be serialized and deserialized."""
        from cli_rpg.models.shop import Shop, ShopItem
        from cli_rpg.models.item import Item, ItemType

        item = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        shop = Shop(name="Potion Shop", inventory=[shop_item])
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Welcome!", is_merchant=True, shop=shop)

        data = npc.to_dict()
        restored = NPC.from_dict(data)

        assert restored.shop is not None
        assert restored.shop.name == "Potion Shop"
        assert len(restored.shop.inventory) == 1
