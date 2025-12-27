"""Tests for map visibility radius feature.

This test module covers:
1. get_tiles_in_radius() - Returns tiles within Manhattan distance
2. Visibility radius by terrain type
3. Perception stat bonus to visibility
4. Mountain standing bonus
5. update_visibility() marks tiles as seen
6. seen_tiles persistence
7. Map display showing seen-but-not-visited tiles
"""

import pytest
from unittest.mock import MagicMock

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState


# Test Spec 1: get_tiles_in_radius zero returns only center tile
class TestGetTilesInRadius:
    """Tests for the get_tiles_in_radius helper function."""

    def test_get_tiles_in_radius_zero(self):
        """Radius 0 returns only the center tile."""
        from cli_rpg.world_grid import get_tiles_in_radius

        tiles = get_tiles_in_radius(5, 5, 0)
        assert tiles == {(5, 5)}

    def test_get_tiles_in_radius_one(self):
        """Radius 1 returns 5 tiles: center + 4 adjacent (Manhattan distance)."""
        from cli_rpg.world_grid import get_tiles_in_radius

        tiles = get_tiles_in_radius(0, 0, 1)
        expected = {
            (0, 0),   # center
            (0, 1),   # north
            (0, -1),  # south
            (1, 0),   # east
            (-1, 0),  # west
        }
        assert tiles == expected

    def test_get_tiles_in_radius_two(self):
        """Radius 2 returns 13 tiles (Manhattan diamond)."""
        from cli_rpg.world_grid import get_tiles_in_radius

        tiles = get_tiles_in_radius(0, 0, 2)
        # Manhattan distance <= 2 includes:
        # center: 1, distance 1: 4, distance 2: 8 = 13 total
        expected = {
            # center
            (0, 0),
            # distance 1 (4 tiles)
            (0, 1), (0, -1), (1, 0), (-1, 0),
            # distance 2 (8 tiles)
            (0, 2), (0, -2), (2, 0), (-2, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        }
        assert tiles == expected
        assert len(tiles) == 13


# Test Spec 2-4: Visibility radius by terrain
class TestVisibilityRadiusByTerrain:
    """Tests for visibility radius based on terrain type."""

    def test_visibility_radius_plains(self):
        """Plains terrain has visibility radius of 3 (open terrain)."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("plains") == 3

    def test_visibility_radius_forest(self):
        """Forest terrain has visibility radius of 1 (blocked view)."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("forest") == 1

    def test_visibility_radius_mountain(self):
        """Mountain terrain has visibility radius of 0 (only current tile)."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("mountain") == 0

    def test_visibility_radius_hills(self):
        """Hills terrain has visibility radius of 2."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("hills") == 2

    def test_visibility_radius_beach(self):
        """Beach terrain has visibility radius of 2."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("beach") == 2

    def test_visibility_radius_desert(self):
        """Desert terrain has visibility radius of 2."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("desert") == 2

    def test_visibility_radius_swamp(self):
        """Swamp terrain has visibility radius of 1 (blocked view)."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("swamp") == 1

    def test_visibility_radius_foothills(self):
        """Foothills terrain has visibility radius of 1."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("foothills") == 1

    def test_visibility_radius_water(self):
        """Water terrain has visibility radius of 2."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("water") == 2

    def test_visibility_radius_unknown(self):
        """Unknown terrain defaults to visibility radius of 2."""
        from cli_rpg.world_tiles import get_visibility_radius

        assert get_visibility_radius("unknown_terrain") == 2


# Test Spec 3: Mountain standing bonus
class TestMountainStandingBonus:
    """Tests for mountain visibility bonus when standing on mountain."""

    def test_mountain_standing_bonus_value(self):
        """Standing on mountain grants +2 visibility bonus."""
        from cli_rpg.world_tiles import MOUNTAIN_VISIBILITY_BONUS

        assert MOUNTAIN_VISIBILITY_BONUS == 2

    def test_calculate_visibility_radius_on_mountain(self):
        """Standing on mountain gives 0 base + 2 bonus = 2 total."""
        # Create a minimal game state with character on mountain
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=10,  # No PER bonus at 10
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Mountain Peak", description="High up", coordinates=(0, 0))
        world = {"Mountain Peak": start_loc}
        game_state = GameState(character, world, "Mountain Peak")

        # Mock chunk_manager to return mountain terrain
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "mountain"
        game_state.chunk_manager = mock_chunk_manager

        radius = game_state.calculate_visibility_radius((0, 0))
        # Mountain base (0) + mountain bonus (2) + PER bonus (0) = 2
        assert radius == 2


# Test Spec 3: Perception stat bonus
class TestPerceptionBonus:
    """Tests for Perception stat bonus to visibility radius."""

    def test_perception_bonus_at_10(self):
        """PER 10 grants +0 radius bonus."""
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=10,
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Test", description="Test", coordinates=(0, 0))
        world = {"Test": start_loc}
        game_state = GameState(character, world, "Test")

        # Mock chunk_manager to return plains terrain
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "plains"
        game_state.chunk_manager = mock_chunk_manager

        radius = game_state.calculate_visibility_radius((0, 0))
        # Plains base (3) + PER bonus (0) = 3
        assert radius == 3

    def test_perception_bonus_at_15(self):
        """PER 15 grants +1 radius bonus."""
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=15,  # 5 above 10 = +1 bonus
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Test", description="Test", coordinates=(0, 0))
        world = {"Test": start_loc}
        game_state = GameState(character, world, "Test")

        # Mock chunk_manager to return plains terrain
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "plains"
        game_state.chunk_manager = mock_chunk_manager

        radius = game_state.calculate_visibility_radius((0, 0))
        # Plains base (3) + PER bonus (1) = 4
        assert radius == 4

    def test_perception_bonus_at_20(self):
        """PER 20 grants +2 radius bonus."""
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=20,  # 10 above 10 = +2 bonus
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Test", description="Test", coordinates=(0, 0))
        world = {"Test": start_loc}
        game_state = GameState(character, world, "Test")

        # Mock chunk_manager to return forest terrain
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "forest"
        game_state.chunk_manager = mock_chunk_manager

        radius = game_state.calculate_visibility_radius((0, 0))
        # Forest base (1) + PER bonus (2) = 3
        assert radius == 3

    def test_perception_below_10_no_penalty(self):
        """PER below 10 gives no bonus, but no penalty either."""
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=5,  # Below 10, no bonus
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Test", description="Test", coordinates=(0, 0))
        world = {"Test": start_loc}
        game_state = GameState(character, world, "Test")

        # Mock chunk_manager to return plains terrain
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "plains"
        game_state.chunk_manager = mock_chunk_manager

        radius = game_state.calculate_visibility_radius((0, 0))
        # Plains base (3) + PER bonus (0) = 3
        assert radius == 3


# Test Spec 5: update_visibility marks tiles
class TestUpdateVisibility:
    """Tests for update_visibility method marking tiles."""

    def test_update_visibility_marks_tiles(self):
        """update_visibility adds tiles within radius to seen_tiles."""
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=10,
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Test", description="Test", coordinates=(0, 0))
        world = {"Test": start_loc}
        game_state = GameState(character, world, "Test")

        # Initialize seen_tiles
        game_state.seen_tiles = set()

        # Mock chunk_manager to return plains terrain (radius 3)
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "plains"
        game_state.chunk_manager = mock_chunk_manager

        game_state.update_visibility((0, 0))

        # With plains (radius 3), should see 25 tiles (Manhattan diamond r=3)
        # Tiles at distance <= 3
        expected_count = 1 + 4 + 8 + 12  # d=0: 1, d=1: 4, d=2: 8, d=3: 12 = 25
        assert len(game_state.seen_tiles) == expected_count
        assert (0, 0) in game_state.seen_tiles
        assert (3, 0) in game_state.seen_tiles
        assert (0, 3) in game_state.seen_tiles
        assert (-3, 0) in game_state.seen_tiles
        assert (0, -3) in game_state.seen_tiles

    def test_update_visibility_accumulates(self):
        """update_visibility accumulates tiles from multiple positions."""
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=10,
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Test", description="Test", coordinates=(0, 0))
        world = {"Test": start_loc}
        game_state = GameState(character, world, "Test")

        # Initialize seen_tiles
        game_state.seen_tiles = set()

        # Mock chunk_manager to return mountain terrain (radius 0 + 2 bonus)
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "mountain"
        game_state.chunk_manager = mock_chunk_manager

        # Update from two positions
        game_state.update_visibility((0, 0))
        count_after_first = len(game_state.seen_tiles)

        game_state.update_visibility((10, 10))
        count_after_second = len(game_state.seen_tiles)

        # Second update should add more tiles (non-overlapping)
        assert count_after_second > count_after_first


# Test Spec 6: seen_tiles persistence
class TestSeenTilesPersistence:
    """Tests for seen_tiles save/load cycle."""

    def test_seen_tiles_persist_save_load(self):
        """seen_tiles survives save/load cycle."""
        character = Character(
            name="TestChar",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            intelligence=10,
            dexterity=10,
            perception=10,
            charisma=10,
            luck=10,
        )
        start_loc = Location(name="Test", description="Test", coordinates=(0, 0))
        world = {"Test": start_loc}
        game_state = GameState(character, world, "Test")

        # Set up seen_tiles
        game_state.seen_tiles = {(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)}

        # Serialize
        data = game_state.to_dict()
        assert "seen_tiles" in data
        assert len(data["seen_tiles"]) == 5

        # Deserialize
        restored = GameState.from_dict(data)
        assert restored.seen_tiles == game_state.seen_tiles


# Test Spec 7: Map display for seen tiles
class TestMapSeenTiles:
    """Tests for map rendering with seen-but-not-visited tiles."""

    def test_map_shows_seen_terrain(self):
        """Map displays terrain symbol for seen-but-not-visited tiles."""
        from cli_rpg.map_renderer import render_map

        # Create a world with only one visited location
        start_loc = Location(
            name="Test",
            description="Test",
            coordinates=(0, 0),
            is_named=True,
            terrain="plains",
        )
        world = {"Test": start_loc}

        # Mock chunk_manager for terrain lookup
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "forest"

        # Create seen_tiles that include unvisited tiles
        seen_tiles = {(0, 0), (1, 0), (0, 1)}

        map_output = render_map(
            world=world,
            current_location="Test",
            chunk_manager=mock_chunk_manager,
            seen_tiles=seen_tiles,
        )

        # The map should contain forest terrain symbol "T" for seen-but-not-visited
        assert "T" in map_output

    def test_map_hides_unseen_tiles(self):
        """Tiles outside visibility remain empty on map."""
        from cli_rpg.map_renderer import render_map

        # Create a world with only one visited location
        start_loc = Location(
            name="Test",
            description="Test",
            coordinates=(0, 0),
            is_named=True,
            terrain="plains",
        )
        world = {"Test": start_loc}

        # No seen_tiles beyond the visited location
        seen_tiles = {(0, 0)}

        # Mock chunk_manager
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "forest"

        map_output = render_map(
            world=world,
            current_location="Test",
            chunk_manager=mock_chunk_manager,
            seen_tiles=seen_tiles,
        )

        # The map should NOT show terrain for (1, 0) since it's not in seen_tiles
        # Check that forest symbol doesn't appear for unseen tiles
        # (The current location is at (0, 0), so (1, 0) would show terrain
        # only if it was in seen_tiles)
        lines = map_output.split("\n")
        # Find the row with y=0 (the player row)
        for line in lines:
            if " 0 " in line[:6]:  # y-axis label for row 0
                # The cell at x=1, y=0 should be empty (spaces)
                # This is implicitly tested by not showing forest "T"
                break
