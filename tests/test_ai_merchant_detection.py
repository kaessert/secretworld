"""Tests for AI-generated merchant detection and shop creation."""

import pytest
from cli_rpg.ai_world import _create_npcs_from_data, _create_default_merchant_shop
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop


class TestMerchantRoleInference:
    """Tests for inferring merchant role from NPC names."""

    def test_merchant_role_inferred_from_name(self):
        """NPC with 'Merchant' in name should get is_merchant=True."""
        # Spec: If NPC name contains "merchant", infer role="merchant"
        npc_data = [
            {
                "name": "Tech Merchant",
                "description": "A seller of technological wares",
                "role": "villager"  # AI returned wrong role
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True
        assert npcs[0].name == "Tech Merchant"

    def test_trader_role_inferred_from_name(self):
        """NPC with 'Trader' in name should get is_merchant=True."""
        # Spec: "trader" keyword should also trigger merchant inference
        npc_data = [
            {
                "name": "Desert Trader",
                "description": "A wandering desert trader",
                "role": "villager"
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True

    def test_vendor_role_inferred_from_name(self):
        """NPC with 'Vendor' in name should get is_merchant=True."""
        # Spec: "vendor" keyword should also trigger merchant inference
        npc_data = [
            {
                "name": "Street Vendor",
                "description": "Sells wares on the street",
                "role": "villager"
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True

    def test_shopkeeper_role_inferred_from_name(self):
        """NPC with 'Shopkeeper' in name should get is_merchant=True."""
        # Spec: "shopkeeper" keyword should also trigger merchant inference
        npc_data = [
            {
                "name": "Village Shopkeeper",
                "description": "Runs the local shop",
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True

    def test_seller_role_inferred_from_name(self):
        """NPC with 'Seller' in name should get is_merchant=True."""
        # Spec: "seller" keyword should also trigger merchant inference
        npc_data = [
            {
                "name": "Potion Seller",
                "description": "Sells magical potions",
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True

    def test_dealer_role_inferred_from_name(self):
        """NPC with 'Dealer' in name should get is_merchant=True."""
        # Spec: "dealer" keyword should also trigger merchant inference
        npc_data = [
            {
                "name": "Arms Dealer",
                "description": "Deals in weapons",
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True

    def test_explicit_merchant_role_preserved(self):
        """NPC with explicit role='merchant' works regardless of name."""
        # Spec: Explicit role="merchant" should always work
        npc_data = [
            {
                "name": "Bob",  # No merchant keywords in name
                "description": "A friendly merchant",
                "role": "merchant"
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True
        assert npcs[0].name == "Bob"

    def test_non_merchant_names_stay_villager(self):
        """NPC without merchant keywords stays is_merchant=False."""
        # Spec: NPCs without merchant-related names should NOT be merchants
        npc_data = [
            {
                "name": "Town Guard",
                "description": "Guards the town",
                "role": "villager"
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is False

    def test_case_insensitive_merchant_detection(self):
        """Merchant detection should be case-insensitive."""
        # Spec: Case shouldn't matter - "MERCHANT", "Merchant", "merchant" all work
        npc_data = [
            {
                "name": "TRAVELING MERCHANT",
                "description": "A loud merchant",
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True


class TestMerchantShopCreation:
    """Tests for default shop creation for AI-generated merchants."""

    def test_ai_merchant_has_default_shop(self):
        """Inferred merchant NPC should get a Shop object."""
        # Spec: AI merchants get a default shop when is_merchant=True
        npc_data = [
            {
                "name": "Wandering Merchant",
                "description": "A merchant on the road",
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        assert npcs[0].is_merchant is True
        assert npcs[0].shop is not None
        assert isinstance(npcs[0].shop, Shop)

    def test_ai_merchant_shop_has_items(self):
        """Default merchant shop should contain buyable items."""
        # Spec: Default shop has at least basic consumables
        npc_data = [
            {
                "name": "Generic Trader",
                "description": "A simple trader",
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        shop = npcs[0].shop
        assert shop is not None
        assert len(shop.inventory) > 0
        # Verify items have prices
        for shop_item in shop.inventory:
            assert shop_item.buy_price > 0

    def test_explicit_merchant_gets_shop(self):
        """Merchant with explicit role='merchant' should also get a shop."""
        # Spec: Any is_merchant=True NPC should get a shop
        npc_data = [
            {
                "name": "Bob",
                "description": "A friendly merchant",
                "role": "merchant"
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert npcs[0].shop is not None
        assert isinstance(npcs[0].shop, Shop)

    def test_non_merchant_no_shop(self):
        """Non-merchant NPCs should NOT get a shop."""
        # Spec: Only merchants get shops
        npc_data = [
            {
                "name": "Town Guard",
                "description": "Guards the town",
                "role": "villager"
            }
        ]
        npcs = _create_npcs_from_data(npc_data)

        assert npcs[0].is_merchant is False
        assert npcs[0].shop is None


class TestDefaultMerchantShop:
    """Tests for the _create_default_merchant_shop helper function."""

    def test_default_shop_has_name(self):
        """Default shop should have a name."""
        shop = _create_default_merchant_shop()
        assert shop.name is not None
        assert len(shop.name) > 0

    def test_default_shop_has_health_potion(self):
        """Default shop should include a health potion."""
        # Spec: Basic consumables should be available
        shop = _create_default_merchant_shop()
        potion = shop.find_item_by_name("Health Potion")
        assert potion is not None
        assert potion.item.heal_amount > 0

    def test_default_shop_has_antidote(self):
        """Default shop should include an antidote."""
        shop = _create_default_merchant_shop()
        antidote = shop.find_item_by_name("Antidote")
        assert antidote is not None

    def test_default_shop_has_rations(self):
        """Default shop should include travel rations."""
        shop = _create_default_merchant_shop()
        rations = shop.find_item_by_name("Travel Rations")
        assert rations is not None

    def test_default_shop_items_have_prices(self):
        """All default shop items should have buy prices."""
        shop = _create_default_merchant_shop()
        for shop_item in shop.inventory:
            assert shop_item.buy_price > 0


class TestTerrainAwareMerchantShops:
    """Tests for terrain-based default shop inventories."""

    def test_default_shop_no_terrain_has_standard_items(self):
        """Default shop without terrain has standard consumables."""
        # Spec: Default shop without terrain_type has standard consumables
        shop = _create_default_merchant_shop()
        assert shop.find_item_by_name("Health Potion") is not None

    def test_mountain_terrain_shop_has_climbing_gear(self):
        """Mountain terrain shop includes mountain-appropriate items."""
        # Spec: Mountain merchants have climbing gear, cold-weather items, pickaxes
        shop = _create_default_merchant_shop(terrain_type="mountain")
        item_names = [si.item.name for si in shop.inventory]
        assert any("pick" in name.lower() or "climbing" in name.lower()
                   or "warm" in name.lower() for name in item_names)

    def test_swamp_terrain_shop_has_antidotes(self):
        """Swamp terrain shop emphasizes poison cures."""
        # Spec: Swamp merchants have antidotes, insect repellent, waterproof gear
        shop = _create_default_merchant_shop(terrain_type="swamp")
        antidote = shop.find_item_by_name("Antidote")
        assert antidote is not None

    def test_desert_terrain_shop_has_water(self):
        """Desert terrain shop includes water/hydration items."""
        # Spec: Desert merchants have water skins, sun protection, heat-resistant items
        shop = _create_default_merchant_shop(terrain_type="desert")
        item_names = [si.item.name for si in shop.inventory]
        assert any("water" in name.lower() for name in item_names)

    def test_forest_terrain_shop_has_trail_supplies(self):
        """Forest terrain shop has trail/camping supplies."""
        # Spec: Forest merchants have trail rations, rope, camping supplies
        shop = _create_default_merchant_shop(terrain_type="forest")
        item_names = [si.item.name for si in shop.inventory]
        assert any("ration" in name.lower() or "rope" in name.lower()
                   for name in item_names)

    def test_beach_terrain_shop_has_fishing_gear(self):
        """Beach/coastal terrain shop has fishing/water items."""
        # Spec: Beach/coastal merchants have fishing gear, rope, water-related items
        shop = _create_default_merchant_shop(terrain_type="beach")
        item_names = [si.item.name for si in shop.inventory]
        assert any("fish" in name.lower() or "rope" in name.lower()
                   for name in item_names)

    def test_all_terrain_shops_have_health_potion(self):
        """All terrain shops should include health potion as baseline."""
        # Spec: Health Potion is always included as baseline for all terrain types
        for terrain in ["mountain", "swamp", "desert", "forest", "beach", "plains"]:
            shop = _create_default_merchant_shop(terrain_type=terrain)
            assert shop.find_item_by_name("Health Potion") is not None, \
                f"Health Potion missing for terrain: {terrain}"
