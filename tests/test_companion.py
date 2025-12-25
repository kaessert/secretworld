"""Tests for Companion model and BondLevel enum."""

import pytest
from cli_rpg.models.companion import Companion, BondLevel


class TestCompanionCreation:
    """Test companion creation and defaults."""

    def test_create_companion_basic(self):
        """Test creating a companion with required fields."""
        # Spec: Companion dataclass with name, description, bond_points, recruited_at
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square"
        )
        assert companion.name == "Elara"
        assert companion.description == "A wandering minstrel"
        assert companion.recruited_at == "Town Square"

    def test_companion_default_bond_is_stranger(self):
        """Test that new companions start at STRANGER bond level (0 points)."""
        # Spec: bond_points default 0, bond_level computed from bond_points
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square"
        )
        assert companion.bond_points == 0
        assert companion.get_bond_level() == BondLevel.STRANGER


class TestBondProgression:
    """Test bond level thresholds and progression."""

    def test_bond_level_thresholds(self):
        """Test that bond levels match thresholds: 0-24=stranger, 25-49=acquaintance, 50-74=trusted, 75-100=devoted."""
        # Spec: Bond levels - STRANGER (0-24), ACQUAINTANCE (25-49), TRUSTED (50-74), DEVOTED (75-100)

        # Test STRANGER range (0-24)
        for points in [0, 12, 24]:
            companion = Companion(
                name="Test", description="Test", recruited_at="Test", bond_points=points
            )
            assert companion.get_bond_level() == BondLevel.STRANGER, f"Expected STRANGER at {points} points"

        # Test ACQUAINTANCE range (25-49)
        for points in [25, 37, 49]:
            companion = Companion(
                name="Test", description="Test", recruited_at="Test", bond_points=points
            )
            assert companion.get_bond_level() == BondLevel.ACQUAINTANCE, f"Expected ACQUAINTANCE at {points} points"

        # Test TRUSTED range (50-74)
        for points in [50, 62, 74]:
            companion = Companion(
                name="Test", description="Test", recruited_at="Test", bond_points=points
            )
            assert companion.get_bond_level() == BondLevel.TRUSTED, f"Expected TRUSTED at {points} points"

        # Test DEVOTED range (75-100)
        for points in [75, 88, 100]:
            companion = Companion(
                name="Test", description="Test", recruited_at="Test", bond_points=points
            )
            assert companion.get_bond_level() == BondLevel.DEVOTED, f"Expected DEVOTED at {points} points"

    def test_add_bond_increases_points(self):
        """Test that add_bond increases bond_points."""
        # Spec: add_bond(amount) adds points
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square"
        )
        assert companion.bond_points == 0

        companion.add_bond(10)
        assert companion.bond_points == 10

        companion.add_bond(5)
        assert companion.bond_points == 15

    def test_add_bond_returns_message_on_level_up(self):
        """Test that add_bond returns a message when bond level increases."""
        # Spec: add_bond returns Optional[str] - message if level changes
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=23
        )
        assert companion.get_bond_level() == BondLevel.STRANGER

        # Add 2 points to cross into ACQUAINTANCE
        message = companion.add_bond(2)
        assert message is not None
        assert "Elara" in message  # Message should mention companion name
        assert companion.get_bond_level() == BondLevel.ACQUAINTANCE

    def test_add_bond_returns_none_when_no_level_change(self):
        """Test that add_bond returns None when no level threshold is crossed."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=10
        )

        message = companion.add_bond(5)
        assert message is None
        assert companion.bond_points == 15
        assert companion.get_bond_level() == BondLevel.STRANGER

    def test_add_bond_caps_at_100(self):
        """Test that bond_points cannot exceed 100."""
        # Spec: bond_points 0-100
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=95
        )

        companion.add_bond(50)  # Try to add more than the cap allows
        assert companion.bond_points == 100  # Should cap at 100

    def test_add_bond_level_up_to_devoted(self):
        """Test level up message when reaching DEVOTED."""
        companion = Companion(
            name="Lyra",
            description="A fierce warrior",
            recruited_at="Castle",
            bond_points=73
        )

        message = companion.add_bond(5)  # Cross into DEVOTED at 75
        assert message is not None
        assert "Lyra" in message


class TestBondDisplay:
    """Test bond display formatting."""

    def test_get_bond_display_format(self):
        """Test that bond display shows level name and visual bar."""
        # Spec: get_bond_display() returns formatted bond bar with level name
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=50
        )

        display = companion.get_bond_display()
        # Should contain the level name
        assert "Trusted" in display or "TRUSTED" in display
        # Should contain some visual indication of progress (bar characters)
        assert any(char in display for char in ["█", "░", "▓", "▒", "|"])


class TestCompanionSerialization:
    """Test companion serialization (to_dict/from_dict)."""

    def test_companion_to_dict(self):
        """Test serialization of companion to dictionary."""
        # Spec: to_dict() for serialization
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=35
        )

        data = companion.to_dict()
        assert data["name"] == "Elara"
        assert data["description"] == "A wandering minstrel"
        assert data["recruited_at"] == "Town Square"
        assert data["bond_points"] == 35

    def test_companion_from_dict(self):
        """Test deserialization of companion from dictionary."""
        # Spec: from_dict() for deserialization
        data = {
            "name": "Lyra",
            "description": "A fierce warrior",
            "recruited_at": "Castle",
            "bond_points": 60
        }

        companion = Companion.from_dict(data)
        assert companion.name == "Lyra"
        assert companion.description == "A fierce warrior"
        assert companion.recruited_at == "Castle"
        assert companion.bond_points == 60
        assert companion.get_bond_level() == BondLevel.TRUSTED

    def test_companion_roundtrip_serialization(self):
        """Test that serialization followed by deserialization preserves all data."""
        original = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=75
        )

        data = original.to_dict()
        restored = Companion.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.recruited_at == original.recruited_at
        assert restored.bond_points == original.bond_points
        assert restored.get_bond_level() == original.get_bond_level()


class TestBondLevelEnum:
    """Test BondLevel enum values."""

    def test_bond_level_values(self):
        """Test that BondLevel enum has expected values."""
        # Ensure enum exists with expected members
        assert BondLevel.STRANGER is not None
        assert BondLevel.ACQUAINTANCE is not None
        assert BondLevel.TRUSTED is not None
        assert BondLevel.DEVOTED is not None

    def test_bond_level_display_names(self):
        """Test that bond levels have user-friendly display names."""
        # Each level should have a displayable value
        assert BondLevel.STRANGER.value is not None
        assert BondLevel.ACQUAINTANCE.value is not None
        assert BondLevel.TRUSTED.value is not None
        assert BondLevel.DEVOTED.value is not None
