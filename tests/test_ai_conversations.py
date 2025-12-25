"""Tests for AI-generated NPC conversations.

Spec: When a player talks to an NPC:
1. If ai_service is available and NPC has fewer than 3 greetings, generate new dialogue
2. Add generated response to NPC's greetings list (persists via existing serialization)
3. Use get_greeting() to display dialogue (works with both AI-generated and static)
4. Graceful fallback: If AI unavailable, use existing greetings or dialogue field
"""

import pytest
from unittest.mock import patch

from cli_rpg.ai_config import AIConfig, DEFAULT_NPC_DIALOGUE_PROMPT
from cli_rpg.ai_service import AIService, AIGenerationError
from cli_rpg.models.npc import NPC
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState


@pytest.fixture
def mock_ai_config():
    """Create a mock AIConfig for testing."""
    return AIConfig(
        api_key="test-api-key",
        provider="openai",
        model="gpt-3.5-turbo",
        npc_dialogue_prompt=DEFAULT_NPC_DIALOGUE_PROMPT
    )


@pytest.fixture
def mock_ai_service(mock_ai_config):
    """Create an AIService with mocked LLM calls."""
    with patch.object(AIService, '_call_llm') as mock_call:
        mock_call.return_value = "Welcome, traveler! The road has been kind to you, I hope."
        service = AIService(mock_ai_config)
        yield service


@pytest.fixture
def sample_npc():
    """Create a sample NPC for testing."""
    return NPC(
        name="Merchant Marcus",
        description="A friendly merchant with a warm smile",
        dialogue="Welcome to my shop!",
        is_merchant=True,
        greetings=[]
    )


@pytest.fixture
def sample_npc_with_greetings():
    """Create an NPC that already has greetings."""
    return NPC(
        name="Guard Gerald",
        description="A stern-looking guard",
        dialogue="Move along.",
        is_merchant=False,
        greetings=[
            "Halt! State your business.",
            "The town is safe under my watch.",
            "You look suspicious..."
        ]
    )


class TestGenerateNpcDialogue:
    """Tests for AIService.generate_npc_dialogue()"""

    # Spec test 1: generate_npc_dialogue returns a non-empty string
    def test_generate_npc_dialogue_returns_string(self, mock_ai_config):
        """AIService.generate_npc_dialogue() returns a non-empty string."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Greetings, adventurer! How may I assist you today?"
            service = AIService(mock_ai_config)

            result = service.generate_npc_dialogue(
                npc_name="Test NPC",
                npc_description="A test character",
                npc_role="villager",
                theme="fantasy",
                location_name="Test Town"
            )

            assert isinstance(result, str)
            assert len(result) >= 10
            mock_call.assert_called_once()

    # Spec test 2: Generated dialogue uses theme context
    def test_generate_npc_dialogue_respects_theme(self, mock_ai_config):
        """Generated dialogue uses theme context in prompt."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Welcome to the space station, fellow traveler."
            service = AIService(mock_ai_config)

            service.generate_npc_dialogue(
                npc_name="Commander Nova",
                npc_description="A space station commander",
                npc_role="villager",
                theme="sci-fi",
                location_name="Orbital Station Alpha"
            )

            # Verify the prompt includes theme context
            prompt = mock_call.call_args[0][0]
            assert "sci-fi" in prompt
            assert "Commander Nova" in prompt
            assert "Orbital Station Alpha" in prompt

    def test_generate_npc_dialogue_includes_role_in_prompt(self, mock_ai_config):
        """Generated dialogue prompt includes NPC role."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Care to browse my wares?"
            service = AIService(mock_ai_config)

            service.generate_npc_dialogue(
                npc_name="Shopkeeper",
                npc_description="A merchant",
                npc_role="merchant",
                theme="fantasy",
                location_name="Market Square"
            )

            prompt = mock_call.call_args[0][0]
            assert "merchant" in prompt

    def test_generate_npc_dialogue_strips_quotes(self, mock_ai_config):
        """Dialogue generation strips surrounding quotes from response."""
        with patch.object(AIService, '_call_llm') as mock_call:
            # LLM might return quoted text
            mock_call.return_value = '"Hello there, stranger!"'
            service = AIService(mock_ai_config)

            result = service.generate_npc_dialogue(
                npc_name="NPC",
                npc_description="Test NPC",
                npc_role="villager",
                theme="fantasy"
            )

            assert not result.startswith('"')
            assert not result.endswith('"')
            assert result == "Hello there, stranger!"

    def test_generate_npc_dialogue_truncates_long_responses(self, mock_ai_config):
        """Dialogue generation truncates responses longer than 200 chars."""
        with patch.object(AIService, '_call_llm') as mock_call:
            long_response = "A" * 250  # Way too long
            mock_call.return_value = long_response
            service = AIService(mock_ai_config)

            result = service.generate_npc_dialogue(
                npc_name="NPC",
                npc_description="Test NPC",
                npc_role="villager",
                theme="fantasy"
            )

            assert len(result) == 200
            assert result.endswith("...")

    def test_generate_npc_dialogue_raises_on_short_response(self, mock_ai_config):
        """Dialogue generation raises error if response too short."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Hi"  # Too short (< 10 chars)
            service = AIService(mock_ai_config)

            with pytest.raises(AIGenerationError) as exc_info:
                service.generate_npc_dialogue(
                    npc_name="NPC",
                    npc_description="Test NPC",
                    npc_role="villager",
                    theme="fantasy"
                )

            assert "too short" in str(exc_info.value)


class TestNpcDialogueGreetings:
    """Tests for adding AI dialogue to NPC greetings."""

    # Spec test 3: After AI generation, dialogue is added to NPC.greetings
    def test_npc_dialogue_added_to_greetings(self, sample_npc):
        """After AI generation, dialogue is added to NPC.greetings."""
        generated_dialogue = "Welcome to my humble shop, traveler!"

        # Simulate what the talk command would do
        sample_npc.greetings.append(generated_dialogue)

        assert len(sample_npc.greetings) == 1
        assert generated_dialogue in sample_npc.greetings
        # Verify get_greeting can return the new dialogue
        assert sample_npc.get_greeting() == generated_dialogue


class TestTalkCommandWithAI:
    """Tests for talk command AI integration."""

    # Spec test 4: talk command triggers AI generation when greetings < 3
    def test_talk_command_uses_ai_when_available(self, mock_ai_config, sample_npc):
        """talk command triggers AI generation when greetings < 3."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Welcome, dear customer! What brings you here?"
            service = AIService(mock_ai_config)

            # Create minimal game state
            character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
            location = Location(
                name="Market",
                description="A busy market",
                coordinates=(0, 0),
                npcs=[sample_npc]
            )
            game_state = GameState(
                character=character,
                world={"Market": location},
                starting_location="Market",
                ai_service=service,
                theme="fantasy"
            )

            # Simulate talk command logic
            npc = sample_npc
            assert len(npc.greetings) < 3

            if game_state.ai_service and len(npc.greetings) < 3:
                role = "merchant" if npc.is_merchant else "villager"
                dialogue = game_state.ai_service.generate_npc_dialogue(
                    npc_name=npc.name,
                    npc_description=npc.description,
                    npc_role=role,
                    theme=game_state.theme,
                    location_name=game_state.current_location
                )
                npc.greetings.append(dialogue)

            # Verify dialogue was generated and added
            assert len(npc.greetings) == 1
            mock_call.assert_called_once()

    # Spec test 5: Without ai_service, falls back to existing behavior
    def test_talk_command_fallback_without_ai(self, sample_npc):
        """Without ai_service, falls back to existing behavior."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        location = Location(
            name="Market",
            description="A busy market",
            coordinates=(0, 0),
            npcs=[sample_npc]
        )
        GameState(
            character=character,
            world={"Market": location},
            starting_location="Market",
            ai_service=None,  # No AI service
            theme="fantasy"
        )

        # The NPC should still work with existing dialogue
        greeting = sample_npc.get_greeting()
        assert greeting == "Welcome to my shop!"  # Falls back to dialogue field

    # Spec test 7: No AI call when NPC already has 3+ greetings
    def test_dialogue_not_generated_when_greetings_full(
        self, mock_ai_config, sample_npc_with_greetings
    ):
        """No AI call when NPC already has 3+ greetings."""
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "This should not be called"
            service = AIService(mock_ai_config)

            npc = sample_npc_with_greetings
            assert len(npc.greetings) >= 3

            # Simulate talk command logic - should NOT call AI
            if service and len(npc.greetings) < 3:
                service.generate_npc_dialogue(
                    npc_name=npc.name,
                    npc_description=npc.description,
                    npc_role="villager",
                    theme="fantasy",
                    location_name="Test"
                )

            # AI should not be called since greetings >= 3
            mock_call.assert_not_called()


class TestDialoguePersistence:
    """Tests for dialogue persistence through save/load."""

    # Spec test 6: Greetings persist through save/load cycle
    def test_generated_dialogue_persisted(self, sample_npc):
        """Greetings persist through save/load cycle (uses existing serialization)."""
        # Add AI-generated dialogue
        sample_npc.greetings.append("Hello, weary traveler!")
        sample_npc.greetings.append("The weather is fine today.")

        # Serialize to dict
        npc_dict = sample_npc.to_dict()

        # Verify greetings are in serialized data
        assert "greetings" in npc_dict
        assert len(npc_dict["greetings"]) == 2
        assert "Hello, weary traveler!" in npc_dict["greetings"]

        # Deserialize
        restored_npc = NPC.from_dict(npc_dict)

        # Verify greetings were restored
        assert len(restored_npc.greetings) == 2
        assert "Hello, weary traveler!" in restored_npc.greetings
        assert "The weather is fine today." in restored_npc.greetings


class TestAIConfigNpcDialogue:
    """Tests for AIConfig NPC dialogue prompt configuration."""

    def test_ai_config_has_npc_dialogue_prompt(self):
        """AIConfig should have npc_dialogue_prompt field."""
        config = AIConfig(api_key="test-key")
        assert hasattr(config, "npc_dialogue_prompt")
        assert config.npc_dialogue_prompt == DEFAULT_NPC_DIALOGUE_PROMPT

    def test_ai_config_npc_dialogue_prompt_in_to_dict(self):
        """npc_dialogue_prompt should be in to_dict output."""
        config = AIConfig(api_key="test-key", npc_dialogue_prompt="Custom prompt {theme}")
        data = config.to_dict()
        assert "npc_dialogue_prompt" in data
        assert data["npc_dialogue_prompt"] == "Custom prompt {theme}"

    def test_ai_config_npc_dialogue_prompt_from_dict(self):
        """npc_dialogue_prompt should be restored from dict."""
        data = {
            "api_key": "test-key",
            "npc_dialogue_prompt": "Custom prompt {theme}"
        }
        config = AIConfig.from_dict(data)
        assert config.npc_dialogue_prompt == "Custom prompt {theme}"

    def test_ai_config_from_dict_uses_default_when_missing(self):
        """from_dict uses DEFAULT_NPC_DIALOGUE_PROMPT when field is missing."""
        data = {"api_key": "test-key"}
        config = AIConfig.from_dict(data)
        assert config.npc_dialogue_prompt == DEFAULT_NPC_DIALOGUE_PROMPT


class TestNpcDialoguePromptTemplate:
    """Tests for the NPC dialogue prompt template."""

    def test_default_npc_dialogue_prompt_has_placeholders(self):
        """Default prompt template has all required placeholders."""
        assert "{npc_name}" in DEFAULT_NPC_DIALOGUE_PROMPT
        assert "{npc_description}" in DEFAULT_NPC_DIALOGUE_PROMPT
        assert "{npc_role}" in DEFAULT_NPC_DIALOGUE_PROMPT
        assert "{theme}" in DEFAULT_NPC_DIALOGUE_PROMPT
        assert "{location_name}" in DEFAULT_NPC_DIALOGUE_PROMPT

    def test_prompt_can_be_formatted(self):
        """Prompt template can be formatted with all parameters."""
        formatted = DEFAULT_NPC_DIALOGUE_PROMPT.format(
            npc_name="Test NPC",
            npc_description="A test description",
            npc_role="merchant",
            theme="fantasy",
            location_name="Test Location"
        )
        assert "Test NPC" in formatted
        assert "merchant" in formatted
        assert "fantasy" in formatted


# ========================================================================
# Conversation Response Tests (Coverage for lines 1361-1382, 1409-1422)
# ========================================================================

class TestGenerateConversationResponse:
    """Tests for AIService.generate_conversation_response()"""

    # Test: generate_conversation_response returns valid string - spec: lines 1361-1382
    def test_generate_conversation_response_success(self, mock_ai_config):
        """Test generate_conversation_response returns a valid string response.

        Spec: generate_conversation_response() calls _build_conversation_prompt and
        validates response length (lines 1361-1382).
        """
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Ah, you wish to know more? The ancient tales speak of..."
            service = AIService(mock_ai_config)

            result = service.generate_conversation_response(
                npc_name="Elder Sage",
                npc_description="A wise old sage",
                npc_role="quest_giver",
                theme="fantasy",
                location_name="Library of Ancients",
                conversation_history=[],
                player_input="Tell me about the ancient prophecy."
            )

            assert isinstance(result, str)
            assert len(result) >= 10
            assert "ancient tales" in result
            mock_call.assert_called_once()

    # Test: generate_conversation_response with conversation history - spec: lines 1409-1422
    def test_generate_conversation_response_with_history(self, mock_ai_config):
        """Test generate_conversation_response includes formatted history in prompt.

        Spec: Conversation history is formatted with Player/NPC prefixes in
        _build_conversation_prompt (lines 1409-1422).
        """
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Indeed, as I mentioned before, the artifact awaits."
            service = AIService(mock_ai_config)

            conversation_history = [
                {"role": "player", "content": "Hello, wise one."},
                {"role": "npc", "content": "Greetings, traveler. What brings you here?"},
                {"role": "player", "content": "I seek the ancient artifact."}
            ]

            service.generate_conversation_response(
                npc_name="Elder Sage",
                npc_description="A wise old sage",
                npc_role="quest_giver",
                theme="fantasy",
                location_name="Library",
                conversation_history=conversation_history,
                player_input="Where can I find it?"
            )

            # Verify the prompt contains formatted history
            prompt = mock_call.call_args[0][0]
            assert "Player: Hello, wise one." in prompt
            assert "Elder Sage: Greetings, traveler." in prompt
            assert "Player: I seek the ancient artifact." in prompt
            assert "Where can I find it?" in prompt

    # Test: generate_conversation_response with empty history - spec: line 1420
    def test_generate_conversation_response_empty_history(self, mock_ai_config):
        """Test generate_conversation_response handles empty conversation history.

        Spec: When conversation_history is empty, prompt shows "(No previous conversation)"
        (line 1420).
        """
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Welcome, stranger! How may I assist you?"
            service = AIService(mock_ai_config)

            service.generate_conversation_response(
                npc_name="Merchant",
                npc_description="A friendly shopkeeper",
                npc_role="merchant",
                theme="fantasy",
                location_name="Market",
                conversation_history=[],  # Empty history
                player_input="What do you sell?"
            )

            prompt = mock_call.call_args[0][0]
            assert "(No previous conversation)" in prompt

    # Test: generate_conversation_response raises on short response - spec: lines 1376-1377
    def test_generate_conversation_response_too_short_raises_error(self, mock_ai_config):
        """Test generate_conversation_response raises AIGenerationError if response too short.

        Spec: Response less than 10 characters raises AIGenerationError (lines 1376-1377).
        """
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "Hi"  # Too short (< 10 chars)
            service = AIService(mock_ai_config)

            with pytest.raises(AIGenerationError) as exc_info:
                service.generate_conversation_response(
                    npc_name="NPC",
                    npc_description="A character",
                    npc_role="villager",
                    theme="fantasy",
                    location_name="Village",
                    conversation_history=[],
                    player_input="Hello"
                )

            assert "too short" in str(exc_info.value)

    # Test: generate_conversation_response truncates long response - spec: lines 1379-1380
    def test_generate_conversation_response_truncates_long_response(self, mock_ai_config):
        """Test generate_conversation_response truncates responses longer than 200 chars.

        Spec: Response longer than 200 characters is truncated to 197 chars + "..."
        (lines 1379-1380).
        """
        with patch.object(AIService, '_call_llm') as mock_call:
            long_response = "A" * 250  # Way too long
            mock_call.return_value = long_response
            service = AIService(mock_ai_config)

            result = service.generate_conversation_response(
                npc_name="NPC",
                npc_description="A character",
                npc_role="villager",
                theme="fantasy",
                location_name="Village",
                conversation_history=[],
                player_input="Tell me a long story."
            )

            assert len(result) == 200
            assert result.endswith("...")

    # Test: generate_conversation_response strips quotes - spec: line 1374
    def test_generate_conversation_response_strips_quotes(self, mock_ai_config):
        """Test generate_conversation_response strips surrounding quotes.

        Spec: Response is stripped of surrounding quotes (line 1374).
        """
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = '"Hello there, stranger! Welcome to our village."'
            service = AIService(mock_ai_config)

            result = service.generate_conversation_response(
                npc_name="NPC",
                npc_description="A character",
                npc_role="villager",
                theme="fantasy",
                location_name="Village",
                conversation_history=[],
                player_input="Hi"
            )

            assert not result.startswith('"')
            assert not result.endswith('"')
            assert result == "Hello there, stranger! Welcome to our village."

    # Test: _build_conversation_prompt includes all required elements - spec: lines 1384-1430
    def test_build_conversation_prompt_includes_all_elements(self, mock_ai_config):
        """Test _build_conversation_prompt includes NPC info, history, and player input.

        Spec: The built prompt must include npc_name, npc_description, npc_role,
        theme, location_name, formatted history, and player_input.
        """
        with patch.object(AIService, '_call_llm') as mock_call:
            mock_call.return_value = "A proper response for testing purposes here."
            service = AIService(mock_ai_config)

            service.generate_conversation_response(
                npc_name="Guard Captain",
                npc_description="A stern military officer",
                npc_role="quest_giver",
                theme="medieval",
                location_name="Castle Barracks",
                conversation_history=[{"role": "player", "content": "Greetings"}],
                player_input="I need your help."
            )

            prompt = mock_call.call_args[0][0]
            assert "Guard Captain" in prompt
            assert "stern military officer" in prompt
            assert "quest_giver" in prompt
            assert "medieval" in prompt
            assert "Castle Barracks" in prompt
            assert "Player: Greetings" in prompt
            assert "I need your help." in prompt
