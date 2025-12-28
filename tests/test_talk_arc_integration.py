"""Tests for NPC arc integration with the talk command.

Spec: Integrate NPC character arcs into the talk command so dialogue interactions
record TALKED interactions and modify arc points (1-3 per conversation). This enables
relationship progression over time, with visual feedback when arc stage changes.
"""

import pytest
from unittest.mock import patch

from cli_rpg.models.npc import NPC
from cli_rpg.models.npc_arc import NPCArc, NPCArcStage, InteractionType
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState


@pytest.fixture
def basic_npc():
    """Create a basic NPC for testing."""
    return NPC(
        name="Test Merchant",
        description="A friendly merchant for testing.",
        dialogue="Hello, traveler!",
    )


@pytest.fixture
def npc_with_arc():
    """Create an NPC with an existing arc."""
    npc = NPC(
        name="Old Friend",
        description="An old friend from your past.",
        dialogue="It's good to see you again.",
    )
    npc.arc = NPCArc(arc_points=30)  # ACQUAINTANCE stage
    return npc


@pytest.fixture
def game_state_with_npc(basic_npc):
    """Create a GameState with an NPC in the current location."""
    from cli_rpg.models.character import Character, CharacterClass

    character = Character(
        name="Hero",
        strength=10,
        dexterity=10,
        intelligence=10,
        character_class=CharacterClass.WARRIOR,
    )
    location = Location(
        name="Test Town",
        description="A quiet test town.",
        coordinates=(0, 0),
        npcs=[basic_npc],
    )
    world = {"Test Town": location}
    gs = GameState(
        character=character,
        world=world,
        starting_location="Test Town",
    )
    return gs


class TestTalkInitializesNPCArc:
    """Test: NPCs without arc get one created on first talk."""

    def test_talk_initializes_npc_arc_if_none(self, game_state_with_npc, basic_npc):
        """Talking to an NPC without an arc should initialize one."""
        from cli_rpg.main import handle_exploration_command

        # NPC starts with no arc
        assert basic_npc.arc is None

        # Talk to the NPC
        with patch("random.randint", return_value=2):  # Fix random for predictability
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        # NPC should now have an arc
        assert basic_npc.arc is not None
        assert isinstance(basic_npc.arc, NPCArc)


class TestTalkRecordsInteraction:
    """Test: Talking adds TALKED interaction to arc history."""

    def test_talk_records_talked_interaction(self, game_state_with_npc, basic_npc):
        """Talking should record a TALKED interaction."""
        from cli_rpg.main import handle_exploration_command

        with patch("random.randint", return_value=2):
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        # Arc should have one interaction
        assert len(basic_npc.arc.interactions) == 1
        assert basic_npc.arc.interactions[0].interaction_type == InteractionType.TALKED


class TestTalkAddsArcPoints:
    """Test: Talking increases arc_points by 1-3."""

    def test_talk_adds_arc_points_minimum(self, game_state_with_npc, basic_npc):
        """Talking should add at least 1 arc point."""
        from cli_rpg.main import handle_exploration_command

        with patch("random.randint", return_value=1):
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        assert basic_npc.arc.arc_points == 1

    def test_talk_adds_arc_points_maximum(self, game_state_with_npc, basic_npc):
        """Talking should add at most 3 arc points."""
        from cli_rpg.main import handle_exploration_command

        with patch("random.randint", return_value=3):
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        assert basic_npc.arc.arc_points == 3


class TestTalkUsesGameTimeTimestamp:
    """Test: Interaction timestamp is game_state.game_time.total_hours."""

    def test_talk_uses_game_time_timestamp(self, game_state_with_npc, basic_npc):
        """Interaction should use game time for timestamp."""
        from cli_rpg.main import handle_exploration_command

        # Set a specific game time
        game_state_with_npc.game_time.total_hours = 42

        with patch("random.randint", return_value=2):
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        assert basic_npc.arc.interactions[0].timestamp == 42


class TestTalkDisplaysStageChangeMessage:
    """Test: When arc crosses threshold, output includes stage change message."""

    def test_talk_displays_stage_change_message(self, game_state_with_npc, basic_npc):
        """Stage change should be displayed when crossing threshold."""
        from cli_rpg.main import handle_exploration_command

        # Pre-set arc to just below ACQUAINTANCE threshold (25)
        basic_npc.arc = NPCArc(arc_points=24)

        with patch("random.randint", return_value=2):  # Will push to 26, crossing threshold
            _, output = handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        # Should mention stage change
        assert "Relationship changed" in output
        assert "stranger" in output.lower()
        assert "acquaintance" in output.lower()


class TestArcPersistsAcrossMultipleTalks:
    """Test: Repeated talks accumulate points."""

    def test_arc_persists_across_multiple_talks(self, game_state_with_npc, basic_npc):
        """Multiple talks should accumulate arc points."""
        from cli_rpg.main import handle_exploration_command

        # Talk multiple times with fixed random value
        with patch("random.randint", return_value=2):
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
            # Exit conversation first
            game_state_with_npc.current_npc = None
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
            game_state_with_npc.current_npc = None
            handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        # Should have accumulated 6 points (2 + 2 + 2)
        assert basic_npc.arc.arc_points == 6
        # Should have 3 interactions recorded
        assert len(basic_npc.arc.interactions) == 3


class TestArcStageAffectsGreeting:
    """Test: Arc stage modifies NPC greeting (TRUSTED/DEVOTED get warmer greetings)."""

    def test_devoted_npc_has_warm_greeting(self):
        """NPCs at DEVOTED stage should have warm arc-based greeting."""
        npc = NPC(
            name="Best Friend",
            description="Your closest companion.",
            dialogue="Hey there.",
            greetings=["Hey there.", "What's up?"],
        )
        npc.arc = NPCArc(arc_points=80)  # DEVOTED

        arc_greeting = npc.get_arc_greeting_modifier()
        assert arc_greeting is not None
        assert "dear friend" in arc_greeting.lower() or "pleasure" in arc_greeting.lower()

    def test_trusted_npc_has_friendly_greeting(self):
        """NPCs at TRUSTED stage should have friendly arc-based greeting."""
        npc = NPC(
            name="Good Ally",
            description="A reliable ally.",
            dialogue="Hello.",
        )
        npc.arc = NPCArc(arc_points=55)  # TRUSTED

        arc_greeting = npc.get_arc_greeting_modifier()
        assert arc_greeting is not None
        assert "good to see you" in arc_greeting.lower()

    def test_acquaintance_npc_has_casual_greeting(self):
        """NPCs at ACQUAINTANCE stage should have casual arc-based greeting."""
        npc = NPC(
            name="Casual Contact",
            description="Someone you've met a few times.",
            dialogue="Hi.",
        )
        npc.arc = NPCArc(arc_points=30)  # ACQUAINTANCE

        arc_greeting = npc.get_arc_greeting_modifier()
        assert arc_greeting is not None
        assert "you again" in arc_greeting.lower()

    def test_stranger_npc_has_no_arc_greeting(self):
        """NPCs at STRANGER stage should not have arc-based greeting."""
        npc = NPC(
            name="New Face",
            description="Someone you just met.",
            dialogue="Who are you?",
        )
        npc.arc = NPCArc(arc_points=10)  # STRANGER

        arc_greeting = npc.get_arc_greeting_modifier()
        assert arc_greeting is None

    def test_no_arc_has_no_greeting_modifier(self):
        """NPCs without an arc should not have arc-based greeting."""
        npc = NPC(
            name="Unknown",
            description="A mysterious stranger.",
            dialogue="...",
        )
        # No arc set

        arc_greeting = npc.get_arc_greeting_modifier()
        assert arc_greeting is None

    def test_get_greeting_uses_arc_greeting_when_high_stage(self):
        """get_greeting should use arc greeting for high relationship stages."""
        npc = NPC(
            name="Trusted Ally",
            description="Someone you trust deeply.",
            dialogue="Default dialogue.",
            greetings=["Normal greeting 1", "Normal greeting 2"],
        )
        npc.arc = NPCArc(arc_points=60)  # TRUSTED

        greeting = npc.get_greeting()
        # Should return the arc-based greeting, not the normal one
        assert "good to see you" in greeting.lower()
