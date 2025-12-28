"""Tests for armor weight class restrictions.

Spec: Add armor weight categories to differentiate class equipment choices:
- ArmorWeight enum: LIGHT, MEDIUM, HEAVY
- Class restrictions:
  - Mage: Can only equip LIGHT armor
  - Rogue: Can only equip LIGHT or MEDIUM armor
  - Warrior: Can equip all armor weights (only class for HEAVY)
  - Ranger: Can only equip LIGHT or MEDIUM armor
  - Cleric: Can only equip LIGHT or MEDIUM armor
- Backward compatibility: Existing armor items (no weight) default to LIGHT
"""

import pytest

from cli_rpg.models.item import Item, ItemType, ArmorWeight
from cli_rpg.models.character import Character, CharacterClass, CLASS_ARMOR_RESTRICTIONS


class TestArmorWeightEnum:
    """Tests for ArmorWeight enum (Spec: LIGHT, MEDIUM, HEAVY)."""

    def test_armor_weight_has_three_values(self):
        """ArmorWeight enum should have exactly 3 values."""
        assert len(ArmorWeight) == 3

    def test_armor_weight_values(self):
        """ArmorWeight enum should have LIGHT, MEDIUM, HEAVY values."""
        assert ArmorWeight.LIGHT.value == "light"
        assert ArmorWeight.MEDIUM.value == "medium"
        assert ArmorWeight.HEAVY.value == "heavy"


class TestItemArmorWeight:
    """Tests for Item armor_weight field (Spec: optional field, defaults to None)."""

    def test_item_armor_defaults_to_none(self):
        """Armor items without weight should default to None for backward compat."""
        armor = Item(
            name="Leather Armor",
            description="Basic protection",
            item_type=ItemType.ARMOR,
            defense_bonus=2,
        )
        assert armor.armor_weight is None

    def test_item_armor_with_weight(self):
        """Armor items can specify a weight."""
        heavy_armor = Item(
            name="Plate Armor",
            description="Full plate protection",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )
        assert heavy_armor.armor_weight == ArmorWeight.HEAVY

    def test_item_serialization_with_weight(self):
        """Item with armor_weight should serialize and deserialize correctly."""
        armor = Item(
            name="Chain Mail",
            description="Interlocking rings",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
            armor_weight=ArmorWeight.MEDIUM,
        )
        data = armor.to_dict()
        assert data["armor_weight"] == "medium"

        restored = Item.from_dict(data)
        assert restored.armor_weight == ArmorWeight.MEDIUM

    def test_item_serialization_without_weight_backward_compat(self):
        """Item without armor_weight should deserialize to None for backward compat."""
        # Simulate old save data without armor_weight field
        data = {
            "name": "Old Armor",
            "description": "From old save",
            "item_type": "armor",
            "defense_bonus": 2,
        }
        restored = Item.from_dict(data)
        assert restored.armor_weight is None

    def test_item_str_shows_weight_for_armor(self):
        """Item string representation should show weight for armor items."""
        armor = Item(
            name="Plate Armor",
            description="Heavy protection",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )
        armor_str = str(armor)
        assert "Heavy" in armor_str


class TestCharacterArmorRestrictions:
    """Tests for class-based armor restrictions (Spec: per-class weight limits)."""

    def test_class_armor_restrictions_defined(self):
        """CLASS_ARMOR_RESTRICTIONS should define allowed weights for each class."""
        assert CharacterClass.MAGE in CLASS_ARMOR_RESTRICTIONS
        assert CharacterClass.ROGUE in CLASS_ARMOR_RESTRICTIONS
        assert CharacterClass.WARRIOR in CLASS_ARMOR_RESTRICTIONS
        assert CharacterClass.RANGER in CLASS_ARMOR_RESTRICTIONS
        assert CharacterClass.CLERIC in CLASS_ARMOR_RESTRICTIONS

    def test_mage_can_equip_light_armor(self):
        """Mages can equip LIGHT armor (Spec: only LIGHT)."""
        mage = Character(
            name="Test Mage",
            strength=8,
            dexterity=10,
            intelligence=14,
            character_class=CharacterClass.MAGE,
        )
        light_armor = Item(
            name="Robes",
            description="Mage robes",
            item_type=ItemType.ARMOR,
            defense_bonus=1,
            armor_weight=ArmorWeight.LIGHT,
        )
        assert mage.can_equip_armor(light_armor) is True

    def test_mage_cannot_equip_medium_armor(self):
        """Mages cannot equip MEDIUM armor (Spec: only LIGHT)."""
        mage = Character(
            name="Test Mage",
            strength=8,
            dexterity=10,
            intelligence=14,
            character_class=CharacterClass.MAGE,
        )
        medium_armor = Item(
            name="Chain Mail",
            description="Metal rings",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
            armor_weight=ArmorWeight.MEDIUM,
        )
        assert mage.can_equip_armor(medium_armor) is False

    def test_mage_cannot_equip_heavy_armor(self):
        """Mages cannot equip HEAVY armor (Spec: only LIGHT)."""
        mage = Character(
            name="Test Mage",
            strength=8,
            dexterity=10,
            intelligence=14,
            character_class=CharacterClass.MAGE,
        )
        heavy_armor = Item(
            name="Plate Armor",
            description="Full plate",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )
        assert mage.can_equip_armor(heavy_armor) is False

    def test_warrior_can_equip_all_armor(self):
        """Warriors can equip all armor weights (Spec: all weights)."""
        warrior = Character(
            name="Test Warrior",
            strength=14,
            dexterity=10,
            intelligence=8,
            character_class=CharacterClass.WARRIOR,
        )

        light_armor = Item(
            name="Leather",
            description="Light protection",
            item_type=ItemType.ARMOR,
            defense_bonus=1,
            armor_weight=ArmorWeight.LIGHT,
        )
        medium_armor = Item(
            name="Chain Mail",
            description="Medium protection",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
            armor_weight=ArmorWeight.MEDIUM,
        )
        heavy_armor = Item(
            name="Plate",
            description="Heavy protection",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )

        assert warrior.can_equip_armor(light_armor) is True
        assert warrior.can_equip_armor(medium_armor) is True
        assert warrior.can_equip_armor(heavy_armor) is True

    def test_rogue_can_equip_light_and_medium(self):
        """Rogues can equip LIGHT and MEDIUM armor (Spec: LIGHT/MEDIUM only)."""
        rogue = Character(
            name="Test Rogue",
            strength=10,
            dexterity=14,
            intelligence=10,
            character_class=CharacterClass.ROGUE,
        )

        light_armor = Item(
            name="Leather",
            description="Light protection",
            item_type=ItemType.ARMOR,
            defense_bonus=1,
            armor_weight=ArmorWeight.LIGHT,
        )
        medium_armor = Item(
            name="Studded Leather",
            description="Medium protection",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
            armor_weight=ArmorWeight.MEDIUM,
        )
        heavy_armor = Item(
            name="Plate",
            description="Heavy protection",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )

        assert rogue.can_equip_armor(light_armor) is True
        assert rogue.can_equip_armor(medium_armor) is True
        assert rogue.can_equip_armor(heavy_armor) is False

    def test_ranger_can_equip_light_and_medium(self):
        """Rangers can equip LIGHT and MEDIUM armor (Spec: LIGHT/MEDIUM only)."""
        ranger = Character(
            name="Test Ranger",
            strength=10,
            dexterity=12,
            intelligence=10,
            character_class=CharacterClass.RANGER,
        )

        light_armor = Item(
            name="Leather",
            description="Light protection",
            item_type=ItemType.ARMOR,
            defense_bonus=1,
            armor_weight=ArmorWeight.LIGHT,
        )
        medium_armor = Item(
            name="Scale Mail",
            description="Medium protection",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
            armor_weight=ArmorWeight.MEDIUM,
        )
        heavy_armor = Item(
            name="Plate",
            description="Heavy protection",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )

        assert ranger.can_equip_armor(light_armor) is True
        assert ranger.can_equip_armor(medium_armor) is True
        assert ranger.can_equip_armor(heavy_armor) is False

    def test_cleric_can_equip_light_and_medium(self):
        """Clerics can equip LIGHT and MEDIUM armor (Spec: LIGHT/MEDIUM only)."""
        cleric = Character(
            name="Test Cleric",
            strength=10,
            dexterity=8,
            intelligence=12,
            character_class=CharacterClass.CLERIC,
        )

        light_armor = Item(
            name="Robes",
            description="Light protection",
            item_type=ItemType.ARMOR,
            defense_bonus=1,
            armor_weight=ArmorWeight.LIGHT,
        )
        medium_armor = Item(
            name="Chain Mail",
            description="Medium protection",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
            armor_weight=ArmorWeight.MEDIUM,
        )
        heavy_armor = Item(
            name="Plate",
            description="Heavy protection",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )

        assert cleric.can_equip_armor(light_armor) is True
        assert cleric.can_equip_armor(medium_armor) is True
        assert cleric.can_equip_armor(heavy_armor) is False

    def test_no_class_can_equip_any_armor(self):
        """Characters without a class can equip any armor (backward compat)."""
        char = Character(
            name="Classless Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=None,
        )

        heavy_armor = Item(
            name="Plate",
            description="Heavy protection",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )

        assert char.can_equip_armor(heavy_armor) is True

    def test_armor_without_weight_can_be_equipped(self):
        """Armor without weight (old saves) can be equipped by any class (backward compat)."""
        mage = Character(
            name="Test Mage",
            strength=8,
            dexterity=10,
            intelligence=14,
            character_class=CharacterClass.MAGE,
        )
        # Old-style armor without weight field (defaults to None, treated as LIGHT)
        old_armor = Item(
            name="Old Armor",
            description="From old save",
            item_type=ItemType.ARMOR,
            defense_bonus=2,
        )
        assert old_armor.armor_weight is None
        assert mage.can_equip_armor(old_armor) is True


class TestEquipCommand:
    """Tests for equip command integration with armor restrictions."""

    def test_equip_restricted_armor_shows_error_message(self):
        """Equipping armor too heavy for class should show descriptive error."""
        mage = Character(
            name="Test Mage",
            strength=8,
            dexterity=10,
            intelligence=14,
            character_class=CharacterClass.MAGE,
        )
        heavy_armor = Item(
            name="Plate Armor",
            description="Heavy plate",
            item_type=ItemType.ARMOR,
            defense_bonus=5,
            armor_weight=ArmorWeight.HEAVY,
        )
        mage.inventory.add_item(heavy_armor)

        # Try to equip via character method (returns tuple with success, message)
        success, message = mage.equip_armor_with_validation(heavy_armor)
        assert success is False
        assert "too heavy" in message.lower() or "cannot equip" in message.lower()

    def test_equip_allowed_armor_succeeds(self):
        """Equipping allowed armor should succeed."""
        mage = Character(
            name="Test Mage",
            strength=8,
            dexterity=10,
            intelligence=14,
            character_class=CharacterClass.MAGE,
        )
        light_armor = Item(
            name="Robes",
            description="Mage robes",
            item_type=ItemType.ARMOR,
            defense_bonus=1,
            armor_weight=ArmorWeight.LIGHT,
        )
        mage.inventory.add_item(light_armor)

        success, message = mage.equip_armor_with_validation(light_armor)
        assert success is True
        assert mage.inventory.equipped_armor == light_armor
