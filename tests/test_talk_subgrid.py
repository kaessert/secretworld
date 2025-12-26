"""Tests for talk command working correctly in SubGrid sublocations.

Tests the fix for the bug where talk command couldn't find NPCs inside
SubGrid sublocations (e.g., building interiors, dungeons).
"""
import pytest
from cli_rpg.main import handle_exploration_command
from cli_rpg.game_state import GameState
from cli_rpg.world_grid import SubGrid
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType


@pytest.fixture
def game_state_in_subgrid():
    """Create a game state where the player is inside a SubGrid sublocation with an NPC."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

    # Create overworld location that has a sub-grid
    town = Location(name="Town", description="A quiet town")
    world = {"Town": town}

    # Create SubGrid with an NPC inside
    sub_grid = SubGrid(parent_name="Town")
    merchant = NPC(
        name="Shop Keeper",
        description="A friendly shopkeeper",
        dialogue="Welcome to my shop inside the market!",
        is_merchant=False,
    )
    market_interior = Location(
        name="Market Interior",
        description="Inside the market building",
        npcs=[merchant],
    )
    sub_grid.add_location(market_interior, 0, 0)

    game = GameState(char, world, starting_location="Town")

    # Simulate player entering the SubGrid sublocation
    game.current_sub_grid = sub_grid
    game.current_location = "Market Interior"
    game.in_sub_location = True

    return game


class TestTalkInSubGrid:
    """Tests for talk command inside SubGrid sublocations - spec: SubGrid NPC access."""

    def test_talk_finds_npc_in_subgrid(self, game_state_in_subgrid):
        """Talk command should find NPCs inside SubGrid sublocations.

        Bug fix: talk command was using game_state.world.get() which only
        looks in overworld, not in SubGrid. Fix uses get_current_location().
        """
        cont, msg = handle_exploration_command(game_state_in_subgrid, "talk", [])
        # Should NOT return "no NPCs here" - should find the Shop Keeper
        assert "no npc" not in msg.lower()
        assert cont is True
        # Should show the NPC's dialogue or name
        assert "shop keeper" in msg.lower() or "welcome" in msg.lower()

    def test_talk_to_specific_npc_in_subgrid(self, game_state_in_subgrid):
        """Talk command with NPC name should work inside SubGrid sublocations."""
        cont, msg = handle_exploration_command(
            game_state_in_subgrid, "talk", ["Shop", "Keeper"]
        )
        assert cont is True
        assert "no npc" not in msg.lower()
        # Should show the NPC's dialogue
        assert "welcome" in msg.lower() or "shop keeper" in msg.lower()

    def test_talk_npc_not_found_in_subgrid(self, game_state_in_subgrid):
        """Talk command shows error when NPC not found in SubGrid."""
        cont, msg = handle_exploration_command(
            game_state_in_subgrid, "talk", ["NonExistent"]
        )
        assert cont is True
        # Should indicate NPC not found (not "no NPCs here")
        assert "don't see" in msg.lower() or "not here" in msg.lower()


class TestTalkInSubGridWithMerchant:
    """Tests for talk command with merchant NPCs in SubGrid."""

    def test_talk_to_merchant_in_subgrid_sets_shop(self):
        """Talk to merchant NPC inside SubGrid should set current shop."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Create overworld
        town = Location(name="Town", description="A quiet town")
        world = {"Town": town}

        # Create SubGrid with a merchant inside
        sub_grid = SubGrid(parent_name="Town")
        potion = Item(
            name="Health Potion",
            description="Heals 25 HP",
            item_type=ItemType.CONSUMABLE,
            heal_amount=25,
        )
        shop = Shop(name="Interior Shop", inventory=[ShopItem(item=potion, buy_price=50)])
        merchant = NPC(
            name="Interior Merchant",
            description="A shopkeeper inside the building",
            dialogue="Welcome! Browse my wares.",
            is_merchant=True,
            shop=shop,
        )
        shop_interior = Location(
            name="Shop Interior",
            description="Inside the shop building",
            npcs=[merchant],
        )
        sub_grid.add_location(shop_interior, 0, 0)

        game = GameState(char, world, starting_location="Town")
        game.current_sub_grid = sub_grid
        game.current_location = "Shop Interior"
        game.in_sub_location = True

        # Talk to merchant
        cont, msg = handle_exploration_command(game, "talk", ["Interior", "Merchant"])
        assert cont is True
        assert "welcome" in msg.lower()
        # Shop context should be set
        assert game.current_shop is not None
        assert game.current_shop.name == "Interior Shop"
