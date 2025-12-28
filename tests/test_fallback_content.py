"""Tests for FallbackContentProvider.

Tests verify:
1. get_room_content returns deterministic room data
2. get_npc_content returns deterministic NPC data
3. get_item_content returns deterministic item data
4. get_quest_content returns deterministic quest data
5. Same seed produces identical output (determinism)
6. Different seeds produce different output (variety)
7. All RoomType values have fallback templates
8. All ENTERABLE_CATEGORIES have fallback templates
9. Category-specific content for dungeons
10. Role-specific content for merchants
"""

import pytest
from cli_rpg.fallback_content import FallbackContentProvider
from cli_rpg.procedural_interiors import RoomType
from cli_rpg.world_tiles import ENTERABLE_CATEGORIES


class TestGetRoomContent:
    """Tests for get_room_content method."""

    def test_returns_name_and_description(self):
        """Test 1: get_room_content returns dict with name and description."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_room_content(RoomType.ENTRY, "dungeon")

        assert "name" in result
        assert "description" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["description"], str)
        assert len(result["name"]) > 0
        assert len(result["description"]) > 0

    def test_deterministic_with_same_seed(self):
        """Test 5: Same seed produces identical output."""
        provider1 = FallbackContentProvider(seed=42)
        provider2 = FallbackContentProvider(seed=42)

        result1 = provider1.get_room_content(RoomType.CHAMBER, "cave")
        result2 = provider2.get_room_content(RoomType.CHAMBER, "cave")

        assert result1 == result2

    def test_different_with_different_seeds(self):
        """Test 6: Different seeds produce different output across multiple calls."""
        provider1 = FallbackContentProvider(seed=42)
        provider2 = FallbackContentProvider(seed=123)

        # Make multiple calls and check that at least one differs
        # This is more robust than checking a single call
        differences_found = False
        for room_type in RoomType:
            for category in ["dungeon", "cave", "temple"]:
                result1 = provider1.get_room_content(room_type, category)
                result2 = provider2.get_room_content(room_type, category)
                if result1["name"] != result2["name"] or result1["description"] != result2["description"]:
                    differences_found = True
                    break
            if differences_found:
                break

        assert differences_found, "Different seeds should produce at least some different content"

    def test_all_room_types_have_templates(self):
        """Test 7: All RoomType values have fallback templates."""
        provider = FallbackContentProvider(seed=42)

        for room_type in RoomType:
            result = provider.get_room_content(room_type, "dungeon")
            assert "name" in result
            assert "description" in result
            assert len(result["name"]) > 0, f"Empty name for {room_type}"
            assert len(result["description"]) > 0, f"Empty description for {room_type}"

    def test_dungeon_category_themed_content(self):
        """Test 9: Dungeon category returns dungeon-themed content."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_room_content(RoomType.ENTRY, "dungeon")

        # Description should reference dungeon-related terms
        dungeon_keywords = ["dungeon", "dark", "passage", "entrance", "shadow", "depth"]
        description_lower = result["description"].lower()
        has_keyword = any(kw in description_lower for kw in dungeon_keywords)
        assert has_keyword, f"Description '{result['description']}' should contain dungeon-themed keywords"


class TestGetNpcContent:
    """Tests for get_npc_content method."""

    def test_returns_npc_data(self):
        """Test 2: get_npc_content returns dict with name, description, dialogue."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_npc_content("merchant", "town")

        assert "name" in result
        assert "description" in result
        assert "dialogue" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["description"], str)
        assert isinstance(result["dialogue"], str)
        assert len(result["name"]) > 0
        assert len(result["description"]) > 0
        assert len(result["dialogue"]) > 0

    def test_deterministic_with_same_seed(self):
        """Test 5: Same seed produces identical NPC output."""
        provider1 = FallbackContentProvider(seed=42)
        provider2 = FallbackContentProvider(seed=42)

        result1 = provider1.get_npc_content("guard", "city")
        result2 = provider2.get_npc_content("guard", "city")

        assert result1 == result2

    def test_merchant_role_content(self):
        """Test 10: Merchant role returns merchant-specific content."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_npc_content("merchant", "town")

        # Name or description should reference trading/merchant terms
        merchant_keywords = ["merchant", "trader", "vendor", "wares", "goods", "sell", "buy", "shop"]
        combined = f"{result['name']} {result['description']} {result['dialogue']}".lower()
        has_keyword = any(kw in combined for kw in merchant_keywords)
        assert has_keyword, f"Merchant NPC should have trading-related content"


class TestGetItemContent:
    """Tests for get_item_content method."""

    def test_returns_item_data(self):
        """Test 3: get_item_content returns dict with name, description, stats."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_item_content("weapon", "dungeon")

        assert "name" in result
        assert "description" in result
        assert "item_type" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["description"], str)
        assert len(result["name"]) > 0
        assert len(result["description"]) > 0

    def test_deterministic_with_same_seed(self):
        """Test 5: Same seed produces identical item output."""
        provider1 = FallbackContentProvider(seed=42)
        provider2 = FallbackContentProvider(seed=42)

        result1 = provider1.get_item_content("armor", "temple")
        result2 = provider2.get_item_content("armor", "temple")

        assert result1 == result2

    def test_weapon_type_has_damage_bonus(self):
        """Weapons should have damage_bonus stat."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_item_content("weapon", "dungeon")

        assert "damage_bonus" in result or result["item_type"] != "weapon"

    def test_armor_type_has_defense_bonus(self):
        """Armor should have defense_bonus stat."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_item_content("armor", "temple")

        assert "defense_bonus" in result or result["item_type"] != "armor"


class TestGetQuestContent:
    """Tests for get_quest_content method."""

    def test_returns_quest_data(self):
        """Test 4: get_quest_content returns dict with name, description, objective."""
        provider = FallbackContentProvider(seed=42)
        result = provider.get_quest_content("dungeon")

        assert "name" in result
        assert "description" in result
        assert "objective_type" in result
        assert "target" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["description"], str)
        assert len(result["name"]) > 0
        assert len(result["description"]) > 0

    def test_deterministic_with_same_seed(self):
        """Test 5: Same seed produces identical quest output."""
        provider1 = FallbackContentProvider(seed=42)
        provider2 = FallbackContentProvider(seed=42)

        result1 = provider1.get_quest_content("cave")
        result2 = provider2.get_quest_content("cave")

        assert result1 == result2


class TestCategorySupport:
    """Tests for category-specific support."""

    def test_all_enterable_categories_have_room_templates(self):
        """Test 8: All ENTERABLE_CATEGORIES have fallback room templates."""
        provider = FallbackContentProvider(seed=42)

        for category in ENTERABLE_CATEGORIES:
            result = provider.get_room_content(RoomType.CHAMBER, category)
            assert "name" in result, f"No name for category {category}"
            assert "description" in result, f"No description for category {category}"
            assert len(result["description"]) > 0, f"Empty description for category {category}"

    def test_category_specific_descriptions(self):
        """Different categories should produce different descriptions."""
        provider = FallbackContentProvider(seed=42)

        dungeon_result = provider.get_room_content(RoomType.CHAMBER, "dungeon")

        # Reset to same seed for fair comparison
        provider2 = FallbackContentProvider(seed=42)
        temple_result = provider2.get_room_content(RoomType.CHAMBER, "temple")

        # Descriptions should differ between dungeon and temple
        assert dungeon_result["description"] != temple_result["description"], \
            "Dungeon and temple should have different descriptions"


class TestReproducibility:
    """Tests for deterministic reproducibility across calls."""

    def test_multiple_calls_same_provider(self):
        """Multiple calls to same provider produce consistent sequence."""
        provider = FallbackContentProvider(seed=42)

        # Make multiple calls
        room1 = provider.get_room_content(RoomType.ENTRY, "dungeon")
        npc1 = provider.get_npc_content("guard", "town")
        item1 = provider.get_item_content("weapon", "cave")

        # New provider with same seed
        provider2 = FallbackContentProvider(seed=42)

        room2 = provider2.get_room_content(RoomType.ENTRY, "dungeon")
        npc2 = provider2.get_npc_content("guard", "town")
        item2 = provider2.get_item_content("weapon", "cave")

        assert room1 == room2
        assert npc1 == npc2
        assert item1 == item2

    def test_seed_isolation(self):
        """Provider instances with different seeds are isolated."""
        provider1 = FallbackContentProvider(seed=1)
        provider2 = FallbackContentProvider(seed=2)

        # Interleave calls
        result1a = provider1.get_room_content(RoomType.CHAMBER, "dungeon")
        result2a = provider2.get_room_content(RoomType.CHAMBER, "dungeon")
        result1b = provider1.get_npc_content("merchant", "town")
        result2b = provider2.get_npc_content("merchant", "town")

        # Verify they don't interfere with each other
        provider1_fresh = FallbackContentProvider(seed=1)
        provider2_fresh = FallbackContentProvider(seed=2)

        result1a_fresh = provider1_fresh.get_room_content(RoomType.CHAMBER, "dungeon")
        result2a_fresh = provider2_fresh.get_room_content(RoomType.CHAMBER, "dungeon")
        result1b_fresh = provider1_fresh.get_npc_content("merchant", "town")
        result2b_fresh = provider2_fresh.get_npc_content("merchant", "town")

        assert result1a == result1a_fresh
        assert result2a == result2a_fresh
        assert result1b == result1b_fresh
        assert result2b == result2b_fresh
