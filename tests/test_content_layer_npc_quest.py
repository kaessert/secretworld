"""Tests for ContentLayer NPC and quest generation integration.

These tests verify that ContentLayer correctly generates NPCs and quests using
FallbackContentProvider when AI is unavailable, with deterministic seeding.

Spec: ContentLayer.generate_npc_content() and generate_quest_content() provide
NPC/quest content with AI-first approach falling back to FallbackContentProvider.
"""

import random
import pytest
from unittest.mock import Mock

from cli_rpg.content_layer import ContentLayer


@pytest.fixture
def content_layer():
    """Create a ContentLayer instance."""
    return ContentLayer()


# =============================================================================
# Test 1: ContentLayer generates NPCs with fallback when AI unavailable
# =============================================================================
def test_generate_npc_content_fallback_when_ai_unavailable(content_layer):
    """Verify NPC generation uses fallback when AI unavailable.

    Spec: ContentLayer.generate_npc_content() returns valid NPC dict with
    name, description, and dialogue when ai_service=None.
    """
    rng = random.Random(42)

    npc_content = content_layer.generate_npc_content(
        role="merchant",
        category="dungeon",
        coords=(0, 0, 0),
        ai_service=None,
        generation_context=None,
        rng=rng,
    )

    # Verify required fields exist and are non-empty
    assert "name" in npc_content
    assert "description" in npc_content
    assert "dialogue" in npc_content
    assert npc_content["name"] != ""
    assert npc_content["description"] != ""
    assert npc_content["dialogue"] != ""


# =============================================================================
# Test 2: ContentLayer generates quests with fallback when AI unavailable
# =============================================================================
def test_generate_quest_content_fallback_when_ai_unavailable(content_layer):
    """Verify quest generation uses fallback when AI unavailable.

    Spec: ContentLayer.generate_quest_content() returns valid quest dict with
    name, description, objective_type, and target when ai_service=None.
    """
    rng = random.Random(42)

    quest_content = content_layer.generate_quest_content(
        category="dungeon",
        coords=(0, 0, 0),
        ai_service=None,
        generation_context=None,
        rng=rng,
    )

    # Verify required fields exist
    assert quest_content is not None
    assert "name" in quest_content
    assert "description" in quest_content
    assert "objective_type" in quest_content
    assert "target" in quest_content
    assert quest_content["name"] != ""
    assert quest_content["description"] != ""


# =============================================================================
# Test 3: Same seed produces identical NPC content (determinism)
# =============================================================================
def test_generate_npc_content_deterministic(content_layer):
    """Verify same seed → same NPC content (determinism).

    Spec: Given same inputs and seed, ContentLayer produces identical NPC content.
    """
    rng1 = random.Random(12345)
    rng2 = random.Random(12345)

    npc_content_1 = content_layer.generate_npc_content(
        role="guard",
        category="town",
        coords=(1, 2, 3),
        ai_service=None,
        generation_context=None,
        rng=rng1,
    )

    npc_content_2 = content_layer.generate_npc_content(
        role="guard",
        category="town",
        coords=(1, 2, 3),
        ai_service=None,
        generation_context=None,
        rng=rng2,
    )

    assert npc_content_1["name"] == npc_content_2["name"]
    assert npc_content_1["description"] == npc_content_2["description"]
    assert npc_content_1["dialogue"] == npc_content_2["dialogue"]


# =============================================================================
# Test 4: Same seed produces identical quest content (determinism)
# =============================================================================
def test_generate_quest_content_deterministic(content_layer):
    """Verify same seed → same quest content (determinism).

    Spec: Given same inputs and seed, ContentLayer produces identical quest content.
    """
    rng1 = random.Random(12345)
    rng2 = random.Random(12345)

    quest_content_1 = content_layer.generate_quest_content(
        category="cave",
        coords=(2, 3, 0),
        ai_service=None,
        generation_context=None,
        rng=rng1,
    )

    quest_content_2 = content_layer.generate_quest_content(
        category="cave",
        coords=(2, 3, 0),
        ai_service=None,
        generation_context=None,
        rng=rng2,
    )

    assert quest_content_1["name"] == quest_content_2["name"]
    assert quest_content_1["description"] == quest_content_2["description"]
    assert quest_content_1["objective_type"] == quest_content_2["objective_type"]
    assert quest_content_1["target"] == quest_content_2["target"]


# =============================================================================
# Test 5: AI-generated NPC content used when available
# =============================================================================
def test_generate_npc_content_uses_ai_when_available(content_layer):
    """Verify AI-generated NPC content used when available.

    Spec: When ai_service.generate_npc_content() succeeds, ContentLayer
    returns AI-generated content instead of fallback.
    """
    rng = random.Random(42)

    # Create mock AI service
    mock_ai = Mock()
    mock_ai.generate_npc_content = Mock(return_value={
        "name": "Gandalf the Grey",
        "description": "A wise wizard with a long grey beard.",
        "dialogue": "You shall not pass!",
    })

    npc_content = content_layer.generate_npc_content(
        role="quest_giver",
        category="dungeon",
        coords=(0, 0, 0),
        ai_service=mock_ai,
        generation_context=None,
        rng=rng,
    )

    # AI should have been called
    assert mock_ai.generate_npc_content.called

    # Content should be AI-generated
    assert npc_content["name"] == "Gandalf the Grey"
    assert npc_content["description"] == "A wise wizard with a long grey beard."
    assert npc_content["dialogue"] == "You shall not pass!"


# =============================================================================
# Test 6: AI-generated quest content used when available
# =============================================================================
def test_generate_quest_content_uses_ai_when_available(content_layer):
    """Verify AI-generated quest content used when available.

    Spec: When ai_service.generate_quest() succeeds, ContentLayer
    returns AI-generated content instead of fallback.
    """
    rng = random.Random(42)

    # Create mock AI service
    mock_ai = Mock()
    mock_ai.generate_quest = Mock(return_value={
        "name": "The Ring of Doom",
        "description": "Destroy the One Ring in the fires of Mount Doom.",
        "objective_type": "explore",
        "target": "Mount Doom",
    })

    # Create mock generation context
    mock_context = Mock()
    mock_context.world = Mock()
    mock_context.world.theme = "fantasy"
    mock_context.region = Mock()

    quest_content = content_layer.generate_quest_content(
        category="dungeon",
        coords=(0, 0, 0),
        ai_service=mock_ai,
        generation_context=mock_context,
        rng=rng,
    )

    # AI should have been called
    assert mock_ai.generate_quest.called

    # Content should be AI-generated
    assert quest_content["name"] == "The Ring of Doom"
    assert quest_content["description"] == "Destroy the One Ring in the fires of Mount Doom."
    assert quest_content["objective_type"] == "explore"
    assert quest_content["target"] == "Mount Doom"


# =============================================================================
# Test 7: AI failure falls back to FallbackContentProvider for NPC
# =============================================================================
def test_generate_npc_content_fallback_on_ai_failure(content_layer):
    """Verify AI failure → fallback for NPC content.

    Spec: When ai_service.generate_npc_content() raises exception,
    ContentLayer falls back to FallbackContentProvider.
    """
    rng = random.Random(42)

    # Create mock AI service that fails
    mock_ai = Mock()
    mock_ai.generate_npc_content = Mock(side_effect=Exception("AI unavailable"))

    npc_content = content_layer.generate_npc_content(
        role="merchant",
        category="town",
        coords=(0, 0, 0),
        ai_service=mock_ai,
        generation_context=None,
        rng=rng,
    )

    # Should still return valid content from fallback
    assert "name" in npc_content
    assert "description" in npc_content
    assert "dialogue" in npc_content
    assert npc_content["name"] != ""


# =============================================================================
# Test 8: AI failure falls back to FallbackContentProvider for quest
# =============================================================================
def test_generate_quest_content_fallback_on_ai_failure(content_layer):
    """Verify AI failure → fallback for quest content.

    Spec: When ai_service.generate_quest() raises exception,
    ContentLayer falls back to FallbackContentProvider.
    """
    rng = random.Random(42)

    # Create mock AI service that fails
    mock_ai = Mock()
    mock_ai.generate_quest = Mock(side_effect=Exception("AI unavailable"))

    # Create mock generation context
    mock_context = Mock()
    mock_context.world = Mock()
    mock_context.world.theme = "fantasy"
    mock_context.region = Mock()

    quest_content = content_layer.generate_quest_content(
        category="temple",
        coords=(0, 0, 0),
        ai_service=mock_ai,
        generation_context=mock_context,
        rng=rng,
    )

    # Should still return valid content from fallback
    assert quest_content is not None
    assert "name" in quest_content
    assert "description" in quest_content
    assert quest_content["name"] != ""


# =============================================================================
# Test 9: NPC content varies by role
# =============================================================================
def test_generate_npc_content_varies_by_role(content_layer):
    """Verify NPC content varies by role.

    Spec: Different roles produce thematically appropriate NPC content.
    """
    rng1 = random.Random(42)
    rng2 = random.Random(42)

    merchant_content = content_layer.generate_npc_content(
        role="merchant",
        category="town",
        coords=(0, 0, 0),
        ai_service=None,
        generation_context=None,
        rng=rng1,
    )

    guard_content = content_layer.generate_npc_content(
        role="guard",
        category="town",
        coords=(0, 0, 0),
        ai_service=None,
        generation_context=None,
        rng=rng2,
    )

    # Different roles should have different content
    # (with same seed, same RNG state, but different roles)
    # At minimum, names or dialogues should differ due to role-specific templates
    assert merchant_content["dialogue"] != guard_content["dialogue"]


# =============================================================================
# Test 10: Quest content varies by category
# =============================================================================
def test_generate_quest_content_varies_by_category(content_layer):
    """Verify quest content varies by category.

    Spec: Different categories produce thematically appropriate quests.
    """
    rng1 = random.Random(42)
    rng2 = random.Random(42)

    dungeon_quest = content_layer.generate_quest_content(
        category="dungeon",
        coords=(0, 0, 0),
        ai_service=None,
        generation_context=None,
        rng=rng1,
    )

    temple_quest = content_layer.generate_quest_content(
        category="temple",
        coords=(0, 0, 0),
        ai_service=None,
        generation_context=None,
        rng=rng2,
    )

    # Different categories should produce different quests
    # (templates differ by category)
    assert dungeon_quest["name"] != temple_quest["name"]
