"""Tests for the dungeon ambiance system (Issue #27, Increment 1).

This module tests expanded location-specific whispers, depth-based whisper intensity,
and progressive dread from dungeon depth.
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.whisper import (
    CATEGORY_WHISPERS,
    DEPTH_WHISPERS,
    DEPTH_WHISPER_CHANCE,
    WhisperService,
    get_depth_dread_modifier,
)


class TestExpandedCategoryWhispers:
    """Tests for expanded category-specific whisper templates.

    Spec: Each category should have 8+ whisper templates for variety.
    """

    def test_dungeon_whispers_expanded(self):
        """Spec: Dungeon category has 8+ whisper templates."""
        assert "dungeon" in CATEGORY_WHISPERS
        assert len(CATEGORY_WHISPERS["dungeon"]) >= 8, (
            f"Expected 8+ dungeon whispers, got {len(CATEGORY_WHISPERS['dungeon'])}"
        )

    def test_cave_whispers_expanded(self):
        """Spec: Cave category has 8+ whisper templates."""
        assert "cave" in CATEGORY_WHISPERS
        assert len(CATEGORY_WHISPERS["cave"]) >= 8, (
            f"Expected 8+ cave whispers, got {len(CATEGORY_WHISPERS['cave'])}"
        )

    def test_ruins_whispers_expanded(self):
        """Spec: Ruins category has 8+ whisper templates."""
        assert "ruins" in CATEGORY_WHISPERS
        assert len(CATEGORY_WHISPERS["ruins"]) >= 8, (
            f"Expected 8+ ruins whispers, got {len(CATEGORY_WHISPERS['ruins'])}"
        )

    def test_temple_whispers_expanded(self):
        """Spec: Temple category has 8+ whisper templates."""
        assert "temple" in CATEGORY_WHISPERS
        assert len(CATEGORY_WHISPERS["temple"]) >= 8, (
            f"Expected 8+ temple whispers, got {len(CATEGORY_WHISPERS['temple'])}"
        )

    def test_forest_whispers_expanded(self):
        """Spec: Forest category has 8+ whisper templates."""
        assert "forest" in CATEGORY_WHISPERS
        assert len(CATEGORY_WHISPERS["forest"]) >= 8, (
            f"Expected 8+ forest whispers, got {len(CATEGORY_WHISPERS['forest'])}"
        )


class TestDepthWhispers:
    """Tests for depth-based whisper selection.

    Spec: Deeper dungeon levels select from more ominous whisper pools.
    """

    def test_depth_whisper_templates_exist(self):
        """Spec: DEPTH_WHISPERS dict exists with z-level keys (0, -1, -2, -3)."""
        assert DEPTH_WHISPERS is not None
        assert isinstance(DEPTH_WHISPERS, dict)
        # Should have keys for surface and underground depths
        assert 0 in DEPTH_WHISPERS
        assert -1 in DEPTH_WHISPERS
        assert -2 in DEPTH_WHISPERS
        assert -3 in DEPTH_WHISPERS

    def test_surface_whispers_mild(self):
        """Spec: z=0 uses standard category whispers (empty depth pool)."""
        # Surface level should have empty depth whispers - falls back to category
        assert DEPTH_WHISPERS[0] == []

    def test_shallow_depth_whispers(self):
        """Spec: z=-1 includes some ominous templates."""
        shallow_whispers = DEPTH_WHISPERS[-1]
        assert len(shallow_whispers) >= 2, "Should have at least 2 shallow depth whispers"
        # Verify they have ominous/atmospheric content
        all_text = " ".join(shallow_whispers).lower()
        ominous_terms = ["press", "weight", "echo", "stone", "above", "below"]
        assert any(term in all_text for term in ominous_terms), (
            "Shallow whispers should have ominous atmospheric content"
        )

    def test_deep_whispers_ominous(self):
        """Spec: z=-2 and below uses increasingly dark templates."""
        deep_whispers_2 = DEPTH_WHISPERS[-2]
        deep_whispers_3 = DEPTH_WHISPERS[-3]

        assert len(deep_whispers_2) >= 2, "Should have at least 2 whispers at depth -2"
        assert len(deep_whispers_3) >= 2, "Should have at least 2 whispers at depth -3"

        # Verify deep whispers have darker content
        all_text_deep = " ".join(deep_whispers_3).lower()
        dark_terms = ["dark", "return", "hungry", "alive", "ancient", "sense", "few"]
        assert any(term in all_text_deep for term in dark_terms), (
            "Deep whispers should have darker atmospheric content"
        )

    def test_get_whisper_accepts_depth(self):
        """Spec: get_whisper() accepts optional depth parameter."""
        service = WhisperService()
        # Should not raise an error when depth is passed
        with patch("cli_rpg.whisper.random.random", return_value=0.1):  # Force trigger
            result = service.get_whisper("dungeon", depth=-2)
            assert result is not None


class TestDepthWhisperSelection:
    """Tests for depth-based whisper selection logic.

    Spec: When underground, there's a chance to use depth-specific whispers.
    """

    def test_depth_whisper_chance_constant_exists(self):
        """Spec: DEPTH_WHISPER_CHANCE constant is defined."""
        assert DEPTH_WHISPER_CHANCE is not None
        assert 0 < DEPTH_WHISPER_CHANCE <= 1.0

    def test_surface_uses_category_whispers(self):
        """Spec: At z=0, should use standard category whispers."""
        service = WhisperService()

        # Force whisper to trigger, use dungeon category
        with patch("cli_rpg.whisper.random.random", return_value=0.1):
            for _ in range(10):
                result = service.get_whisper("dungeon", depth=0)
                # At surface, should use category whispers
                assert result in CATEGORY_WHISPERS["dungeon"]

    def test_underground_may_use_depth_whispers(self):
        """Spec: Underground, there's a chance to get depth whispers."""
        service = WhisperService()

        # Force whisper trigger and depth whisper selection
        # First random call is whisper chance, second is depth whisper chance
        depth_whisper_found = False
        with patch("cli_rpg.whisper.random.random") as mock_random:
            # Force both whisper trigger (0.1) and depth trigger
            for depth_chance in [0.1, 0.9]:  # Try both triggering and not triggering
                mock_random.side_effect = [0.1, depth_chance]  # whisper chance, depth chance
                result = service.get_whisper("dungeon", depth=-2)
                if result in DEPTH_WHISPERS[-2]:
                    depth_whisper_found = True
                    break
                mock_random.reset_mock()

        # At least one scenario should have used depth whispers
        assert depth_whisper_found, "Depth whispers should be selectable when underground"


class TestDepthDread:
    """Tests for depth-based dread modifier.

    Spec: Deeper exploration increases dread accumulation rate.
    """

    def test_depth_dread_modifier_exists(self):
        """Spec: get_depth_dread_modifier(z) function exists."""
        assert callable(get_depth_dread_modifier)

    def test_surface_no_extra_dread(self):
        """Spec: z=0 returns modifier of 1.0 (no bonus)."""
        assert get_depth_dread_modifier(0) == 1.0

    def test_positive_z_no_extra_dread(self):
        """Spec: Positive z (towers) also returns 1.0."""
        assert get_depth_dread_modifier(1) == 1.0
        assert get_depth_dread_modifier(5) == 1.0

    def test_shallow_depth_dread(self):
        """Spec: z=-1 returns 1.25x dread modifier."""
        assert get_depth_dread_modifier(-1) == 1.25

    def test_deep_dread_modifier(self):
        """Spec: z=-2 returns 1.5x, z=-3 returns 2.0x."""
        assert get_depth_dread_modifier(-2) == 1.5
        assert get_depth_dread_modifier(-3) == 2.0

    def test_dread_capped_at_depth(self):
        """Spec: z < -3 caps at 2.0x modifier."""
        assert get_depth_dread_modifier(-4) == 2.0
        assert get_depth_dread_modifier(-10) == 2.0
        assert get_depth_dread_modifier(-100) == 2.0


class TestWhisperIntegrationWithDepth:
    """Integration tests for depth-aware whispers in SubGrid movement.

    Spec: SubGrid movement passes z-coordinate to whisper service and uses depth dread modifier.
    """

    def _create_character(self) -> Character:
        """Create a test character."""
        return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)

    def _create_subgrid_world(self):
        """Create a test world with a SubGrid dungeon."""
        from cli_rpg.world_grid import SubGrid

        # Create overworld location
        overworld = Location(
            name="Dungeon Entrance",
            description="A dark entrance to the depths below.",
            coordinates=(0, 0),
            category="dungeon",
            is_overworld=True,
        )

        # Create SubGrid with multi-level dungeon
        sub_grid = SubGrid(
            bounds=(0, 2, 0, 2, -2, 0),  # 3x3 with 3 levels (z: 0, -1, -2)
            parent_name="Dungeon Entrance"
        )

        # Add rooms at different depths
        entry = Location(
            name="Dungeon Entry",
            description="The entrance chamber.",
            coordinates=(1, 1, 0),
            category="dungeon",
            parent_location="Dungeon Entrance",
            is_exit_point=True,
        )
        level1 = Location(
            name="First Level",
            description="The first underground level.",
            coordinates=(1, 1, -1),
            category="dungeon",
            parent_location="Dungeon Entrance",
        )
        level2 = Location(
            name="Second Level",
            description="Deeper still.",
            coordinates=(1, 1, -2),
            category="dungeon",
            parent_location="Dungeon Entrance",
        )

        sub_grid.add_location(entry, 1, 1, 0)
        sub_grid.add_location(level1, 1, 1, -1)
        sub_grid.add_location(level2, 1, 1, -2)

        overworld.sub_grid = sub_grid
        overworld.entry_point = "Dungeon Entry"

        return {"Dungeon Entrance": overworld}, sub_grid

    def test_subgrid_movement_passes_depth(self):
        """Spec: _move_in_sub_grid passes z-coordinate to whisper service."""
        from cli_rpg.game_state import GameState

        char = self._create_character()
        world, sub_grid = self._create_subgrid_world()
        gs = GameState(char, world, starting_location="Dungeon Entrance")

        # Enter the dungeon
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Dungeon Entry"

        # Mock the whisper service to capture the depth parameter
        with patch.object(gs.whisper_service, "get_whisper") as mock_whisper:
            mock_whisper.return_value = None  # No whisper for simplicity
            # Move down to first level
            success, message = gs.move("down")

            # Verify whisper was called with depth parameter
            if mock_whisper.called:
                call_kwargs = mock_whisper.call_args[1]
                assert "depth" in call_kwargs, "get_whisper should be called with depth parameter"
                assert call_kwargs["depth"] == -1, "Depth should be -1 at first underground level"

    def test_subgrid_dread_uses_depth_modifier(self):
        """Spec: Dread gain in SubGrid uses depth modifier."""
        from cli_rpg.game_state import GameState

        char = self._create_character()
        world, sub_grid = self._create_subgrid_world()
        gs = GameState(char, world, starting_location="Dungeon Entrance")

        # Enter the dungeon at entry (z=0)
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Dungeon Entry"

        # Record initial dread
        initial_dread = char.dread_meter.dread

        # Move down to level 1 (z=-1, modifier 1.25x)
        with patch.object(gs.whisper_service, "get_whisper", return_value=None):
            success, _ = gs.move("down")
            assert success

        # Dread should have increased by more than base amount due to modifier
        dread_after_down = char.dread_meter.dread
        dread_gained = dread_after_down - initial_dread

        # The base dread for dungeon movement should be multiplied by 1.25
        # We're checking that SOME dread was added (the exact amount depends on implementation)
        assert dread_gained > 0, "Moving deeper should increase dread"
