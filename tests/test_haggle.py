"""Tests for haggle command and mechanics.

Spec: thoughts/current_plan.md
"""
import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.models.character import Character
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState
from cli_rpg.social_skills import calculate_haggle_chance, attempt_haggle


class TestCalculateHaggleChance:
    """Tests for calculate_haggle_chance function."""

    def test_calculate_haggle_chance_base(self):
        """Test base formula: 25% + CHA×2%, max 85%.

        With CHA 10: 25 + 10*2 = 45%
        """
        # Spec: test 1 - base formula
        result = calculate_haggle_chance(charisma=10, persuaded=False)
        assert result == 45  # 25 + 10*2 = 45

    def test_calculate_haggle_chance_low_cha(self):
        """Test with low CHA (5): 25 + 5*2 = 35%."""
        result = calculate_haggle_chance(charisma=5, persuaded=False)
        assert result == 35  # 25 + 5*2 = 35

    def test_calculate_haggle_chance_high_cha(self):
        """Test with high CHA (20): 25 + 20*2 = 65%."""
        result = calculate_haggle_chance(charisma=20, persuaded=False)
        assert result == 65  # 25 + 20*2 = 65

    def test_calculate_haggle_chance_max_cap(self):
        """Test that chance is capped at 85%."""
        # With CHA 40: 25 + 40*2 = 105, should cap at 85
        result = calculate_haggle_chance(charisma=40, persuaded=False)
        assert result == 85  # Max cap

    def test_calculate_haggle_chance_with_persuaded_bonus(self):
        """Test +15% bonus when NPC is persuaded.

        With CHA 10 + persuaded: 25 + 10*2 + 15 = 60%
        """
        # Spec: test 2 - +15% when persuaded
        result = calculate_haggle_chance(charisma=10, persuaded=True)
        assert result == 60  # 25 + 10*2 + 15 = 60


class TestAttemptHaggle:
    """Tests for attempt_haggle function."""

    def make_character(self, charisma: int = 10) -> Character:
        """Create a test character with specified CHA."""
        return Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=charisma,
        )

    def make_merchant_npc(self, haggleable: bool = True, haggle_cooldown: int = 0, persuaded: bool = False) -> NPC:
        """Create a test merchant NPC."""
        shop = Shop(
            name="Test Shop",
            inventory=[
                ShopItem(item=Item(name="Sword", description="A sword", item_type=ItemType.WEAPON), buy_price=100)
            ]
        )
        npc = NPC(
            name="Merchant",
            description="A merchant",
            dialogue="Welcome to my shop!",
            is_merchant=True,
            shop=shop,
            haggleable=haggleable,
            haggle_cooldown=haggle_cooldown,
        )
        npc.persuaded = persuaded
        return npc

    def test_haggle_success_grants_discount(self):
        """Test that successful haggle returns 15% bonus.

        Spec: test 3 - success sets bonus = 0.15
        With CHA 20: chance = 25 + 20*2 = 65%, crit threshold = 6.5 (roll ≤ 6)
        So roll = 10 is normal success (10 <= 65 but 10 > 6)
        """
        character = self.make_character(charisma=20)  # High CHA for good chance
        npc = self.make_merchant_npc()

        # Mock random.randint to succeed but not crit (roll = 10, above crit threshold 6)
        with patch("cli_rpg.social_skills.random.randint", return_value=10):
            success, message, bonus, cooldown = attempt_haggle(character, npc)

        assert success is True
        assert bonus == 0.15
        assert cooldown == 0
        assert "15%" in message or "deal" in message.lower()

    def test_haggle_critical_success_grants_larger_discount(self):
        """Test critical success (roll ≤ 10% of success chance) gives 25% bonus.

        Spec: test 4 - 25% bonus on crit
        With CHA 10: chance = 45%, crit threshold = 4.5 (roll ≤ 4)
        """
        character = self.make_character(charisma=10)
        npc = self.make_merchant_npc()

        # Mock random.randint to roll within crit threshold (roll = 4)
        with patch("cli_rpg.social_skills.random.randint", return_value=4):
            success, message, bonus, cooldown = attempt_haggle(character, npc)

        assert success is True
        assert bonus == 0.25  # Critical success bonus
        assert "rare" in message.lower() or "exceptional" in message.lower()

    def test_haggle_failure_no_effect(self):
        """Test that failed haggle returns 0 bonus.

        Spec: test 5 - failed haggle keeps haggle_bonus = 0
        """
        character = self.make_character(charisma=10)  # 45% chance
        npc = self.make_merchant_npc()

        # Mock random.randint to fail (roll = 50, above 45% threshold)
        with patch("cli_rpg.social_skills.random.randint", return_value=50):
            success, message, bonus, cooldown = attempt_haggle(character, npc)

        assert success is False
        assert bonus == 0.0
        assert cooldown == 0

    def test_haggle_critical_failure_sets_cooldown(self):
        """Test critical failure (roll ≥ 95) sets cooldown = 3.

        Spec: test 6 - roll ≥ 95 sets cooldown = 3
        """
        character = self.make_character(charisma=10)
        npc = self.make_merchant_npc()

        # Mock random.randint to crit fail (roll = 95)
        with patch("cli_rpg.social_skills.random.randint", return_value=95):
            success, message, bonus, cooldown = attempt_haggle(character, npc)

        assert success is False
        assert bonus == 0.0
        assert cooldown == 3
        assert "refuse" in message.lower() or "angry" in message.lower()

    def test_haggle_stubborn_merchant(self):
        """Test NPC with haggleable=False refuses to haggle.

        Spec: test 8 - NPC with haggleable=False refuses
        """
        character = self.make_character(charisma=20)
        npc = self.make_merchant_npc(haggleable=False)

        success, message, bonus, cooldown = attempt_haggle(character, npc)

        assert success is False
        assert bonus == 0.0
        assert "won't haggle" in message.lower() or "refuse" in message.lower() or "stubborn" in message.lower()

    def test_haggle_cooldown_blocks_attempt(self):
        """Test that cooldown > 0 blocks haggle attempts.

        Spec: test 9 - can't haggle when cooldown > 0
        """
        character = self.make_character(charisma=20)
        npc = self.make_merchant_npc(haggle_cooldown=2)

        success, message, bonus, cooldown = attempt_haggle(character, npc)

        assert success is False
        assert bonus == 0.0
        assert "wait" in message.lower() or "cooldown" in message.lower() or "angry" in message.lower()


class TestHaggleIntegration:
    """Integration tests for haggle with game state."""

    def make_game_state(self, charisma: int = 10) -> GameState:
        """Create a minimal game state for testing."""
        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=charisma,
        )
        character.add_gold(500)

        shop = Shop(
            name="Test Shop",
            inventory=[
                ShopItem(item=Item(name="Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5), buy_price=100)
            ]
        )
        npc = NPC(
            name="Merchant",
            description="A merchant",
            dialogue="Welcome!",
            is_merchant=True,
            shop=shop,
        )

        location = Location(
            name="Town Square",
            description="A bustling town square",
            npcs=[npc],
            coordinates=(0, 0),
        )

        world = {"Town Square": location}
        game_state = GameState(character, world, "Town Square")
        game_state.current_shop = shop
        game_state.current_npc = npc
        return game_state

    def test_haggle_not_at_shop(self):
        """Test error when current_shop is None.

        Spec: test 7 - error when current_shop is None
        """
        game_state = self.make_game_state()
        game_state.current_shop = None

        # Haggle attempt should fail
        success, message, bonus, cooldown = attempt_haggle(
            game_state.current_character, None
        )

        assert success is False
        assert "shop" in message.lower() or "merchant" in message.lower()

    def test_buy_applies_haggle_bonus(self):
        """Test that buy price is reduced by haggle_bonus.

        Spec: test 11 - buy price reduced by haggle_bonus
        Item price 100, with 15% haggle_bonus: final = 85
        """
        from cli_rpg.main import handle_exploration_command

        game_state = self.make_game_state(charisma=10)  # CHA 10 = no modifier
        game_state.haggle_bonus = 0.15

        initial_gold = game_state.current_character.gold

        # Buy the sword (base price 100)
        with patch("cli_rpg.main.autosave"):  # Don't actually save
            success, message = handle_exploration_command(game_state, "buy", ["sword"])

        # Price should be 100 * (1 - 0.15) = 85
        expected_price = int(100 * (1 - 0.15))  # 85
        assert game_state.current_character.gold == initial_gold - expected_price
        assert "85" in message or "bought" in message.lower()

    def test_sell_applies_haggle_bonus(self):
        """Test that sell price is increased by haggle_bonus.

        Spec: test 12 - sell price increased by haggle_bonus
        """
        from cli_rpg.main import handle_exploration_command

        game_state = self.make_game_state(charisma=10)
        game_state.haggle_bonus = 0.15

        # Add an item to sell
        sword = Item(name="Old Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5)
        game_state.current_character.inventory.add_item(sword)
        initial_gold = game_state.current_character.gold

        with patch("cli_rpg.main.autosave"):  # Don't actually save
            success, message = handle_exploration_command(game_state, "sell", ["Old", "Sword"])

        # Base sell price: 10 + (5 + 0 + 0) * 2 = 20
        # With 15% bonus: 20 * 1.15 = 23
        base_price = 10 + (5 + 0 + 0) * 2  # 20
        expected_price = int(base_price * (1 + 0.15))  # 23

        assert game_state.current_character.gold == initial_gold + expected_price

    def test_haggle_bonus_consumed_after_buy(self):
        """Test that haggle_bonus is reset to 0 after purchase.

        Spec: test 13 - bonus reset to 0 after purchase
        """
        from cli_rpg.main import handle_exploration_command

        game_state = self.make_game_state()
        game_state.haggle_bonus = 0.15

        with patch("cli_rpg.main.autosave"):
            handle_exploration_command(game_state, "buy", ["sword"])

        assert game_state.haggle_bonus == 0.0

    def test_haggle_bonus_consumed_after_sell(self):
        """Test that haggle_bonus is reset to 0 after sale.

        Spec: test 14 - bonus reset to 0 after sale
        """
        from cli_rpg.main import handle_exploration_command

        game_state = self.make_game_state()
        game_state.haggle_bonus = 0.15

        sword = Item(name="Old Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5)
        game_state.current_character.inventory.add_item(sword)

        with patch("cli_rpg.main.autosave"):
            handle_exploration_command(game_state, "sell", ["Old", "Sword"])

        assert game_state.haggle_bonus == 0.0

    def test_haggle_cooldown_decrements(self):
        """Test that cooldown is reduced by exploration commands.

        Spec: test 10 - cooldown reduced each command
        """
        game_state = self.make_game_state()
        npc = game_state.current_npc
        npc.haggle_cooldown = 3

        # Simulate exploration command that should decrement cooldown
        # This happens at the start of handle_exploration_command
        from cli_rpg.main import handle_exploration_command

        with patch("cli_rpg.main.autosave"):
            handle_exploration_command(game_state, "look", [])

        # Cooldown should have decremented
        assert npc.haggle_cooldown == 2


class TestNPCHaggleAttributes:
    """Tests for NPC haggleable and haggle_cooldown attributes."""

    def test_npc_default_haggleable(self):
        """Test NPC is haggleable by default."""
        npc = NPC(
            name="Merchant",
            description="A merchant",
            dialogue="Welcome!",
        )
        assert npc.haggleable is True

    def test_npc_default_haggle_cooldown(self):
        """Test NPC has 0 haggle_cooldown by default."""
        npc = NPC(
            name="Merchant",
            description="A merchant",
            dialogue="Welcome!",
        )
        assert npc.haggle_cooldown == 0

    def test_npc_to_dict_includes_haggle_fields(self):
        """Test NPC serialization includes haggle fields."""
        npc = NPC(
            name="Merchant",
            description="A merchant",
            dialogue="Welcome!",
            haggleable=False,
            haggle_cooldown=2,
        )
        data = npc.to_dict()
        assert data["haggleable"] is False
        assert data["haggle_cooldown"] == 2

    def test_npc_from_dict_with_haggle_fields(self):
        """Test NPC deserialization handles haggle fields."""
        data = {
            "name": "Merchant",
            "description": "A merchant",
            "dialogue": "Welcome!",
            "haggleable": False,
            "haggle_cooldown": 2,
        }
        npc = NPC.from_dict(data)
        assert npc.haggleable is False
        assert npc.haggle_cooldown == 2

    def test_npc_from_dict_backwards_compat(self):
        """Test NPC deserialization with defaults for backward compatibility."""
        data = {
            "name": "Merchant",
            "description": "A merchant",
            "dialogue": "Welcome!",
        }
        npc = NPC.from_dict(data)
        assert npc.haggleable is True  # Default
        assert npc.haggle_cooldown == 0  # Default


class TestGameStateHaggleBonus:
    """Tests for GameState haggle_bonus attribute."""

    def test_game_state_default_haggle_bonus(self):
        """Test GameState has 0.0 haggle_bonus by default."""
        character = Character(
            name="Test Hero",
            strength=10, dexterity=10,
            intelligence=10, charisma=10,
        )
        location = Location(
            name="Town",
            description="A town",
            coordinates=(0, 0),
        )
        world = {"Town": location}
        game_state = GameState(character, world, "Town")

        assert game_state.haggle_bonus == 0.0

    def test_haggle_in_known_commands(self):
        """Test that 'haggle' is in KNOWN_COMMANDS."""
        from cli_rpg.game_state import KNOWN_COMMANDS
        assert "haggle" in KNOWN_COMMANDS
