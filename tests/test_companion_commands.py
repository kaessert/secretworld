"""Tests for companions and recruit commands."""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.companion import Companion, BondLevel
from cli_rpg.game_state import GameState
from cli_rpg.main import handle_exploration_command


def create_test_game_state(
    npcs=None,
    companions=None
):
    """Create a minimal game state for testing."""
    character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
    location = Location(
        name="Town Square",
        description="A bustling town center",
        connections={"north": "Forest"},
        npcs=npcs or [],
        coordinates=(0, 0)
    )
    world = {"Town Square": location}
    game_state = GameState(character, world, "Town Square")

    # Add companions if provided
    if companions:
        game_state.companions = companions

    return game_state


class TestCompanionsCommand:
    """Tests for the 'companions' command."""

    def test_companions_command_no_companions(self):
        """Test companions command shows 'no companions' message when party is empty."""
        # Spec: Show "No companions in your party." if empty
        game_state = create_test_game_state()
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "companions", [])

        assert success is True
        assert "no companions" in message.lower() or "No companions" in message

    def test_companions_command_with_one_companion(self):
        """Test companions command shows single companion with bond display."""
        # Spec: List each companion with bond display
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=30
        )
        game_state = create_test_game_state(companions=[companion])

        success, message = handle_exploration_command(game_state, "companions", [])

        assert success is True
        assert "Elara" in message
        # Should show bond information
        assert "Acquaintance" in message or "acquaintance" in message or "Bond" in message

    def test_companions_command_with_multiple_companions(self):
        """Test companions command shows all companions."""
        companions = [
            Companion(
                name="Elara",
                description="A wandering minstrel",
                recruited_at="Town Square",
                bond_points=30
            ),
            Companion(
                name="Gareth",
                description="A retired soldier",
                recruited_at="Barracks",
                bond_points=75
            ),
        ]
        game_state = create_test_game_state(companions=companions)

        success, message = handle_exploration_command(game_state, "companions", [])

        assert success is True
        assert "Elara" in message
        assert "Gareth" in message


class TestRecruitCommand:
    """Tests for the 'recruit' command."""

    def test_recruit_no_npc_specified(self):
        """Test recruit command without NPC name shows error."""
        # Spec: recruit command needs an NPC name argument
        game_state = create_test_game_state()

        success, message = handle_exploration_command(game_state, "recruit", [])

        assert success is True
        assert "recruit" in message.lower() or "specify" in message.lower() or "who" in message.lower()

    def test_recruit_npc_not_found(self):
        """Test recruit command with nonexistent NPC shows error."""
        # Spec: Find NPC by name in current location
        npc = NPC(name="Marcus", description="A blacksmith", dialogue="Hello!")
        game_state = create_test_game_state(npcs=[npc])

        success, message = handle_exploration_command(game_state, "recruit", ["NonExistent"])

        assert success is True
        assert "not" in message.lower() or "find" in message.lower() or "don't see" in message.lower()

    def test_recruit_npc_not_recruitable(self):
        """Test recruit command on non-recruitable NPC shows error."""
        # Spec: Check is_recruitable flag
        npc = NPC(
            name="Marcus",
            description="A blacksmith",
            dialogue="Hello!",
            is_recruitable=False  # Not recruitable
        )
        game_state = create_test_game_state(npcs=[npc])

        success, message = handle_exploration_command(game_state, "recruit", ["Marcus"])

        assert success is True
        assert "cannot" in message.lower() or "won't" in message.lower() or "not" in message.lower()

    def test_recruit_success_adds_companion(self):
        """Test successful recruit adds companion to party."""
        # Spec: Create Companion from NPC data, add to game_state.companions
        npc = NPC(
            name="Elara",
            description="A wandering minstrel",
            dialogue="I'd love to join you!",
            is_recruitable=True
        )
        game_state = create_test_game_state(npcs=[npc])
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "recruit", ["Elara"])

        assert success is True
        assert len(game_state.companions) == 1
        companion = game_state.companions[0]
        assert companion.name == "Elara"
        assert companion.description == "A wandering minstrel"
        assert companion.recruited_at == "Town Square"
        assert companion.bond_points == 0  # Starts as stranger

    def test_recruit_already_in_party(self):
        """Test recruiting an NPC that's already in party shows error."""
        npc = NPC(
            name="Elara",
            description="A wandering minstrel",
            dialogue="Hello!",
            is_recruitable=True
        )
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square"
        )
        game_state = create_test_game_state(npcs=[npc], companions=[companion])

        success, message = handle_exploration_command(game_state, "recruit", ["Elara"])

        assert success is True
        assert "already" in message.lower()
        # Should still only have one companion
        assert len(game_state.companions) == 1

    def test_recruit_success_message(self):
        """Test recruit command returns success message."""
        # Spec: Return success message
        npc = NPC(
            name="Elara",
            description="A wandering minstrel",
            dialogue="I'd love to join you!",
            is_recruitable=True
        )
        game_state = create_test_game_state(npcs=[npc])
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "recruit", ["Elara"])

        assert success is True
        assert "Elara" in message
        # Should indicate successful recruitment
        assert "join" in message.lower() or "recruit" in message.lower() or "party" in message.lower()

    def test_recruit_case_insensitive(self):
        """Test recruit command is case-insensitive for NPC name."""
        npc = NPC(
            name="Elara",
            description="A wandering minstrel",
            dialogue="Hello!",
            is_recruitable=True
        )
        game_state = create_test_game_state(npcs=[npc])
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "recruit", ["elara"])

        assert success is True
        assert len(game_state.companions) == 1
        assert game_state.companions[0].name == "Elara"


class TestDismissCommand:
    """Tests for the 'dismiss' command."""

    def test_dismiss_no_companion_specified(self):
        """Test dismiss command without companion name shows error."""
        game_state = create_test_game_state()
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "dismiss", [])

        assert success is True
        assert "dismiss" in message.lower() or "specify" in message.lower()

    def test_dismiss_companion_not_in_party(self):
        """Test dismiss command with nonexistent companion shows error."""
        game_state = create_test_game_state()
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "dismiss", ["Elara"])

        assert success is True
        assert "no companion" in message.lower() or "not" in message.lower()

    def test_dismiss_success_removes_companion(self):
        """Test successful dismiss removes companion from party."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=30
        )
        game_state = create_test_game_state(companions=[companion])

        success, message = handle_exploration_command(game_state, "dismiss", ["Elara"])

        assert success is True
        assert len(game_state.companions) == 0
        assert "left" in message.lower() or "dismiss" in message.lower()

    def test_dismiss_case_insensitive(self):
        """Test dismiss command is case-insensitive."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square"
        )
        game_state = create_test_game_state(companions=[companion])

        success, message = handle_exploration_command(game_state, "dismiss", ["elara"])

        assert success is True
        assert len(game_state.companions) == 0


class TestCompanionsInKnownCommands:
    """Test that companions, recruit, and dismiss are in KNOWN_COMMANDS."""

    def test_companions_in_known_commands(self):
        """Test that 'companions' is a recognized command."""
        from cli_rpg.game_state import KNOWN_COMMANDS
        assert "companions" in KNOWN_COMMANDS

    def test_recruit_in_known_commands(self):
        """Test that 'recruit' is a recognized command."""
        from cli_rpg.game_state import KNOWN_COMMANDS
        assert "recruit" in KNOWN_COMMANDS

    def test_dismiss_in_known_commands(self):
        """Test that 'dismiss' is a recognized command."""
        from cli_rpg.game_state import KNOWN_COMMANDS
        assert "dismiss" in KNOWN_COMMANDS
