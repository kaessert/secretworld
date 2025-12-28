"""Tests for enterable sublocations functionality.

These tests verify that named locations with enterable categories (dungeons,
caves, towns, etc.) can be entered via on-demand SubGrid generation.

Spec: Enterable Sublocations
- ENTERABLE_CATEGORIES constant defines which categories are enterable
- is_enterable_category() helper checks if a category is enterable
- generate_subgrid_for_location() creates SubGrid for enterable locations
- GameState.enter() generates SubGrid on-demand for enterable locations
- Location.get_layered_description() shows "Enter:" prompt for enterable locations
"""

import pytest
from unittest.mock import Mock, MagicMock
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState
from cli_rpg.world_tiles import (
    ENTERABLE_CATEGORIES,
    is_enterable_category,
)
from cli_rpg.ai_world import (
    generate_subgrid_for_location,
    _generate_fallback_interior,
)
from cli_rpg.world_grid import SubGrid


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock()
    return service


@pytest.fixture
def basic_character():
    """Create a basic test character."""
    return Character(
        name="TestHero",
        strength=10,
        dexterity=10,
        intelligence=10,
        charisma=10,
        perception=10,
        luck=10,
    )


@pytest.fixture
def dungeon_location():
    """Create a dungeon location for testing."""
    return Location(
        name="Dark Dungeon",
        description="A foreboding dungeon entrance.",
        coordinates=(1, 0),
        category="dungeon",
        is_overworld=True,
        is_named=True,
    )


@pytest.fixture
def cave_location():
    """Create a cave location for testing."""
    return Location(
        name="Crystal Cave",
        description="A cave with glittering crystals.",
        coordinates=(2, 0),
        category="cave",
        is_overworld=True,
        is_named=True,
    )


@pytest.fixture
def town_location():
    """Create a town location for testing."""
    return Location(
        name="Riverside Town",
        description="A peaceful town by the river.",
        coordinates=(3, 0),
        category="town",
        is_overworld=True,
        is_named=True,
    )


@pytest.fixture
def basic_world(dungeon_location, cave_location, town_location):
    """Create a basic world with enterable locations."""
    town_square = Location(
        name="Town Square",
        description="A bustling town square.",
        coordinates=(0, 0),
        category="town",
        is_overworld=True,
        is_named=True,
    )
    return {
        "Town Square": town_square,
        "Dark Dungeon": dungeon_location,
        "Crystal Cave": cave_location,
        "Riverside Town": town_location,
    }


class TestEnterableCategoriesConstant:
    """Tests for ENTERABLE_CATEGORIES constant.

    Spec: ENTERABLE_CATEGORIES contains expected categories
    """

    def test_enterable_categories_contains_dungeon(self):
        """Verify dungeon is in ENTERABLE_CATEGORIES.

        Spec: Adventure locations: dungeon
        """
        assert "dungeon" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_cave(self):
        """Verify cave is in ENTERABLE_CATEGORIES.

        Spec: Adventure locations: cave
        """
        assert "cave" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_ruins(self):
        """Verify ruins is in ENTERABLE_CATEGORIES.

        Spec: Adventure locations: ruins
        """
        assert "ruins" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_temple(self):
        """Verify temple is in ENTERABLE_CATEGORIES.

        Spec: Adventure locations: temple
        """
        assert "temple" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_town(self):
        """Verify town is in ENTERABLE_CATEGORIES.

        Spec: Settlements: town
        """
        assert "town" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_village(self):
        """Verify village is in ENTERABLE_CATEGORIES.

        Spec: Settlements: village
        """
        assert "village" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_city(self):
        """Verify city is in ENTERABLE_CATEGORIES.

        Spec: Settlements: city
        """
        assert "city" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_settlement(self):
        """Verify settlement is in ENTERABLE_CATEGORIES.

        Spec: Settlements: settlement
        """
        assert "settlement" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_tavern(self):
        """Verify tavern is in ENTERABLE_CATEGORIES.

        Spec: Commercial buildings: tavern
        """
        assert "tavern" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_shop(self):
        """Verify shop is in ENTERABLE_CATEGORIES.

        Spec: Commercial buildings: shop
        """
        assert "shop" in ENTERABLE_CATEGORIES

    def test_enterable_categories_contains_inn(self):
        """Verify inn is in ENTERABLE_CATEGORIES.

        Spec: Commercial buildings: inn
        """
        assert "inn" in ENTERABLE_CATEGORIES


class TestIsEnterableCategory:
    """Tests for is_enterable_category() helper function.

    Spec: is_enterable_category returns correct values
    """

    def test_dungeon_is_enterable(self):
        """Verify dungeon returns True.

        Spec: Dungeon category is enterable
        """
        assert is_enterable_category("dungeon") is True

    def test_cave_is_enterable(self):
        """Verify cave returns True.

        Spec: Cave category is enterable
        """
        assert is_enterable_category("cave") is True

    def test_town_is_enterable(self):
        """Verify town returns True.

        Spec: Town category is enterable
        """
        assert is_enterable_category("town") is True

    def test_temple_is_enterable(self):
        """Verify temple returns True.

        Spec: Temple category is enterable
        """
        assert is_enterable_category("temple") is True

    def test_forest_is_not_enterable(self):
        """Verify forest returns False.

        Spec: Forest category is not enterable (open terrain)
        """
        assert is_enterable_category("forest") is False

    def test_wilderness_is_not_enterable(self):
        """Verify wilderness returns False.

        Spec: Wilderness category is not enterable (open terrain)
        """
        assert is_enterable_category("wilderness") is False

    def test_plains_is_not_enterable(self):
        """Verify plains returns False.

        Spec: Plains category is not enterable (open terrain)
        """
        assert is_enterable_category("plains") is False

    def test_none_is_not_enterable(self):
        """Verify None returns False.

        Spec: None category is not enterable
        """
        assert is_enterable_category(None) is False

    def test_case_insensitive(self):
        """Verify case-insensitive matching.

        Spec: Category matching is case-insensitive
        """
        assert is_enterable_category("DUNGEON") is True
        assert is_enterable_category("Dungeon") is True
        assert is_enterable_category("Town") is True


class TestGenerateSubgridForLocation:
    """Tests for generate_subgrid_for_location() function.

    Spec: generate_subgrid_for_location creates SubGrid
    """

    def test_generates_subgrid_for_dungeon(self, dungeon_location):
        """Verify SubGrid is generated for dungeon.

        Spec: generate_subgrid_for_location creates SubGrid for dungeon
        """
        sub_grid = generate_subgrid_for_location(
            location=dungeon_location,
            ai_service=None,  # Use fallback
            theme="fantasy",
        )

        assert isinstance(sub_grid, SubGrid)
        assert len(sub_grid._by_name) > 0

    def test_generates_subgrid_for_cave(self, cave_location):
        """Verify SubGrid is generated for cave.

        Spec: generate_subgrid_for_location creates SubGrid for cave
        """
        sub_grid = generate_subgrid_for_location(
            location=cave_location,
            ai_service=None,  # Use fallback
            theme="fantasy",
        )

        assert isinstance(sub_grid, SubGrid)
        assert len(sub_grid._by_name) > 0

    def test_generates_subgrid_for_town(self, town_location):
        """Verify SubGrid is generated for town.

        Spec: generate_subgrid_for_location creates SubGrid for town
        """
        sub_grid = generate_subgrid_for_location(
            location=town_location,
            ai_service=None,  # Use fallback
            theme="fantasy",
        )

        assert isinstance(sub_grid, SubGrid)
        assert len(sub_grid._by_name) > 0

    def test_subgrid_has_entry_point(self, dungeon_location):
        """Verify generated SubGrid has is_exit_point location for exit.

        Spec: Generated SubGrid has is_exit_point location
        """
        sub_grid = generate_subgrid_for_location(
            location=dungeon_location,
            ai_service=None,
            theme="fantasy",
        )

        # At least one location should be an exit point
        exit_points = [
            loc for loc in sub_grid._by_name.values()
            if loc.is_exit_point
        ]
        assert len(exit_points) >= 1

    def test_subgrid_parent_name_set(self, dungeon_location):
        """Verify SubGrid parent_name is set correctly.

        Spec: SubGrid parent_name should match parent location
        """
        sub_grid = generate_subgrid_for_location(
            location=dungeon_location,
            ai_service=None,
            theme="fantasy",
        )

        assert sub_grid.parent_name == dungeon_location.name

    def test_boss_placed_in_dungeon_subgrid(self, dungeon_location):
        """Verify boss is placed in furthest room for dungeon SubGrids.

        Spec: Boss is placed in furthest room for dungeon SubGrids
        """
        sub_grid = generate_subgrid_for_location(
            location=dungeon_location,
            ai_service=None,
            theme="fantasy",
        )

        # At least one location should have a boss
        boss_rooms = [
            loc for loc in sub_grid._by_name.values()
            if loc.boss_enemy is not None
        ]
        assert len(boss_rooms) >= 1

    def test_no_boss_in_town_subgrid(self, town_location):
        """Verify no boss is placed in town SubGrids.

        Spec: Towns don't have bosses
        """
        sub_grid = generate_subgrid_for_location(
            location=town_location,
            ai_service=None,
            theme="fantasy",
        )

        # No location should have a boss in town
        boss_rooms = [
            loc for loc in sub_grid._by_name.values()
            if loc.boss_enemy is not None
        ]
        assert len(boss_rooms) == 0


class TestFallbackInteriorGeneration:
    """Tests for _generate_fallback_interior() helper function.

    Spec: Fallback interior generation creates location data
    """

    def test_dungeon_fallback_has_entrance(self, dungeon_location):
        """Verify dungeon fallback includes entrance.

        Spec: Dungeon fallback has entrance room
        """
        interior_data = _generate_fallback_interior(dungeon_location)

        assert len(interior_data) >= 1
        # First room should be at (0, 0)
        assert interior_data[0]["relative_coords"] == (0, 0)

    def test_town_fallback_has_gate(self, town_location):
        """Verify town fallback includes gate.

        Spec: Town fallback has gate/entrance
        """
        interior_data = _generate_fallback_interior(town_location)

        assert len(interior_data) >= 1
        # First room should be at (0, 0)
        assert interior_data[0]["relative_coords"] == (0, 0)

    def test_fallback_includes_multiple_rooms(self, dungeon_location):
        """Verify fallback generates multiple rooms.

        Spec: Fallback creates connected interior layout
        """
        interior_data = _generate_fallback_interior(dungeon_location)

        assert len(interior_data) >= 2


class TestEnterGeneratesSubgridOnDemand:
    """Tests for GameState.enter() on-demand SubGrid generation.

    Spec: enter() generates SubGrid when needed for enterable location
    """

    def test_enter_generates_subgrid_for_dungeon(
        self, basic_character, dungeon_location
    ):
        """Verify enter() generates SubGrid for dungeon without existing SubGrid.

        Spec: enter() generates SubGrid on-demand for enterable location
        """
        world = {
            "Dark Dungeon": dungeon_location,
        }
        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location="Dark Dungeon",
        )

        # SubGrid should not exist yet
        assert dungeon_location.sub_grid is None

        # Enter the dungeon (will generate SubGrid)
        success, message = game_state.enter()

        # SubGrid should now exist
        assert dungeon_location.sub_grid is not None
        assert success is True

    def test_enter_uses_existing_subgrid(self, basic_character, dungeon_location):
        """Verify enter() uses existing SubGrid if already populated.

        Spec: enter() uses existing SubGrid if already populated
        """
        # Pre-create SubGrid
        existing_sub_grid = SubGrid(
            bounds=(-3, 3, -3, 3, -2, 0),
            parent_name=dungeon_location.name,
        )
        entry_loc = Location(
            name="Existing Entry",
            description="An existing entry point.",
            category="dungeon",
            is_exit_point=True,
        )
        existing_sub_grid.add_location(entry_loc, 0, 0)
        dungeon_location.sub_grid = existing_sub_grid
        dungeon_location.entry_point = "Existing Entry"

        world = {"Dark Dungeon": dungeon_location}
        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location="Dark Dungeon",
        )

        # Enter the dungeon
        success, message = game_state.enter()

        # Should use existing SubGrid, not generate new one
        assert dungeon_location.sub_grid is existing_sub_grid
        assert success is True

    def test_enter_fails_for_non_enterable(self, basic_character):
        """Verify enter() fails for non-enterable category locations.

        Spec: enter() fails for non-enterable category locations
        """
        forest_location = Location(
            name="Dense Forest",
            description="A thick forest.",
            coordinates=(0, 0),
            category="forest",
            is_overworld=True,
            is_named=True,
        )

        world = {"Dense Forest": forest_location}
        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location="Dense Forest",
        )

        # Try to enter - should fail
        success, message = game_state.enter()

        assert success is False
        assert "nothing to enter" in message or "open wilderness" in message

    def test_enter_sets_entry_point(self, basic_character, dungeon_location):
        """Verify enter() sets entry_point after generating SubGrid.

        Spec: entry_point is set from is_exit_point location
        """
        world = {"Dark Dungeon": dungeon_location}
        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location="Dark Dungeon",
        )

        # entry_point should not exist yet
        assert dungeon_location.entry_point is None

        # Enter the dungeon
        game_state.enter()

        # entry_point should now be set
        assert dungeon_location.entry_point is not None


class TestLocationDescriptionShowsEnter:
    """Tests for Location.get_layered_description() showing Enter prompt.

    Spec: get_layered_description shows Enter: for enterable locations
    """

    def test_description_shows_enter_for_dungeon(self, dungeon_location):
        """Verify description shows Enter: for dungeon.

        Spec: Shows Enter: for enterable categories without sub_grid
        """
        description = dungeon_location.get_layered_description()

        assert "Enter:" in description
        assert dungeon_location.name in description

    def test_description_shows_enter_for_cave(self, cave_location):
        """Verify description shows Enter: for cave.

        Spec: Shows Enter: for enterable categories without sub_grid
        """
        description = cave_location.get_layered_description()

        assert "Enter:" in description

    def test_description_shows_enter_for_town(self, town_location):
        """Verify description shows Enter: for town.

        Spec: Shows Enter: for enterable categories without sub_grid
        """
        description = town_location.get_layered_description()

        assert "Enter:" in description

    def test_description_no_enter_for_forest(self):
        """Verify description does not show Enter: for forest.

        Spec: Does not show Enter: for non-enterable categories
        """
        forest_location = Location(
            name="Dense Forest",
            description="A thick forest.",
            coordinates=(0, 0),
            category="forest",
            is_overworld=True,
            is_named=True,
        )

        description = forest_location.get_layered_description()

        # Should not have Enter: prompt (forest is not enterable)
        assert "\nEnter:" not in description

    def test_description_shows_entry_point_if_subgrid_exists(self, dungeon_location):
        """Verify description shows entry_point name if SubGrid exists.

        Spec: Shows entry_point name when SubGrid is populated
        """
        # Create SubGrid with entry point
        sub_grid = SubGrid(
            bounds=(-3, 3, -3, 3, -2, 0),
            parent_name=dungeon_location.name,
        )
        entry_loc = Location(
            name="Dungeon Entrance",
            description="The dungeon entrance.",
            category="dungeon",
            is_exit_point=True,
        )
        sub_grid.add_location(entry_loc, 0, 0)
        dungeon_location.sub_grid = sub_grid
        dungeon_location.entry_point = "Dungeon Entrance"

        description = dungeon_location.get_layered_description()

        assert "Enter:" in description
        assert "Dungeon Entrance" in description


class TestEnterableLocationIntegration:
    """Integration tests for the full enterable sublocation flow.

    Spec: Full flow from overworld to interior and back
    """

    def test_full_enter_exit_flow(self, basic_character, dungeon_location):
        """Verify full enter/exit flow works correctly.

        Spec: Player can enter, navigate, and exit enterable locations
        """
        world = {"Dark Dungeon": dungeon_location}
        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location="Dark Dungeon",
        )

        # Enter the dungeon
        success, message = game_state.enter()
        assert success is True
        assert game_state.in_sub_location is True

        # Exit back to overworld
        exit_success, exit_message = game_state.exit_location()
        assert exit_success is True
        assert game_state.in_sub_location is False
        assert game_state.current_location == "Dark Dungeon"
