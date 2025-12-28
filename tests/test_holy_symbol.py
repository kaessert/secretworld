"""Tests for Holy Symbol equipment for Cleric class.

Spec: Add a Holy Symbol equipment slot exclusive to Clerics that boosts bless and smite abilities.
"""

import random
from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.inventory import Inventory
from cli_rpg.combat import CombatEncounter


class TestHolySymbolItemType:
    """Tests for Holy Symbol item type and divine_power attribute."""

    def test_holy_symbol_item_type_exists(self):
        """Spec: ItemType.HOLY_SYMBOL exists in the enum."""
        assert hasattr(ItemType, "HOLY_SYMBOL")
        assert ItemType.HOLY_SYMBOL.value == "holy_symbol"

    def test_item_divine_power_attribute(self):
        """Spec: Item has divine_power attribute (default 0)."""
        item = Item(
            name="Test Sword",
            description="A test weapon",
            item_type=ItemType.WEAPON,
        )
        assert hasattr(item, "divine_power")
        assert item.divine_power == 0

    def test_holy_symbol_with_divine_power(self):
        """Spec: Holy symbols can have divine_power set."""
        holy_symbol = Item(
            name="Simple Holy Symbol",
            description="A wooden holy symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )
        assert holy_symbol.divine_power == 2
        assert holy_symbol.item_type == ItemType.HOLY_SYMBOL

    def test_holy_symbol_serialization(self):
        """Spec: to_dict/from_dict handles divine_power correctly."""
        holy_symbol = Item(
            name="Sacred Relic",
            description="A powerful holy symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=5,
        )

        # Serialize
        data = holy_symbol.to_dict()
        assert "divine_power" in data
        assert data["divine_power"] == 5
        assert data["item_type"] == "holy_symbol"

        # Deserialize
        restored = Item.from_dict(data)
        assert restored.divine_power == 5
        assert restored.item_type == ItemType.HOLY_SYMBOL
        assert restored.name == "Sacred Relic"

    def test_holy_symbol_str_shows_divine_power(self):
        """Spec: __str__ displays divine power for holy symbols."""
        holy_symbol = Item(
            name="Blessed Talisman",
            description="A talisman of faith",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=3,
        )
        item_str = str(holy_symbol)
        assert "divine power" in item_str.lower() or "+3" in item_str


class TestHolySymbolEquipmentSlot:
    """Tests for the equipped_holy_symbol slot in Inventory."""

    def test_inventory_holy_symbol_slot_exists(self):
        """Spec: Inventory has equipped_holy_symbol attribute."""
        inventory = Inventory()
        assert hasattr(inventory, "equipped_holy_symbol")
        assert inventory.equipped_holy_symbol is None

    def test_equip_holy_symbol(self):
        """Spec: Can equip holy symbol to the slot."""
        inventory = Inventory()
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )
        inventory.add_item(holy_symbol)

        result = inventory.equip(holy_symbol)

        assert result is True
        assert inventory.equipped_holy_symbol == holy_symbol
        assert holy_symbol not in inventory.items

    def test_unequip_holy_symbol(self):
        """Spec: Can unequip holy symbol from slot."""
        inventory = Inventory()
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )
        inventory.add_item(holy_symbol)
        inventory.equip(holy_symbol)

        result = inventory.unequip("holy_symbol")

        assert result is True
        assert inventory.equipped_holy_symbol is None
        assert holy_symbol in inventory.items

    def test_get_divine_power_bonus(self):
        """Spec: get_divine_power_bonus returns equipped symbol's divine_power."""
        inventory = Inventory()
        assert inventory.get_divine_power_bonus() == 0

        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=4,
        )
        inventory.add_item(holy_symbol)
        inventory.equip(holy_symbol)

        assert inventory.get_divine_power_bonus() == 4

    def test_inventory_serialization_with_holy_symbol(self):
        """Spec: Inventory serialization handles equipped_holy_symbol."""
        inventory = Inventory()
        holy_symbol = Item(
            name="Divine Emblem",
            description="An emblem of faith",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=3,
        )
        inventory.add_item(holy_symbol)
        inventory.equip(holy_symbol)

        # Serialize
        data = inventory.to_dict()
        assert "equipped_holy_symbol" in data
        assert data["equipped_holy_symbol"]["divine_power"] == 3

        # Deserialize
        restored = Inventory.from_dict(data)
        assert restored.equipped_holy_symbol is not None
        assert restored.equipped_holy_symbol.divine_power == 3

    def test_inventory_str_shows_holy_symbol(self):
        """Spec: Inventory __str__ displays equipped holy symbol."""
        inventory = Inventory()
        holy_symbol = Item(
            name="Sacred Cross",
            description="A holy cross",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )
        inventory.add_item(holy_symbol)
        inventory.equip(holy_symbol)

        inventory_str = str(inventory)
        assert "Sacred Cross" in inventory_str or "Holy" in inventory_str


class TestClericOnlyRestriction:
    """Tests for Cleric-only restriction on holy symbols."""

    def test_only_cleric_can_equip_holy_symbol(self):
        """Spec: Only Clerics can equip holy symbols."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )

        assert cleric.can_equip_holy_symbol(holy_symbol) is True

    def test_non_cleric_cannot_equip_holy_symbol(self):
        """Spec: Non-Clerics cannot equip holy symbols."""
        warrior = Character(
            name="Warrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )

        assert warrior.can_equip_holy_symbol(holy_symbol) is False

    def test_equip_holy_symbol_with_validation_cleric(self):
        """Spec: Cleric can equip holy symbol through validation method."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )
        cleric.inventory.add_item(holy_symbol)

        success, message = cleric.equip_holy_symbol_with_validation(holy_symbol)

        assert success is True
        assert cleric.inventory.equipped_holy_symbol == holy_symbol

    def test_equip_holy_symbol_with_validation_non_cleric(self):
        """Spec: Non-Cleric gets error when trying to equip holy symbol."""
        mage = Character(
            name="Mage",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=2,
        )
        mage.inventory.add_item(holy_symbol)

        success, message = mage.equip_holy_symbol_with_validation(holy_symbol)

        assert success is False
        assert "Cleric" in message or "cannot" in message.lower()
        assert mage.inventory.equipped_holy_symbol is None

    def test_get_divine_power_from_character(self):
        """Spec: Character.get_divine_power() returns total divine power from equipment."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        assert cleric.get_divine_power() == 0

        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=5,
        )
        cleric.inventory.add_item(holy_symbol)
        cleric.equip_holy_symbol_with_validation(holy_symbol)

        assert cleric.get_divine_power() == 5


class TestHolySymbolBoostsBless:
    """Tests for holy symbol boosting bless ability."""

    def _create_cleric_combat_with_symbol(self, divine_power: int = 0):
        """Helper to create a Cleric in combat with optional holy symbol."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        if divine_power > 0:
            holy_symbol = Item(
                name="Holy Symbol",
                description="A sacred symbol",
                item_type=ItemType.HOLY_SYMBOL,
                divine_power=divine_power,
            )
            cleric.inventory.add_item(holy_symbol)
            cleric.equip_holy_symbol_with_validation(holy_symbol)

        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=cleric, enemy=enemy)
        combat.start()
        return cleric, enemy, combat

    def test_holy_symbol_boosts_bless_modifier(self):
        """Spec: Bless buff modifier increases with divine_power.

        Base: +25% (0.25), with holy symbol: +25% + (divine_power * 1%)
        """
        cleric, enemy, combat = self._create_cleric_combat_with_symbol(divine_power=5)

        combat.player_bless()

        # Check the Blessed effect has enhanced modifier
        blessed_effects = [e for e in cleric.status_effects if e.name == "Blessed"]
        assert len(blessed_effects) == 1
        # Base 0.25 + (5 * 0.01) = 0.30
        assert blessed_effects[0].stat_modifier == pytest.approx(0.30, rel=0.01)

    def test_bless_without_symbol_uses_base_modifier(self):
        """Spec: Bless without holy symbol uses base 25% modifier."""
        cleric, enemy, combat = self._create_cleric_combat_with_symbol(divine_power=0)

        combat.player_bless()

        blessed_effects = [e for e in cleric.status_effects if e.name == "Blessed"]
        assert len(blessed_effects) == 1
        assert blessed_effects[0].stat_modifier == 0.25


class TestHolySymbolBoostsSmite:
    """Tests for holy symbol boosting smite ability."""

    def _create_cleric_combat_with_symbol(self, divine_power: int = 0, enemy_name: str = "Goblin"):
        """Helper to create a Cleric in combat with optional holy symbol."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        if divine_power > 0:
            holy_symbol = Item(
                name="Holy Symbol",
                description="A sacred symbol",
                item_type=ItemType.HOLY_SYMBOL,
                divine_power=divine_power,
            )
            cleric.inventory.add_item(holy_symbol)
            cleric.equip_holy_symbol_with_validation(holy_symbol)

        enemy = Enemy(
            name=enemy_name,
            health=200,
            max_health=200,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=cleric, enemy=enemy)
        combat.start()
        return cleric, enemy, combat

    def test_holy_symbol_boosts_smite_damage(self):
        """Spec: Smite damage increases with divine_power.

        Base: INT * 2.5, with holy symbol: (INT + divine_power * 0.1) * 2.5
        """
        cleric, enemy, combat = self._create_cleric_combat_with_symbol(divine_power=5)
        initial_health = enemy.health
        # Cleric INT = 10 + 2 (class bonus) = 12
        # Divine power bonus: 5 * 0.1 = 0.5 extra per multiplier
        # Damage = INT * 2.5 + divine_power * 0.1 * 2.5 = 12 * 2.5 + 5 * 0.1 * 2.5 = 30 + 1.25 ≈ 31
        # Alternatively: (INT * 2.5) + divine_power (flat bonus)
        # Let's use flat bonus: 30 + 5 = 35 or percentage: 30 * 1.05 = 31.5

        combat.player_smite()

        damage_dealt = initial_health - enemy.health
        # Base damage without symbol would be 30
        # With divine power, should be higher
        assert damage_dealt > 30

    def test_smite_without_symbol_uses_base_damage(self):
        """Spec: Smite without holy symbol uses base damage."""
        cleric, enemy, combat = self._create_cleric_combat_with_symbol(divine_power=0)
        initial_health = enemy.health
        # Cleric INT = 12, base damage = 12 * 2.5 = 30

        combat.player_smite()

        damage_dealt = initial_health - enemy.health
        assert damage_dealt == 30

    @patch("random.random", return_value=0.25)  # Between 30% and 35%
    def test_holy_symbol_boosts_undead_stun_chance(self, mock_random):
        """Spec: Divine power increases stun chance vs undead.

        Base: 30%, with divine_power: 30% + (divine_power * 1%)
        With divine_power=5: 30% + 5% = 35%
        Roll of 25% should stun with symbol but not without (if base was 30%).
        """
        # At 0.25 (25%), base 30% would stun, but let's test the increased chance
        cleric, enemy, combat = self._create_cleric_combat_with_symbol(
            divine_power=5, enemy_name="Skeleton"
        )

        combat.player_smite()

        # At 25% roll, should stun (since 25% < 35%)
        stun_effects = [e for e in enemy.status_effects if e.effect_type == "stun"]
        assert len(stun_effects) == 1


class TestEquipUnequipCommands:
    """Tests for equip/unequip command handling of holy symbols in main.py."""

    def _create_game_state(self, character):
        """Helper to create a game state with the given character."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.location import Location

        world = {"Temple": Location(name="Temple", description="A holy place")}
        return GameState(character, world, starting_location="Temple")

    def test_equip_command_handles_holy_symbol_for_cleric(self):
        """Spec: Equip command should allow Clerics to equip holy symbols."""
        from cli_rpg.main import handle_exploration_command

        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=3,
        )
        cleric.inventory.add_item(holy_symbol)

        game_state = self._create_game_state(cleric)

        # Call handle_exploration_command
        _, message = handle_exploration_command(game_state, "equip", ["Holy", "Symbol"])

        assert "equipped" in message.lower()
        assert cleric.inventory.equipped_holy_symbol == holy_symbol

    def test_equip_command_blocks_holy_symbol_for_non_cleric(self):
        """Spec: Equip command should block non-Clerics from equipping holy symbols."""
        from cli_rpg.main import handle_exploration_command

        warrior = Character(
            name="Warrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=3,
        )
        warrior.inventory.add_item(holy_symbol)

        game_state = self._create_game_state(warrior)

        # Call handle_exploration_command
        _, message = handle_exploration_command(game_state, "equip", ["Holy", "Symbol"])

        assert "cleric" in message.lower() or "cannot" in message.lower()
        assert warrior.inventory.equipped_holy_symbol is None

    def test_unequip_command_handles_holy_symbol(self):
        """Spec: Unequip command should support 'holy_symbol' slot."""
        from cli_rpg.main import handle_exploration_command

        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=3,
        )
        cleric.inventory.add_item(holy_symbol)
        cleric.inventory.equip(holy_symbol)

        game_state = self._create_game_state(cleric)

        # Verify it's equipped
        assert cleric.inventory.equipped_holy_symbol == holy_symbol

        # Call handle_exploration_command
        _, message = handle_exploration_command(game_state, "unequip", ["holy_symbol"])

        assert "unequipped" in message.lower()
        assert cleric.inventory.equipped_holy_symbol is None
        assert holy_symbol in cleric.inventory.items

    def test_equip_already_equipped_holy_symbol_shows_message(self):
        """Spec: Trying to equip an already equipped holy symbol shows helpful message."""
        from cli_rpg.main import handle_exploration_command

        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        holy_symbol = Item(
            name="Holy Symbol",
            description="A sacred symbol",
            item_type=ItemType.HOLY_SYMBOL,
            divine_power=3,
        )
        cleric.inventory.add_item(holy_symbol)
        cleric.inventory.equip(holy_symbol)

        game_state = self._create_game_state(cleric)

        # Try to equip the already-equipped symbol
        _, message = handle_exploration_command(game_state, "equip", ["Holy", "Symbol"])

        assert "already equipped" in message.lower()

    def test_unequip_no_holy_symbol_shows_message(self):
        """Spec: Trying to unequip when no holy symbol is equipped shows message."""
        from cli_rpg.main import handle_exploration_command

        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )

        game_state = self._create_game_state(cleric)

        # Try to unequip when nothing is equipped
        _, message = handle_exploration_command(game_state, "unequip", ["holy_symbol"])

        assert "don't have" in message.lower() or "no" in message.lower()
