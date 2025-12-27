"""Tests for SubGrid integration with districts.

Tests the districts field on SubGrid and serialization of districts.
"""

import pytest

from cli_rpg.world_grid import SubGrid, SUBGRID_BOUNDS, get_subgrid_bounds
from cli_rpg.models.district import District, DistrictType


class TestSubGridBounds:
    """Tests for new SubGrid bounds entries."""

    def test_metropolis_bounds(self):
        """SUBGRID_BOUNDS has metropolis entry with 25x25 size."""
        # Spec: Add `"metropolis": (-12, 12, -12, 12, 0, 0)` (25x25) to SUBGRID_BOUNDS
        bounds = SUBGRID_BOUNDS["metropolis"]
        assert bounds == (-12, 12, -12, 12, 0, 0)
        # Verify 25x25 size
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        assert width == 25
        assert height == 25

    def test_capital_bounds(self):
        """SUBGRID_BOUNDS has capital entry with 33x33 size."""
        # Spec: Add `"capital": (-16, 16, -16, 16, 0, 0)` (33x33) to SUBGRID_BOUNDS
        bounds = SUBGRID_BOUNDS["capital"]
        assert bounds == (-16, 16, -16, 16, 0, 0)
        # Verify 33x33 size
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        assert width == 33
        assert height == 33

    def test_get_subgrid_bounds_metropolis(self):
        """get_subgrid_bounds returns metropolis bounds correctly."""
        bounds = get_subgrid_bounds("metropolis")
        assert bounds == (-12, 12, -12, 12, 0, 0)

    def test_get_subgrid_bounds_capital(self):
        """get_subgrid_bounds returns capital bounds correctly."""
        bounds = get_subgrid_bounds("capital")
        assert bounds == (-16, 16, -16, 16, 0, 0)


class TestSubGridDistricts:
    """Tests for SubGrid districts field."""

    def test_subgrid_has_districts_field(self):
        """SubGrid has districts field defaulting to empty list."""
        # Spec: Add `districts: list[District] = field(default_factory=list)` to SubGrid
        subgrid = SubGrid()
        assert hasattr(subgrid, "districts")
        assert subgrid.districts == []

    def test_subgrid_with_districts(self):
        """SubGrid can store District instances."""
        district = District(
            name="Market Quarter",
            district_type=DistrictType.MARKET,
            description="A bustling market",
            bounds=(-4, 0, -4, 0),
        )

        subgrid = SubGrid()
        subgrid.districts = [district]

        assert len(subgrid.districts) == 1
        assert subgrid.districts[0].name == "Market Quarter"


class TestSubGridDistrictsSerialization:
    """Tests for SubGrid serialization with districts."""

    def test_subgrid_to_dict_includes_districts(self):
        """SubGrid.to_dict includes districts serialized."""
        # Spec: Update SubGrid.to_dict() for district serialization
        district = District(
            name="Temple Quarter",
            district_type=DistrictType.TEMPLE,
            description="Sacred grounds",
            bounds=(0, 4, 0, 4),
            atmosphere="serene",
            prosperity="wealthy",
            notable_features=["Grand Temple"],
        )

        subgrid = SubGrid(parent_name="Great City")
        subgrid.districts = [district]

        data = subgrid.to_dict()

        assert "districts" in data
        assert len(data["districts"]) == 1
        assert data["districts"][0]["name"] == "Temple Quarter"
        assert data["districts"][0]["district_type"] == "Temple"

    def test_subgrid_from_dict_restores_districts(self):
        """SubGrid.from_dict restores districts from serialized data."""
        # Spec: Update SubGrid.from_dict() to restore districts with backward compatibility
        data = {
            "locations": [],
            "bounds": [-8, 8, -8, 8, 0, 0],
            "parent_name": "Capital City",
            "secret_passages": [],
            "districts": [
                {
                    "name": "Noble Quarter",
                    "district_type": "Noble",
                    "description": "Home of aristocracy",
                    "bounds": [0, 8, 0, 8],
                    "atmosphere": "refined",
                    "prosperity": "wealthy",
                    "notable_features": ["Duke's Manor"],
                }
            ],
        }

        subgrid = SubGrid.from_dict(data)

        assert len(subgrid.districts) == 1
        assert subgrid.districts[0].name == "Noble Quarter"
        assert subgrid.districts[0].district_type == DistrictType.NOBLE
        assert subgrid.districts[0].bounds == (0, 8, 0, 8)

    def test_subgrid_districts_serialization_roundtrip(self):
        """SubGrid with districts survives serialization roundtrip."""
        districts = [
            District(
                name="Market District",
                district_type=DistrictType.MARKET,
                description="Commerce central",
                bounds=(-8, -1, -8, -1),
            ),
            District(
                name="Temple District",
                district_type=DistrictType.TEMPLE,
                description="Holy grounds",
                bounds=(1, 8, 1, 8),
            ),
        ]

        original = SubGrid(
            bounds=(-8, 8, -8, 8, 0, 0),
            parent_name="Metropolis",
        )
        original.districts = districts

        data = original.to_dict()
        restored = SubGrid.from_dict(data)

        assert len(restored.districts) == 2
        assert restored.districts[0].name == "Market District"
        assert restored.districts[1].name == "Temple District"

    def test_subgrid_from_dict_backward_compatibility(self):
        """SubGrid.from_dict handles missing districts key (backward compatibility)."""
        # Spec: Backward compatibility - no districts key should default to empty list
        data = {
            "locations": [],
            "bounds": [-5, 5, -5, 5, 0, 0],
            "parent_name": "Old Town",
            "secret_passages": [],
            # No "districts" key - legacy save format
        }

        subgrid = SubGrid.from_dict(data)

        assert subgrid.districts == []

    def test_subgrid_empty_districts_serialization(self):
        """SubGrid with empty districts serializes correctly."""
        subgrid = SubGrid(parent_name="Small Village")

        data = subgrid.to_dict()

        assert data["districts"] == []
