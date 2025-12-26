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


# =============================================================================
# Tests for crafting recipes - existence
# =============================================================================


def test_torch_recipe_exists():
    """Spec: torch recipe should exist with correct ingredients (1 Wood + 1 Fiber)."""
    from cli_rpg.crafting import CRAFTING_RECIPES

    assert "torch" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["torch"]
    assert recipe["ingredients"] == {"Wood": 1, "Fiber": 1}
    assert recipe["output"]["name"] == "Torch"


def test_iron_sword_recipe_exists():
    """Spec: iron sword recipe should exist with correct ingredients (2 Iron Ore + 1 Wood)."""
    from cli_rpg.crafting import CRAFTING_RECIPES

    assert "iron sword" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["iron sword"]
    assert recipe["ingredients"] == {"Iron Ore": 2, "Wood": 1}
    assert recipe["output"]["name"] == "Iron Sword"


# =============================================================================
# Tests for crafting - success cases
# =============================================================================


def test_craft_torch_consumes_ingredients():
    """Spec: crafting torch should consume 1 Wood and 1 Fiber from inventory."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    inv = game_state.current_character.inventory

    # Add ingredients
    wood = Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE)
    fiber = Item(name="Fiber", description="Fiber for crafting", item_type=ItemType.RESOURCE)
    inv.add_item(wood)
    inv.add_item(fiber)

    success, msg = execute_craft(game_state, "torch")

    assert success is True
    assert "Crafted" in msg or "crafted" in msg

    # Verify ingredients consumed
    assert inv.find_item_by_name("Wood") is None
    assert inv.find_item_by_name("Fiber") is None


def test_craft_adds_item_to_inventory():
    """Spec: crafting should add the output item to inventory."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    inv = game_state.current_character.inventory

    # Add ingredients for torch
    wood = Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE)
    fiber = Item(name="Fiber", description="Fiber for crafting", item_type=ItemType.RESOURCE)
    inv.add_item(wood)
    inv.add_item(fiber)

    initial_count = len(inv.items)
    execute_craft(game_state, "torch")

    # 2 ingredients removed, 1 item added = net -1
    assert len(inv.items) == initial_count - 1

    # Verify the torch was added
    torch = inv.find_item_by_name("Torch")
    assert torch is not None
    assert torch.item_type == ItemType.CONSUMABLE


def test_craft_torch_has_light_duration():
    """Spec: crafted torch should have light_duration of 10."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    inv = game_state.current_character.inventory

    # Add ingredients
    wood = Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE)
    fiber = Item(name="Fiber", description="Fiber for crafting", item_type=ItemType.RESOURCE)
    inv.add_item(wood)
    inv.add_item(fiber)

    execute_craft(game_state, "torch")

    torch = inv.find_item_by_name("Torch")
    assert torch is not None
    assert torch.light_duration == 10


# =============================================================================
# Tests for crafting - failure cases
# =============================================================================


def test_craft_fails_missing_ingredients():
    """Spec: crafting should fail with error when missing all ingredients."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()

    success, msg = execute_craft(game_state, "torch")

    assert success is False
    assert "Missing" in msg or "missing" in msg


def test_craft_fails_partial_ingredients():
    """Spec: crafting should fail when only some ingredients are present."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    inv = game_state.current_character.inventory

    # Only add wood (missing fiber)
    wood = Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE)
    inv.add_item(wood)

    success, msg = execute_craft(game_state, "torch")

    assert success is False
    assert "Missing" in msg or "missing" in msg
    assert "Fiber" in msg  # Should mention what's missing


def test_craft_fails_unknown_recipe():
    """Spec: crafting should fail with error for invalid recipe name."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()

    success, msg = execute_craft(game_state, "magic wand")

    assert success is False
    assert "Unknown" in msg or "unknown" in msg


def test_craft_succeeds_when_ingredients_free_space():
    """Spec: crafting should succeed when removing ingredients frees enough space.

    For a 2-ingredient recipe like torch, even a full inventory works because
    we remove 2 items and add 1.
    """
    from cli_rpg.crafting import execute_craft

    character = make_character()
    inv = character.inventory

    # Add ingredients first
    wood = Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE)
    fiber = Item(name="Fiber", description="Fiber for crafting", item_type=ItemType.RESOURCE)
    inv.add_item(wood)
    inv.add_item(fiber)

    # Fill remaining capacity with junk (inventory now full)
    remaining = inv.capacity - 2
    for i in range(remaining):
        inv.add_item(
            Item(name=f"Junk {i}", description="Filler item", item_type=ItemType.MISC)
        )

    location = make_location()
    game_state = make_game_state(character=character, location=location)

    # Torch: 2 ingredients -> 1 item, so we free 1 slot
    success, msg = execute_craft(game_state, "torch")

    assert success is True  # Should succeed because net space freed
    assert "Crafted" in msg or "crafted" in msg


# =============================================================================
# Tests for recipe list
# =============================================================================


def test_recipes_list_shows_all_recipes():
    """Spec: get_recipes_list should include all defined recipes."""
    from cli_rpg.crafting import get_recipes_list, CRAFTING_RECIPES

    output = get_recipes_list()

    # Check header is present
    assert "Available" in output or "Recipes" in output

    # Check each recipe appears in output
    for key, recipe in CRAFTING_RECIPES.items():
        assert recipe["name"] in output
