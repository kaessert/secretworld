"""Tests for Inventory model.

Spec requirements tested:
- Inventory has max capacity (default 20)
- Inventory has list of items
- Inventory has equipped weapon/armor slots
- Methods: add_item(), remove_item(), equip(), unequip(), is_full()
- Serialization with to_dict() / from_dict()
"""
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.inventory import Inventory


class TestInventoryCreation:
    """Test inventory creation."""

    def test_inventory_creation_default(self):
        """Test: Create inventory with default capacity (spec requirement)"""
        inventory = Inventory()
        assert inventory.capacity == 20
        assert len(inventory.items) == 0
        assert inventory.equipped_weapon is None
        assert inventory.equipped_armor is None

    def test_inventory_creation_custom_capacity(self):
        """Test: Create inventory with custom capacity"""
        inventory = Inventory(capacity=10)
        assert inventory.capacity == 10

    def test_inventory_creation_with_items(self):
        """Test: Create inventory with initial items"""
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory = Inventory(items=[sword])
        assert len(inventory.items) == 1
        assert inventory.items[0] == sword


class TestInventoryAddItem:
    """Test add_item() method."""

    def test_add_item_success(self):
        """Test: Add item to inventory (spec requirement)"""
        inventory = Inventory()
        sword = Item(name="Iron Sword", description="A sword", item_type=ItemType.WEAPON)

        result = inventory.add_item(sword)

        assert result is True
        assert len(inventory.items) == 1
        assert sword in inventory.items

    def test_add_multiple_items(self):
        """Test: Add multiple items to inventory"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)
        shield = Item(name="Shield", description="Round", item_type=ItemType.ARMOR)
        potion = Item(name="Potion", description="Heals", item_type=ItemType.CONSUMABLE)

        inventory.add_item(sword)
        inventory.add_item(shield)
        inventory.add_item(potion)

        assert len(inventory.items) == 3

    def test_add_item_full_inventory(self):
        """Test: Reject adding item when inventory is full (spec requirement)"""
        inventory = Inventory(capacity=2)
        item1 = Item(name="Item1", description="First", item_type=ItemType.MISC)
        item2 = Item(name="Item2", description="Second", item_type=ItemType.MISC)
        item3 = Item(name="Item3", description="Third", item_type=ItemType.MISC)

        inventory.add_item(item1)
        inventory.add_item(item2)
        result = inventory.add_item(item3)

        assert result is False
        assert len(inventory.items) == 2
        assert item3 not in inventory.items


class TestInventoryRemoveItem:
    """Test remove_item() method."""

    def test_remove_item_success(self):
        """Test: Remove item from inventory (spec requirement)"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory.add_item(sword)

        result = inventory.remove_item(sword)

        assert result is True
        assert sword not in inventory.items
        assert len(inventory.items) == 0

    def test_remove_item_not_found(self):
        """Test: Remove item not in inventory returns False"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)

        result = inventory.remove_item(sword)

        assert result is False

    def test_remove_item_by_name(self):
        """Test: Remove item by name"""
        inventory = Inventory()
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory.add_item(sword)

        result = inventory.remove_item_by_name("Iron Sword")

        assert result is True
        assert len(inventory.items) == 0

    def test_remove_item_by_name_not_found(self):
        """Test: Remove item by name when not found"""
        inventory = Inventory()

        result = inventory.remove_item_by_name("Nonexistent")

        assert result is False


class TestInventoryCapacity:
    """Test inventory capacity limits (spec requirement)."""

    def test_is_full_empty_inventory(self):
        """Test: is_full() returns False for empty inventory"""
        inventory = Inventory(capacity=5)
        assert inventory.is_full() is False

    def test_is_full_partial_inventory(self):
        """Test: is_full() returns False when not at capacity"""
        inventory = Inventory(capacity=5)
        item = Item(name="Item", description="Test", item_type=ItemType.MISC)
        inventory.add_item(item)
        assert inventory.is_full() is False

    def test_is_full_at_capacity(self):
        """Test: is_full() returns True when at capacity (spec requirement)"""
        inventory = Inventory(capacity=2)
        item1 = Item(name="Item1", description="First", item_type=ItemType.MISC)
        item2 = Item(name="Item2", description="Second", item_type=ItemType.MISC)
        inventory.add_item(item1)
        inventory.add_item(item2)

        assert inventory.is_full() is True

    def test_remaining_space(self):
        """Test: Get remaining space in inventory"""
        inventory = Inventory(capacity=10)
        item = Item(name="Item", description="Test", item_type=ItemType.MISC)
        inventory.add_item(item)
        inventory.add_item(item)

        assert inventory.remaining_space() == 8


class TestInventoryEquipWeapon:
    """Test equip() for weapons (spec requirement)."""

    def test_equip_weapon_from_inventory(self):
        """Test: Equip weapon from inventory (spec requirement)"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        inventory.add_item(sword)

        result = inventory.equip(sword)

        assert result is True
        assert inventory.equipped_weapon == sword
        assert sword not in inventory.items  # Equipped items are removed from general inventory

    def test_equip_weapon_replaces_existing(self):
        """Test: Equipping new weapon unequips old one"""
        inventory = Inventory()
        sword1 = Item(name="Sword1", description="Old", item_type=ItemType.WEAPON, damage_bonus=3)
        sword2 = Item(name="Sword2", description="New", item_type=ItemType.WEAPON, damage_bonus=7)
        inventory.add_item(sword1)
        inventory.add_item(sword2)

        inventory.equip(sword1)
        inventory.equip(sword2)

        assert inventory.equipped_weapon == sword2
        assert sword1 in inventory.items  # Old weapon returned to inventory

    def test_equip_weapon_not_in_inventory(self):
        """Test: Cannot equip item not in inventory"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)

        result = inventory.equip(sword)

        assert result is False
        assert inventory.equipped_weapon is None


class TestInventoryEquipArmor:
    """Test equip() for armor (spec requirement)."""

    def test_equip_armor_from_inventory(self):
        """Test: Equip armor from inventory (spec requirement)"""
        inventory = Inventory()
        armor = Item(name="Chainmail", description="Metal", item_type=ItemType.ARMOR, defense_bonus=5)
        inventory.add_item(armor)

        result = inventory.equip(armor)

        assert result is True
        assert inventory.equipped_armor == armor
        assert armor not in inventory.items

    def test_equip_armor_replaces_existing(self):
        """Test: Equipping new armor unequips old one"""
        inventory = Inventory()
        armor1 = Item(name="Leather", description="Light", item_type=ItemType.ARMOR, defense_bonus=2)
        armor2 = Item(name="Plate", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=10)
        inventory.add_item(armor1)
        inventory.add_item(armor2)

        inventory.equip(armor1)
        inventory.equip(armor2)

        assert inventory.equipped_armor == armor2
        assert armor1 in inventory.items

    def test_equip_non_equippable_item(self):
        """Test: Cannot equip consumable or misc items"""
        inventory = Inventory()
        potion = Item(name="Potion", description="Heals", item_type=ItemType.CONSUMABLE)
        key = Item(name="Key", description="Opens", item_type=ItemType.MISC)
        inventory.add_item(potion)
        inventory.add_item(key)

        assert inventory.equip(potion) is False
        assert inventory.equip(key) is False
        assert inventory.equipped_weapon is None
        assert inventory.equipped_armor is None


class TestInventoryUnequip:
    """Test unequip() method (spec requirement)."""

    def test_unequip_weapon(self):
        """Test: Unequip weapon returns it to inventory (spec requirement)"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory.add_item(sword)
        inventory.equip(sword)

        result = inventory.unequip("weapon")

        assert result is True
        assert inventory.equipped_weapon is None
        assert sword in inventory.items

    def test_unequip_armor(self):
        """Test: Unequip armor returns it to inventory (spec requirement)"""
        inventory = Inventory()
        armor = Item(name="Armor", description="Protective", item_type=ItemType.ARMOR)
        inventory.add_item(armor)
        inventory.equip(armor)

        result = inventory.unequip("armor")

        assert result is True
        assert inventory.equipped_armor is None
        assert armor in inventory.items

    def test_unequip_empty_slot(self):
        """Test: Unequip empty slot returns False"""
        inventory = Inventory()

        result = inventory.unequip("weapon")

        assert result is False

    def test_unequip_when_inventory_full(self):
        """Test: Cannot unequip when inventory is full"""
        inventory = Inventory(capacity=1)
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)
        other = Item(name="Other", description="Item", item_type=ItemType.MISC)
        inventory.add_item(sword)
        inventory.equip(sword)
        inventory.add_item(other)  # Fill the only slot

        result = inventory.unequip("weapon")

        assert result is False
        assert inventory.equipped_weapon == sword  # Still equipped


class TestInventoryStatBonuses:
    """Test equipped item stat bonuses (spec requirement)."""

    def test_get_total_damage_bonus(self):
        """Test: Get total damage bonus from equipped weapon (spec requirement)"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=10)
        inventory.add_item(sword)
        inventory.equip(sword)

        assert inventory.get_damage_bonus() == 10

    def test_get_total_damage_bonus_no_weapon(self):
        """Test: Damage bonus is 0 with no weapon"""
        inventory = Inventory()
        assert inventory.get_damage_bonus() == 0

    def test_get_total_defense_bonus(self):
        """Test: Get total defense bonus from equipped armor (spec requirement)"""
        inventory = Inventory()
        armor = Item(name="Armor", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=8)
        inventory.add_item(armor)
        inventory.equip(armor)

        assert inventory.get_defense_bonus() == 8

    def test_get_total_defense_bonus_no_armor(self):
        """Test: Defense bonus is 0 with no armor"""
        inventory = Inventory()
        assert inventory.get_defense_bonus() == 0


class TestInventorySerialization:
    """Test inventory serialization (spec requirement)."""

    def test_inventory_to_dict_empty(self):
        """Test: Serialize empty inventory"""
        inventory = Inventory()
        data = inventory.to_dict()

        assert data["capacity"] == 20
        assert data["items"] == []
        assert data["equipped_weapon"] is None
        assert data["equipped_armor"] is None

    def test_inventory_to_dict_with_items(self):
        """Test: Serialize inventory with items"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        inventory.add_item(sword)

        data = inventory.to_dict()

        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Sword"

    def test_inventory_to_dict_with_equipped(self):
        """Test: Serialize inventory with equipped items (spec requirement)"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        armor = Item(name="Armor", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=3)
        inventory.add_item(sword)
        inventory.add_item(armor)
        inventory.equip(sword)
        inventory.equip(armor)

        data = inventory.to_dict()

        assert data["equipped_weapon"] is not None
        assert data["equipped_weapon"]["name"] == "Sword"
        assert data["equipped_armor"] is not None
        assert data["equipped_armor"]["name"] == "Armor"

    def test_inventory_from_dict_empty(self):
        """Test: Deserialize empty inventory"""
        data = {
            "capacity": 20,
            "items": [],
            "equipped_weapon": None,
            "equipped_armor": None
        }
        inventory = Inventory.from_dict(data)

        assert inventory.capacity == 20
        assert len(inventory.items) == 0

    def test_inventory_from_dict_with_items(self):
        """Test: Deserialize inventory with items"""
        data = {
            "capacity": 20,
            "items": [
                {
                    "name": "Sword",
                    "description": "Sharp",
                    "item_type": "weapon",
                    "damage_bonus": 5,
                    "defense_bonus": 0,
                    "heal_amount": 0
                }
            ],
            "equipped_weapon": None,
            "equipped_armor": None
        }
        inventory = Inventory.from_dict(data)

        assert len(inventory.items) == 1
        assert inventory.items[0].name == "Sword"

    def test_inventory_from_dict_with_equipped(self):
        """Test: Deserialize inventory with equipped items (spec requirement)"""
        data = {
            "capacity": 20,
            "items": [],
            "equipped_weapon": {
                "name": "Sword",
                "description": "Sharp",
                "item_type": "weapon",
                "damage_bonus": 10,
                "defense_bonus": 0,
                "heal_amount": 0
            },
            "equipped_armor": {
                "name": "Plate",
                "description": "Heavy",
                "item_type": "armor",
                "damage_bonus": 0,
                "defense_bonus": 15,
                "heal_amount": 0
            }
        }
        inventory = Inventory.from_dict(data)

        assert inventory.equipped_weapon is not None
        assert inventory.equipped_weapon.name == "Sword"
        assert inventory.equipped_weapon.damage_bonus == 10
        assert inventory.equipped_armor is not None
        assert inventory.equipped_armor.name == "Plate"
        assert inventory.equipped_armor.defense_bonus == 15

    def test_inventory_serialization_roundtrip(self):
        """Test: to_dict() -> from_dict() produces equivalent Inventory"""
        original = Inventory(capacity=15)
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        armor = Item(name="Armor", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=3)
        potion = Item(name="Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=20)

        original.add_item(sword)
        original.add_item(armor)
        original.add_item(potion)
        original.equip(sword)
        original.equip(armor)

        data = original.to_dict()
        restored = Inventory.from_dict(data)

        assert restored.capacity == original.capacity
        assert len(restored.items) == len(original.items)
        assert restored.equipped_weapon.name == original.equipped_weapon.name
        assert restored.equipped_armor.name == original.equipped_armor.name
        assert restored.get_damage_bonus() == original.get_damage_bonus()
        assert restored.get_defense_bonus() == original.get_defense_bonus()


class TestInventoryFindItem:
    """Test item lookup methods."""

    def test_find_item_by_name(self):
        """Test: Find item by name"""
        inventory = Inventory()
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory.add_item(sword)

        found = inventory.find_item_by_name("Iron Sword")

        assert found == sword

    def test_find_item_by_name_not_found(self):
        """Test: Return None when item not found"""
        inventory = Inventory()

        found = inventory.find_item_by_name("Nonexistent")

        assert found is None

    def test_find_item_by_name_case_insensitive(self):
        """Test: Find item case-insensitively"""
        inventory = Inventory()
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory.add_item(sword)

        found = inventory.find_item_by_name("iron sword")

        assert found == sword


class TestInventoryListItems:
    """Test inventory listing."""

    def test_list_items_empty(self):
        """Test: List items in empty inventory"""
        inventory = Inventory()
        items = inventory.list_items()
        assert items == []

    def test_list_items_with_items(self):
        """Test: List items returns all items"""
        inventory = Inventory()
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)
        potion = Item(name="Potion", description="Heals", item_type=ItemType.CONSUMABLE)
        inventory.add_item(sword)
        inventory.add_item(potion)

        items = inventory.list_items()

        assert len(items) == 2
