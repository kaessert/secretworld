"""Tests for terrain-specific map symbols for unnamed locations.

Spec: Show terrain-specific symbols for unnamed locations (is_named=False) on the map,
while preserving letter identifiers only for named locations (is_named=True).
"""

import pytest

from cli_rpg.world_tiles import TERRAIN_MAP_SYMBOLS, get_terrain_symbol
from cli_rpg.models.location import Location
from cli_rpg.map_renderer import render_map


class TestTerrainMapSymbolsConstant:
    """Test TERRAIN_MAP_SYMBOLS constant exists with all terrain types."""

    # Spec: Verify TERRAIN_MAP_SYMBOLS dict exists in world_tiles.py with all 9 terrain types
    def test_terrain_map_symbols_constant_exists(self):
        """TERRAIN_MAP_SYMBOLS dict exists with all 9 terrain types."""
        expected_terrains = {
            "forest", "plains", "hills", "desert", "swamp",
            "beach", "foothills", "mountain", "water"
        }
        assert isinstance(TERRAIN_MAP_SYMBOLS, dict)
        assert set(TERRAIN_MAP_SYMBOLS.keys()) == expected_terrains


class TestGetTerrainSymbol:
    """Test get_terrain_symbol() function."""

    # Spec: Test get_terrain_symbol() returns expected symbol for each terrain
    def test_get_terrain_symbol_returns_correct_symbol(self):
        """get_terrain_symbol() returns correct symbol for each terrain type."""
        expected_symbols = {
            "forest": "T",
            "plains": ".",
            "hills": "n",
            "desert": ":",
            "swamp": "%",
            "beach": ",",
            "foothills": "^",
            "mountain": "M",
            "water": "~",
        }
        for terrain, expected in expected_symbols.items():
            assert get_terrain_symbol(terrain) == expected, f"Wrong symbol for {terrain}"

    # Spec: Unknown terrain returns '.' (plains default)
    def test_get_terrain_symbol_unknown_terrain_returns_default(self):
        """Unknown terrain returns '.' (plains default)."""
        assert get_terrain_symbol("unknown_terrain") == "."
        assert get_terrain_symbol("") == "."
        assert get_terrain_symbol("lava") == "."


class TestUnnamedLocationOnMap:
    """Test unnamed locations show terrain symbols on map."""

    # Spec: Map grid shows terrain symbol (e.g., 'T') for unnamed forest, not letter
    def test_unnamed_location_shows_terrain_symbol_on_map(self):
        """Map grid shows 'T' for unnamed forest, not letter."""
        # Create an unnamed forest location adjacent to player
        unnamed_forest = Location(
            name="Dense Woods",
            description="A forest tile",
            coordinates=(1, 0),
            terrain="forest",
            is_named=False,
        )
        # Create player's current location
        current = Location(
            name="Starting Point",
            description="You are here",
            coordinates=(0, 0),
            terrain="plains",
            is_named=True,
        )
        world = {
            "Starting Point": current,
            "Dense Woods": unnamed_forest,
        }

        map_output = render_map(world, "Starting Point")

        # The map should contain 'T' for the forest terrain, not a letter symbol
        # Check that 'T' appears in the map grid (not in legend)
        lines = map_output.split("\n")
        # Find map grid lines (those with coordinates)
        grid_lines = [l for l in lines if l.strip().startswith("│") and any(c.isdigit() for c in l)]
        grid_text = "\n".join(grid_lines)

        # 'T' should appear in grid (forest terrain symbol)
        assert "T" in grid_text, f"Expected 'T' in grid for unnamed forest. Grid:\n{grid_text}"

        # Legend should NOT have an entry for the unnamed location
        legend_start = map_output.find("Legend:")
        legend_section = map_output[legend_start:] if legend_start != -1 else ""
        assert "Dense Woods" not in legend_section, "Unnamed location should not appear in legend"


class TestNamedLocationOnMap:
    """Test named locations show letter symbols on map."""

    # Spec: Map grid shows letter (A, B...) for named locations
    def test_named_location_shows_letter_on_map(self):
        """Map grid shows letter (A, B...) for named locations."""
        # Create a named location adjacent to player
        named_location = Location(
            name="Riverside Village",
            description="A small village by the river",
            coordinates=(1, 0),
            terrain="plains",
            is_named=True,
            category="town",
        )
        # Create player's current location
        current = Location(
            name="Starting Point",
            description="You are here",
            coordinates=(0, 0),
            terrain="plains",
            is_named=True,
        )
        world = {
            "Starting Point": current,
            "Riverside Village": named_location,
        }

        map_output = render_map(world, "Starting Point")

        # The map should contain a letter (A-Z) for the named location
        lines = map_output.split("\n")
        grid_lines = [l for l in lines if l.strip().startswith("│") and any(c.isdigit() for c in l)]
        grid_text = "\n".join(grid_lines)

        # Check that a letter symbol appears (not terrain symbol '.')
        # Named location at (1,0) should get letter 'A' since it's the first in sorted order
        assert "A" in grid_text or "R" in grid_text, f"Expected letter in grid for named location. Grid:\n{grid_text}"

        # Legend SHOULD have an entry for the named location
        legend_start = map_output.find("Legend:")
        legend_section = map_output[legend_start:] if legend_start != -1 else ""
        assert "Riverside Village" in legend_section, "Named location should appear in legend"


class TestLegend:
    """Test legend behavior for named vs unnamed locations."""

    # Spec: Legend lists only named locations, not terrain descriptions
    def test_legend_excludes_unnamed_locations(self):
        """Legend lists only named locations."""
        unnamed = Location(
            name="Murky Bog",
            description="Swamp terrain",
            coordinates=(0, 1),
            terrain="swamp",
            is_named=False,
        )
        named = Location(
            name="Town Hall",
            description="The town center",
            coordinates=(1, 0),
            terrain="plains",
            is_named=True,
            category="town",
        )
        current = Location(
            name="Starting Point",
            description="You are here",
            coordinates=(0, 0),
            is_named=True,
        )
        world = {
            "Starting Point": current,
            "Murky Bog": unnamed,
            "Town Hall": named,
        }

        map_output = render_map(world, "Starting Point")
        legend_start = map_output.find("Legend:")
        legend_section = map_output[legend_start:] if legend_start != -1 else ""

        # Named location should be in legend
        assert "Town Hall" in legend_section

        # Unnamed location should NOT be in legend
        assert "Murky Bog" not in legend_section

    # Spec: Legend explains terrain symbols (e.g., 'T = forest')
    def test_legend_includes_terrain_symbol_key(self):
        """Legend explains terrain symbols."""
        current = Location(
            name="Starting Point",
            description="You are here",
            coordinates=(0, 0),
            is_named=True,
        )
        unnamed = Location(
            name="Forest Area",
            description="Trees",
            coordinates=(1, 0),
            terrain="forest",
            is_named=False,
        )
        world = {
            "Starting Point": current,
            "Forest Area": unnamed,
        }

        map_output = render_map(world, "Starting Point")

        # Check for terrain symbol key in output
        assert "Terrain:" in map_output or "T=forest" in map_output, \
            f"Expected terrain key in map output. Got:\n{map_output}"


class TestMixedLocations:
    """Test maps with both named and unnamed locations."""

    # Spec: Grid correctly distinguishes named (letters) vs unnamed (terrain symbols)
    def test_mixed_named_unnamed_locations(self):
        """Grid correctly distinguishes named (letters) vs unnamed (terrain symbols)."""
        current = Location(
            name="Starting Point",
            description="You are here",
            coordinates=(0, 0),
            terrain="plains",
            is_named=True,
        )
        # Unnamed locations - should show terrain symbols
        unnamed_forest = Location(
            name="Dense Woods",
            description="Forest",
            coordinates=(-1, 0),
            terrain="forest",
            is_named=False,
        )
        unnamed_mountain = Location(
            name="Rocky Peak",
            description="Mountain",
            coordinates=(0, 1),
            terrain="mountain",
            is_named=False,
        )
        # Named locations - should show letters
        named_village = Location(
            name="Elder Village",
            description="A village",
            coordinates=(1, 0),
            terrain="plains",
            is_named=True,
            category="town",
        )
        named_dungeon = Location(
            name="Dark Cave",
            description="A dungeon",
            coordinates=(0, -1),
            terrain="mountain",
            is_named=True,
            category="dungeon",
        )

        world = {
            "Starting Point": current,
            "Dense Woods": unnamed_forest,
            "Rocky Peak": unnamed_mountain,
            "Elder Village": named_village,
            "Dark Cave": named_dungeon,
        }

        map_output = render_map(world, "Starting Point")

        # Extract grid lines
        lines = map_output.split("\n")
        grid_lines = [l for l in lines if l.strip().startswith("│") and any(c.isdigit() for c in l)]
        grid_text = "\n".join(grid_lines)

        # Terrain symbols for unnamed locations
        assert "T" in grid_text, "Expected 'T' for unnamed forest"
        assert "M" in grid_text, "Expected 'M' for unnamed mountain"

        # Extract legend
        legend_start = map_output.find("Legend:")
        legend_section = map_output[legend_start:] if legend_start != -1 else ""

        # Named locations should be in legend
        assert "Elder Village" in legend_section
        assert "Dark Cave" in legend_section

        # Unnamed locations should NOT be in legend
        assert "Dense Woods" not in legend_section
        assert "Rocky Peak" not in legend_section


class TestWaterSymbol:
    """Test water terrain symbol consistency."""

    # Spec: Water terrain uses existing '~' symbol (already implemented)
    def test_water_symbol_consistent(self):
        """Water terrain uses '~' symbol."""
        assert get_terrain_symbol("water") == "~"
        assert TERRAIN_MAP_SYMBOLS["water"] == "~"
