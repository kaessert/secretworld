"""Test that all named locations have enterable categories.

Spec:
- Named locations (is_named=True) should always have an enterable category
- New wilderness categories (grove, waystation, campsite, hollow, overlook) should be enterable
- WILDERNESS_ENTERABLE_FALLBACK should map non-enterable categories to enterable ones
- get_enterable_category() should always return an enterable category
"""
import pytest
from cli_rpg.world_tiles import (
    ENTERABLE_CATEGORIES,
    get_enterable_category,
    is_enterable_category,
    WILDERNESS_ENTERABLE_FALLBACK,
)


class TestWildernessCategoriesInEnterable:
    """Verify new wilderness categories are in ENTERABLE_CATEGORIES."""

    def test_grove_in_enterable(self):
        """grove should be in ENTERABLE_CATEGORIES."""
        assert "grove" in ENTERABLE_CATEGORIES

    def test_waystation_in_enterable(self):
        """waystation should be in ENTERABLE_CATEGORIES."""
        assert "waystation" in ENTERABLE_CATEGORIES

    def test_campsite_in_enterable(self):
        """campsite should be in ENTERABLE_CATEGORIES."""
        assert "campsite" in ENTERABLE_CATEGORIES

    def test_hollow_in_enterable(self):
        """hollow should be in ENTERABLE_CATEGORIES."""
        assert "hollow" in ENTERABLE_CATEGORIES

    def test_overlook_in_enterable(self):
        """overlook should be in ENTERABLE_CATEGORIES."""
        assert "overlook" in ENTERABLE_CATEGORIES


class TestWildernessEnterableFallback:
    """Verify WILDERNESS_ENTERABLE_FALLBACK values are all enterable."""

    def test_all_fallback_targets_are_enterable(self):
        """All target values in WILDERNESS_ENTERABLE_FALLBACK should be enterable."""
        for source, target in WILDERNESS_ENTERABLE_FALLBACK.items():
            assert target in ENTERABLE_CATEGORIES, \
                f"Fallback {source} -> {target} is not enterable"

    def test_forest_fallback_exists(self):
        """forest should have a fallback."""
        assert "forest" in WILDERNESS_ENTERABLE_FALLBACK

    def test_wilderness_fallback_exists(self):
        """wilderness should have a fallback."""
        assert "wilderness" in WILDERNESS_ENTERABLE_FALLBACK

    def test_mountain_fallback_exists(self):
        """mountain should have a fallback."""
        assert "mountain" in WILDERNESS_ENTERABLE_FALLBACK


class TestGetEnterableCategory:
    """Verify get_enterable_category always returns an enterable category."""

    def test_already_enterable_category_unchanged(self):
        """Categories already enterable should be returned unchanged."""
        assert get_enterable_category("dungeon", None) == "dungeon"
        assert get_enterable_category("cave", None) == "cave"
        assert get_enterable_category("town", None) == "town"
        assert get_enterable_category("village", None) == "village"

    def test_non_enterable_category_gets_fallback(self):
        """Non-enterable categories should get appropriate fallback."""
        # forest -> grove
        result = get_enterable_category("forest", "forest")
        assert is_enterable_category(result)

        # wilderness -> campsite (default)
        result = get_enterable_category("wilderness", "wilderness")
        assert is_enterable_category(result)

    def test_terrain_fallback_used_when_category_none(self):
        """When category is None, terrain should be used for fallback."""
        result = get_enterable_category(None, "swamp")
        assert is_enterable_category(result)

    def test_terrain_fallback_used_when_category_non_enterable(self):
        """Terrain fallback should be used for non-enterable categories."""
        result = get_enterable_category("forest", "forest")
        assert is_enterable_category(result)

    def test_default_fallback_when_no_match(self):
        """Default to campsite when no fallback found."""
        result = get_enterable_category(None, None)
        assert result == "campsite"
        assert is_enterable_category(result)

    def test_all_common_terrains_produce_enterable(self):
        """Test that all common terrain types produce enterable results."""
        terrains = ["forest", "mountain", "plains", "desert", "swamp", "beach", "hills"]
        for terrain in terrains:
            result = get_enterable_category(terrain, terrain)
            assert is_enterable_category(result), \
                f"get_enterable_category({terrain!r}, {terrain!r}) = {result!r} not enterable"

    def test_case_insensitive(self):
        """Category and terrain matching should be case insensitive."""
        # Already enterable - should preserve original
        result = get_enterable_category("Dungeon", None)
        assert result == "Dungeon"  # Preserved as-is since it's enterable

        # Non-enterable - should get fallback
        result = get_enterable_category("Forest", "Forest")
        assert is_enterable_category(result)


class TestIsEnterableCategory:
    """Verify is_enterable_category works correctly."""

    def test_enterable_categories_return_true(self):
        """Known enterable categories should return True."""
        assert is_enterable_category("dungeon") is True
        assert is_enterable_category("cave") is True
        assert is_enterable_category("grove") is True
        assert is_enterable_category("waystation") is True

    def test_non_enterable_categories_return_false(self):
        """Non-enterable categories should return False."""
        assert is_enterable_category("forest") is False
        assert is_enterable_category("wilderness") is False
        assert is_enterable_category("mountain") is False

    def test_none_returns_false(self):
        """None should return False."""
        assert is_enterable_category(None) is False

    def test_case_insensitive(self):
        """Category matching should be case insensitive."""
        assert is_enterable_category("Dungeon") is True
        assert is_enterable_category("CAVE") is True
        assert is_enterable_category("Grove") is True
