"""Tests for brave player rewards (dread treasures).

Spec: Players at 75%+ dread who examine locations carefully (3rd look)
have a 30% chance to discover special "dread treasures" - powerful items
only accessible to those who brave the darkness.
"""
import pytest
from unittest.mock import patch

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType
from cli_rpg.game_state import GameState
from cli_rpg.brave_rewards import (
    check_for_dread_treasure,
    get_discovery_message,
    BRAVE_REWARD_DREAD_THRESHOLD,
    DREAD_TREASURE_CHANCE,
    DREAD_TREASURES,
)


def create_test_character():
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


def create_test_world():
    cave = Location(
        name="Dark Cave",
        description="A foreboding cave.",
        connections={},
        coordinates=(0, 0),
        category="cave",
        secrets="Ancient bones litter the floor."
    )
    return {"Dark Cave": cave}


class TestCheckForDreadTreasure:
    """Test treasure discovery conditions.

    Spec: Treasure requires 75%+ dread AND 3rd+ look AND 30% chance roll.
    """

    def test_no_treasure_below_threshold(self):
        """No treasure found below 75% dread."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=74, look_count=3, location_name="Cave")
        assert result is None

    def test_no_treasure_before_3rd_look(self):
        """No treasure found on 1st or 2nd look."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=80, look_count=2, location_name="Cave")
        assert result is None

    def test_treasure_at_high_dread_3rd_look(self):
        """Treasure found at 75%+ dread on 3rd+ look when chance succeeds."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=75, look_count=3, location_name="Cave")
        assert result is not None
        assert isinstance(result, Item)

    def test_respects_30_percent_chance(self):
        """Treasure not found when chance roll fails (> 0.30)."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.5):
            result = check_for_dread_treasure(dread_level=90, look_count=3, location_name="Cave")
        assert result is None

    def test_treasure_is_valid_item(self):
        """Discovered treasure is a valid Item with stats."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=80, look_count=5, location_name="Cave")
        assert result.name in [t["name"] for t in DREAD_TREASURES]


class TestDreadTreasureItems:
    """Test the treasure item definitions.

    Spec: All treasures should be valid items with thematic names,
    descriptions, and at least one stat bonus.
    """

    def test_all_treasures_have_names(self):
        """All treasures have valid names."""
        for treasure in DREAD_TREASURES:
            assert len(treasure["name"]) >= 2

    def test_all_treasures_have_descriptions(self):
        """All treasures have descriptions."""
        for treasure in DREAD_TREASURES:
            assert len(treasure["description"]) >= 1

    def test_treasures_have_stats(self):
        """Each treasure has at least one stat bonus."""
        for treasure in DREAD_TREASURES:
            has_stat = any([
                treasure.get("damage_bonus", 0) > 0,
                treasure.get("defense_bonus", 0) > 0,
                treasure.get("heal_amount", 0) > 0,
                treasure.get("light_duration", 0) > 0,
            ])
            assert has_stat, f"{treasure['name']} has no stat bonus"


class TestGameStateLookIntegration:
    """Test integration with GameState.look().

    Spec: When looking at 75%+ dread on 3rd look, check for dread treasure
    and add to inventory if found.
    """

    def test_look_at_high_dread_can_find_treasure(self):
        """Looking at 75%+ dread on 3rd look can find treasure."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Dark Cave")
        char.dread_meter.dread = 80

        # Look twice first
        game_state.look()
        game_state.look()

        # Force treasure find on 3rd look
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = game_state.look()

        assert "darkness reveals" in result.lower() or "discover" in result.lower()

    def test_look_at_low_dread_no_treasure(self):
        """Looking at low dread never finds treasure."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Dark Cave")
        char.dread_meter.dread = 50

        game_state.look()
        game_state.look()

        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = game_state.look()

        assert "discover" not in result.lower()


class TestDiscoveryMessage:
    """Test discovery message formatting.

    Spec: Discovery message should be thematic and include item name.
    """

    def test_message_contains_item_name(self):
        """Discovery message includes item name."""
        item = Item(
            name="Shadow Essence",
            description="A vial of darkness",
            item_type=ItemType.CONSUMABLE,
            heal_amount=50
        )
        message = get_discovery_message(item)
        assert "Shadow Essence" in message

    def test_message_is_thematic(self):
        """Discovery message has thematic content."""
        item = Item(name="Test Item", description="Test", item_type=ItemType.MISC)
        message = get_discovery_message(item)
        assert "darkness" in message.lower()
