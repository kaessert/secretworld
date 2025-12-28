"""Tests for NPC arc integration with the talk command and dialogue choices.

Spec: Integrate NPC character arcs into the talk command so dialogue interactions
present dialogue choices that modify arc points (Friendly +3, Neutral +1, Aggressive -2).
This enables relationship progression over time, with visual feedback when arc stage changes.

Updated: Now tests the dialogue choice system instead of automatic random +1-3 points.
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


class TestTalkShowsDialogueChoices:
    """Test: Talk command shows dialogue choice prompt."""

    def test_talk_shows_dialogue_choices(self, game_state_with_npc, basic_npc):
        """Talking to an NPC should display dialogue choice options."""
        from cli_rpg.main import handle_exploration_command

        _, output = handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        # Should show dialogue choice options
        assert "[1]" in output
        assert "[2]" in output
        assert "[3]" in output
        assert "Friendly" in output
        assert "Neutral" in output
        assert "Aggressive" in output

    def test_talk_sets_pending_dialogue_choice(self, game_state_with_npc, basic_npc):
        """Talking to an NPC should set pending_dialogue_choice flag."""
        from cli_rpg.main import handle_exploration_command

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        assert game_state_with_npc.pending_dialogue_choice is True


class TestDialogueChoiceInitializesNPCArc:
    """Test: NPCs without arc get one created when dialogue choice is made."""

    def test_dialogue_choice_initializes_npc_arc_if_none(self, game_state_with_npc, basic_npc):
        """Making a dialogue choice should initialize NPC arc if none exists."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        # NPC starts with no arc
        assert basic_npc.arc is None

        # Talk to the NPC
        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])

        # Make a dialogue choice (Friendly = 1)
        handle_conversation_input(game_state_with_npc, "1")

        # NPC should now have an arc
        assert basic_npc.arc is not None
        assert isinstance(basic_npc.arc, NPCArc)


class TestDialogueChoiceRecordsInteraction:
    """Test: Dialogue choice adds DIALOGUE_CHOICE interaction to arc history."""

    def test_dialogue_choice_records_interaction(self, game_state_with_npc, basic_npc):
        """Making a dialogue choice should record a DIALOGUE_CHOICE interaction."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "1")

        # Arc should have one interaction
        assert len(basic_npc.arc.interactions) == 1
        assert basic_npc.arc.interactions[0].interaction_type == InteractionType.DIALOGUE_CHOICE


class TestDialogueChoiceAddsArcPoints:
    """Test: Dialogue choices add correct arc points."""

    def test_friendly_choice_adds_3_points(self, game_state_with_npc, basic_npc):
        """Friendly dialogue choice should add 3 arc points."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "1")  # Friendly

        assert basic_npc.arc.arc_points == 3

    def test_neutral_choice_adds_1_point(self, game_state_with_npc, basic_npc):
        """Neutral dialogue choice should add 1 arc point."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "2")  # Neutral

        assert basic_npc.arc.arc_points == 1

    def test_aggressive_choice_subtracts_2_points(self, game_state_with_npc, basic_npc):
        """Aggressive dialogue choice should subtract 2 arc points."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "3")  # Aggressive

        assert basic_npc.arc.arc_points == -2

    def test_word_input_friendly(self, game_state_with_npc, basic_npc):
        """Word input 'friendly' should work same as '1'."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "friendly")

        assert basic_npc.arc.arc_points == 3


class TestDialogueChoiceUsesGameTimeTimestamp:
    """Test: Interaction timestamp is game_state.game_time.total_hours."""

    def test_dialogue_choice_uses_game_time_timestamp(self, game_state_with_npc, basic_npc):
        """Interaction should use game time for timestamp."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        # Set a specific game time
        game_state_with_npc.game_time.total_hours = 42

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "1")

        assert basic_npc.arc.interactions[0].timestamp == 42


class TestDialogueChoiceDisplaysStageChangeMessage:
    """Test: When arc crosses threshold, output includes stage change message."""

    def test_dialogue_choice_displays_stage_change_message(self, game_state_with_npc, basic_npc):
        """Stage change should be displayed when crossing threshold."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        # Pre-set arc to just below ACQUAINTANCE threshold (25)
        basic_npc.arc = NPCArc(arc_points=24)

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        _, output = handle_conversation_input(game_state_with_npc, "1")  # +3 -> 27

        # Should mention stage change
        assert "Relationship changed" in output
        assert "stranger" in output.lower()
        assert "acquaintance" in output.lower()


class TestArcPersistsAcrossMultipleTalks:
    """Test: Repeated talks accumulate points."""

    def test_arc_persists_across_multiple_talks(self, game_state_with_npc, basic_npc):
        """Multiple talks should accumulate arc points based on choices."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        # Talk and choose friendly (3 times)
        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "1")  # +3
        game_state_with_npc.current_npc = None
        game_state_with_npc.pending_dialogue_choice = False

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "1")  # +3
        game_state_with_npc.current_npc = None
        game_state_with_npc.pending_dialogue_choice = False

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        handle_conversation_input(game_state_with_npc, "1")  # +3

        # Should have accumulated 9 points (3 + 3 + 3)
        assert basic_npc.arc.arc_points == 9
        # Should have 3 interactions recorded
        assert len(basic_npc.arc.interactions) == 3


class TestDialogueChoiceClearsPendingState:
    """Test: Making a choice clears pending_dialogue_choice flag."""

    def test_choice_clears_pending_state(self, game_state_with_npc, basic_npc):
        """Making a dialogue choice should clear pending flag."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        assert game_state_with_npc.pending_dialogue_choice is True

        handle_conversation_input(game_state_with_npc, "1")
        assert game_state_with_npc.pending_dialogue_choice is False


class TestInvalidDialogueInputRepromptsChoices:
    """Test: Invalid input re-displays dialogue choices."""

    def test_invalid_input_reprompts(self, game_state_with_npc, basic_npc):
        """Invalid dialogue input should show choices again."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        _, output = handle_conversation_input(game_state_with_npc, "hello")  # Invalid

        # Should show choices again
        assert "[1]" in output
        assert "[2]" in output
        assert "[3]" in output
        # Should still be pending
        assert game_state_with_npc.pending_dialogue_choice is True


class TestExitClearsPendingChoice:
    """Test: Exiting conversation clears pending dialogue choice."""

    def test_bye_clears_pending_choice(self, game_state_with_npc, basic_npc):
        """Saying 'bye' should clear pending dialogue choice."""
        from cli_rpg.main import handle_exploration_command, handle_conversation_input

        handle_exploration_command(game_state_with_npc, "talk", ["Test", "Merchant"])
        assert game_state_with_npc.pending_dialogue_choice is True

        handle_conversation_input(game_state_with_npc, "bye")
        assert game_state_with_npc.pending_dialogue_choice is False


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
