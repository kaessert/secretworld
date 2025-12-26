"""Tests for Faction model and ReputationLevel enum."""

import pytest
from cli_rpg.models.faction import Faction, ReputationLevel
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState


class TestFactionCreation:
    """Test faction creation and defaults."""

    def test_faction_creation(self):
        """Test creating a faction with name, description, and default reputation=50."""
        # Spec: Faction dataclass with name, description, reputation (1-100 scale)
        faction = Faction(
            name="Town Guard",
            description="The local militia protecting settlements"
        )
        assert faction.name == "Town Guard"
        assert faction.description == "The local militia protecting settlements"
        assert faction.reputation == 50  # Default neutral

    def test_faction_reputation_clamped_high(self):
        """Test that reputation is clamped to max 100."""
        # Spec: Reputation clamped to 1-100
        faction = Faction(
            name="Test Faction",
            description="Test",
            reputation=150  # Over max
        )
        assert faction.reputation == 100

    def test_faction_reputation_clamped_low(self):
        """Test that reputation is clamped to min 1."""
        # Spec: Reputation clamped to 1-100
        faction = Faction(
            name="Test Faction",
            description="Test",
            reputation=-50  # Under min
        )
        assert faction.reputation == 1


class TestReputationLevel:
    """Test reputation level thresholds."""

    def test_get_reputation_level_hostile(self):
        """Test HOSTILE level for reputation 1-19."""
        # Spec: HOSTILE (1-19)
        for rep in [1, 10, 19]:
            faction = Faction(name="Test", description="Test", reputation=rep)
            assert faction.get_reputation_level() == ReputationLevel.HOSTILE, f"Expected HOSTILE at {rep}"

    def test_get_reputation_level_unfriendly(self):
        """Test UNFRIENDLY level for reputation 20-39."""
        # Spec: UNFRIENDLY (20-39)
        for rep in [20, 30, 39]:
            faction = Faction(name="Test", description="Test", reputation=rep)
            assert faction.get_reputation_level() == ReputationLevel.UNFRIENDLY, f"Expected UNFRIENDLY at {rep}"

    def test_get_reputation_level_neutral(self):
        """Test NEUTRAL level for reputation 40-59."""
        # Spec: NEUTRAL (40-59)
        for rep in [40, 50, 59]:
            faction = Faction(name="Test", description="Test", reputation=rep)
            assert faction.get_reputation_level() == ReputationLevel.NEUTRAL, f"Expected NEUTRAL at {rep}"

    def test_get_reputation_level_friendly(self):
        """Test FRIENDLY level for reputation 60-79."""
        # Spec: FRIENDLY (60-79)
        for rep in [60, 70, 79]:
            faction = Faction(name="Test", description="Test", reputation=rep)
            assert faction.get_reputation_level() == ReputationLevel.FRIENDLY, f"Expected FRIENDLY at {rep}"

    def test_get_reputation_level_honored(self):
        """Test HONORED level for reputation 80-100."""
        # Spec: HONORED (80-100)
        for rep in [80, 90, 100]:
            faction = Faction(name="Test", description="Test", reputation=rep)
            assert faction.get_reputation_level() == ReputationLevel.HONORED, f"Expected HONORED at {rep}"


class TestReputationChanges:
    """Test reputation modification methods."""

    def test_add_reputation_increases_points(self):
        """Test that add_reputation increases reputation."""
        # Spec: add_reputation(amount) adds rep
        faction = Faction(name="Test", description="Test", reputation=50)
        faction.add_reputation(10)
        assert faction.reputation == 60

    def test_add_reputation_returns_message_on_level_up(self):
        """Test that add_reputation returns a message when level increases."""
        # Spec: add_reputation returns level-up message if threshold crossed
        faction = Faction(name="Town Guard", description="Test", reputation=58)
        assert faction.get_reputation_level() == ReputationLevel.NEUTRAL

        message = faction.add_reputation(5)  # Cross into FRIENDLY at 60
        assert message is not None
        assert "Town Guard" in message
        assert faction.get_reputation_level() == ReputationLevel.FRIENDLY

    def test_add_reputation_returns_none_when_no_level_change(self):
        """Test that add_reputation returns None when no level threshold is crossed."""
        faction = Faction(name="Test", description="Test", reputation=50)
        message = faction.add_reputation(5)
        assert message is None
        assert faction.reputation == 55

    def test_add_reputation_caps_at_100(self):
        """Test that reputation cannot exceed 100."""
        faction = Faction(name="Test", description="Test", reputation=95)
        faction.add_reputation(50)  # Try to add more than the cap allows
        assert faction.reputation == 100

    def test_reduce_reputation_decreases_points(self):
        """Test that reduce_reputation decreases reputation."""
        # Spec: reduce_reputation(amount) reduces rep
        faction = Faction(name="Test", description="Test", reputation=50)
        faction.reduce_reputation(10)
        assert faction.reputation == 40

    def test_reduce_reputation_returns_message_on_level_down(self):
        """Test that reduce_reputation returns a message when level decreases."""
        # Spec: reduce_reputation returns level-down message if threshold crossed
        faction = Faction(name="Merchant Guild", description="Test", reputation=41)
        assert faction.get_reputation_level() == ReputationLevel.NEUTRAL

        message = faction.reduce_reputation(5)  # Cross into UNFRIENDLY at 39
        assert message is not None
        assert "Merchant Guild" in message
        assert faction.get_reputation_level() == ReputationLevel.UNFRIENDLY

    def test_reduce_reputation_returns_none_when_no_level_change(self):
        """Test that reduce_reputation returns None when no level threshold is crossed."""
        faction = Faction(name="Test", description="Test", reputation=50)
        message = faction.reduce_reputation(5)
        assert message is None
        assert faction.reputation == 45

    def test_reduce_reputation_floors_at_1(self):
        """Test that reputation cannot go below 1."""
        faction = Faction(name="Test", description="Test", reputation=10)
        faction.reduce_reputation(50)  # Try to reduce more than the floor allows
        assert faction.reputation == 1


class TestReputationDisplay:
    """Test reputation display formatting."""

    def test_reputation_display_format(self):
        """Test that reputation display shows level name and visual bar."""
        # Spec: get_reputation_display() returns visual bar like companion bond display
        faction = Faction(name="Town Guard", description="Test", reputation=50)

        display = faction.get_reputation_display()
        # Should contain the level name
        assert "Neutral" in display or "NEUTRAL" in display
        # Should contain some visual indication of progress (bar characters)
        assert any(char in display for char in ["█", "░", "▓", "▒", "|"])


class TestFactionSerialization:
    """Test faction serialization (to_dict/from_dict)."""

    def test_faction_to_dict(self):
        """Test serialization of faction to dictionary."""
        # Spec: to_dict() for serialization
        faction = Faction(
            name="Town Guard",
            description="The local militia protecting settlements",
            reputation=65
        )

        data = faction.to_dict()
        assert data["name"] == "Town Guard"
        assert data["description"] == "The local militia protecting settlements"
        assert data["reputation"] == 65

    def test_faction_from_dict(self):
        """Test deserialization of faction from dictionary."""
        # Spec: from_dict() for deserialization
        data = {
            "name": "Merchant Guild",
            "description": "Traders and shopkeepers",
            "reputation": 75
        }

        faction = Faction.from_dict(data)
        assert faction.name == "Merchant Guild"
        assert faction.description == "Traders and shopkeepers"
        assert faction.reputation == 75
        assert faction.get_reputation_level() == ReputationLevel.FRIENDLY

    def test_faction_roundtrip_serialization(self):
        """Test that serialization followed by deserialization preserves all data."""
        original = Faction(
            name="Thieves Guild",
            description="A shadowy network of rogues",
            reputation=25
        )

        data = original.to_dict()
        restored = Faction.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.reputation == original.reputation
        assert restored.get_reputation_level() == original.get_reputation_level()


class TestReputationLevelEnum:
    """Test ReputationLevel enum values."""

    def test_reputation_level_values(self):
        """Test that ReputationLevel enum has expected values."""
        # Ensure enum exists with expected members
        assert ReputationLevel.HOSTILE is not None
        assert ReputationLevel.UNFRIENDLY is not None
        assert ReputationLevel.NEUTRAL is not None
        assert ReputationLevel.FRIENDLY is not None
        assert ReputationLevel.HONORED is not None

    def test_reputation_level_display_names(self):
        """Test that reputation levels have user-friendly display names."""
        # Each level should have a displayable value
        assert ReputationLevel.HOSTILE.value is not None
        assert ReputationLevel.UNFRIENDLY.value is not None
        assert ReputationLevel.NEUTRAL.value is not None
        assert ReputationLevel.FRIENDLY.value is not None
        assert ReputationLevel.HONORED.value is not None


class TestGameStateFactions:
    """Test faction integration with GameState."""

    def _create_test_game_state(self) -> GameState:
        """Create a minimal GameState for testing."""
        character = Character(
            name="Test",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        world = {
            "Town Square": Location(
                name="Town Square",
                description="A central square",
                connections={"north": "Market"}
            ),
            "Market": Location(
                name="Market",
                description="A busy market",
                connections={"south": "Town Square"}
            )
        }
        return GameState(character, world, "Town Square")

    def test_factions_field_default_empty(self):
        """Test that new GameState has empty factions list by default."""
        # Spec: factions field on GameState, defaults to empty list
        game_state = self._create_test_game_state()
        assert hasattr(game_state, 'factions')
        assert game_state.factions == []

    def test_factions_persistence(self):
        """Test that factions are saved and loaded correctly."""
        # Spec: Factions saved/loaded correctly
        game_state = self._create_test_game_state()
        game_state.factions = [
            Faction(name="Town Guard", description="The local militia", reputation=65),
            Faction(name="Merchant Guild", description="Traders", reputation=40)
        ]

        # Serialize
        data = game_state.to_dict()
        assert "factions" in data
        assert len(data["factions"]) == 2

        # Deserialize
        restored = GameState.from_dict(data)
        assert len(restored.factions) == 2
        assert restored.factions[0].name == "Town Guard"
        assert restored.factions[0].reputation == 65
        assert restored.factions[1].name == "Merchant Guild"
        assert restored.factions[1].reputation == 40

    def test_factions_backward_compat(self):
        """Test that old saves without factions load with empty list."""
        # Spec: Old saves without factions load with empty list
        game_state = self._create_test_game_state()
        data = game_state.to_dict()

        # Remove factions to simulate old save format
        del data["factions"]

        # Deserialize should still work with empty list
        restored = GameState.from_dict(data)
        assert hasattr(restored, 'factions')
        assert restored.factions == []


class TestReputationCommand:
    """Test the reputation command parsing."""

    def test_reputation_command_in_known_commands(self):
        """Test that reputation is a recognized command."""
        # Spec: reputation command to view faction standings
        from cli_rpg.game_state import KNOWN_COMMANDS
        assert "reputation" in KNOWN_COMMANDS

    def test_reputation_alias(self):
        """Test that 'rep' is an alias for 'reputation'."""
        # Spec: reputation and alias 'rep' in command aliases
        from cli_rpg.game_state import parse_command
        cmd, args = parse_command("rep")
        assert cmd == "reputation"
        assert args == []
