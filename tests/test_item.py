"""Tests for Item model.

Spec requirements tested:
- Items have name (2-30 chars), description (1-200 chars)
- Items have type (weapon/armor/consumable/misc)
- Items have stat modifiers
- Items support to_dict() / from_dict() for serialization
"""
import pytest
from cli_rpg.models.item import Item, ItemType


class TestItemCreation:
    """Test item creation and validation."""

    def test_item_creation_valid_weapon(self):
        """Test: Create weapon item with valid attributes (spec requirement)"""
        item = Item(
            name="Iron Sword",
            description="A sturdy iron sword",
            item_type=ItemType.WEAPON,
            damage_bonus=5
        )
        assert item.name == "Iron Sword"
        assert item.description == "A sturdy iron sword"
        assert item.item_type == ItemType.WEAPON
        assert item.damage_bonus == 5
        assert item.defense_bonus == 0
        assert item.heal_amount == 0

    def test_item_creation_valid_armor(self):
        """Test: Create armor item with valid attributes (spec requirement)"""
        item = Item(
            name="Leather Armor",
            description="Basic leather protection",
            item_type=ItemType.ARMOR,
            defense_bonus=3
        )
        assert item.name == "Leather Armor"
        assert item.item_type == ItemType.ARMOR
        assert item.defense_bonus == 3
        assert item.damage_bonus == 0

    def test_item_creation_valid_consumable(self):
        """Test: Create consumable item with heal amount (spec requirement)"""
        item = Item(
            name="Health Potion",
            description="Restores health when consumed",
            item_type=ItemType.CONSUMABLE,
            heal_amount=25
        )
        assert item.name == "Health Potion"
        assert item.item_type == ItemType.CONSUMABLE
        assert item.heal_amount == 25

    def test_item_creation_valid_misc(self):
        """Test: Create misc item without combat stats (spec requirement)"""
        item = Item(
            name="Old Key",
            description="An ancient key found in the dungeon",
            item_type=ItemType.MISC
        )
        assert item.name == "Old Key"
        assert item.item_type == ItemType.MISC
        assert item.damage_bonus == 0
        assert item.defense_bonus == 0
        assert item.heal_amount == 0


class TestItemNameValidation:
    """Test item name validation (spec: 2-30 chars)."""

    def test_item_name_minimum_length(self):
        """Test: Accept name with 2 characters (spec requirement)"""
        item = Item(
            name="Ax",
            description="A simple axe",
            item_type=ItemType.WEAPON
        )
        assert item.name == "Ax"

    def test_item_name_maximum_length(self):
        """Test: Accept name with 30 characters (spec requirement)"""
        long_name = "A" * 30
        item = Item(
            name=long_name,
            description="A long-named item",
            item_type=ItemType.MISC
        )
        assert item.name == long_name

    def test_item_name_too_short(self):
        """Test: Reject name < 2 chars (spec requirement)"""
        with pytest.raises(ValueError, match="at least 2 characters"):
            Item(
                name="A",
                description="Too short",
                item_type=ItemType.MISC
            )

    def test_item_name_too_long(self):
        """Test: Reject name > 30 chars (spec requirement)"""
        with pytest.raises(ValueError, match="at most 30 characters"):
            Item(
                name="A" * 31,
                description="Too long name",
                item_type=ItemType.MISC
            )

    def test_item_name_empty(self):
        """Test: Reject empty name (spec requirement)"""
        with pytest.raises(ValueError, match="cannot be empty"):
            Item(
                name="",
                description="No name",
                item_type=ItemType.MISC
            )


class TestItemDescriptionValidation:
    """Test item description validation (spec: 1-200 chars)."""

    def test_item_description_minimum_length(self):
        """Test: Accept description with 1 character (spec requirement)"""
        item = Item(
            name="Rock",
            description="A",
            item_type=ItemType.MISC
        )
        assert item.description == "A"

    def test_item_description_maximum_length(self):
        """Test: Accept description with 200 characters (spec requirement)"""
        long_desc = "A" * 200
        item = Item(
            name="Item",
            description=long_desc,
            item_type=ItemType.MISC
        )
        assert item.description == long_desc

    def test_item_description_empty(self):
        """Test: Reject empty description (spec requirement)"""
        with pytest.raises(ValueError, match="description.*at least 1 character"):
            Item(
                name="Item",
                description="",
                item_type=ItemType.MISC
            )

    def test_item_description_too_long(self):
        """Test: Reject description > 200 chars (spec requirement)"""
        with pytest.raises(ValueError, match="description.*at most 200 characters"):
            Item(
                name="Item",
                description="A" * 201,
                item_type=ItemType.MISC
            )


class TestItemTypeValidation:
    """Test item type validation (spec: weapon/armor/consumable/misc)."""

    def test_item_type_weapon(self):
        """Test: Accept WEAPON type (spec requirement)"""
        item = Item(name="Sword", description="Sharp blade", item_type=ItemType.WEAPON)
        assert item.item_type == ItemType.WEAPON

    def test_item_type_armor(self):
        """Test: Accept ARMOR type (spec requirement)"""
        item = Item(name="Shield", description="Wooden shield", item_type=ItemType.ARMOR)
        assert item.item_type == ItemType.ARMOR

    def test_item_type_consumable(self):
        """Test: Accept CONSUMABLE type (spec requirement)"""
        item = Item(name="Potion", description="Healing liquid", item_type=ItemType.CONSUMABLE)
        assert item.item_type == ItemType.CONSUMABLE

    def test_item_type_misc(self):
        """Test: Accept MISC type (spec requirement)"""
        item = Item(name="Key", description="Opens locks", item_type=ItemType.MISC)
        assert item.item_type == ItemType.MISC


class TestItemStatModifiers:
    """Test item stat modifiers."""

    def test_item_damage_bonus(self):
        """Test: Item can have damage bonus (spec requirement)"""
        item = Item(
            name="Steel Sword",
            description="A sharp steel sword",
            item_type=ItemType.WEAPON,
            damage_bonus=10
        )
        assert item.damage_bonus == 10

    def test_item_defense_bonus(self):
        """Test: Item can have defense bonus (spec requirement)"""
        item = Item(
            name="Chainmail",
            description="Linked metal rings",
            item_type=ItemType.ARMOR,
            defense_bonus=8
        )
        assert item.defense_bonus == 8

    def test_item_heal_amount(self):
        """Test: Consumable can have heal amount (spec requirement)"""
        item = Item(
            name="Greater Potion",
            description="Powerful healing potion",
            item_type=ItemType.CONSUMABLE,
            heal_amount=50
        )
        assert item.heal_amount == 50

    def test_item_negative_damage_bonus_rejected(self):
        """Test: Reject negative damage bonus"""
        with pytest.raises(ValueError, match="damage_bonus.*cannot be negative"):
            Item(
                name="Broken Sword",
                description="Worthless",
                item_type=ItemType.WEAPON,
                damage_bonus=-5
            )

    def test_item_negative_defense_bonus_rejected(self):
        """Test: Reject negative defense bonus"""
        with pytest.raises(ValueError, match="defense_bonus.*cannot be negative"):
            Item(
                name="Cursed Armor",
                description="Cursed",
                item_type=ItemType.ARMOR,
                defense_bonus=-3
            )

    def test_item_negative_heal_amount_rejected(self):
        """Test: Reject negative heal amount"""
        with pytest.raises(ValueError, match="heal_amount.*cannot be negative"):
            Item(
                name="Poison",
                description="Toxic",
                item_type=ItemType.CONSUMABLE,
                heal_amount=-10
            )


class TestItemSerialization:
    """Test item serialization (spec requirement)."""

    def test_item_to_dict_weapon(self):
        """Test: Serialize weapon to dict (spec requirement)"""
        item = Item(
            name="Iron Sword",
            description="A sturdy iron sword",
            item_type=ItemType.WEAPON,
            damage_bonus=5
        )
        data = item.to_dict()

        assert data["name"] == "Iron Sword"
        assert data["description"] == "A sturdy iron sword"
        assert data["item_type"] == "weapon"
        assert data["damage_bonus"] == 5
        assert data["defense_bonus"] == 0
        assert data["heal_amount"] == 0

    def test_item_to_dict_armor(self):
        """Test: Serialize armor to dict (spec requirement)"""
        item = Item(
            name="Shield",
            description="A wooden shield",
            item_type=ItemType.ARMOR,
            defense_bonus=4
        )
        data = item.to_dict()

        assert data["item_type"] == "armor"
        assert data["defense_bonus"] == 4

    def test_item_to_dict_consumable(self):
        """Test: Serialize consumable to dict (spec requirement)"""
        item = Item(
            name="Potion",
            description="Heals wounds",
            item_type=ItemType.CONSUMABLE,
            heal_amount=30
        )
        data = item.to_dict()

        assert data["item_type"] == "consumable"
        assert data["heal_amount"] == 30

    def test_item_from_dict_weapon(self):
        """Test: Deserialize weapon from dict (spec requirement)"""
        data = {
            "name": "Iron Sword",
            "description": "A sturdy iron sword",
            "item_type": "weapon",
            "damage_bonus": 5,
            "defense_bonus": 0,
            "heal_amount": 0
        }
        item = Item.from_dict(data)

        assert item.name == "Iron Sword"
        assert item.description == "A sturdy iron sword"
        assert item.item_type == ItemType.WEAPON
        assert item.damage_bonus == 5

    def test_item_from_dict_armor(self):
        """Test: Deserialize armor from dict (spec requirement)"""
        data = {
            "name": "Steel Armor",
            "description": "Heavy protection",
            "item_type": "armor",
            "damage_bonus": 0,
            "defense_bonus": 10,
            "heal_amount": 0
        }
        item = Item.from_dict(data)

        assert item.item_type == ItemType.ARMOR
        assert item.defense_bonus == 10

    def test_item_from_dict_consumable(self):
        """Test: Deserialize consumable from dict (spec requirement)"""
        data = {
            "name": "Elixir",
            "description": "Magical healing",
            "item_type": "consumable",
            "damage_bonus": 0,
            "defense_bonus": 0,
            "heal_amount": 100
        }
        item = Item.from_dict(data)

        assert item.item_type == ItemType.CONSUMABLE
        assert item.heal_amount == 100

    def test_item_serialization_roundtrip(self):
        """Test: to_dict() -> from_dict() produces equivalent Item (spec requirement)"""
        original = Item(
            name="Magic Staff",
            description="Channels magical energy",
            item_type=ItemType.WEAPON,
            damage_bonus=8
        )
        data = original.to_dict()
        restored = Item.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.item_type == original.item_type
        assert restored.damage_bonus == original.damage_bonus
        assert restored.defense_bonus == original.defense_bonus
        assert restored.heal_amount == original.heal_amount


class TestItemStringRepresentation:
    """Test item string representation."""

    def test_item_str_weapon(self):
        """Test: String representation includes key info"""
        item = Item(
            name="Iron Sword",
            description="A sturdy iron sword",
            item_type=ItemType.WEAPON,
            damage_bonus=5
        )
        str_repr = str(item)
        assert "Iron Sword" in str_repr
        assert "weapon" in str_repr.lower()

    def test_item_str_armor(self):
        """Test: String representation for armor"""
        item = Item(
            name="Shield",
            description="Wooden shield",
            item_type=ItemType.ARMOR,
            defense_bonus=3
        )
        str_repr = str(item)
        assert "Shield" in str_repr
        assert "armor" in str_repr.lower()

    def test_item_str_consumable_with_heal(self):
        """Test: String representation for consumable shows heal amount"""
        item = Item(
            name="Health Potion",
            description="Restores health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=25
        )
        str_repr = str(item)
        assert "Health Potion" in str_repr
        assert "consumable" in str_repr.lower()
        assert "heals 25 HP" in str_repr
