"""Tests for GenerationContext model."""

import pytest
from datetime import datetime

from cli_rpg.models.generation_context import GenerationContext
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.models.settlement_context import SettlementContext
from cli_rpg.models.lore_context import LoreContext


# --- Fixtures ---


@pytest.fixture
def world_context() -> WorldContext:
    """Create a sample WorldContext for testing."""
    return WorldContext(
        theme="fantasy",
        theme_essence="epic high fantasy with ancient magic",
        naming_style="Old English with Celtic influence",
        tone="heroic, adventurous",
        generated_at=datetime(2024, 1, 15, 10, 30, 0),
        creation_myth="Forged by gods from primordial chaos",
        major_conflicts=["War of the Ancients", "The Sundering"],
        legendary_artifacts=["Sword of Light", "Crown of Shadows"],
        prophecies=["The chosen one shall rise"],
        major_factions=["The Crown", "The Mage's Circle"],
        faction_tensions={"The Crown": ["The Mage's Circle"]},
        economic_era="stable",
    )


@pytest.fixture
def region_context() -> RegionContext:
    """Create a sample RegionContext for testing."""
    return RegionContext(
        name="Darkwood Forest",
        theme="ancient forest, hidden paths, fey creatures",
        danger_level="dangerous",
        landmarks=["The Elder Tree", "Moonwell"],
        coordinates=(50, 50),
        generated_at=datetime(2024, 1, 15, 11, 0, 0),
        primary_resources=["timber", "herbs"],
        scarce_resources=["iron"],
        trade_goods=["elven crafts"],
        price_modifier=1.2,
        founding_story="Created by ancient druids",
        historical_events=["The Great Fire of 300 AE"],
        ruined_civilizations=["The Forest Elves"],
        legendary_locations=["The Lost Grove"],
        common_creatures=["wolves", "sprites"],
        weather_tendency="foggy",
        ambient_sounds=["bird calls", "rustling leaves"],
    )


@pytest.fixture
def settlement_context() -> SettlementContext:
    """Create a sample SettlementContext for testing."""
    return SettlementContext(
        settlement_name="Thornhaven",
        location_coordinates=(55, 52),
        generated_at=datetime(2024, 1, 15, 12, 0, 0),
        notable_families=["House Thorn", "House Maple"],
        npc_relationships=[{"npc_a": "Lord Thorn", "npc_b": "Lady Maple", "type": "rivalry"}],
        trade_routes=[{"origin": "Thornhaven", "destination": "Ironforge", "goods": "timber"}],
        local_guilds=["Woodcutters Guild", "Herbalists Circle"],
        market_specialty="herbal remedies",
        government_type="council",
        political_figures=[{"name": "Elder Oakheart", "title": "Chief Elder"}],
        current_tensions=["land dispute with Ironforge"],
        population_size="town",
        prosperity_level="modest",
        social_issues=["shortage of iron tools"],
    )


@pytest.fixture
def world_lore_context() -> LoreContext:
    """Create a sample world-level LoreContext for testing."""
    return LoreContext(
        region_name="World",
        coordinates=(0, 0),
        generated_at=datetime(2024, 1, 15, 13, 0, 0),
        historical_events=[{"name": "Creation", "date": "Year 0"}],
        legendary_items=[{"name": "Orb of Creation", "powers": "reality warping"}],
        legendary_places=[{"name": "The First Temple", "danger_level": "legendary"}],
        prophecies=[{"name": "The End Times", "text": "All shall return to void"}],
        ancient_civilizations=[{"name": "The First Ones", "era": "Before Time"}],
        creation_myths=["In the beginning, there was void"],
        deities=[{"name": "The Creator", "domain": "creation"}],
    )


@pytest.fixture
def region_lore_context() -> LoreContext:
    """Create a sample region-level LoreContext for testing."""
    return LoreContext(
        region_name="Darkwood Forest",
        coordinates=(50, 50),
        generated_at=datetime(2024, 1, 15, 14, 0, 0),
        historical_events=[{"name": "The Fey Incursion", "date": "500 AE"}],
        legendary_items=[{"name": "Heartwood Staff", "powers": "nature magic"}],
        legendary_places=[{"name": "The Fey Gate", "danger_level": "extreme"}],
        prophecies=[{"name": "Return of the Fey", "text": "They shall return"}],
        ancient_civilizations=[{"name": "The Wild Elves", "era": "First Age"}],
        creation_myths=["The forest grew from a single seed"],
        deities=[{"name": "The Green Lady", "domain": "nature"}],
    )


# --- Test: Creation with world only (minimal context) ---


def test_creation_with_world_only(world_context: WorldContext):
    """Test creating GenerationContext with only WorldContext (minimal required)."""
    # Spec: GenerationContext requires only WorldContext; other layers are optional
    ctx = GenerationContext(world=world_context)

    assert ctx.world is world_context
    assert ctx.region is None
    assert ctx.settlement is None
    assert ctx.world_lore is None
    assert ctx.region_lore is None


# --- Test: Creation with all layers ---


def test_creation_with_all_layers(
    world_context: WorldContext,
    region_context: RegionContext,
    settlement_context: SettlementContext,
    world_lore_context: LoreContext,
    region_lore_context: LoreContext,
):
    """Test creating GenerationContext with all context layers populated."""
    # Spec: GenerationContext can hold all 6 layers
    ctx = GenerationContext(
        world=world_context,
        region=region_context,
        settlement=settlement_context,
        world_lore=world_lore_context,
        region_lore=region_lore_context,
    )

    assert ctx.world is world_context
    assert ctx.region is region_context
    assert ctx.settlement is settlement_context
    assert ctx.world_lore is world_lore_context
    assert ctx.region_lore is region_lore_context


# --- Test: to_prompt_context with world only ---


def test_to_prompt_context_world_only(world_context: WorldContext):
    """Test to_prompt_context output structure with only WorldContext."""
    # Spec: to_prompt_context returns dict with world fields when only world is present
    ctx = GenerationContext(world=world_context)
    prompt_ctx = ctx.to_prompt_context()

    # WorldContext fields should be present
    assert prompt_ctx["theme"] == "fantasy"
    assert prompt_ctx["theme_essence"] == "epic high fantasy with ancient magic"
    assert prompt_ctx["naming_style"] == "Old English with Celtic influence"
    assert prompt_ctx["tone"] == "heroic, adventurous"
    assert prompt_ctx["creation_myth"] == "Forged by gods from primordial chaos"
    assert "War of the Ancients" in prompt_ctx["major_conflicts"]
    assert "Sword of Light" in prompt_ctx["legendary_artifacts"]
    assert prompt_ctx["economic_era"] == "stable"

    # Region/Settlement/Lore fields should NOT be present when layers are None
    assert "region_name" not in prompt_ctx
    assert "settlement_name" not in prompt_ctx
    assert "world_historical_events" not in prompt_ctx
    assert "region_historical_events" not in prompt_ctx


# --- Test: to_prompt_context with all layers ---


def test_to_prompt_context_full(
    world_context: WorldContext,
    region_context: RegionContext,
    settlement_context: SettlementContext,
    world_lore_context: LoreContext,
    region_lore_context: LoreContext,
):
    """Test to_prompt_context includes all layer fields when fully populated."""
    # Spec: to_prompt_context aggregates all available layers into output dict
    ctx = GenerationContext(
        world=world_context,
        region=region_context,
        settlement=settlement_context,
        world_lore=world_lore_context,
        region_lore=region_lore_context,
    )
    prompt_ctx = ctx.to_prompt_context()

    # WorldContext fields
    assert prompt_ctx["theme"] == "fantasy"
    assert prompt_ctx["theme_essence"] == "epic high fantasy with ancient magic"

    # RegionContext fields
    assert prompt_ctx["region_name"] == "Darkwood Forest"
    assert prompt_ctx["region_theme"] == "ancient forest, hidden paths, fey creatures"
    assert prompt_ctx["danger_level"] == "dangerous"
    assert "The Elder Tree" in prompt_ctx["landmarks"]
    assert prompt_ctx["region_coordinates"] == (50, 50)
    assert "timber" in prompt_ctx["primary_resources"]
    assert "wolves" in prompt_ctx["common_creatures"]

    # SettlementContext fields
    assert prompt_ctx["settlement_name"] == "Thornhaven"
    assert prompt_ctx["settlement_coordinates"] == (55, 52)
    assert "House Thorn" in prompt_ctx["notable_families"]
    assert prompt_ctx["government_type"] == "council"
    assert prompt_ctx["population_size"] == "town"
    assert "Woodcutters Guild" in prompt_ctx["local_guilds"]

    # World LoreContext fields (prefixed with world_)
    assert len(prompt_ctx["world_historical_events"]) > 0
    assert prompt_ctx["world_legendary_items"][0]["name"] == "Orb of Creation"
    assert prompt_ctx["world_deities"][0]["name"] == "The Creator"

    # Region LoreContext fields (prefixed with region_)
    assert len(prompt_ctx["region_historical_events"]) > 0
    assert prompt_ctx["region_legendary_items"][0]["name"] == "Heartwood Staff"
    assert prompt_ctx["region_deities"][0]["name"] == "The Green Lady"


# --- Test: to_dict serialization ---


def test_to_dict_serialization(
    world_context: WorldContext,
    region_context: RegionContext,
    settlement_context: SettlementContext,
):
    """Test to_dict serializes all present layers correctly."""
    # Spec: to_dict returns dict with each layer's to_dict output
    ctx = GenerationContext(
        world=world_context,
        region=region_context,
        settlement=settlement_context,
    )
    data = ctx.to_dict()

    assert "world" in data
    assert data["world"]["theme"] == "fantasy"

    assert "region" in data
    assert data["region"]["name"] == "Darkwood Forest"

    assert "settlement" in data
    assert data["settlement"]["settlement_name"] == "Thornhaven"

    # None layers should not appear
    assert "world_lore" not in data
    assert "region_lore" not in data


# --- Test: from_dict deserialization ---


def test_from_dict_deserialization(
    world_context: WorldContext,
    region_context: RegionContext,
    settlement_context: SettlementContext,
    world_lore_context: LoreContext,
    region_lore_context: LoreContext,
):
    """Test from_dict correctly restores GenerationContext from serialized data."""
    # Spec: from_dict round-trips with to_dict
    original = GenerationContext(
        world=world_context,
        region=region_context,
        settlement=settlement_context,
        world_lore=world_lore_context,
        region_lore=region_lore_context,
    )
    data = original.to_dict()
    restored = GenerationContext.from_dict(data)

    # Verify all layers restored
    assert restored.world.theme == original.world.theme
    assert restored.world.theme_essence == original.world.theme_essence

    assert restored.region is not None
    assert restored.region.name == original.region.name
    assert restored.region.danger_level == original.region.danger_level

    assert restored.settlement is not None
    assert restored.settlement.settlement_name == original.settlement.settlement_name

    assert restored.world_lore is not None
    assert len(restored.world_lore.deities) > 0

    assert restored.region_lore is not None
    assert restored.region_lore.region_name == original.region_lore.region_name


# --- Test: from_dict with minimal data (backward compatibility) ---


def test_from_dict_minimal(world_context: WorldContext):
    """Test from_dict handles minimal data (only world context)."""
    # Spec: from_dict works with only required fields for backward compatibility
    data = {"world": world_context.to_dict()}
    restored = GenerationContext.from_dict(data)

    assert restored.world.theme == "fantasy"
    assert restored.region is None
    assert restored.settlement is None
    assert restored.world_lore is None
    assert restored.region_lore is None


# --- Test: Optional layers None handling ---


def test_optional_layers_none(world_context: WorldContext):
    """Test that None optional layers are handled gracefully in all methods."""
    # Spec: All methods handle None optional layers without errors
    ctx = GenerationContext(world=world_context)

    # to_prompt_context should not error with None layers
    prompt_ctx = ctx.to_prompt_context()
    assert isinstance(prompt_ctx, dict)
    assert "theme" in prompt_ctx

    # to_dict should not include None layers
    data = ctx.to_dict()
    assert "world" in data
    assert "region" not in data
    assert "settlement" not in data

    # from_dict with serialized None layers should work
    restored = GenerationContext.from_dict(data)
    assert restored.region is None
    assert restored.settlement is None
