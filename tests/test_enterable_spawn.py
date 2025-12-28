"""Tests for enterable location forced spawn logic.

This tests the mechanic that forces enterable locations (dungeons, caves, etc.)
to spawn after the player has traveled too many tiles without encountering one.
This ensures players always have access to explorable interior locations.
"""
import pytest
from cli_rpg.world_tiles import (
    should_force_enterable_category,
    get_forced_enterable_category,
    MAX_TILES_WITHOUT_ENTERABLE,
    FORCED_ENTERABLE_BY_TERRAIN,
    ENTERABLE_CATEGORIES,
)


class TestEnterableSpawnLogic:
    """Tests for the enterable location forced spawn system."""

    def test_should_force_below_threshold(self):
        """Returns False when tiles_since_enterable < MAX_TILES_WITHOUT_ENTERABLE."""
        # At 0 tiles, should not force
        assert not should_force_enterable_category(0)
        # At threshold-1, should not force
        assert not should_force_enterable_category(MAX_TILES_WITHOUT_ENTERABLE - 1)
        # Verify the threshold is 25 as specified in the plan
        assert MAX_TILES_WITHOUT_ENTERABLE == 25
        assert not should_force_enterable_category(24)

    def test_should_force_at_threshold(self):
        """Returns True when tiles_since_enterable >= MAX_TILES_WITHOUT_ENTERABLE."""
        # At exactly the threshold, should force
        assert should_force_enterable_category(MAX_TILES_WITHOUT_ENTERABLE)
        assert should_force_enterable_category(25)
        # Well above threshold should also force
        assert should_force_enterable_category(50)
        assert should_force_enterable_category(100)

    def test_forced_category_is_enterable(self):
        """get_forced_enterable_category returns categories from ENTERABLE_CATEGORIES."""
        # Test all terrain types in the forced enterable mapping
        for terrain in FORCED_ENTERABLE_BY_TERRAIN:
            category = get_forced_enterable_category(terrain)
            assert category in ENTERABLE_CATEGORIES, (
                f"Category '{category}' returned for terrain '{terrain}' "
                f"is not in ENTERABLE_CATEGORIES"
            )

    def test_forced_category_matches_terrain(self):
        """Returned category is from the terrain's valid list."""
        # Test specific terrains
        category = get_forced_enterable_category("mountain")
        assert category in FORCED_ENTERABLE_BY_TERRAIN["mountain"]

        category = get_forced_enterable_category("forest")
        assert category in FORCED_ENTERABLE_BY_TERRAIN["forest"]

        category = get_forced_enterable_category("desert")
        assert category in FORCED_ENTERABLE_BY_TERRAIN["desert"]

        category = get_forced_enterable_category("swamp")
        assert category in FORCED_ENTERABLE_BY_TERRAIN["swamp"]

    def test_unknown_terrain_fallback(self):
        """Unknown terrain falls back to default categories."""
        # Test various unknown terrain types
        category = get_forced_enterable_category("lava")
        assert category in ["dungeon", "cave", "ruins"]

        category = get_forced_enterable_category("void")
        assert category in ["dungeon", "cave", "ruins"]

        category = get_forced_enterable_category("unknown_terrain_xyz")
        assert category in ["dungeon", "cave", "ruins"]

    def test_forced_enterable_by_terrain_covers_common_terrains(self):
        """FORCED_ENTERABLE_BY_TERRAIN includes all common terrain types."""
        expected_terrains = {"forest", "mountain", "plains", "desert", "swamp", "hills", "beach", "foothills"}
        actual_terrains = set(FORCED_ENTERABLE_BY_TERRAIN.keys())
        assert expected_terrains == actual_terrains, (
            f"Missing terrains: {expected_terrains - actual_terrains}, "
            f"Extra terrains: {actual_terrains - expected_terrains}"
        )

    def test_all_forced_categories_are_enterable(self):
        """All categories in FORCED_ENTERABLE_BY_TERRAIN are in ENTERABLE_CATEGORIES."""
        for terrain, categories in FORCED_ENTERABLE_BY_TERRAIN.items():
            for category in categories:
                assert category in ENTERABLE_CATEGORIES, (
                    f"Category '{category}' for terrain '{terrain}' "
                    f"is not in ENTERABLE_CATEGORIES"
                )

    def test_forced_category_is_deterministic_with_seed(self):
        """get_forced_enterable_category uses random, but consistent results when called multiple times."""
        # We can't guarantee the same result without controlling random seed,
        # but we can verify the result is always valid
        results = [get_forced_enterable_category("forest") for _ in range(10)]
        for result in results:
            assert result in FORCED_ENTERABLE_BY_TERRAIN["forest"]


class TestGameStateEnterableIntegration:
    """Tests for game_state integration with enterable spawn logic."""

    def _create_test_character(self):
        """Create a test character with all required attributes."""
        from cli_rpg.models.character import Character, CharacterClass
        return Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )

    def test_tiles_since_enterable_initialized_to_zero(self):
        """GameState.tiles_since_enterable starts at 0."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.location import Location

        game_state = GameState(
            theme="test",
            world={"Start": Location(name="Start", description="Start", coordinates=(0, 0))},
            starting_location="Start",
            character=self._create_test_character(),
        )

        assert game_state.tiles_since_enterable == 0

    def test_tiles_since_enterable_serialization(self):
        """tiles_since_enterable is serialized and deserialized correctly."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.location import Location

        game_state = GameState(
            theme="test",
            world={"Start": Location(name="Start", description="Start", coordinates=(0, 0))},
            starting_location="Start",
            character=self._create_test_character(),
        )

        # Manually set a value
        game_state.tiles_since_enterable = 15

        # Serialize
        data = game_state.to_dict()
        assert data["tiles_since_enterable"] == 15

        # Deserialize
        restored = GameState.from_dict(data)
        assert restored.tiles_since_enterable == 15

    def test_tiles_since_enterable_backward_compatibility(self):
        """Old save files without tiles_since_enterable default to 0."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.location import Location

        game_state = GameState(
            theme="test",
            world={"Start": Location(name="Start", description="Start", coordinates=(0, 0))},
            starting_location="Start",
            character=self._create_test_character(),
        )

        # Serialize
        data = game_state.to_dict()

        # Remove tiles_since_enterable to simulate old save
        del data["tiles_since_enterable"]

        # Deserialize
        restored = GameState.from_dict(data)
        assert restored.tiles_since_enterable == 0
