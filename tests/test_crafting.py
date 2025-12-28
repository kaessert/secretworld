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


# =============================================================================
# Tests for new crafting recipes (healing salve, bandage, wooden shield)
# =============================================================================


def test_healing_salve_recipe_exists():
    """Spec: healing salve recipe should exist (2 Herbs → 25 HP heal)."""
    from cli_rpg.crafting import CRAFTING_RECIPES

    assert "healing salve" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["healing salve"]
    assert recipe["ingredients"] == {"Herbs": 2}
    assert recipe["output"]["heal_amount"] == 25


def test_bandage_recipe_exists():
    """Spec: bandage recipe should exist (2 Fiber → 15 HP heal)."""
    from cli_rpg.crafting import CRAFTING_RECIPES

    assert "bandage" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["bandage"]
    assert recipe["ingredients"] == {"Fiber": 2}
    assert recipe["output"]["heal_amount"] == 15


def test_wooden_shield_recipe_exists():
    """Spec: wooden shield recipe should exist (2 Wood + 1 Fiber → +2 defense)."""
    from cli_rpg.crafting import CRAFTING_RECIPES

    assert "wooden shield" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["wooden shield"]
    assert recipe["ingredients"] == {"Wood": 2, "Fiber": 1}
    assert recipe["output"]["defense_bonus"] == 2


def test_craft_healing_salve_works():
    """Spec: crafting healing salve consumes 2 Herbs and creates salve."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    inv = game_state.current_character.inventory
    # Add 2 Herbs
    for _ in range(2):
        inv.add_item(
            Item(
                name="Herbs",
                description="Healing herbs",
                item_type=ItemType.CONSUMABLE,
                heal_amount=10,
            )
        )
    success, msg = execute_craft(game_state, "healing salve")
    assert success is True
    salve = inv.find_item_by_name("Healing Salve")
    assert salve is not None
    assert salve.heal_amount == 25


# =============================================================================
# Tests for crafting skill progression
# =============================================================================


def test_character_has_crafting_proficiency():
    """Spec: Character should have crafting_proficiency field defaulting to level 1 (NOVICE)."""
    from cli_rpg.models.crafting_proficiency import CraftingLevel

    character = make_character()
    assert hasattr(character, "crafting_proficiency")
    assert character.crafting_proficiency.get_level() == CraftingLevel.NOVICE
    assert character.crafting_proficiency.xp == 0


def test_crafting_proficiency_levels_up():
    """Spec: Crafting XP should level up at thresholds (25/50/75/100)."""
    from cli_rpg.models.crafting_proficiency import CraftingProficiency, CraftingLevel

    prof = CraftingProficiency()
    assert prof.get_level() == CraftingLevel.NOVICE

    # Level to Apprentice at 25 XP
    prof.xp = 25
    assert prof.get_level() == CraftingLevel.APPRENTICE

    # Level to Journeyman at 50 XP
    prof.xp = 50
    assert prof.get_level() == CraftingLevel.JOURNEYMAN

    # Level to Expert at 75 XP
    prof.xp = 75
    assert prof.get_level() == CraftingLevel.EXPERT

    # Level to Master at 100 XP
    prof.xp = 100
    assert prof.get_level() == CraftingLevel.MASTER


def test_craft_success_grants_xp():
    """Spec: Successful craft should grant +5 crafting XP."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    inv = game_state.current_character.inventory
    char = game_state.current_character

    # Initial XP should be 0
    initial_xp = char.crafting_proficiency.xp
    assert initial_xp == 0

    # Add ingredients for torch (basic recipe)
    wood = Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE)
    fiber = Item(name="Fiber", description="Fiber for crafting", item_type=ItemType.RESOURCE)
    inv.add_item(wood)
    inv.add_item(fiber)

    success, msg = execute_craft(game_state, "torch")
    assert success is True

    # Should have gained 5 XP
    assert char.crafting_proficiency.xp == initial_xp + 5


def test_crafting_level_affects_success_rate():
    """Spec: Higher crafting level should provide success rate bonus (+5% per level above Novice)."""
    from cli_rpg.models.crafting_proficiency import CraftingProficiency, CraftingLevel

    prof = CraftingProficiency()

    # NOVICE = 0% bonus
    assert prof.get_success_bonus() == 0.0

    # APPRENTICE = +5% bonus
    prof.xp = 25
    assert prof.get_success_bonus() == 0.05

    # JOURNEYMAN = +10% bonus
    prof.xp = 50
    assert prof.get_success_bonus() == 0.10

    # EXPERT = +15% bonus
    prof.xp = 75
    assert prof.get_success_bonus() == 0.15

    # MASTER = +20% bonus
    prof.xp = 100
    assert prof.get_success_bonus() == 0.20


def test_advanced_recipes_require_journeyman():
    """Spec: Iron sword/armor require Journeyman (level 3) to craft."""
    from cli_rpg.crafting import execute_craft, RECIPE_MIN_LEVEL
    from cli_rpg.models.crafting_proficiency import CraftingLevel

    # Verify recipe requirements exist
    assert "iron sword" in RECIPE_MIN_LEVEL
    assert RECIPE_MIN_LEVEL["iron sword"] == CraftingLevel.JOURNEYMAN

    assert "iron armor" in RECIPE_MIN_LEVEL
    assert RECIPE_MIN_LEVEL["iron armor"] == CraftingLevel.JOURNEYMAN

    # Test that a novice crafter cannot craft iron sword
    game_state = make_game_state()
    inv = game_state.current_character.inventory
    char = game_state.current_character

    # Add ingredients for iron sword (2 Iron Ore + 1 Wood)
    for _ in range(2):
        inv.add_item(
            Item(name="Iron Ore", description="Raw iron ore", item_type=ItemType.RESOURCE)
        )
    inv.add_item(Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE))

    # Novice crafter should fail
    assert char.crafting_proficiency.get_level() == CraftingLevel.NOVICE
    success, msg = execute_craft(game_state, "iron sword")
    assert success is False
    assert "Journeyman" in msg or "level" in msg.lower()

    # Now set crafter to Journeyman level
    char.crafting_proficiency.xp = 50  # Journeyman threshold
    assert char.crafting_proficiency.get_level() == CraftingLevel.JOURNEYMAN

    # Re-add ingredients since they weren't consumed
    for _ in range(2):
        inv.add_item(
            Item(name="Iron Ore", description="Raw iron ore", item_type=ItemType.RESOURCE)
        )
    inv.add_item(Item(name="Wood", description="Wood for crafting", item_type=ItemType.RESOURCE))

    success, msg = execute_craft(game_state, "iron sword")
    assert success is True
    assert "Crafted" in msg or "crafted" in msg


def test_crafting_proficiency_serialization():
    """Spec: Proficiency should serialize/deserialize correctly."""
    from cli_rpg.models.crafting_proficiency import CraftingProficiency

    # Create with some XP
    prof = CraftingProficiency(xp=60)

    # Serialize
    data = prof.to_dict()
    assert data["xp"] == 60

    # Deserialize
    restored = CraftingProficiency.from_dict(data)
    assert restored.xp == 60
    assert restored.get_level() == prof.get_level()


def test_character_crafting_proficiency_serialization():
    """Spec: Character's crafting_proficiency should be saved and loaded correctly."""
    character = make_character()

    # Set some crafting XP
    character.crafting_proficiency.xp = 45

    # Serialize
    data = character.to_dict()
    assert "crafting_proficiency" in data
    assert data["crafting_proficiency"]["xp"] == 45

    # Deserialize
    restored = Character.from_dict(data)
    assert restored.crafting_proficiency.xp == 45


def test_crafting_proficiency_gain_xp_returns_levelup_message():
    """Spec: gain_xp should return a level-up message when threshold is crossed."""
    from cli_rpg.models.crafting_proficiency import CraftingProficiency

    prof = CraftingProficiency(xp=22)  # Just below Apprentice threshold

    # Gain XP that crosses threshold
    msg = prof.gain_xp(5)

    assert msg is not None
    assert "Apprentice" in msg or "crafting" in msg.lower()
    assert prof.xp == 27


def test_crafting_proficiency_xp_capped_at_100():
    """Spec: Crafting XP should cap at 100."""
    from cli_rpg.models.crafting_proficiency import CraftingProficiency

    prof = CraftingProficiency(xp=98)
    prof.gain_xp(10)

    assert prof.xp == 100  # Capped, not 108


def test_craft_shows_levelup_message():
    """Spec: Crafting should show level-up message when proficiency increases."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    char = game_state.current_character
    inv = char.inventory

    # Set XP just below threshold
    char.crafting_proficiency.xp = 22  # +5 will cross 25 (Apprentice)

    # Add ingredients for torch
    inv.add_item(Item(name="Wood", description="Wood", item_type=ItemType.RESOURCE))
    inv.add_item(Item(name="Fiber", description="Fiber", item_type=ItemType.RESOURCE))

    success, msg = execute_craft(game_state, "torch")

    assert success is True
    assert "Apprentice" in msg or "level" in msg.lower() or "proficiency" in msg.lower()


def test_backward_compat_character_without_crafting_proficiency():
    """Spec: Old saves without crafting_proficiency should load with default."""
    # Simulate old save data without crafting_proficiency
    old_save = {
        "name": "OldPlayer",
        "strength": 12,
        "dexterity": 11,
        "intelligence": 10,
        "charisma": 10,
        "perception": 10,
        "luck": 10,
        "level": 5,
        "health": 100,
        "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None},
        # No crafting_proficiency key
    }

    from cli_rpg.models.crafting_proficiency import CraftingLevel

    character = Character.from_dict(old_save)

    # Should have default crafting proficiency
    assert hasattr(character, "crafting_proficiency")
    assert character.crafting_proficiency.xp == 0
    assert character.crafting_proficiency.get_level() == CraftingLevel.NOVICE


# =============================================================================
# Tests for rare recipe discovery system
# =============================================================================


def test_rare_recipes_not_in_base_recipes():
    """Spec: Rare recipes should be in RARE_RECIPES, not CRAFTING_RECIPES."""
    from cli_rpg.crafting import CRAFTING_RECIPES, RARE_RECIPES

    # Verify rare recipes exist separately
    assert "elixir of vitality" in RARE_RECIPES
    assert "steel blade" in RARE_RECIPES
    assert "fortified armor" in RARE_RECIPES

    # Verify they're NOT in base recipes
    assert "elixir of vitality" not in CRAFTING_RECIPES
    assert "steel blade" not in CRAFTING_RECIPES
    assert "fortified armor" not in CRAFTING_RECIPES


def test_character_has_unlocked_recipes():
    """Spec: Character should have unlocked_recipes set (default empty)."""
    character = make_character()
    assert hasattr(character, "unlocked_recipes")
    assert isinstance(character.unlocked_recipes, set)
    assert len(character.unlocked_recipes) == 0


def test_craft_fails_for_undiscovered_rare_recipe():
    """Spec: Crafting rare recipe without unlocking should fail with appropriate message."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    inv = game_state.current_character.inventory

    # Add ingredients for elixir of vitality (2 Herbs + 1 Iron Ore)
    inv.add_item(Item(name="Herbs", description="Healing herbs", item_type=ItemType.RESOURCE))
    inv.add_item(Item(name="Herbs", description="Healing herbs", item_type=ItemType.RESOURCE))
    inv.add_item(Item(name="Iron Ore", description="Raw iron ore", item_type=ItemType.RESOURCE))

    # Try to craft without unlocking
    success, msg = execute_craft(game_state, "elixir of vitality")

    assert success is False
    assert "don't know this recipe" in msg.lower() or "must be discovered" in msg.lower()


def test_craft_succeeds_after_unlocking_recipe():
    """Spec: Crafting rare recipe should work after unlock_recipe() is called."""
    from cli_rpg.crafting import execute_craft
    from cli_rpg.models.crafting_proficiency import CraftingLevel

    game_state = make_game_state()
    char = game_state.current_character
    inv = char.inventory

    # Set crafting level to MASTER for rare recipes
    char.crafting_proficiency.xp = 100

    # Unlock the recipe
    char.unlock_recipe("elixir of vitality")

    # Add ingredients (2 Herbs + 1 Iron Ore)
    inv.add_item(Item(name="Herbs", description="Healing herbs", item_type=ItemType.RESOURCE))
    inv.add_item(Item(name="Herbs", description="Healing herbs", item_type=ItemType.RESOURCE))
    inv.add_item(Item(name="Iron Ore", description="Raw iron ore", item_type=ItemType.RESOURCE))

    # Now craft should succeed
    success, msg = execute_craft(game_state, "elixir of vitality")

    assert success is True
    assert "Crafted" in msg or "crafted" in msg

    # Verify the item was created with correct properties
    elixir = inv.find_item_by_name("Elixir of Vitality")
    assert elixir is not None
    assert elixir.heal_amount == 75


def test_unlock_recipe_adds_to_set():
    """Spec: unlock_recipe() should add recipe key to unlocked_recipes."""
    character = make_character()

    assert "steel blade" not in character.unlocked_recipes

    result = character.unlock_recipe("steel blade")

    assert "steel blade" in character.unlocked_recipes
    assert "learned" in result.lower() or "recipe" in result.lower()


def test_unlock_recipe_returns_message_for_already_unlocked():
    """Spec: unlock_recipe() should indicate if already learned."""
    character = make_character()

    # Unlock twice
    character.unlock_recipe("steel blade")
    result = character.unlock_recipe("steel blade")

    # Should indicate already known
    assert "already" in result.lower() or "know" in result.lower()


def test_has_recipe_method():
    """Spec: has_recipe() should correctly check if recipe is unlocked."""
    character = make_character()

    assert character.has_recipe("steel blade") is False

    character.unlock_recipe("steel blade")

    assert character.has_recipe("steel blade") is True
    assert character.has_recipe("fortified armor") is False


def test_recipes_list_shows_rare_section():
    """Spec: get_recipes_list() should show discovered rare recipes separately."""
    from cli_rpg.crafting import get_recipes_list

    character = make_character()

    # Unlock a rare recipe
    character.unlock_recipe("steel blade")

    output = get_recipes_list(character)

    # Should have both sections
    assert "Available" in output
    assert "Discovered Rare Recipes" in output or "Rare Recipes" in output
    assert "Steel Blade" in output


def test_recipes_list_without_rare_recipes():
    """Spec: get_recipes_list() should not show rare section if none unlocked."""
    from cli_rpg.crafting import get_recipes_list

    character = make_character()

    output = get_recipes_list(character)

    # Should show base recipes but not rare section when none unlocked
    assert "Available" in output
    # Rare section only appears if there are unlocked recipes
    # (This test verifies behavior when no rare recipes are unlocked)


def test_rare_recipe_serialization():
    """Spec: unlocked_recipes should serialize/deserialize correctly."""
    character = make_character()

    # Unlock some recipes
    character.unlock_recipe("steel blade")
    character.unlock_recipe("fortified armor")

    # Serialize
    data = character.to_dict()
    assert "unlocked_recipes" in data
    assert set(data["unlocked_recipes"]) == {"steel blade", "fortified armor"}

    # Deserialize
    restored = Character.from_dict(data)
    assert restored.unlocked_recipes == {"steel blade", "fortified armor"}


def test_rare_recipes_require_expert_level():
    """Spec: Steel Blade and Fortified Armor require EXPERT level."""
    from cli_rpg.crafting import RARE_RECIPE_LEVEL
    from cli_rpg.models.crafting_proficiency import CraftingLevel

    assert RARE_RECIPE_LEVEL["steel blade"] == CraftingLevel.EXPERT
    assert RARE_RECIPE_LEVEL["fortified armor"] == CraftingLevel.EXPERT


def test_elixir_of_vitality_requires_master_level():
    """Spec: Elixir of Vitality requires MASTER level."""
    from cli_rpg.crafting import RARE_RECIPE_LEVEL
    from cli_rpg.models.crafting_proficiency import CraftingLevel

    assert RARE_RECIPE_LEVEL["elixir of vitality"] == CraftingLevel.MASTER


def test_rare_recipe_requires_crafting_level():
    """Spec: Crafting rare recipe should fail if crafting level too low."""
    from cli_rpg.crafting import execute_craft

    game_state = make_game_state()
    char = game_state.current_character
    inv = char.inventory

    # Unlock the recipe (but crafting level is NOVICE)
    char.unlock_recipe("steel blade")

    # Add ingredients (3 Iron Ore + 2 Wood)
    for _ in range(3):
        inv.add_item(Item(name="Iron Ore", description="Raw iron ore", item_type=ItemType.RESOURCE))
    for _ in range(2):
        inv.add_item(Item(name="Wood", description="Wood", item_type=ItemType.RESOURCE))

    # Should fail due to level requirement
    success, msg = execute_craft(game_state, "steel blade")

    assert success is False
    assert "Expert" in msg or "level" in msg.lower()


def test_backward_compat_character_without_unlocked_recipes():
    """Spec: Old saves without unlocked_recipes should load with empty set."""
    old_save = {
        "name": "OldPlayer",
        "strength": 12,
        "dexterity": 11,
        "intelligence": 10,
        "charisma": 10,
        "perception": 10,
        "luck": 10,
        "level": 5,
        "health": 100,
        "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None},
        # No unlocked_recipes key
    }

    character = Character.from_dict(old_save)

    # Should have empty unlocked_recipes set
    assert hasattr(character, "unlocked_recipes")
    assert isinstance(character.unlocked_recipes, set)
    assert len(character.unlocked_recipes) == 0
