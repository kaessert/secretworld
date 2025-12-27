"""Tests for WFC ChunkManager integration with GameState.

Tests verify:
1. GameState accepts optional chunk_manager parameter
2. Movement uses WFC terrain when chunk_manager is provided
3. Impassable terrain (water) blocks movement
4. Terrain-aware location generation
5. Persistence of chunk_manager state
"""

import pytest
from unittest.mock import Mock, patch

from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.world import generate_fallback_location
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY, TERRAIN_PASSABLE


@pytest.fixture
def basic_character() -> Character:
    """Create a basic character for testing."""
    return Character(
        name="TestHero",
        character_class=CharacterClass.WARRIOR,
        strength=12,
        dexterity=10,
        intelligence=8,
        charisma=8,
    )


@pytest.fixture
def basic_world() -> dict[str, Location]:
    """Create a minimal world for testing."""
    origin = Location(
        name="Origin",
        description="The starting location",
        coordinates=(0, 0),
    )
    return {"Origin": origin}


@pytest.fixture
def chunk_manager() -> ChunkManager:
    """Create a ChunkManager for testing.

    Note: seed=1 chosen because it produces passable terrain at (0,1)
    which is required for movement tests. WFC output is deterministic
    but terrain distribution varies with penalty configurations.
    """
    return ChunkManager(
        tile_registry=DEFAULT_TILE_REGISTRY,
        world_seed=1,
    )


class TestGameStateWithChunkManager:
    """Tests for GameState with WFC chunk_manager integration."""

    def test_gamestate_with_chunk_manager(
        self, basic_character, basic_world, chunk_manager
    ):
        """Test #1: GameState accepts optional chunk_manager parameter."""
        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
            chunk_manager=chunk_manager,
        )
        assert gs.chunk_manager is chunk_manager
        assert gs.chunk_manager.world_seed == 1

    def test_gamestate_without_chunk_manager(self, basic_character, basic_world):
        """Test #2: GameState works without chunk_manager (backward compat)."""
        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
        )
        assert gs.chunk_manager is None

    def test_move_triggers_chunk_generation(
        self, basic_character, basic_world, chunk_manager
    ):
        """Test #3: Moving to unexplored coords generates terrain via WFC."""
        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
            chunk_manager=chunk_manager,
        )

        # Move north from (0, 0) to (0, 1)
        success, _ = gs.move("north")
        assert success

        # Verify a new location was generated at (0, 1)
        new_location = gs._get_location_by_coordinates((0, 1))
        assert new_location is not None

        # Verify terrain was set on the location
        assert new_location.terrain is not None
        assert new_location.terrain in DEFAULT_TILE_REGISTRY.get_all_tile_names()

    def test_terrain_stored_on_location(
        self, basic_character, basic_world, chunk_manager
    ):
        """Test #4: Generated Location has terrain field from WFC."""
        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
            chunk_manager=chunk_manager,
        )

        # Move north
        success, _ = gs.move("north")
        assert success

        # Get the new location and verify terrain
        new_location = gs._get_location_by_coordinates((0, 1))
        assert new_location is not None
        assert hasattr(new_location, "terrain")
        # Terrain should be one of the valid WFC tiles
        valid_terrains = {"forest", "mountain", "plains", "water", "desert", "swamp", "hills", "beach", "foothills"}
        assert new_location.terrain in valid_terrains

    def test_move_blocks_impassable_terrain(self, basic_character, basic_world):
        """Test #5: Cannot move onto water tiles."""
        # Create a mock chunk_manager that returns water for target coords
        mock_cm = Mock(spec=ChunkManager)
        mock_cm.get_tile_at = Mock(return_value="water")

        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
            chunk_manager=mock_cm,
        )

        # Attempt to move north (should be blocked by water)
        success, message = gs.move("north")
        assert not success
        assert "impassable" in message.lower() or "water" in message.lower()


class TestTerrainAwareLocationGeneration:
    """Tests for terrain-aware fallback location generation."""

    def test_fallback_uses_terrain_type(self):
        """Test #6: generate_fallback_location accepts terrain param."""
        source = Location(
            name="Source",
            description="Source location",
            coordinates=(0, 0),
        )

        # Generate with terrain parameter
        location = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1),
            terrain="forest",
        )

        assert location is not None
        assert location.terrain == "forest"

    def test_location_category_from_terrain(self):
        """Test #7: Location category matches terrain type."""
        source = Location(
            name="Source",
            description="Source location",
            coordinates=(0, 0),
        )

        # Forest terrain should produce forest category
        location = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1),
            terrain="forest",
        )

        assert location.category == "forest"

        # Swamp terrain should produce swamp category
        location2 = generate_fallback_location(
            direction="south",
            source_location=source,
            target_coords=(0, -1),
            terrain="swamp",
        )

        assert location2.category == "swamp"


class TestChunkManagerPersistence:
    """Tests for ChunkManager persistence through GameState."""

    def test_save_includes_chunk_manager(
        self, basic_character, basic_world, chunk_manager
    ):
        """Test #8: to_dict() includes chunk_manager when present."""
        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
            chunk_manager=chunk_manager,
        )

        # Pre-generate a chunk so there's state to save
        chunk_manager.get_or_generate_chunk(0, 0)

        data = gs.to_dict()
        assert "chunk_manager" in data
        assert data["chunk_manager"]["world_seed"] == 1
        assert "chunks" in data["chunk_manager"]

    def test_load_restores_chunk_manager(
        self, basic_character, basic_world, chunk_manager
    ):
        """Test #9: from_dict() restores chunk_manager."""
        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
            chunk_manager=chunk_manager,
        )

        # Generate a chunk
        chunk_manager.get_or_generate_chunk(0, 0)

        # Serialize
        data = gs.to_dict()

        # Deserialize
        restored_gs = GameState.from_dict(data)

        assert restored_gs.chunk_manager is not None
        assert restored_gs.chunk_manager.world_seed == 1

        # Verify chunk was restored
        restored_tile = restored_gs.chunk_manager.get_tile_at(0, 0)
        original_tile = chunk_manager.get_tile_at(0, 0)
        assert restored_tile == original_tile

    def test_load_without_chunk_manager(self, basic_character, basic_world):
        """Test #10: Old saves without chunk_manager load successfully."""
        gs = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Origin",
        )

        # Serialize (no chunk_manager)
        data = gs.to_dict()
        assert "chunk_manager" not in data

        # Deserialize
        restored_gs = GameState.from_dict(data)
        assert restored_gs.chunk_manager is None


class TestWFCDefaultBehavior:
    """Tests for WFC being default behavior."""

    def test_wfc_enabled_by_default_in_start_game(self, basic_character, basic_world):
        """Test: start_game uses WFC by default (use_wfc=True)."""
        # Spec: Replace --wfc flag with --no-wfc so WFC is enabled by default
        import inspect
        from cli_rpg.main import start_game
        sig = inspect.signature(start_game)
        assert sig.parameters['use_wfc'].default is True

    def test_no_wfc_flag_disables_wfc(self):
        """Test: --no-wfc flag sets no_wfc=True."""
        # Spec: Replace --wfc flag with --no-wfc flag
        from cli_rpg.main import parse_args
        args = parse_args(['--no-wfc'])
        assert args.no_wfc is True

    def test_no_wfc_flag_not_set_by_default(self):
        """Test: --no-wfc flag is False by default."""
        # Spec: WFC terrain generation is enabled by default
        from cli_rpg.main import parse_args
        args = parse_args([])
        assert args.no_wfc is False
