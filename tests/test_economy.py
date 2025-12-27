"""Tests for the living economy system."""
import pytest

from cli_rpg.models.economy import EconomyState, LOCATION_BONUSES
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.world_event import WorldEvent
from cli_rpg.economy import get_economy_price_modifier, update_economy_from_events


class TestEconomyStateBasics:
    """Unit tests for EconomyState core functionality."""

    # Test 1: Spec - All modifiers start at 1.0
    def test_default_economy_state(self):
        """Default EconomyState has neutral modifiers."""
        state = EconomyState()
        assert state.item_supply == {}
        assert state.regional_disruption == 1.0
        assert state.last_update_hour == 0

    # Test 2: Spec - Buy adds 0.05 to item supply
    def test_record_buy_increases_supply_modifier(self):
        """record_buy increases item supply modifier by 0.05."""
        state = EconomyState()
        state.record_buy("Health Potion")
        assert state.item_supply["Health Potion"] == pytest.approx(1.05)

        state.record_buy("Health Potion")
        assert state.item_supply["Health Potion"] == pytest.approx(1.10)

    # Test 3: Spec - Supply modifier caps at 1.5
    def test_record_buy_caps_at_max(self):
        """Supply modifier caps at MAX_SUPPLY_MOD (1.5)."""
        state = EconomyState()
        # Simulate 15 buys (would be 1.75 without cap)
        for _ in range(15):
            state.record_buy("Rare Item")
        assert state.item_supply["Rare Item"] == pytest.approx(1.5)

    # Test 4: Spec - Sell reduces by 0.03
    def test_record_sell_decreases_supply_modifier(self):
        """record_sell decreases item supply modifier by 0.03."""
        state = EconomyState()
        state.record_sell("Common Sword")
        assert state.item_supply["Common Sword"] == pytest.approx(0.97)

        state.record_sell("Common Sword")
        assert state.item_supply["Common Sword"] == pytest.approx(0.94)

    # Test 5: Spec - Supply modifier floors at 0.7
    def test_record_sell_caps_at_min(self):
        """Supply modifier floors at MIN_SUPPLY_MOD (0.7)."""
        state = EconomyState()
        # Simulate 15 sells (would be 0.55 without floor)
        for _ in range(15):
            state.record_sell("Common Item")
        assert state.item_supply["Common Item"] == pytest.approx(0.7)

    # Test 6: Spec - Modifiers drift 5% toward 1.0 per 6 hours
    def test_time_recovery_drifts_toward_baseline(self):
        """Modifiers drift 5% toward 1.0 every 6 hours."""
        state = EconomyState()
        state.last_update_hour = 0

        # Start with elevated supply (expensive item)
        state.item_supply["Expensive"] = 1.2
        # Start with surplus (cheap item)
        state.item_supply["Cheap"] = 0.8

        # Advance 6 hours (1 interval)
        state.update_time(6)
        assert state.item_supply["Expensive"] == pytest.approx(1.15)  # 1.2 - 0.05
        assert state.item_supply["Cheap"] == pytest.approx(0.85)  # 0.8 + 0.05

        # Advance another 6 hours (12 total = 2 intervals from start)
        state.update_time(12)
        assert state.item_supply["Expensive"] == pytest.approx(1.10)
        assert state.item_supply["Cheap"] == pytest.approx(0.90)

    def test_time_recovery_removes_baseline_entries(self):
        """Items at baseline (1.0) are removed from item_supply dict."""
        state = EconomyState()
        state.last_update_hour = 0
        state.item_supply["AlmostNormal"] = 1.02  # Will hit 1.0 after 1 recovery

        # Advance 6 hours
        state.update_time(6)
        # Should be removed (was 1.02, clamped to 1.0, then deleted)
        assert "AlmostNormal" not in state.item_supply

    # Test 7: Spec - get_modifier combines supply, location, and disruption
    def test_get_economy_modifier_combines_factors(self):
        """get_modifier combines supply, location, and disruption."""
        state = EconomyState()
        state.item_supply["Healing Salve"] = 1.2  # 20% scarcity
        state.regional_disruption = 1.1  # 10% disruption

        # At a temple, consumables are 15% cheaper (0.85)
        # Combined: 1.2 * 0.85 * 1.1 = 1.122
        modifier = state.get_modifier("Healing Salve", "consumable", "temple")
        assert modifier == pytest.approx(1.122)

    def test_get_modifier_no_location_bonus(self):
        """get_modifier works without location bonus."""
        state = EconomyState()
        state.item_supply["Sword"] = 1.1
        state.regional_disruption = 1.0

        # No location category - just supply modifier
        modifier = state.get_modifier("Sword", "weapon", None)
        assert modifier == pytest.approx(1.1)

    # Test 8: Spec - to_dict/from_dict preserves state
    def test_serialization_roundtrip(self):
        """EconomyState serializes and deserializes correctly."""
        state = EconomyState()
        state.item_supply = {"Potion": 1.15, "Sword": 0.85}
        state.regional_disruption = 1.2
        state.last_update_hour = 14

        data = state.to_dict()
        restored = EconomyState.from_dict(data)

        assert restored.item_supply == state.item_supply
        assert restored.regional_disruption == state.regional_disruption
        assert restored.last_update_hour == state.last_update_hour

    def test_from_dict_handles_none(self):
        """from_dict returns default state when given None."""
        state = EconomyState.from_dict(None)
        assert state.item_supply == {}
        assert state.regional_disruption == 1.0
        assert state.last_update_hour == 0


class TestLocationBonuses:
    """Unit tests for location-based price bonuses."""

    # Test 9: Spec - Consumables 15% cheaper at temples
    def test_temple_consumable_discount(self):
        """Consumables are 15% cheaper at temples."""
        state = EconomyState()
        modifier = state.get_modifier("Health Potion", "consumable", "temple")
        assert modifier == pytest.approx(0.85)

    # Test 10: Spec - Weapons 10% cheaper at towns
    def test_town_weapon_discount(self):
        """Weapons are 10% cheaper at towns."""
        state = EconomyState()
        modifier = state.get_modifier("Iron Sword", "weapon", "town")
        assert modifier == pytest.approx(0.90)

    def test_village_weapon_discount(self):
        """Weapons are 10% cheaper at villages (same as towns)."""
        state = EconomyState()
        modifier = state.get_modifier("Iron Sword", "weapon", "village")
        assert modifier == pytest.approx(0.90)

    # Test 11: Spec - Resources 20% cheaper in forests
    def test_forest_resource_discount(self):
        """Resources are 20% cheaper in forests."""
        state = EconomyState()
        modifier = state.get_modifier("Wood Bundle", "resource", "forest")
        assert modifier == pytest.approx(0.80)

    def test_no_discount_wrong_item_type(self):
        """No discount when item type doesn't match location."""
        state = EconomyState()
        # Weapons at temple (temple only discounts consumables)
        modifier = state.get_modifier("Iron Sword", "weapon", "temple")
        assert modifier == pytest.approx(1.0)


class TestWorldEventIntegration:
    """Unit tests for world event effects on economy."""

    def _create_event(self, event_type: str, is_active: bool = True) -> WorldEvent:
        """Helper to create test events."""
        return WorldEvent(
            event_id=f"test_{event_type}_001",
            name=f"Test {event_type.title()}",
            description=f"A test {event_type} event",
            event_type=event_type,
            affected_locations=["Town Square"],
            start_hour=0,
            duration_hours=12,
            is_active=is_active,
        )

    # Test 12: Spec - Active invasion sets disruption = 1.2
    def test_invasion_increases_prices(self):
        """Active invasion sets regional_disruption to 1.2."""
        state = EconomyState()
        events = [self._create_event("invasion")]

        update_economy_from_events(state, events)
        assert state.regional_disruption == pytest.approx(1.2)

    # Test 13: Spec - Active caravan sets disruption = 0.9
    def test_caravan_decreases_prices(self):
        """Active caravan sets regional_disruption to 0.9."""
        state = EconomyState()
        events = [self._create_event("caravan")]

        update_economy_from_events(state, events)
        assert state.regional_disruption == pytest.approx(0.9)

    # Test 14: Spec - Disruption returns to 1.0 after event ends
    def test_disruption_clears_when_event_ends(self):
        """Disruption returns to 1.0 when events are inactive."""
        state = EconomyState()

        # First, activate an invasion
        events = [self._create_event("invasion")]
        update_economy_from_events(state, events)
        assert state.regional_disruption == pytest.approx(1.2)

        # Now mark event as inactive
        events[0].is_active = False
        update_economy_from_events(state, events)
        assert state.regional_disruption == pytest.approx(1.0)

    def test_invasion_takes_priority_over_caravan(self):
        """When both invasion and caravan active, invasion takes priority."""
        state = EconomyState()
        events = [
            self._create_event("caravan"),
            self._create_event("invasion"),
        ]

        update_economy_from_events(state, events)
        # Invasion wins - prices stay high, not low
        assert state.regional_disruption == pytest.approx(1.2)

    def test_inactive_events_ignored(self):
        """Inactive events don't affect economy."""
        state = EconomyState()
        events = [self._create_event("invasion", is_active=False)]

        update_economy_from_events(state, events)
        assert state.regional_disruption == pytest.approx(1.0)


class TestEconomyPriceModifier:
    """Tests for the get_economy_price_modifier helper function."""

    def test_basic_modifier_calculation(self):
        """get_economy_price_modifier correctly calculates modifier."""
        state = EconomyState()
        state.item_supply["Test Potion"] = 1.1

        item = Item(
            name="Test Potion",
            description="A test potion",
            item_type=ItemType.CONSUMABLE,
        )

        modifier = get_economy_price_modifier(item, state, None)
        assert modifier == pytest.approx(1.1)

    def test_modifier_with_location(self):
        """get_economy_price_modifier includes location bonus."""
        state = EconomyState()

        item = Item(
            name="Healing Herb",
            description="A medicinal herb",
            item_type=ItemType.CONSUMABLE,
        )

        modifier = get_economy_price_modifier(item, state, "temple")
        assert modifier == pytest.approx(0.85)


class TestTimeRecoveryEdgeCases:
    """Edge case tests for time-based recovery."""

    def test_midnight_wrap(self):
        """Time recovery handles midnight wrap correctly."""
        state = EconomyState()
        state.last_update_hour = 22
        state.item_supply["Item"] = 1.2

        # Advance to 4am next day (6 hours later)
        state.update_time(4)
        assert state.item_supply["Item"] == pytest.approx(1.15)

    def test_multiple_recovery_intervals(self):
        """Multiple recovery intervals are applied correctly."""
        state = EconomyState()
        state.last_update_hour = 0
        state.item_supply["Item"] = 1.3

        # Advance 18 hours (3 intervals)
        state.update_time(18)
        # 1.3 -> 1.25 -> 1.20 -> 1.15
        assert state.item_supply["Item"] == pytest.approx(1.15)

    def test_recovery_doesnt_overshoot_baseline(self):
        """Recovery doesn't overshoot 1.0 baseline."""
        state = EconomyState()
        state.last_update_hour = 0
        state.item_supply["Item"] = 1.02

        # Advance 6 hours - should clamp to 1.0, not 0.97
        state.update_time(6)
        # Item at exactly 1.0 is removed from dict
        assert "Item" not in state.item_supply

    def test_less_than_interval_no_recovery(self):
        """No recovery if less than RECOVERY_INTERVAL hours passed."""
        state = EconomyState()
        state.last_update_hour = 0
        state.item_supply["Item"] = 1.2

        # Advance only 5 hours (less than 6)
        state.update_time(5)
        assert state.item_supply["Item"] == pytest.approx(1.2)
        assert state.last_update_hour == 0  # Not updated


class TestBuySellIntegration:
    """Integration tests for economy modifiers in buy/sell commands.

    Tests 15-18 from spec: Verify economy modifiers are applied in actual
    buy/sell transactions and shop displays.
    """

    def _make_game_state(self, charisma: int = 10, location_category: str = None):
        """Create a minimal game state for testing buy/sell.

        Args:
            charisma: Character's CHA stat (10 = no price modifier)
            location_category: Optional category for location (e.g., "temple", "forest")
        """
        from unittest.mock import patch
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.models.npc import NPC
        from cli_rpg.models.shop import Shop, ShopItem
        from cli_rpg.game_state import GameState

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=charisma,
        )
        character.add_gold(1000)

        # Create shop with consumable and weapon items
        shop = Shop(
            name="Test Shop",
            inventory=[
                ShopItem(
                    item=Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=20),
                    buy_price=100,
                ),
                ShopItem(
                    item=Item(name="Iron Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5),
                    buy_price=200,
                ),
            ],
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
            category=location_category,
        )

        world = {"Town Square": location}
        game_state = GameState(character, world, "Town Square")
        game_state.current_shop = shop
        game_state.current_npc = npc
        return game_state

    # Test 15: Spec - Final price includes economy factor on buy
    def test_buy_applies_economy_modifier(self):
        """Buy price includes economy supply/demand modifier.

        Spec: test 15 - buy command applies economy modifier
        Base price 100, with item_supply = 1.2 (scarce): final = 120
        """
        from unittest.mock import patch
        from cli_rpg.main import handle_exploration_command

        game_state = self._make_game_state(charisma=10)  # CHA 10 = no modifier
        # Set supply modifier for Health Potion (20% scarcity = 20% price increase)
        game_state.economy_state.item_supply["Health Potion"] = 1.2

        initial_gold = game_state.current_character.gold

        with patch("cli_rpg.main.autosave"):
            success, message = handle_exploration_command(game_state, "buy", ["Health", "Potion"])

        # Base price 100 * economy_mod 1.2 = 120
        expected_price = 120
        assert game_state.current_character.gold == initial_gold - expected_price
        assert "120" in message or "bought" in message.lower()

    # Test 16: Spec - Sell price includes economy factor
    def test_sell_applies_economy_modifier(self):
        """Sell price includes economy supply/demand modifier.

        Spec: test 16 - sell command applies economy modifier
        """
        from unittest.mock import patch
        from cli_rpg.main import handle_exploration_command

        game_state = self._make_game_state(charisma=10)
        # Set surplus for the item (cheaper = lower sell price)
        game_state.economy_state.item_supply["Old Sword"] = 0.8  # 20% surplus

        # Add an item to sell
        sword = Item(name="Old Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5)
        game_state.current_character.inventory.add_item(sword)
        initial_gold = game_state.current_character.gold

        with patch("cli_rpg.main.autosave"):
            success, message = handle_exploration_command(game_state, "sell", ["Old", "Sword"])

        # Base sell price: 10 + (5 + 0 + 0) * 2 = 20
        # With economy modifier 0.8: 20 * 0.8 = 16
        base_price = 10 + (5 + 0 + 0) * 2  # 20
        expected_price = int(base_price * 0.8)  # 16
        assert game_state.current_character.gold == initial_gold + expected_price

    # Test 17: Spec - Shop command shows economy-adjusted prices
    def test_shop_display_shows_economy_adjusted_prices(self):
        """Shop command displays prices with economy modifiers applied.

        Spec: test 17 - shop display shows economy-adjusted prices
        """
        from cli_rpg.main import handle_exploration_command

        game_state = self._make_game_state(charisma=10)
        # Set supply modifier for Health Potion
        game_state.economy_state.item_supply["Health Potion"] = 1.2  # 20% increase

        success, message = handle_exploration_command(game_state, "shop", [])

        # Health Potion base 100 * 1.2 = 120
        assert "120" in message
        # Iron Sword base 200 with no modifier should show 200
        assert "200" in message

    # Test 18: Spec - Economy + faction modifiers stack correctly
    def test_economy_modifier_stacks_with_faction(self):
        """Economy and faction modifiers stack multiplicatively.

        Spec: test 18 - economy + faction modifiers stack correctly
        Price = base * cha * economy * faction
        """
        from unittest.mock import patch
        from cli_rpg.main import handle_exploration_command
        from cli_rpg.models.faction import Faction

        game_state = self._make_game_state(charisma=10)  # CHA 10 = no modifier
        # Set economy modifier
        game_state.economy_state.item_supply["Health Potion"] = 1.1  # 10% increase

        # Set faction modifier (Merchant Guild with Friendly reputation = 10% discount)
        # Friendly level = 60-79 reputation points
        merchant_guild = Faction(
            name="Merchant Guild",  # Must match exact name used in faction_shop.py
            description="A guild of merchants",
            reputation=75  # Friendly = -10% on buy
        )
        game_state.factions = [merchant_guild]

        initial_gold = game_state.current_character.gold

        with patch("cli_rpg.main.autosave"):
            success, message = handle_exploration_command(game_state, "buy", ["Health", "Potion"])

        # Base 100 * cha(1.0) * economy(1.1) * faction(0.9) = 99
        # (int truncation: 100 * 1.1 = 110, then 110 * 0.9 = 99)
        expected_price = int(int(100 * 1.1) * 0.9)  # 99
        assert game_state.current_character.gold == initial_gold - expected_price

    def test_buy_records_transaction_in_economy(self):
        """Buying an item increases its supply modifier (makes it scarcer).

        Verifies record_buy is called after successful purchase.
        """
        from unittest.mock import patch
        from cli_rpg.main import handle_exploration_command

        game_state = self._make_game_state(charisma=10)
        assert "Health Potion" not in game_state.economy_state.item_supply

        with patch("cli_rpg.main.autosave"):
            success, message = handle_exploration_command(game_state, "buy", ["Health", "Potion"])

        # After buying, item_supply should be 1.05 (baseline 1.0 + 0.05)
        assert game_state.economy_state.item_supply["Health Potion"] == pytest.approx(1.05)

    def test_sell_records_transaction_in_economy(self):
        """Selling an item decreases its supply modifier (creates surplus).

        Verifies record_sell is called after successful sale.
        """
        from unittest.mock import patch
        from cli_rpg.main import handle_exploration_command

        game_state = self._make_game_state(charisma=10)
        # Add an item to sell
        sword = Item(name="Old Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5)
        game_state.current_character.inventory.add_item(sword)

        assert "Old Sword" not in game_state.economy_state.item_supply

        with patch("cli_rpg.main.autosave"):
            success, message = handle_exploration_command(game_state, "sell", ["Old", "Sword"])

        # After selling, item_supply should be 0.97 (baseline 1.0 - 0.03)
        assert game_state.economy_state.item_supply["Old Sword"] == pytest.approx(0.97)

    def test_location_category_affects_price(self):
        """Location category provides discounts on matching item types.

        Temples give 15% discount on consumables.
        """
        from cli_rpg.main import handle_exploration_command

        game_state = self._make_game_state(charisma=10, location_category="temple")

        success, message = handle_exploration_command(game_state, "shop", [])

        # Health Potion (consumable) at temple: 100 * 0.85 = 85
        assert "85" in message
        # Iron Sword (weapon) at temple: no discount = 200
        assert "200" in message
