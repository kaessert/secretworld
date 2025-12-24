"""Tests for Character-Inventory integration.

Spec requirements tested:
- Character has inventory
- Equipped weapon affects attack damage
- Equipped armor affects damage reduction
- Use consumable to heal
- Inventory persists in save/load
"""
import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.inventory import Inventory


class TestCharacterHasInventory:
    """Test that Character has inventory (spec requirement)."""

    def test_character_has_inventory_by_default(self):
        """Test: New character has empty inventory (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        assert hasattr(character, 'inventory')
        assert isinstance(character.inventory, Inventory)
        assert len(character.inventory.items) == 0

    def test_character_inventory_default_capacity(self):
        """Test: Character inventory has default capacity of 20"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        assert character.inventory.capacity == 20

    def test_character_can_add_items(self):
        """Test: Character can add items to inventory"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)

        result = character.inventory.add_item(sword)

        assert result is True
        assert sword in character.inventory.items


class TestCharacterEquipItem:
    """Test character equipment (spec requirement)."""

    def test_equip_weapon(self):
        """Test: Character can equip weapon (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        character.inventory.add_item(sword)

        result = character.equip_item(sword)

        assert result is True
        assert character.inventory.equipped_weapon == sword

    def test_equip_armor(self):
        """Test: Character can equip armor (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        armor = Item(name="Armor", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=5)
        character.inventory.add_item(armor)

        result = character.equip_item(armor)

        assert result is True
        assert character.inventory.equipped_armor == armor


class TestEquippedWeaponAffectsAttack:
    """Test that equipped weapon affects attack damage (spec requirement)."""

    def test_get_attack_power_no_weapon(self):
        """Test: Attack power equals strength with no weapon"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        assert character.get_attack_power() == 10

    def test_get_attack_power_with_weapon(self):
        """Test: Equipped weapon adds to attack power (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=8)
        character.inventory.add_item(sword)
        character.equip_item(sword)

        # Attack power should be strength + weapon bonus
        assert character.get_attack_power() == 18

    def test_attack_power_changes_when_weapon_swapped(self):
        """Test: Attack power updates when weapon changes"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword1 = Item(name="Sword1", description="Weak", item_type=ItemType.WEAPON, damage_bonus=3)
        sword2 = Item(name="Sword2", description="Strong", item_type=ItemType.WEAPON, damage_bonus=10)
        character.inventory.add_item(sword1)
        character.inventory.add_item(sword2)

        character.equip_item(sword1)
        assert character.get_attack_power() == 13

        character.equip_item(sword2)
        assert character.get_attack_power() == 20


class TestEquippedArmorAffectsDefense:
    """Test that equipped armor affects damage reduction (spec requirement)."""

    def test_get_defense_no_armor(self):
        """Test: Defense equals constitution (strength) with no armor"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        # Base constitution equals strength
        assert character.get_defense() == 10

    def test_get_defense_with_armor(self):
        """Test: Equipped armor adds to defense (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        armor = Item(name="Armor", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=7)
        character.inventory.add_item(armor)
        character.equip_item(armor)

        # Defense should be constitution + armor bonus
        assert character.get_defense() == 17

    def test_defense_changes_when_armor_swapped(self):
        """Test: Defense updates when armor changes"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        armor1 = Item(name="Leather", description="Light", item_type=ItemType.ARMOR, defense_bonus=2)
        armor2 = Item(name="Plate", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=12)
        character.inventory.add_item(armor1)
        character.inventory.add_item(armor2)

        character.equip_item(armor1)
        assert character.get_defense() == 12

        character.equip_item(armor2)
        assert character.get_defense() == 22


class TestUseConsumable:
    """Test consumable usage (spec requirement)."""

    def test_use_health_potion(self):
        """Test: Use consumable to heal (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        character.take_damage(50)
        initial_health = character.health

        potion = Item(
            name="Health Potion",
            description="Restores health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=30
        )
        character.inventory.add_item(potion)

        result, message = character.use_item(potion)

        assert result is True
        assert character.health == initial_health + 30
        assert potion not in character.inventory.items  # Consumable should be consumed
        assert "health" in message.lower() or "heal" in message.lower()

    def test_use_health_potion_caps_at_max(self):
        """Test: Healing doesn't exceed max health"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        character.take_damage(10)

        potion = Item(
            name="Health Potion",
            description="Restores health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=100
        )
        character.inventory.add_item(potion)

        character.use_item(potion)

        assert character.health == character.max_health

    def test_use_item_not_in_inventory(self):
        """Test: Cannot use item not in inventory"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        potion = Item(
            name="Health Potion",
            description="Restores health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=30
        )

        result, message = character.use_item(potion)

        assert result is False
        assert "not in inventory" in message.lower() or "don't have" in message.lower()

    def test_use_non_consumable(self):
        """Test: Cannot use non-consumable items"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON)
        character.inventory.add_item(sword)

        result, message = character.use_item(sword)

        assert result is False
        assert sword in character.inventory.items  # Weapon should remain


class TestCharacterSerializationWithInventory:
    """Test character serialization includes inventory (spec requirement)."""

    def test_character_to_dict_includes_inventory(self):
        """Test: to_dict includes inventory data (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        character.inventory.add_item(sword)

        data = character.to_dict()

        assert "inventory" in data
        assert len(data["inventory"]["items"]) == 1

    def test_character_to_dict_includes_equipped_items(self):
        """Test: to_dict includes equipped items"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        armor = Item(name="Armor", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=3)
        character.inventory.add_item(sword)
        character.inventory.add_item(armor)
        character.equip_item(sword)
        character.equip_item(armor)

        data = character.to_dict()

        assert data["inventory"]["equipped_weapon"] is not None
        assert data["inventory"]["equipped_armor"] is not None

    def test_character_from_dict_restores_inventory(self):
        """Test: from_dict restores inventory (spec requirement)"""
        original = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        original.inventory.add_item(sword)

        data = original.to_dict()
        restored = Character.from_dict(data)

        assert len(restored.inventory.items) == 1
        assert restored.inventory.items[0].name == "Sword"

    def test_character_from_dict_restores_equipped_items(self):
        """Test: from_dict restores equipped items"""
        original = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        sword = Item(name="Sword", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        armor = Item(name="Armor", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=3)
        original.inventory.add_item(sword)
        original.inventory.add_item(armor)
        original.equip_item(sword)
        original.equip_item(armor)

        data = original.to_dict()
        restored = Character.from_dict(data)

        assert restored.inventory.equipped_weapon is not None
        assert restored.inventory.equipped_weapon.name == "Sword"
        assert restored.inventory.equipped_armor is not None
        assert restored.inventory.equipped_armor.name == "Armor"
        assert restored.get_attack_power() == original.get_attack_power()
        assert restored.get_defense() == original.get_defense()

    def test_character_from_dict_backward_compatibility(self):
        """Test: from_dict handles old saves without inventory"""
        # Old save format without inventory
        data = {
            "name": "Hero",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
            "health": 150,
            "max_health": 150,
            "xp": 0
        }

        restored = Character.from_dict(data)

        # Should have empty inventory
        assert restored.inventory is not None
        assert len(restored.inventory.items) == 0
        assert restored.inventory.equipped_weapon is None
        assert restored.inventory.equipped_armor is None


class TestCharacterInventoryIntegrationRoundtrip:
    """Test full serialization roundtrip with inventory."""

    def test_full_roundtrip_with_equipped_and_unequipped(self):
        """Test: Full serialization roundtrip preserves all inventory state"""
        original = Character(
            name="Hero",
            strength=12,
            dexterity=10,
            intelligence=8
        )
        # Add multiple items of different types
        sword = Item(name="Iron Sword", description="Sharp blade", item_type=ItemType.WEAPON, damage_bonus=7)
        armor = Item(name="Chain Mail", description="Metal rings", item_type=ItemType.ARMOR, defense_bonus=5)
        potion = Item(name="Health Pot", description="Red liquid", item_type=ItemType.CONSUMABLE, heal_amount=25)
        key = Item(name="Gold Key", description="Ornate key", item_type=ItemType.MISC)

        original.inventory.add_item(sword)
        original.inventory.add_item(armor)
        original.inventory.add_item(potion)
        original.inventory.add_item(key)

        # Equip weapon and armor
        original.equip_item(sword)
        original.equip_item(armor)

        # Take some damage
        original.take_damage(30)

        # Serialize and deserialize
        data = original.to_dict()
        restored = Character.from_dict(data)

        # Verify all state is preserved
        assert restored.name == original.name
        assert restored.health == original.health
        assert restored.get_attack_power() == original.get_attack_power()
        assert restored.get_defense() == original.get_defense()

        # Inventory items (potion and key should be in items)
        assert len(restored.inventory.items) == 2
        item_names = [item.name for item in restored.inventory.items]
        assert "Health Pot" in item_names
        assert "Gold Key" in item_names

        # Equipped items
        assert restored.inventory.equipped_weapon.name == "Iron Sword"
        assert restored.inventory.equipped_weapon.damage_bonus == 7
        assert restored.inventory.equipped_armor.name == "Chain Mail"
        assert restored.inventory.equipped_armor.defense_bonus == 5
