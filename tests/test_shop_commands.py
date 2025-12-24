"""Tests for shop commands in main game loop.

Tests the talk, buy, sell, and shop commands.
"""
import pytest
from cli_rpg.main import handle_exploration_command
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType


@pytest.fixture
def game_with_shop():
    """Create a game state with a merchant NPC and shop."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    char.add_gold(200)

    potion = Item(name="Health Potion", description="Heals 25 HP", item_type=ItemType.CONSUMABLE, heal_amount=25)
    sword = Item(name="Iron Sword", description="A blade", item_type=ItemType.WEAPON, damage_bonus=5)
    shop_items = [ShopItem(item=potion, buy_price=50), ShopItem(item=sword, buy_price=150)]
    shop = Shop(name="General Store", inventory=shop_items)

    merchant = NPC(name="Merchant", description="A friendly shopkeeper", dialogue="Welcome to my shop!", is_merchant=True, shop=shop)

    town = Location(name="Town", description="A quiet town", npcs=[merchant])
    world = {"Town": town}
    return GameState(char, world, starting_location="Town")


class TestTalkCommand:
    """Tests for talk command - tests spec: Commands (talk)."""

    def test_talk_to_merchant(self, game_with_shop):
        """Talk command shows NPC dialogue and sets current shop."""
        cont, msg = handle_exploration_command(game_with_shop, "talk", ["merchant"])
        assert cont is True
        assert "Welcome to my shop" in msg
        assert game_with_shop.current_shop is not None

    def test_talk_npc_not_found(self, game_with_shop):
        """Talk command shows error when NPC not found."""
        cont, msg = handle_exploration_command(game_with_shop, "talk", ["nobody"])
        assert cont is True
        assert "don't see" in msg.lower() or "not here" in msg.lower()

    def test_talk_no_args(self, game_with_shop):
        """Talk command shows error when no NPC specified."""
        cont, msg = handle_exploration_command(game_with_shop, "talk", [])
        assert cont is True
        assert "who" in msg.lower() or "specify" in msg.lower()


class TestBuyCommand:
    """Tests for buy command - tests spec: Commands (buy)."""

    def test_buy_item_success(self, game_with_shop):
        """Buy command purchases item and deducts gold."""
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["health", "potion"])
        assert cont is True
        assert "bought" in msg.lower() or "purchased" in msg.lower()
        assert game_with_shop.current_character.gold == 150  # 200 - 50
        assert game_with_shop.current_character.inventory.find_item_by_name("Health Potion") is not None

    def test_buy_insufficient_gold(self, game_with_shop):
        """Buy command shows error when insufficient gold."""
        game_with_shop.current_character.gold = 10
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["iron", "sword"])
        assert cont is True
        assert "afford" in msg.lower() or "gold" in msg.lower()

    def test_buy_not_in_shop(self, game_with_shop):
        """Buy command shows error when not at a shop."""
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["health", "potion"])
        assert cont is True
        assert "shop" in msg.lower() or "talk" in msg.lower()

    def test_buy_no_args(self, game_with_shop):
        """Buy command shows error when no item specified."""
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", [])
        assert cont is True
        assert "what" in msg.lower() or "specify" in msg.lower()

    def test_buy_item_not_in_shop(self, game_with_shop):
        """Buy command shows error when item not in shop."""
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["nonexistent"])
        assert cont is True
        assert "doesn't have" in msg.lower() or "not found" in msg.lower()

    def test_buy_partial_name_match(self, game_with_shop):
        """Buy command matches partial item name."""
        # Tests spec: Partial name matching - "sword" matches "Iron Sword"
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["sword"])
        assert cont is True
        assert "bought" in msg.lower()
        assert "Iron Sword" in msg

    def test_buy_partial_name_multiple_matches(self, game_with_shop):
        """Buy command shows options when multiple items match."""
        # Tests spec: Multiple matches - show all matching items as suggestions
        mana_potion = Item(
            name="Mana Potion",
            description="Restores mana",
            item_type=ItemType.CONSUMABLE
        )
        # Add mana potion to the shop via NPC before talking
        merchant = game_with_shop.get_current_location().npcs[0]
        merchant.shop.inventory.append(ShopItem(item=mana_potion, buy_price=75))

        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["potion"])
        assert cont is True
        assert "multiple" in msg.lower()
        assert "Health Potion" in msg
        assert "Mana Potion" in msg

    def test_buy_no_match_shows_available(self, game_with_shop):
        """Buy command shows available items when no match found."""
        # Tests spec: No matches - show "Did you mean...?" with similar items
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "buy", ["wand"])
        assert cont is True
        assert "doesn't have" in msg.lower()
        assert "available" in msg.lower()
        assert "Iron Sword" in msg


class TestSellCommand:
    """Tests for sell command - tests spec: Commands (sell)."""

    def test_sell_item_success(self, game_with_shop):
        """Sell command removes item from inventory and adds gold."""
        item = Item(name="Old Sword", description="Rusty", item_type=ItemType.WEAPON, damage_bonus=2)
        game_with_shop.current_character.inventory.add_item(item)
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        old_gold = game_with_shop.current_character.gold
        cont, msg = handle_exploration_command(game_with_shop, "sell", ["old", "sword"])
        assert cont is True
        assert "sold" in msg.lower()
        assert game_with_shop.current_character.gold > old_gold
        assert game_with_shop.current_character.inventory.find_item_by_name("Old Sword") is None

    def test_sell_item_not_in_inventory(self, game_with_shop):
        """Sell command shows error when item not in inventory."""
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "sell", ["nonexistent"])
        assert cont is True
        assert "don't have" in msg.lower()

    def test_sell_not_in_shop(self, game_with_shop):
        """Sell command shows error when not at a shop."""
        item = Item(name="Old Sword", description="Rusty", item_type=ItemType.WEAPON, damage_bonus=2)
        game_with_shop.current_character.inventory.add_item(item)
        cont, msg = handle_exploration_command(game_with_shop, "sell", ["old", "sword"])
        assert cont is True
        assert "shop" in msg.lower() or "talk" in msg.lower()

    def test_sell_equipped_weapon_shows_helpful_message(self, game_with_shop):
        """Sell command shows helpful message when trying to sell equipped weapon."""
        # Tests spec: Selling equipped items should explain why it fails
        item = Item(name="Battle Axe", description="Sharp", item_type=ItemType.WEAPON, damage_bonus=5)
        game_with_shop.current_character.inventory.add_item(item)
        game_with_shop.current_character.inventory.equip(item)
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "sell", ["battle", "axe"])
        assert cont is True
        assert "equipped" in msg.lower()
        assert "unequip weapon" in msg.lower()

    def test_sell_equipped_armor_shows_helpful_message(self, game_with_shop):
        """Sell command shows helpful message when trying to sell equipped armor."""
        # Tests spec: Selling equipped items should explain why it fails
        item = Item(name="Steel Plate", description="Heavy", item_type=ItemType.ARMOR, defense_bonus=5)
        game_with_shop.current_character.inventory.add_item(item)
        game_with_shop.current_character.inventory.equip(item)
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "sell", ["steel", "plate"])
        assert cont is True
        assert "equipped" in msg.lower()
        assert "unequip armor" in msg.lower()


class TestShopCommand:
    """Tests for shop command - tests spec: Commands (shop)."""

    def test_shop_lists_items(self, game_with_shop):
        """Shop command lists available items and prices."""
        handle_exploration_command(game_with_shop, "talk", ["merchant"])
        cont, msg = handle_exploration_command(game_with_shop, "shop", [])
        assert cont is True
        assert "Health Potion" in msg
        assert "50" in msg  # Price
        assert "Iron Sword" in msg

    def test_shop_not_at_shop(self, game_with_shop):
        """Shop command shows error when not at a shop."""
        cont, msg = handle_exploration_command(game_with_shop, "shop", [])
        assert cont is True
        assert "not at a shop" in msg.lower() or "talk" in msg.lower()


class TestParseShopCommands:
    """Tests for parse_command with shop commands."""

    def test_parse_talk(self):
        """parse_command recognizes talk command."""
        cmd, args = parse_command("talk merchant")
        assert cmd == "talk"
        assert args == ["merchant"]

    def test_parse_buy(self):
        """parse_command recognizes buy command."""
        cmd, args = parse_command("buy health potion")
        assert cmd == "buy"
        assert args == ["health", "potion"]

    def test_parse_sell(self):
        """parse_command recognizes sell command."""
        cmd, args = parse_command("sell old sword")
        assert cmd == "sell"
        assert args == ["old", "sword"]

    def test_parse_shop(self):
        """parse_command recognizes shop command."""
        cmd, args = parse_command("shop")
        assert cmd == "shop"
        assert args == []
