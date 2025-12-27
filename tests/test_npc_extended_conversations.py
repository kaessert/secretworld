"""Tests for AI-powered NPC extended conversations feature.

Tests the multi-turn contextual conversation system where players can have
extended dialogues with NPCs beyond the initial greeting.
"""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.models.npc import NPC
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState
from cli_rpg.ai_service import AIService, AIGenerationError
from cli_rpg.ai_config import AIConfig


# =============================================================================
# NPC Model Tests
# =============================================================================

class TestNPCConversationHistory:
    """Tests for NPC conversation_history field."""

    def test_npc_has_conversation_history_field(self):
        """NPC has conversation_history: List[dict] defaulting to []."""
        npc = NPC(
            name="Test NPC",
            description="A test NPC for conversations",
            dialogue="Hello there!"
        )
        assert hasattr(npc, 'conversation_history')
        assert npc.conversation_history == []
        assert isinstance(npc.conversation_history, list)

    def test_npc_conversation_history_serialization(self):
        """History persists via to_dict/from_dict."""
        npc = NPC(
            name="Test NPC",
            description="A test NPC for conversations",
            dialogue="Hello there!"
        )
        # Add some conversation history
        npc.conversation_history = [
            {"role": "player", "content": "Hello!"},
            {"role": "npc", "content": "Greetings, traveler!"}
        ]

        # Serialize and deserialize
        data = npc.to_dict()
        restored_npc = NPC.from_dict(data)

        assert restored_npc.conversation_history == npc.conversation_history
        assert len(restored_npc.conversation_history) == 2
        assert restored_npc.conversation_history[0]["role"] == "player"
        assert restored_npc.conversation_history[1]["content"] == "Greetings, traveler!"

    def test_npc_add_conversation_entry(self):
        """add_conversation(role, content) adds entry to history."""
        npc = NPC(
            name="Test NPC",
            description="A test NPC",
            dialogue="Hello!"
        )

        npc.add_conversation("player", "What do you sell?")

        assert len(npc.conversation_history) == 1
        assert npc.conversation_history[0] == {"role": "player", "content": "What do you sell?"}

        npc.add_conversation("npc", "I sell fine potions.")

        assert len(npc.conversation_history) == 2
        assert npc.conversation_history[1] == {"role": "npc", "content": "I sell fine potions."}

    def test_npc_conversation_history_capped_at_10(self):
        """Oldest entries removed when exceeding 10."""
        npc = NPC(
            name="Test NPC",
            description="A test NPC",
            dialogue="Hello!"
        )

        # Add 12 entries
        for i in range(12):
            npc.add_conversation("player", f"Message {i}")

        # Should only keep last 10
        assert len(npc.conversation_history) == 10
        # First entry should be "Message 2" (0 and 1 were removed)
        assert npc.conversation_history[0]["content"] == "Message 2"
        # Last entry should be "Message 11"
        assert npc.conversation_history[-1]["content"] == "Message 11"


# =============================================================================
# AIService Tests
# =============================================================================

class TestAIServiceConversation:
    """Tests for AIService.generate_conversation_response()."""

    @pytest.fixture
    def mock_ai_config(self):
        """Create a mock AI config."""
        return AIConfig(api_key="test-key", enable_caching=False)

    def test_generate_conversation_response_returns_string(self, mock_ai_config):
        """generate_conversation_response() returns string."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Indeed, I have many wares for sale today!"

            service = AIService(mock_ai_config)
            response = service.generate_conversation_response(
                npc_name="Merchant Bob",
                npc_description="A jolly merchant",
                npc_role="merchant",
                theme="fantasy",
                location_name="Market Square",
                conversation_history=[],
                player_input="What do you have for sale?"
            )

            assert isinstance(response, str)
            assert len(response) >= 10

    def test_generate_conversation_response_includes_history(self, mock_ai_config):
        """Prompt includes conversation history."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Yes, I remember! Here's your change."

            service = AIService(mock_ai_config)
            history = [
                {"role": "player", "content": "I'd like to buy a potion"},
                {"role": "npc", "content": "That'll be 10 gold!"}
            ]

            service.generate_conversation_response(
                npc_name="Merchant Bob",
                npc_description="A jolly merchant",
                npc_role="merchant",
                theme="fantasy",
                location_name="Market Square",
                conversation_history=history,
                player_input="Here's the gold."
            )

            # Check that the prompt passed to _call_llm includes history
            call_args = mock_call.call_args[0][0]
            assert "I'd like to buy a potion" in call_args
            assert "That'll be 10 gold!" in call_args

    def test_generate_conversation_response_includes_npc_context(self, mock_ai_config):
        """Prompt includes NPC name/description/role."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Welcome to my humble shop!"

            service = AIService(mock_ai_config)
            service.generate_conversation_response(
                npc_name="Elara the Wise",
                npc_description="An ancient sage with knowing eyes",
                npc_role="quest_giver",
                theme="fantasy",
                location_name="Tower of Knowledge",
                conversation_history=[],
                player_input="Hello"
            )

            call_args = mock_call.call_args[0][0]
            assert "Elara the Wise" in call_args
            assert "ancient sage" in call_args
            assert "quest_giver" in call_args
            assert "fantasy" in call_args
            assert "Tower of Knowledge" in call_args

    def test_generate_conversation_response_truncates_long_responses(self, mock_ai_config):
        """Caps response at 200 chars."""
        with patch.object(AIService, '_call_llm') as mock_call:
            # Return a very long response (300+ chars)
            long_response = "A" * 300
            mock_call.return_value = long_response

            service = AIService(mock_ai_config)
            response = service.generate_conversation_response(
                npc_name="Merchant",
                npc_description="A merchant",
                npc_role="merchant",
                theme="fantasy",
                location_name="Shop",
                conversation_history=[],
                player_input="Hello"
            )

            assert len(response) <= 200

    def test_generate_conversation_response_raises_on_short(self, mock_ai_config):
        """Raises AIGenerationError if < 10 chars."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Hi"  # Only 2 chars

            service = AIService(mock_ai_config)

            with pytest.raises(AIGenerationError):
                service.generate_conversation_response(
                    npc_name="Merchant",
                    npc_description="A merchant",
                    npc_role="merchant",
                    theme="fantasy",
                    location_name="Shop",
                    conversation_history=[],
                    player_input="Hello"
                )


# =============================================================================
# GameState Tests
# =============================================================================

class TestGameStateConversation:
    """Tests for GameState conversation mode."""

    @pytest.fixture
    def basic_game_state(self):
        """Create a basic game state for testing."""
        character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        npc = NPC(
            name="Test Merchant",
            description="A friendly merchant",
            dialogue="Welcome, traveler!"
        )
        location = Location(
            name="Town Square",
            description="A bustling town square",
            coordinates=(0, 0),
            npcs=[npc]
        )
        world = {"Town Square": location}
        return GameState(character, world, starting_location="Town Square")

    def test_game_state_in_conversation_property(self, basic_game_state):
        """is_in_conversation returns True when current_npc set."""
        # Initially not in conversation
        assert basic_game_state.is_in_conversation is False

        # Set current_npc
        npc = basic_game_state.world["Town Square"].npcs[0]
        basic_game_state.current_npc = npc

        assert basic_game_state.is_in_conversation is True

        # Clear current_npc
        basic_game_state.current_npc = None
        assert basic_game_state.is_in_conversation is False

    def test_game_state_conversation_mode_blocks_movement(self, basic_game_state):
        """go returns error when in conversation."""
        # Set up adjacent location
        north_location = Location(
            name="North Road",
            description="A road heading north",
            coordinates=(0, 1)
        )
        basic_game_state.world["North Road"] = north_location
        # Connections are implicit via coordinate adjacency

        # Set current_npc to enter conversation mode
        npc = basic_game_state.world["Town Square"].npcs[0]
        basic_game_state.current_npc = npc

        # Try to move - should fail
        success, message = basic_game_state.move("north")

        assert success is False
        assert "conversation" in message.lower() or "talking" in message.lower()


# =============================================================================
# Main Command Handler Tests
# =============================================================================

class TestConversationCommandHandling:
    """Tests for conversation input handling in main.py."""

    @pytest.fixture
    def game_state_with_npc(self):
        """Create a game state with an NPC for conversation testing."""
        character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        npc = NPC(
            name="Village Elder",
            description="A wise village elder",
            dialogue="Greetings, young one."
        )
        location = Location(
            name="Village",
            description="A peaceful village",
            coordinates=(0, 0),
            npcs=[npc]
        )
        world = {"Village": location}
        gs = GameState(character, world, starting_location="Village")
        gs.current_npc = npc  # In conversation mode
        return gs

    def test_conversation_input_sent_to_ai(self, game_state_with_npc):
        """Non-command input during conversation calls AI."""
        from cli_rpg.main import handle_conversation_input

        # Create a mock AI service
        mock_ai = MagicMock()
        mock_ai.generate_conversation_response.return_value = "I have much wisdom to share."
        game_state_with_npc.ai_service = mock_ai

        # Send a conversation message
        should_continue, message = handle_conversation_input(
            game_state_with_npc,
            "Tell me about the village history"
        )

        assert should_continue is True
        assert "I have much wisdom to share" in message
        mock_ai.generate_conversation_response.assert_called_once()

    def test_conversation_bye_exits(self, game_state_with_npc):
        """'bye' clears current_npc and exits conversation mode."""
        from cli_rpg.main import handle_conversation_input

        assert game_state_with_npc.current_npc is not None

        should_continue, message = handle_conversation_input(
            game_state_with_npc,
            "bye"
        )

        assert should_continue is True
        assert game_state_with_npc.current_npc is None
        assert "goodbye" in message.lower() or "farewell" in message.lower() or "leave" in message.lower()

    def test_conversation_leave_exits(self, game_state_with_npc):
        """'leave' clears current_npc."""
        from cli_rpg.main import handle_conversation_input

        assert game_state_with_npc.current_npc is not None

        should_continue, message = handle_conversation_input(
            game_state_with_npc,
            "leave"
        )

        assert should_continue is True
        assert game_state_with_npc.current_npc is None

    def test_conversation_exit_exits(self, game_state_with_npc):
        """'exit' clears current_npc."""
        from cli_rpg.main import handle_conversation_input

        assert game_state_with_npc.current_npc is not None

        should_continue, message = handle_conversation_input(
            game_state_with_npc,
            "exit"
        )

        assert should_continue is True
        assert game_state_with_npc.current_npc is None

    def test_conversation_adds_to_npc_history(self, game_state_with_npc):
        """Both player input and AI response added to history."""
        from cli_rpg.main import handle_conversation_input

        mock_ai = MagicMock()
        mock_ai.generate_conversation_response.return_value = "Indeed, the village is ancient."
        game_state_with_npc.ai_service = mock_ai

        npc = game_state_with_npc.current_npc
        assert len(npc.conversation_history) == 0

        handle_conversation_input(
            game_state_with_npc,
            "How old is this village?"
        )

        # Should have 2 entries: player input and NPC response
        assert len(npc.conversation_history) == 2
        assert npc.conversation_history[0]["role"] == "player"
        assert npc.conversation_history[0]["content"] == "How old is this village?"
        assert npc.conversation_history[1]["role"] == "npc"
        assert "ancient" in npc.conversation_history[1]["content"]

    def test_conversation_fallback_without_ai(self, game_state_with_npc):
        """Without ai_service, returns 'NPC nods thoughtfully.'"""
        from cli_rpg.main import handle_conversation_input

        # Ensure no AI service
        game_state_with_npc.ai_service = None

        should_continue, message = handle_conversation_input(
            game_state_with_npc,
            "Tell me about the kingdom"
        )

        assert should_continue is True
        assert "nods" in message.lower()
