"""Tests for inventory commands in main game loop."""
import pytest
from cli_rpg.main import handle_exploration_command
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType


@pytest.fixture
def game_state_with_items():
    """Create game state with items in inventory."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    sword = Item(name="Iron Sword", description="A sharp blade", item_type=ItemType.WEAPON, damage_bonus=5)
    armor = Item(name="Leather Armor", description="Light protection", item_type=ItemType.ARMOR, defense_bonus=3)
    potion = Item(name="Health Potion", description="Restores health", item_type=ItemType.CONSUMABLE, heal_amount=25)
    char.inventory.add_item(sword)
    char.inventory.add_item(armor)
    char.inventory.add_item(potion)
    world = {"Town": Location(name="Town", description="A quiet town")}
    return GameState(char, world, starting_location="Town")


class TestInventoryCommand:
    """Tests for 'inventory' command - Spec: Display formatted inventory."""

    def test_inventory_shows_items(self, game_state_with_items):
        """Spec: 'inventory' displays all items using Inventory.__str__()."""
        cont, msg = handle_exploration_command(game_state_with_items, "inventory", [])
        assert cont is True
        assert "Iron Sword" in msg
        assert "Leather Armor" in msg
        assert "Health Potion" in msg

    def test_inventory_empty(self):
        """Spec: Empty inventory displays 'No items' message."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A quiet town")}
        gs = GameState(char, world, starting_location="Town")
        cont, msg = handle_exploration_command(gs, "inventory", [])
        assert cont is True
        assert "No items" in msg


class TestEquipCommand:
    """Tests for 'equip' command - Spec: Find item by name, equip it."""

    def test_equip_weapon_success(self, game_state_with_items):
        """Spec: 'equip <item name>' finds and equips the item."""
        cont, msg = handle_exploration_command(game_state_with_items, "equip", ["iron", "sword"])
        assert cont is True
        assert "equipped" in msg.lower() or "Iron Sword" in msg
        assert game_state_with_items.current_character.inventory.equipped_weapon is not None

    def test_equip_item_not_found(self, game_state_with_items):
        """Spec: Error message 'Item not found' when item doesn't exist."""
        cont, msg = handle_exploration_command(game_state_with_items, "equip", ["nonexistent"])
        assert cont is True
        assert "not found" in msg.lower() or "don't have" in msg.lower()

    def test_equip_no_args(self, game_state_with_items):
        """Spec: Error when no item name specified."""
        cont, msg = handle_exploration_command(game_state_with_items, "equip", [])
        assert cont is True
        assert "what" in msg.lower() or "specify" in msg.lower()


class TestUnequipCommand:
    """Tests for 'unequip' command - Spec: Unequip from slot, return to inventory."""

    def test_unequip_weapon_success(self, game_state_with_items):
        """Spec: 'unequip weapon' removes weapon and returns to inventory."""
        gs = game_state_with_items
        sword = gs.current_character.inventory.find_item_by_name("Iron Sword")
        gs.current_character.inventory.equip(sword)
        cont, msg = handle_exploration_command(gs, "unequip", ["weapon"])
        assert cont is True
        assert gs.current_character.inventory.equipped_weapon is None

    def test_unequip_empty_slot(self, game_state_with_items):
        """Spec: Error 'Nothing equipped in that slot' when slot is empty."""
        cont, msg = handle_exploration_command(game_state_with_items, "unequip", ["weapon"])
        assert cont is True
        assert "nothing" in msg.lower() or "not equipped" in msg.lower() or "don't have" in msg.lower()

    def test_unequip_no_args(self, game_state_with_items):
        """Spec: Error when no slot specified."""
        cont, msg = handle_exploration_command(game_state_with_items, "unequip", [])
        assert cont is True
        assert "weapon" in msg.lower() or "armor" in msg.lower()


class TestUseCommand:
    """Tests for 'use' command - Spec: Use consumable item."""

    def test_use_consumable_success(self, game_state_with_items):
        """Spec: 'use <item name>' uses consumable and shows effect."""
        gs = game_state_with_items
        gs.current_character.take_damage(50)  # Damage to test healing
        old_health = gs.current_character.health
        cont, msg = handle_exploration_command(gs, "use", ["health", "potion"])
        assert cont is True
        assert gs.current_character.health > old_health
        assert "healed" in msg.lower() or "used" in msg.lower()

    def test_use_item_not_found(self, game_state_with_items):
        """Spec: Error message when item doesn't exist."""
        cont, msg = handle_exploration_command(game_state_with_items, "use", ["nonexistent"])
        assert cont is True
        assert "not found" in msg.lower() or "don't have" in msg.lower()

    def test_use_no_args(self, game_state_with_items):
        """Spec: Error when no item name specified."""
        cont, msg = handle_exploration_command(game_state_with_items, "use", [])
        assert cont is True
        assert "what" in msg.lower() or "specify" in msg.lower()


class TestParseCommandInventory:
    """Tests for parse_command with new inventory commands."""

    def test_parse_inventory_command(self):
        """Spec: 'inventory' is a recognized command."""
        cmd, args = parse_command("inventory")
        assert cmd == "inventory"

    def test_parse_equip_command(self):
        """Spec: 'equip' parses with item name as args."""
        cmd, args = parse_command("equip iron sword")
        assert cmd == "equip"
        assert args == ["iron", "sword"]

    def test_parse_unequip_command(self):
        """Spec: 'unequip' parses with slot as arg."""
        cmd, args = parse_command("unequip weapon")
        assert cmd == "unequip"
        assert args == ["weapon"]

    def test_parse_use_command(self):
        """Spec: 'use' parses with item name as args."""
        cmd, args = parse_command("use health potion")
        assert cmd == "use"
        assert args == ["health", "potion"]

    def test_parse_drop_command(self):
        """Spec: 'drop' parses with item name as args."""
        cmd, args = parse_command("drop iron sword")
        assert cmd == "drop"
        assert args == ["iron", "sword"]

    def test_parse_drop_shorthand(self):
        """Spec: 'dr' expands to 'drop'."""
        cmd, args = parse_command("dr iron sword")
        assert cmd == "drop"
        assert args == ["iron", "sword"]


class TestUseEquippedItem:
    """Tests for 'use' on equipped items - Spec: Show 'equipped' message, not 'not found'."""

    def test_use_equipped_weapon_shows_equipped_message(self, game_state_with_items):
        """Spec: 'use' on equipped weapon shows equipped message, not 'not found'."""
        gs = game_state_with_items
        sword = gs.current_character.inventory.find_item_by_name("Iron Sword")
        gs.current_character.inventory.equip(sword)
        cont, msg = handle_exploration_command(gs, "use", ["iron", "sword"])
        assert cont is True
        assert "equipped" in msg.lower()
        assert "weapon" in msg.lower()
        assert "don't have" not in msg.lower()

    def test_use_equipped_armor_shows_equipped_message(self, game_state_with_items):
        """Spec: 'use' on equipped armor shows equipped message, not 'not found'."""
        gs = game_state_with_items
        armor = gs.current_character.inventory.find_item_by_name("Leather Armor")
        gs.current_character.inventory.equip(armor)
        cont, msg = handle_exploration_command(gs, "use", ["leather", "armor"])
        assert cont is True
        assert "equipped" in msg.lower()
        assert "armor" in msg.lower()
        assert "don't have" not in msg.lower()


class TestDropCommand:
    """Tests for 'drop' command - Spec: Remove item from inventory permanently."""

    def test_drop_item_success(self, game_state_with_items):
        """Spec: 'drop <item name>' removes item from inventory."""
        gs = game_state_with_items
        # Verify item exists before dropping
        potion = gs.current_character.inventory.find_item_by_name("Health Potion")
        assert potion is not None

        cont, msg = handle_exploration_command(gs, "drop", ["health", "potion"])
        assert cont is True
        assert "dropped" in msg.lower()
        assert "Health Potion" in msg

        # Verify item no longer in inventory
        assert gs.current_character.inventory.find_item_by_name("Health Potion") is None

    def test_drop_item_not_found(self, game_state_with_items):
        """Spec: Error message when item doesn't exist in inventory."""
        cont, msg = handle_exploration_command(game_state_with_items, "drop", ["nonexistent"])
        assert cont is True
        assert "don't have" in msg.lower() or "not found" in msg.lower()

    def test_drop_no_args(self, game_state_with_items):
        """Spec: Error when no item name specified."""
        cont, msg = handle_exploration_command(game_state_with_items, "drop", [])
        assert cont is True
        assert "what" in msg.lower() or "specify" in msg.lower()

    def test_drop_equipped_weapon(self, game_state_with_items):
        """Spec: Cannot drop equipped weapon - must unequip first."""
        gs = game_state_with_items
        sword = gs.current_character.inventory.find_item_by_name("Iron Sword")
        gs.current_character.inventory.equip(sword)

        cont, msg = handle_exploration_command(gs, "drop", ["iron", "sword"])
        assert cont is True
        assert "equipped" in msg.lower()
        assert "unequip" in msg.lower()

    def test_drop_equipped_armor(self, game_state_with_items):
        """Spec: Cannot drop equipped armor - must unequip first."""
        gs = game_state_with_items
        armor = gs.current_character.inventory.find_item_by_name("Leather Armor")
        gs.current_character.inventory.equip(armor)

        cont, msg = handle_exploration_command(gs, "drop", ["leather", "armor"])
        assert cont is True
        assert "equipped" in msg.lower()
        assert "unequip" in msg.lower()
