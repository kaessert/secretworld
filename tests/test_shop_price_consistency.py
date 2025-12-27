"""Tests for shop price consistency.

Regression tests to ensure shop display prices match buy/sell command prices
when CHA modifiers and other price adjustments are applied.

Regression test for ISSUES.md bug: "Shop displays: 'Iron Sword - 100 gold',
Error says: '99 gold needed'"
"""
import pytest
from cli_rpg.main import handle_exploration_command
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.social_skills import get_cha_price_modifier


class TestShopPriceConsistency:
    """Tests for shop display/buy price consistency with modifiers."""

    def test_shop_display_matches_buy_error_with_cha_modifier(self):
        """Shop display price matches buy error message price when CHA modifier applies.

        Regression test for ISSUES.md bug: "Shop displays: 'Iron Sword - 100 gold',
        Error says: '99 gold needed'"

        With CHA 11, buy price modifier is 0.99, so 100g item should show as 99g
        in both the shop display AND the insufficient funds error message.
        """
        # Create character with CHA 11 (gives 0.99 modifier = 1% discount)
        # and insufficient gold to trigger the error message
        char = Character(
            name="Shopper",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=11,  # CHA 11 = 0.99 modifier
        )
        char.add_gold(50)  # Not enough to afford the 99g adjusted price

        # Create shop with 100g item
        sword = Item(
            name="Iron Sword",
            description="A sturdy blade",
            item_type=ItemType.WEAPON,
            damage_bonus=5,
        )
        shop = Shop(name="Armory", inventory=[ShopItem(item=sword, buy_price=100)])
        merchant = NPC(
            name="Smith",
            description="A blacksmith",
            dialogue="Fine weapons here!",
            is_merchant=True,
            shop=shop,
        )
        location = Location(name="Market", description="A busy market", npcs=[merchant])
        game = GameState(char, {"Market": location}, starting_location="Market")

        # First, talk to merchant to open shop
        handle_exploration_command(game, "talk", ["smith"])

        # Get shop display - should show 99g (100 * 0.99)
        _, shop_output = handle_exploration_command(game, "shop", [])
        assert "99 gold" in shop_output, f"Shop should display 99 gold but got: {shop_output}"

        # Try to buy - should show error with same 99g price
        _, buy_output = handle_exploration_command(game, "buy", ["iron", "sword"])
        assert "99 gold" in buy_output, f"Buy error should show 99 gold but got: {buy_output}"

        # Both should reference the same price
        assert "99 gold" in shop_output
        assert "99 gold" in buy_output

    def test_shop_display_matches_buy_error_high_cha(self):
        """Shop display matches buy error with high CHA (significant discount)."""
        # CHA 20 = 0.90 modifier = 10% discount
        # 100g item should show as 90g
        char = Character(
            name="Charmer",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=20,  # CHA 20 = 0.90 modifier
        )
        char.add_gold(50)  # Not enough

        potion = Item(
            name="Elixir",
            description="A rare elixir",
            item_type=ItemType.CONSUMABLE,
            heal_amount=100,
        )
        shop = Shop(name="Apothecary", inventory=[ShopItem(item=potion, buy_price=100)])
        merchant = NPC(
            name="Alchemist",
            description="An alchemist",
            dialogue="Welcome!",
            is_merchant=True,
            shop=shop,
        )
        location = Location(name="Shop", description="A shop", npcs=[merchant])
        game = GameState(char, {"Shop": location}, starting_location="Shop")

        handle_exploration_command(game, "talk", ["alchemist"])

        _, shop_output = handle_exploration_command(game, "shop", [])
        assert "90 gold" in shop_output, f"Shop should display 90 gold but got: {shop_output}"

        _, buy_output = handle_exploration_command(game, "buy", ["elixir"])
        assert "90 gold" in buy_output, f"Buy error should show 90 gold but got: {buy_output}"

    def test_shop_display_matches_buy_error_low_cha(self):
        """Shop display matches buy error with low CHA (price markup)."""
        # CHA 5 = 1.05 modifier = 5% markup
        # 100g item should show as 105g
        char = Character(
            name="Awkward",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=5,  # CHA 5 = 1.05 modifier
        )
        char.add_gold(50)  # Not enough

        armor = Item(
            name="Chainmail",
            description="Protective armor",
            item_type=ItemType.ARMOR,
            defense_bonus=10,
        )
        shop = Shop(name="Armorer", inventory=[ShopItem(item=armor, buy_price=100)])
        merchant = NPC(
            name="Armorsmith",
            description="An armorsmith",
            dialogue="Need protection?",
            is_merchant=True,
            shop=shop,
        )
        location = Location(name="Forge", description="A forge", npcs=[merchant])
        game = GameState(char, {"Forge": location}, starting_location="Forge")

        handle_exploration_command(game, "talk", ["armorsmith"])

        _, shop_output = handle_exploration_command(game, "shop", [])
        assert "105 gold" in shop_output, f"Shop should display 105 gold but got: {shop_output}"

        _, buy_output = handle_exploration_command(game, "buy", ["chainmail"])
        assert "105 gold" in buy_output, f"Buy error should show 105 gold but got: {buy_output}"

    def test_cha_modifier_formula_verified(self):
        """Verify the CHA modifier formula is correct."""
        # CHA 10 = baseline (1.0)
        assert get_cha_price_modifier(10) == 1.0
        # CHA 11 = 0.99 (1% discount)
        assert get_cha_price_modifier(11) == 0.99
        # CHA 15 = 0.95 (5% discount)
        assert get_cha_price_modifier(15) == 0.95
        # CHA 20 = 0.90 (10% discount)
        assert get_cha_price_modifier(20) == 0.90
        # CHA 5 = 1.05 (5% markup)
        assert get_cha_price_modifier(5) == 1.05
        # CHA 1 = 1.09 (9% markup)
        assert get_cha_price_modifier(1) == 1.09
