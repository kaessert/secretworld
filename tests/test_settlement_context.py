"""Tests for SettlementContext model.

Tests the creation, serialization, and deserialization of SettlementContext,
which caches settlement-level information for character networks, politics,
and trade (Layer 5 in the hierarchy).
"""

from datetime import datetime

import pytest

from cli_rpg.models.settlement_context import SettlementContext


class TestSettlementContextCreation:
    """Tests for SettlementContext creation."""

    # Tests spec: test_create_with_all_fields - all fields specified
    def test_create_with_all_fields(self):
        """Test creation with all fields specified."""
        now = datetime.now()
        ctx = SettlementContext(
            settlement_name="Ironhaven",
            location_coordinates=(5, 10),
            generated_at=now,
            # Character Networks
            notable_families=["House Blackwood", "House Ironsmith"],
            npc_relationships=[
                {"npc_a": "Mayor Gruff", "npc_b": "Blacksmith Thorn", "type": "rivalry", "strength": 3}
            ],
            # Economic Connections
            trade_routes=[
                {"origin": "Ironhaven", "destination": "Portside", "goods": "iron ore", "status": "active"}
            ],
            local_guilds=["Blacksmiths Guild", "Miners Union"],
            market_specialty="iron goods",
            # Political Structure
            government_type="council",
            political_figures=[{"name": "Mayor Gruff", "title": "Mayor", "faction": "Miners Union"}],
            current_tensions=["labor disputes", "resource shortage"],
            # Social Atmosphere
            population_size="town",
            prosperity_level="modest",
            social_issues=["unemployment", "housing shortage"],
        )

        assert ctx.settlement_name == "Ironhaven"
        assert ctx.location_coordinates == (5, 10)
        assert ctx.generated_at == now
        assert ctx.notable_families == ["House Blackwood", "House Ironsmith"]
        assert len(ctx.npc_relationships) == 1
        assert ctx.npc_relationships[0]["type"] == "rivalry"
        assert ctx.trade_routes[0]["destination"] == "Portside"
        assert ctx.local_guilds == ["Blacksmiths Guild", "Miners Union"]
        assert ctx.market_specialty == "iron goods"
        assert ctx.government_type == "council"
        assert ctx.political_figures[0]["name"] == "Mayor Gruff"
        assert ctx.current_tensions == ["labor disputes", "resource shortage"]
        assert ctx.population_size == "town"
        assert ctx.prosperity_level == "modest"
        assert ctx.social_issues == ["unemployment", "housing shortage"]

    # Tests spec: test_create_with_minimal_fields - only required, defaults applied
    def test_create_with_minimal_fields(self):
        """Test creation with only required fields (defaults applied)."""
        ctx = SettlementContext(
            settlement_name="Small Village",
            location_coordinates=(0, 0),
        )

        assert ctx.settlement_name == "Small Village"
        assert ctx.location_coordinates == (0, 0)
        assert ctx.generated_at is None
        # All optional fields should have defaults
        assert ctx.notable_families == []
        assert ctx.npc_relationships == []
        assert ctx.trade_routes == []
        assert ctx.local_guilds == []
        assert ctx.market_specialty == ""
        assert ctx.government_type == ""
        assert ctx.political_figures == []
        assert ctx.current_tensions == []
        assert ctx.population_size == ""
        assert ctx.prosperity_level == ""
        assert ctx.social_issues == []

    # Tests spec: test_create_empty_collections - empty lists/strings work
    def test_create_empty_collections(self):
        """Test creation with explicitly empty collections works."""
        ctx = SettlementContext(
            settlement_name="Empty Town",
            location_coordinates=(-3, 7),
            notable_families=[],
            npc_relationships=[],
            trade_routes=[],
            local_guilds=[],
            market_specialty="",
            government_type="",
            political_figures=[],
            current_tensions=[],
            population_size="",
            prosperity_level="",
            social_issues=[],
        )

        assert ctx.notable_families == []
        assert ctx.npc_relationships == []
        assert ctx.trade_routes == []
        assert ctx.local_guilds == []
        assert ctx.market_specialty == ""
        assert ctx.government_type == ""
        assert ctx.political_figures == []
        assert ctx.current_tensions == []
        assert ctx.population_size == ""
        assert ctx.prosperity_level == ""
        assert ctx.social_issues == []


class TestSettlementContextSerialization:
    """Tests for SettlementContext to_dict serialization."""

    # Tests spec: test_to_dict_with_all_fields - datetime→ISO, tuple→list
    def test_to_dict_with_all_fields(self):
        """Test serialization includes all fields with proper conversions."""
        now = datetime(2025, 1, 15, 12, 30, 45)
        ctx = SettlementContext(
            settlement_name="Ironhaven",
            location_coordinates=(5, 10),
            generated_at=now,
            notable_families=["House Blackwood"],
            npc_relationships=[{"npc_a": "A", "npc_b": "B", "type": "ally", "strength": 2}],
            trade_routes=[{"origin": "A", "destination": "B", "goods": "ore", "status": "active"}],
            local_guilds=["Smiths"],
            market_specialty="metalwork",
            government_type="monarchy",
            political_figures=[{"name": "King", "title": "Ruler", "faction": "Crown"}],
            current_tensions=["rebellion"],
            population_size="city",
            prosperity_level="wealthy",
            social_issues=["inequality"],
        )

        data = ctx.to_dict()

        assert data["settlement_name"] == "Ironhaven"
        assert data["location_coordinates"] == [5, 10]  # Tuple converted to list for JSON
        assert data["generated_at"] == "2025-01-15T12:30:45"  # datetime to ISO string
        assert data["notable_families"] == ["House Blackwood"]
        assert data["npc_relationships"] == [{"npc_a": "A", "npc_b": "B", "type": "ally", "strength": 2}]
        assert data["trade_routes"] == [{"origin": "A", "destination": "B", "goods": "ore", "status": "active"}]
        assert data["local_guilds"] == ["Smiths"]
        assert data["market_specialty"] == "metalwork"
        assert data["government_type"] == "monarchy"
        assert data["political_figures"] == [{"name": "King", "title": "Ruler", "faction": "Crown"}]
        assert data["current_tensions"] == ["rebellion"]
        assert data["population_size"] == "city"
        assert data["prosperity_level"] == "wealthy"
        assert data["social_issues"] == ["inequality"]

    # Tests spec: test_to_dict_with_none_generated_at - handles None timestamp
    def test_to_dict_with_none_generated_at(self):
        """Test serialization with no generated_at timestamp."""
        ctx = SettlementContext(
            settlement_name="Small Village",
            location_coordinates=(0, 0),
            generated_at=None,
        )

        data = ctx.to_dict()

        assert data["generated_at"] is None


class TestSettlementContextDeserialization:
    """Tests for SettlementContext from_dict deserialization."""

    # Tests spec: test_from_dict_with_all_fields - restores all data correctly
    def test_from_dict_with_all_fields(self):
        """Test deserialization with all fields present."""
        data = {
            "settlement_name": "Ironhaven",
            "location_coordinates": [5, 10],
            "generated_at": "2025-01-15T12:30:45",
            "notable_families": ["House Blackwood", "House Ironsmith"],
            "npc_relationships": [{"npc_a": "A", "npc_b": "B", "type": "ally", "strength": 2}],
            "trade_routes": [{"origin": "X", "destination": "Y", "goods": "silk", "status": "blocked"}],
            "local_guilds": ["Merchants"],
            "market_specialty": "textiles",
            "government_type": "theocracy",
            "political_figures": [{"name": "High Priest", "title": "Leader", "faction": "Temple"}],
            "current_tensions": ["heresy"],
            "population_size": "village",
            "prosperity_level": "poor",
            "social_issues": ["famine"],
        }

        ctx = SettlementContext.from_dict(data)

        assert ctx.settlement_name == "Ironhaven"
        assert ctx.location_coordinates == (5, 10)  # List converted back to tuple
        assert ctx.generated_at == datetime(2025, 1, 15, 12, 30, 45)  # ISO string to datetime
        assert ctx.notable_families == ["House Blackwood", "House Ironsmith"]
        assert ctx.npc_relationships == [{"npc_a": "A", "npc_b": "B", "type": "ally", "strength": 2}]
        assert ctx.trade_routes == [{"origin": "X", "destination": "Y", "goods": "silk", "status": "blocked"}]
        assert ctx.local_guilds == ["Merchants"]
        assert ctx.market_specialty == "textiles"
        assert ctx.government_type == "theocracy"
        assert ctx.political_figures == [{"name": "High Priest", "title": "Leader", "faction": "Temple"}]
        assert ctx.current_tensions == ["heresy"]
        assert ctx.population_size == "village"
        assert ctx.prosperity_level == "poor"
        assert ctx.social_issues == ["famine"]

    # Tests spec: test_from_dict_backward_compatible - old saves without new fields load with defaults
    def test_from_dict_backward_compatible(self):
        """Test old saves without optional fields load successfully with defaults."""
        # Simulates an old save file with only required fields
        old_save_data = {
            "settlement_name": "Old Settlement",
            "location_coordinates": [3, 4],
            "generated_at": None,
        }

        ctx = SettlementContext.from_dict(old_save_data)

        # Required fields work
        assert ctx.settlement_name == "Old Settlement"
        assert ctx.location_coordinates == (3, 4)
        assert ctx.generated_at is None
        # All optional fields get defaults
        assert ctx.notable_families == []
        assert ctx.npc_relationships == []
        assert ctx.trade_routes == []
        assert ctx.local_guilds == []
        assert ctx.market_specialty == ""
        assert ctx.government_type == ""
        assert ctx.political_figures == []
        assert ctx.current_tensions == []
        assert ctx.population_size == ""
        assert ctx.prosperity_level == ""
        assert ctx.social_issues == []

    # Tests spec: test_from_dict_with_null_generated_at - handles null timestamp
    def test_from_dict_with_null_generated_at(self):
        """Test deserialization when generated_at is null."""
        data = {
            "settlement_name": "Null Timestamp Town",
            "location_coordinates": [0, 0],
            "generated_at": None,
        }

        ctx = SettlementContext.from_dict(data)

        assert ctx.generated_at is None


class TestSettlementContextDefaultFactory:
    """Tests for SettlementContext.default() factory method."""

    # Tests spec: test_default_creates_valid_context - creates valid instance
    def test_default_creates_valid_context(self):
        """Test default factory creates a valid SettlementContext."""
        ctx = SettlementContext.default("Unnamed Settlement", (5, 10))

        assert ctx.settlement_name == "Unnamed Settlement"
        assert ctx.location_coordinates == (5, 10)
        assert ctx.generated_at is None
        # Should have sensible defaults
        assert isinstance(ctx.notable_families, list)
        assert isinstance(ctx.npc_relationships, list)
        assert isinstance(ctx.trade_routes, list)
        assert isinstance(ctx.local_guilds, list)
        assert isinstance(ctx.market_specialty, str)
        assert isinstance(ctx.government_type, str)
        assert isinstance(ctx.political_figures, list)
        assert isinstance(ctx.current_tensions, list)
        assert isinstance(ctx.population_size, str)
        assert isinstance(ctx.prosperity_level, str)
        assert isinstance(ctx.social_issues, list)

    # Tests spec: test_default_with_different_coordinates - works with various coords
    def test_default_with_different_coordinates(self):
        """Test default factory works with various coordinates."""
        ctx1 = SettlementContext.default("Settlement A", (0, 0))
        ctx2 = SettlementContext.default("Settlement B", (-10, 20))

        assert ctx1.location_coordinates == (0, 0)
        assert ctx2.location_coordinates == (-10, 20)


class TestSettlementContextRoundTrip:
    """Tests for serialization/deserialization round-trip."""

    # Tests spec: test_round_trip_preserves_all_data - to_dict→from_dict preserves everything
    def test_round_trip_preserves_all_data(self):
        """Test that to_dict/from_dict preserves all data."""
        now = datetime(2025, 1, 15, 12, 30, 45)
        original = SettlementContext(
            settlement_name="Complete Settlement",
            location_coordinates=(7, 8),
            generated_at=now,
            notable_families=["House Dragon", "House Phoenix"],
            npc_relationships=[
                {"npc_a": "Lord Dragon", "npc_b": "Lady Phoenix", "type": "alliance", "strength": 5}
            ],
            trade_routes=[
                {"origin": "Complete Settlement", "destination": "Capital", "goods": "gems", "status": "active"}
            ],
            local_guilds=["Jewelers Guild", "Traders Consortium"],
            market_specialty="precious gems",
            government_type="oligarchy",
            political_figures=[
                {"name": "Lord Dragon", "title": "Elder", "faction": "Merchants"},
                {"name": "Lady Phoenix", "title": "Elder", "faction": "Traders"},
            ],
            current_tensions=["succession crisis", "trade war"],
            population_size="city",
            prosperity_level="wealthy",
            social_issues=["class divide", "corruption"],
        )

        data = original.to_dict()
        restored = SettlementContext.from_dict(data)

        assert restored.settlement_name == original.settlement_name
        assert restored.location_coordinates == original.location_coordinates
        assert restored.generated_at == original.generated_at
        assert restored.notable_families == original.notable_families
        assert restored.npc_relationships == original.npc_relationships
        assert restored.trade_routes == original.trade_routes
        assert restored.local_guilds == original.local_guilds
        assert restored.market_specialty == original.market_specialty
        assert restored.government_type == original.government_type
        assert restored.political_figures == original.political_figures
        assert restored.current_tensions == original.current_tensions
        assert restored.population_size == original.population_size
        assert restored.prosperity_level == original.prosperity_level
        assert restored.social_issues == original.social_issues

    def test_round_trip_without_generated_at(self):
        """Test round-trip when generated_at is None."""
        original = SettlementContext(
            settlement_name="No Timestamp",
            location_coordinates=(0, 0),
            generated_at=None,
        )

        data = original.to_dict()
        restored = SettlementContext.from_dict(data)

        assert restored.settlement_name == original.settlement_name
        assert restored.generated_at is None
