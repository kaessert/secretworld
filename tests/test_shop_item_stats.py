"""Tests for shop item stats parsing from AI-generated inventory.

These tests verify Step 1 of the NPC generation enhancement plan:
- Shop items get proper ItemType based on 'item_type' field
- Weapons get damage_bonus from AI data
- Armor gets defense_bonus from AI data
- Consumables get heal_amount and stamina_restore from AI data
- Items default to MISC type when item_type is missing
"""

import pytest

from cli_rpg.ai_world import _create_shop_from_ai_inventory
from cli_rpg.models.item import ItemType


class TestShopItemStatsFromAI:
    """Test shop item creation with various item types and stats."""

    def test_weapon_with_damage_bonus(self):
        """Verify weapon items get damage_bonus from AI data."""
        inventory = [
            {"name": "Iron Sword", "price": 100, "item_type": "weapon", "damage_bonus": 5}
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Test Shop")

        assert shop is not None
        assert len(shop.inventory) == 1
        assert shop.inventory[0].item.item_type == ItemType.WEAPON
        assert shop.inventory[0].item.damage_bonus == 5
        assert shop.inventory[0].buy_price == 100

    def test_armor_with_defense_bonus(self):
        """Verify armor items get defense_bonus from AI data."""
        inventory = [
            {"name": "Steel Plate", "price": 150, "item_type": "armor", "defense_bonus": 8}
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Armory")

        assert shop is not None
        assert shop.inventory[0].item.item_type == ItemType.ARMOR
        assert shop.inventory[0].item.defense_bonus == 8

    def test_consumable_with_heal_amount(self):
        """Verify consumables get heal_amount from AI data."""
        inventory = [
            {"name": "Health Potion", "price": 50, "item_type": "consumable", "heal_amount": 30}
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Apothecary")

        assert shop is not None
        assert shop.inventory[0].item.item_type == ItemType.CONSUMABLE
        assert shop.inventory[0].item.heal_amount == 30

    def test_consumable_with_stamina_restore(self):
        """Verify consumables get stamina_restore from AI data."""
        inventory = [
            {
                "name": "Stamina Draught",
                "price": 40,
                "item_type": "consumable",
                "stamina_restore": 25
            }
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Apothecary")

        assert shop is not None
        assert shop.inventory[0].item.item_type == ItemType.CONSUMABLE
        assert shop.inventory[0].item.stamina_restore == 25

    def test_consumable_with_both_stats(self):
        """Verify consumables can have both heal_amount and stamina_restore."""
        inventory = [
            {
                "name": "Rejuvenation Elixir",
                "price": 75,
                "item_type": "consumable",
                "heal_amount": 20,
                "stamina_restore": 15
            }
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Apothecary")

        assert shop is not None
        assert shop.inventory[0].item.heal_amount == 20
        assert shop.inventory[0].item.stamina_restore == 15

    def test_missing_item_type_defaults_to_misc(self):
        """Verify missing item_type defaults to MISC."""
        inventory = [{"name": "Trinket", "price": 25}]
        shop = _create_shop_from_ai_inventory(inventory, "Curio Shop")

        assert shop is not None
        assert shop.inventory[0].item.item_type == ItemType.MISC

    def test_unknown_item_type_defaults_to_misc(self):
        """Verify unknown item_type values default to MISC."""
        inventory = [{"name": "Mystery Box", "price": 50, "item_type": "unknown"}]
        shop = _create_shop_from_ai_inventory(inventory, "Mystery Shop")

        assert shop is not None
        assert shop.inventory[0].item.item_type == ItemType.MISC

    def test_item_type_case_insensitive(self):
        """Verify item_type parsing is case-insensitive."""
        inventory = [
            {"name": "Great Sword", "price": 200, "item_type": "WEAPON", "damage_bonus": 10},
            {"name": "Iron Helm", "price": 80, "item_type": "Armor", "defense_bonus": 3}
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Smithy")

        assert shop is not None
        assert len(shop.inventory) == 2
        assert shop.inventory[0].item.item_type == ItemType.WEAPON
        assert shop.inventory[1].item.item_type == ItemType.ARMOR

    def test_mixed_inventory(self):
        """Verify mixed inventory with different item types works correctly."""
        inventory = [
            {"name": "Long Sword", "price": 120, "item_type": "weapon", "damage_bonus": 6},
            {"name": "Chain Mail", "price": 100, "item_type": "armor", "defense_bonus": 5},
            {"name": "Healing Salve", "price": 35, "item_type": "consumable", "heal_amount": 15},
            {"name": "Old Compass", "price": 20}  # No item_type -> MISC
        ]
        shop = _create_shop_from_ai_inventory(inventory, "General Store")

        assert shop is not None
        assert len(shop.inventory) == 4
        assert shop.inventory[0].item.item_type == ItemType.WEAPON
        assert shop.inventory[0].item.damage_bonus == 6
        assert shop.inventory[1].item.item_type == ItemType.ARMOR
        assert shop.inventory[1].item.defense_bonus == 5
        assert shop.inventory[2].item.item_type == ItemType.CONSUMABLE
        assert shop.inventory[2].item.heal_amount == 15
        assert shop.inventory[3].item.item_type == ItemType.MISC

    def test_stat_defaults_to_zero(self):
        """Verify missing stat fields default to 0."""
        inventory = [
            {"name": "Rusty Blade", "price": 30, "item_type": "weapon"}
            # No damage_bonus specified
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Junk Shop")

        assert shop is not None
        assert shop.inventory[0].item.damage_bonus == 0

    def test_empty_inventory_returns_none(self):
        """Verify empty inventory list returns None."""
        shop = _create_shop_from_ai_inventory([], "Empty Shop")
        assert shop is None

    def test_invalid_item_missing_name_skipped(self):
        """Verify items missing required 'name' field are skipped."""
        inventory = [
            {"price": 50},  # Missing name - should be skipped
            {"name": "Valid Item", "price": 25}
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Test Shop")

        assert shop is not None
        assert len(shop.inventory) == 1
        assert shop.inventory[0].item.name == "Valid Item"

    def test_invalid_item_missing_price_skipped(self):
        """Verify items missing required 'price' field are skipped."""
        inventory = [
            {"name": "No Price Item"},  # Missing price - should be skipped
            {"name": "Valid Item", "price": 30}
        ]
        shop = _create_shop_from_ai_inventory(inventory, "Test Shop")

        assert shop is not None
        assert len(shop.inventory) == 1
        assert shop.inventory[0].item.name == "Valid Item"
