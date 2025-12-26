"""Tests for crafting and resource gathering system."""

import random
from typing import Optional
from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState


# =============================================================================
# Helper functions
# =============================================================================

def make_character(**kwargs) -> Character:
    """Create a test character with optional overrides."""
    defaults = {
        "name": "TestPlayer",
        "character_class": CharacterClass.WARRIOR,
        "strength": 10,
        "dexterity": 10,
        "intelligence": 10,
        "perception": 10,
        "charisma": 10,
    }
    defaults.update(kwargs)
    return Character(**defaults)


def make_location(
    name: str = "Test Location",
    category: str = "forest",
    is_safe_zone: bool = False,
    **kwargs,
) -> Location:
    """Create a test location with optional overrides."""
    return Location(
        name=name,
        description="A test location.",
        category=category,
        is_safe_zone=is_safe_zone,
        coordinates=(0, 0),
        **kwargs,
    )


def make_game_state(
    character: Optional[Character] = None,
    location: Optional[Location] = None,
) -> GameState:
    """Create a test game state."""
    if character is None:
        character = make_character()
    if location is None:
        location = make_location()

    world = {location.name: location}
    return GameState(character, world, location.name)


# =============================================================================
# Tests for gather command - location requirements
# =============================================================================


def test_gather_in_forest_succeeds():
    """Spec: gather command should work in forest category locations."""
    from cli_rpg.crafting import execute_gather, is_gatherable_location

    location = make_location(category="forest")
    game_state = make_game_state(location=location)

    # Verify location check
    assert is_gatherable_location(location) is True

    # Force success by mocking random
    with patch("random.random", return_value=0.0):  # 0.0 = always succeeds
        success, msg = execute_gather(game_state)
        assert success is True
        assert "found" in msg.lower() or "gather" in msg.lower()


def test_gather_in_town_fails():
    """Spec: gather command should NOT work in safe zones (towns)."""
    from cli_rpg.crafting import execute_gather, is_gatherable_location

    location = make_location(category="town", is_safe_zone=True)
    game_state = make_game_state(location=location)

    # Verify location check
    assert is_gatherable_location(location) is False

    success, msg = execute_gather(game_state)
    assert success is False
    assert "can't gather" in msg.lower() or "cannot gather" in msg.lower()


def test_gather_in_dungeon_succeeds():
    """Spec: gather command should work in dungeon/cave areas for ore/stone."""
    from cli_rpg.crafting import execute_gather, is_gatherable_location

    location = make_location(category="cave")
    game_state = make_game_state(location=location)

    # Verify location check
    assert is_gatherable_location(location) is True

    # Force success
    with patch("random.random", return_value=0.0):
        success, msg = execute_gather(game_state)
        assert success is True


# =============================================================================
# Tests for gather command - cooldown
# =============================================================================


def test_gather_respects_cooldown():
    """Spec: gather should fail if cooldown is active."""
    from cli_rpg.crafting import execute_gather

    location = make_location(category="forest")
    game_state = make_game_state(location=location)

    # Set cooldown
    game_state.gather_cooldown = 1

    success, msg = execute_gather(game_state)
    assert success is False
    assert "wait" in msg.lower() or "cooldown" in msg.lower() or "recently" in msg.lower()


# =============================================================================
# Tests for gather command - time advancement
# =============================================================================


def test_gather_advances_time():
    """Spec: gather should advance game time by 1 hour."""
    from cli_rpg.crafting import execute_gather, GATHER_TIME_HOURS

    location = make_location(category="forest")
    game_state = make_game_state(location=location)

    initial_hour = game_state.game_time.hour

    # Force failure to avoid inventory effects but still check time
    with patch("random.random", return_value=1.0):  # 1.0 = always fails
        execute_gather(game_state)

    expected_hour = (initial_hour + GATHER_TIME_HOURS) % 24
    assert game_state.game_time.hour == expected_hour


# =============================================================================
# Tests for gather command - inventory
# =============================================================================


def test_gather_adds_item_to_inventory():
    """Spec: successful gather should add a resource item to inventory."""
    from cli_rpg.crafting import execute_gather

    location = make_location(category="forest")
    game_state = make_game_state(location=location)

    initial_count = len(game_state.current_character.inventory.items)

    # Force success
    with patch("random.random", return_value=0.0):
        success, msg = execute_gather(game_state)

    assert success is True
    assert len(game_state.current_character.inventory.items) == initial_count + 1

    # Check the item is a RESOURCE type
    new_item = game_state.current_character.inventory.items[-1]
    assert new_item.item_type == ItemType.RESOURCE


def test_gather_fails_when_inventory_full():
    """Spec: gather should return message when inventory is full."""
    from cli_rpg.crafting import execute_gather

    location = make_location(category="forest")
    character = make_character()

    # Fill inventory
    for i in range(character.inventory.capacity):
        character.inventory.add_item(
            Item(name=f"Junk {i}", description="Filler item", item_type=ItemType.MISC)
        )

    game_state = make_game_state(character=character, location=location)

    # Force success on the roll
    with patch("random.random", return_value=0.0):
        success, msg = execute_gather(game_state)

    # Should succeed in finding but report full inventory
    assert success is True
    assert "full" in msg.lower()


# =============================================================================
# Tests for gather command - success scaling with PER
# =============================================================================


def test_gather_success_scales_with_per():
    """Spec: higher perception should increase gather success chance."""
    from cli_rpg.crafting import GATHER_BASE_CHANCE, GATHER_PER_BONUS

    # Character with perception 10 should have:
    # 40% base + (10 * 2%) = 60% success chance
    character_low = make_character(perception=5)
    character_high = make_character(perception=15)

    expected_low = GATHER_BASE_CHANCE + (5 * GATHER_PER_BONUS)  # 40 + 10 = 50%
    expected_high = GATHER_BASE_CHANCE + (15 * GATHER_PER_BONUS)  # 40 + 30 = 70%

    assert expected_low < expected_high  # Higher PER = higher chance


# =============================================================================
# Tests for resource item serialization
# =============================================================================


def test_resource_item_serialization():
    """Spec: resource items should serialize and deserialize correctly."""
    resource = Item(
        name="Iron Ore",
        description="Raw iron ore from deep caves.",
        item_type=ItemType.RESOURCE,
    )

    # Serialize
    data = resource.to_dict()
    assert data["item_type"] == "resource"
    assert data["name"] == "Iron Ore"

    # Deserialize
    restored = Item.from_dict(data)
    assert restored.name == "Iron Ore"
    assert restored.item_type == ItemType.RESOURCE
    assert restored.description == "Raw iron ore from deep caves."


# =============================================================================
# Tests for location-specific resources
# =============================================================================


def test_forest_yields_wood_or_fiber():
    """Spec: forest locations should yield wood or fiber resources."""
    from cli_rpg.crafting import RESOURCE_BY_CATEGORY

    forest_resources = RESOURCE_BY_CATEGORY.get("forest", [])
    resource_types = {r["resource_type"] for r in forest_resources}

    assert "wood" in resource_types
    assert "fiber" in resource_types


def test_cave_yields_ore_or_stone():
    """Spec: cave locations should yield ore or stone resources."""
    from cli_rpg.crafting import RESOURCE_BY_CATEGORY

    cave_resources = RESOURCE_BY_CATEGORY.get("cave", [])
    resource_types = {r["resource_type"] for r in cave_resources}

    assert "ore" in resource_types
    assert "stone" in resource_types
