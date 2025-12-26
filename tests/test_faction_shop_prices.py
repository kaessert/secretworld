"""Tests for faction reputation effects on shop prices.

Tests the Merchant Guild faction price modifiers:
- HOSTILE: Trade refused
- UNFRIENDLY: +15% buy, -15% sell
- NEUTRAL: No modifier
- FRIENDLY: -10% buy, +10% sell
- HONORED: -20% buy, +20% sell
"""
import pytest
from cli_rpg.faction_shop import (
    get_faction_price_modifiers,
    get_merchant_guild_faction,
    get_faction_price_message,
    FACTION_PRICE_MODIFIERS,
)
from cli_rpg.models.faction import Faction, ReputationLevel
from cli_rpg.main import handle_exploration_command
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType


def create_merchant_guild(reputation: int = 50) -> Faction:
    """Helper to create a Merchant Guild faction with specific reputation."""
    return Faction(
        name="Merchant Guild",
        description="A coalition of traders and shopkeepers",
        reputation=reputation,
    )


def create_factions_with_merchant_guild(reputation: int = 50) -> list[Faction]:
    """Helper to create faction list with Merchant Guild at specific reputation."""
    return [create_merchant_guild(reputation)]


@pytest.fixture
def game_with_shop_and_factions():
    """Create a game state with a merchant NPC, shop, and faction tracking."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    char.add_gold(500)

    potion = Item(
        name="Health Potion",
        description="Heals 25 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=25,
    )
    sword = Item(
        name="Iron Sword",
        description="A blade",
        item_type=ItemType.WEAPON,
        damage_bonus=5,
    )
    # Set base prices: potion=100, sword=200 for easy math
    shop_items = [ShopItem(item=potion, buy_price=100), ShopItem(item=sword, buy_price=200)]
    shop = Shop(name="General Store", inventory=shop_items)

    merchant = NPC(
        name="Merchant",
        description="A guild shopkeeper",
        dialogue="Welcome!",
        is_merchant=True,
        shop=shop,
    )

    town = Location(name="Town", description="A market town", npcs=[merchant])
    world = {"Town": town}
    game = GameState(char, world, starting_location="Town")
    return game


class TestGetMerchantGuildFaction:
    """Tests for finding the Merchant Guild faction."""

    def test_finds_merchant_guild(self):
        """Finds Merchant Guild when present in faction list."""
        factions = create_factions_with_merchant_guild(50)
        result = get_merchant_guild_faction(factions)
        assert result is not None
        assert result.name == "Merchant Guild"

    def test_returns_none_when_not_present(self):
        """Returns None when Merchant Guild not in faction list."""
        factions = [
            Faction(name="Thieves Guild", description="Rogues and cutpurses", reputation=30)
        ]
        result = get_merchant_guild_faction(factions)
        assert result is None

    def test_returns_none_for_empty_list(self):
        """Returns None for empty faction list."""
        result = get_merchant_guild_faction([])
        assert result is None


class TestGetFactionPriceModifiers:
    """Tests for price modifiers based on faction reputation.

    Tests spec: Faction price modifiers table
    | Reputation Level | Buy Price | Sell Price | Trade Allowed |
    |------------------|-----------|------------|---------------|
    | HOSTILE (1-19)   | N/A       | N/A        | REFUSED       |
    | UNFRIENDLY (20-39) | +15%    | -15%       | Yes           |
    | NEUTRAL (40-59)  | +0%       | +0%        | Yes           |
    | FRIENDLY (60-79) | -10%      | +10%       | Yes           |
    | HONORED (80-100) | -20%      | +20%       | Yes           |
    """

    def test_hostile_refuses_trade(self):
        """HOSTILE reputation (1-19) blocks all trading."""
        factions = create_factions_with_merchant_guild(10)  # HOSTILE
        buy_mod, sell_mod, refused = get_faction_price_modifiers(factions)
        assert refused is True
        assert buy_mod is None
        assert sell_mod is None

    def test_unfriendly_premium_and_penalty(self):
        """UNFRIENDLY reputation (20-39) charges 15% more, pays 15% less."""
        factions = create_factions_with_merchant_guild(30)  # UNFRIENDLY
        buy_mod, sell_mod, refused = get_faction_price_modifiers(factions)
        assert refused is False
        assert buy_mod == 1.15
        assert sell_mod == 0.85

    def test_neutral_no_modifier(self):
        """NEUTRAL reputation (40-59) has no price modifier."""
        factions = create_factions_with_merchant_guild(50)  # NEUTRAL
        buy_mod, sell_mod, refused = get_faction_price_modifiers(factions)
        assert refused is False
        assert buy_mod == 1.0
        assert sell_mod == 1.0

    def test_friendly_discount_and_bonus(self):
        """FRIENDLY reputation (60-79) gets 10% discount on buy, 10% bonus on sell."""
        factions = create_factions_with_merchant_guild(70)  # FRIENDLY
        buy_mod, sell_mod, refused = get_faction_price_modifiers(factions)
        assert refused is False
        assert buy_mod == 0.90
        assert sell_mod == 1.10

    def test_honored_best_prices(self):
        """HONORED reputation (80-100) gets 20% discount on buy, 20% bonus on sell."""
        factions = create_factions_with_merchant_guild(90)  # HONORED
        buy_mod, sell_mod, refused = get_faction_price_modifiers(factions)
        assert refused is False
        assert buy_mod == 0.80
        assert sell_mod == 1.20

    def test_no_merchant_guild_defaults_to_neutral(self):
        """When no Merchant Guild faction exists, treat as neutral (no modifier)."""
        factions = []  # No factions at all
        buy_mod, sell_mod, refused = get_faction_price_modifiers(factions)
        assert refused is False
        assert buy_mod == 1.0
        assert sell_mod == 1.0


class TestGetFactionPriceMessage:
    """Tests for faction-based price display messages."""

    def test_hostile_message(self):
        """HOSTILE shows refusal message."""
        msg = get_faction_price_message(ReputationLevel.HOSTILE)
        assert "refuse" in msg.lower() or "hostil" in msg.lower()

    def test_unfriendly_message(self):
        """UNFRIENDLY shows premium message."""
        msg = get_faction_price_message(ReputationLevel.UNFRIENDLY)
        assert "15%" in msg

    def test_neutral_message(self):
        """NEUTRAL returns empty message (no effect to show)."""
        msg = get_faction_price_message(ReputationLevel.NEUTRAL)
        assert msg == ""

    def test_friendly_message(self):
        """FRIENDLY shows discount message."""
        msg = get_faction_price_message(ReputationLevel.FRIENDLY)
        assert "10%" in msg

    def test_honored_message(self):
        """HONORED shows best discount message."""
        msg = get_faction_price_message(ReputationLevel.HONORED)
        assert "20%" in msg


class TestBuyCommandWithFactionReputation:
    """Tests for buy command integration with faction price modifiers.

    Tests spec: Buy price affected by faction reputation.
    """

    def test_buy_hostile_faction_refuses_trade(self, game_with_shop_and_factions):
        """HOSTILE reputation blocks buy command entirely."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(10)  # HOSTILE

        # Start shop interaction
        handle_exploration_command(game, "talk", ["merchant"])

        # Attempt to buy
        cont, msg = handle_exploration_command(game, "buy", ["health", "potion"])
        assert cont is True
        assert "refuse" in msg.lower() or "reputation" in msg.lower()
        # Ensure no gold was spent
        assert game.current_character.gold == 500
        # Ensure item was not added to inventory
        assert game.current_character.inventory.find_item_by_name("Health Potion") is None

    def test_buy_unfriendly_pays_premium(self, game_with_shop_and_factions):
        """UNFRIENDLY reputation pays 15% more for items."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(30)  # UNFRIENDLY

        # Start shop interaction
        handle_exploration_command(game, "talk", ["merchant"])

        # Base price is 100, +15% = ~115 (114-115 due to float precision)
        cont, msg = handle_exploration_command(game, "buy", ["health", "potion"])
        assert cont is True
        assert "bought" in msg.lower()
        # 500 - 114 (or 115) = 385-386 (int truncation of 114.99999... = 114)
        assert 385 <= game.current_character.gold <= 386

    def test_buy_friendly_gets_discount(self, game_with_shop_and_factions):
        """FRIENDLY reputation gets 10% discount on purchases."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(70)  # FRIENDLY

        handle_exploration_command(game, "talk", ["merchant"])

        # Base price is 100, -10% = 90
        cont, msg = handle_exploration_command(game, "buy", ["health", "potion"])
        assert cont is True
        # 500 - 90 = 410
        assert game.current_character.gold == 410

    def test_buy_honored_gets_best_discount(self, game_with_shop_and_factions):
        """HONORED reputation gets 20% discount on purchases."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(90)  # HONORED

        handle_exploration_command(game, "talk", ["merchant"])

        # Base price is 100, -20% = 80
        cont, msg = handle_exploration_command(game, "buy", ["health", "potion"])
        assert cont is True
        # 500 - 80 = 420
        assert game.current_character.gold == 420

    def test_buy_stacks_with_cha_modifier(self, game_with_shop_and_factions):
        """Faction modifier stacks correctly with CHA modifier."""
        game = game_with_shop_and_factions
        # High CHA for discount
        game.current_character.charisma = 20  # High CHA reduces prices
        game.factions = create_factions_with_merchant_guild(90)  # HONORED (-20%)

        handle_exploration_command(game, "talk", ["merchant"])

        # CHA 20 gives ~0.9 modifier (10% discount from CHA)
        # Faction HONORED gives 0.8 modifier (20% discount)
        # Base 100 * 0.9 (CHA) * 0.8 (faction) = 72
        cont, msg = handle_exploration_command(game, "buy", ["health", "potion"])
        assert cont is True
        # Allow some tolerance for rounding
        expected_gold = 500 - 72  # 428
        assert 426 <= game.current_character.gold <= 430


class TestSellCommandWithFactionReputation:
    """Tests for sell command integration with faction price modifiers.

    Tests spec: Sell price affected by faction reputation.
    """

    def test_sell_hostile_faction_refuses_trade(self, game_with_shop_and_factions):
        """HOSTILE reputation blocks sell command entirely."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(10)  # HOSTILE

        # Add item to sell
        item = Item(
            name="Ruby",
            description="A precious gem",
            item_type=ItemType.CONSUMABLE,
            heal_amount=0,
        )
        game.current_character.inventory.add_item(item)

        handle_exploration_command(game, "talk", ["merchant"])

        cont, msg = handle_exploration_command(game, "sell", ["ruby"])
        assert cont is True
        assert "refuse" in msg.lower() or "reputation" in msg.lower()
        # Item should still be in inventory
        assert game.current_character.inventory.find_item_by_name("Ruby") is not None
        # Gold unchanged
        assert game.current_character.gold == 500

    def test_sell_unfriendly_gets_less(self, game_with_shop_and_factions):
        """UNFRIENDLY reputation receives 15% less gold when selling."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(30)  # UNFRIENDLY

        # Add item with known value (base sell = 10 + stats*2)
        # Item with heal_amount=0, damage_bonus=0, defense_bonus=0: base sell = 10
        item = Item(
            name="Ruby",
            description="A gem",
            item_type=ItemType.CONSUMABLE,
        )
        game.current_character.inventory.add_item(item)

        handle_exploration_command(game, "talk", ["merchant"])

        starting_gold = game.current_character.gold
        cont, msg = handle_exploration_command(game, "sell", ["ruby"])
        assert cont is True
        assert "sold" in msg.lower()

        # Base sell price = 10, with UNFRIENDLY -15% = 8.5 -> 8 (int)
        # With base CHA modifier (1.0 for CHA 10)
        earned = game.current_character.gold - starting_gold
        assert earned == 8  # 10 * 0.85 = 8.5 -> 8

    def test_sell_friendly_gets_bonus(self, game_with_shop_and_factions):
        """FRIENDLY reputation receives 10% more gold when selling."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(70)  # FRIENDLY

        item = Item(
            name="Ruby",
            description="A gem",
            item_type=ItemType.CONSUMABLE,
        )
        game.current_character.inventory.add_item(item)

        handle_exploration_command(game, "talk", ["merchant"])

        starting_gold = game.current_character.gold
        cont, msg = handle_exploration_command(game, "sell", ["ruby"])
        assert cont is True

        # Base sell price = 10, with FRIENDLY +10% = 11
        earned = game.current_character.gold - starting_gold
        assert earned == 11

    def test_sell_honored_gets_best_bonus(self, game_with_shop_and_factions):
        """HONORED reputation receives 20% more gold when selling."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(90)  # HONORED

        item = Item(
            name="Ruby",
            description="A gem",
            item_type=ItemType.CONSUMABLE,
        )
        game.current_character.inventory.add_item(item)

        handle_exploration_command(game, "talk", ["merchant"])

        starting_gold = game.current_character.gold
        cont, msg = handle_exploration_command(game, "sell", ["ruby"])
        assert cont is True

        # Base sell price = 10, with HONORED +20% = 12
        earned = game.current_character.gold - starting_gold
        assert earned == 12


class TestShopCommandWithFactionReputation:
    """Tests for shop display with faction reputation status.

    Tests spec: Shop command shows reputation-based price message.
    """

    def test_shop_hostile_shows_refusal(self, game_with_shop_and_factions):
        """Shop command shows refusal message for HOSTILE reputation."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(10)  # HOSTILE

        cont, msg = handle_exploration_command(game, "shop", [])
        assert cont is True
        assert "refuse" in msg.lower() or "hostil" in msg.lower()

    def test_shop_unfriendly_shows_premium(self, game_with_shop_and_factions):
        """Shop command shows premium message for UNFRIENDLY reputation."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(30)  # UNFRIENDLY

        cont, msg = handle_exploration_command(game, "shop", [])
        assert cont is True
        assert "15%" in msg or "higher" in msg.lower()

    def test_shop_neutral_no_message(self, game_with_shop_and_factions):
        """Shop command shows no reputation message for NEUTRAL."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(50)  # NEUTRAL

        cont, msg = handle_exploration_command(game, "shop", [])
        assert cont is True
        # Should show shop items but no reputation modifier message
        assert "General Store" in msg

    def test_shop_friendly_shows_discount(self, game_with_shop_and_factions):
        """Shop command shows discount message for FRIENDLY reputation."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(70)  # FRIENDLY

        cont, msg = handle_exploration_command(game, "shop", [])
        assert cont is True
        assert "10%" in msg or "discount" in msg.lower()

    def test_shop_honored_shows_best_discount(self, game_with_shop_and_factions):
        """Shop command shows best discount message for HONORED reputation."""
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(90)  # HONORED

        cont, msg = handle_exploration_command(game, "shop", [])
        assert cont is True
        assert "20%" in msg or "honored" in msg.lower()

    def test_shop_displays_faction_adjusted_prices(self, game_with_shop_and_factions):
        """Shop command shows faction-adjusted prices, not base prices.

        Tests spec: Shop display should show the same adjusted prices that
        the buy command uses, preventing confusion when displayed and charged
        prices don't match.
        """
        game = game_with_shop_and_factions
        game.factions = create_factions_with_merchant_guild(90)  # HONORED (-20%)

        cont, msg = handle_exploration_command(game, "shop", [])
        assert cont is True
        # Base price is 100 for Health Potion, HONORED = 80
        assert "80 gold" in msg
        # Should NOT show base price
        assert "100 gold" not in msg
        # Also check Iron Sword: base 200, HONORED = 160
        assert "160 gold" in msg
        assert "200 gold" not in msg
