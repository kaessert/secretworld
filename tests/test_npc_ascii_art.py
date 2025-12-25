"""Tests for NPC ASCII art feature.

Tests cover:
1. NPC model ascii_art field (storage and serialization) - tests spec: NPC ascii_art field
2. Fallback ASCII art templates for NPC roles - tests spec: Fallback NPC ASCII art
3. Talk command displaying ASCII art - tests spec: Talk command shows ASCII art
4. AI-generated NPC ASCII art (mocked) - tests spec: AI NPC ASCII art generation
"""

import pytest
from unittest.mock import Mock, patch

from cli_rpg.models.npc import NPC
from cli_rpg.npc_art import get_fallback_npc_ascii_art


class TestNPCModelAsciiArt:
    """Test NPC model has ascii_art field - tests spec: NPC ascii_art field."""

    def test_npc_model_has_ascii_art_field(self):
        """Verify NPC can store ascii_art."""
        # Tests spec: NPC model has ascii_art field
        ascii_art = r"""
     ___
    /   \
   | o o |
    \ = /
"""
        npc = NPC(
            name="Test Merchant",
            description="A friendly shopkeeper",
            dialogue="Welcome to my shop!",
            ascii_art=ascii_art,
        )

        assert npc.ascii_art == ascii_art

    def test_npc_to_dict_includes_ascii_art(self):
        """Verify to_dict includes ascii_art field when non-empty."""
        # Tests spec: NPC serialization includes ascii_art
        ascii_art = "  /-\\\n  | |\n  \\_/"
        npc = NPC(
            name="Test NPC",
            description="A test character",
            dialogue="Hello!",
            ascii_art=ascii_art,
        )

        data = npc.to_dict()
        assert "ascii_art" in data
        assert data["ascii_art"] == ascii_art

    def test_npc_to_dict_excludes_empty_ascii_art(self):
        """Verify to_dict excludes ascii_art field when empty."""
        # Tests spec: NPC serialization omits empty ascii_art
        npc = NPC(
            name="Test NPC",
            description="A test character",
            dialogue="Hello!",
            ascii_art="",
        )

        data = npc.to_dict()
        assert "ascii_art" not in data

    def test_npc_from_dict_loads_ascii_art(self):
        """Verify from_dict loads ascii_art correctly."""
        # Tests spec: NPC deserialization loads ascii_art
        ascii_art = "  ^-^\n  | |\n  ===\n"
        data = {
            "name": "Test NPC",
            "description": "A test character",
            "dialogue": "Hello!",
            "ascii_art": ascii_art,
        }

        npc = NPC.from_dict(data)
        assert npc.ascii_art == ascii_art

    def test_npc_from_dict_default_ascii_art(self):
        """Verify from_dict defaults ascii_art to empty string."""
        # Tests spec: NPC deserialization defaults ascii_art
        data = {
            "name": "Test NPC",
            "description": "A test character",
            "dialogue": "Hello!",
        }

        npc = NPC.from_dict(data)
        assert npc.ascii_art == ""

    def test_npc_default_ascii_art_is_empty(self):
        """Verify NPC defaults ascii_art to empty string."""
        # Tests spec: NPC default ascii_art is empty
        npc = NPC(
            name="Test NPC",
            description="A test character",
            dialogue="Hello!",
        )

        assert npc.ascii_art == ""


class TestFallbackNPCAsciiArt:
    """Test fallback ASCII art templates for NPC roles - tests spec: Fallback NPC ASCII art."""

    def test_get_fallback_art_merchant(self):
        """Merchant NPCs get merchant art by role."""
        # Tests spec: Fallback art for merchant role
        art = get_fallback_npc_ascii_art("merchant", "Any Name")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3  # At least 3 lines
        assert max(len(line) for line in art.splitlines()) <= 40  # Max 40 chars wide
        # Should contain dollar signs (merchant indicator)
        assert "$$" in art or "$" in art

    def test_get_fallback_art_quest_giver(self):
        """Quest giver NPCs get quest giver art by role."""
        # Tests spec: Fallback art for quest_giver role
        art = get_fallback_npc_ascii_art("quest_giver", "Any Name")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3
        # Should contain scroll indicator
        assert "scroll" in art or "~~~" in art

    def test_get_fallback_art_villager(self):
        """Villager NPCs get villager art by role."""
        # Tests spec: Fallback art for villager role
        art = get_fallback_npc_ascii_art("villager", "Any Name")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_guard(self):
        """Guard NPCs get guard art by role."""
        # Tests spec: Fallback art for guard role
        art = get_fallback_npc_ascii_art("guard", "Any Name")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_elder(self):
        """Elder NPCs get elder art by role."""
        # Tests spec: Fallback art for elder role
        art = get_fallback_npc_ascii_art("elder", "Any Name")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3
        # Should have wavy hair indicator
        assert "~~~" in art or "~" in art

    def test_get_fallback_art_blacksmith(self):
        """Blacksmith NPCs get blacksmith art by role."""
        # Tests spec: Fallback art for blacksmith role
        art = get_fallback_npc_ascii_art("blacksmith", "Any Name")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_innkeeper(self):
        """Innkeeper NPCs get innkeeper art by role."""
        # Tests spec: Fallback art for innkeeper role
        art = get_fallback_npc_ascii_art("innkeeper", "Any Name")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_default(self):
        """Unknown role gets default art."""
        # Tests spec: Fallback art for unknown role
        art = get_fallback_npc_ascii_art(None, "Unknown NPC")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_name_merchant(self):
        """Fallback detects merchant by name keywords."""
        # Tests spec: Name-based fallback for merchant
        for name in ["Trader Bob", "The Vendor", "Town Merchant"]:
            art = get_fallback_npc_ascii_art(None, name)
            assert art
            # Should match merchant art
            assert "$$" in art or "$" in art

    def test_get_fallback_art_by_name_guard(self):
        """Fallback detects guard by name keywords."""
        # Tests spec: Name-based fallback for guard
        for name in ["Town Guard", "Knight Errant", "Captain Smith"]:
            art = get_fallback_npc_ascii_art(None, name)
            assert art
            assert len(art.splitlines()) >= 3


class TestTalkCommandAsciiArt:
    """Test talk command displays ASCII art - tests spec: Talk command shows ASCII art."""

    @pytest.fixture
    def game_state_with_npc(self):
        """Create a game state with an NPC at current location."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1,
            gold=50,
        )

        npc = NPC(
            name="Test Merchant",
            description="A friendly shopkeeper",
            dialogue="Welcome to my shop!",
            is_merchant=True,
        )

        location = Location(
            name="Town Square",
            description="A bustling square",
            coordinates=(0, 0),
            npcs=[npc],
        )

        world = {"Town Square": location}
        game_state = GameState(character, world, "Town Square")
        game_state.theme = "fantasy"
        game_state.ai_service = None

        return game_state, npc

    def test_talk_displays_ascii_art_when_present(self, game_state_with_npc):
        """Talk command displays ASCII art if NPC has it set."""
        # Tests spec: Talk command displays existing ASCII art
        from cli_rpg.main import handle_exploration_command

        game_state, npc = game_state_with_npc
        # Pre-set ASCII art
        ascii_art = r"""
     ___
    /   \
   | o o |
"""
        npc.ascii_art = ascii_art

        _, output = handle_exploration_command(game_state, "talk", ["Test", "Merchant"])

        # Should contain the ASCII art
        assert "___" in output or "/   \\" in output

    def test_talk_uses_fallback_without_ai(self, game_state_with_npc):
        """Talk command uses fallback art when AI unavailable."""
        # Tests spec: Talk command uses fallback art without AI
        from cli_rpg.main import handle_exploration_command

        game_state, npc = game_state_with_npc
        game_state.ai_service = None
        npc.ascii_art = ""  # Ensure no art set

        _, output = handle_exploration_command(game_state, "talk", ["Test", "Merchant"])

        # NPC should now have fallback art set
        assert npc.ascii_art
        assert len(npc.ascii_art.splitlines()) >= 3
        # Output should contain the greeting
        assert "Welcome to my shop!" in output or npc.name in output


class TestAINPCAsciiArtGeneration:
    """Test AI NPC ASCII art generation - tests spec: AI NPC ASCII art generation."""

    def test_ai_npc_ascii_art_generation(self):
        """AIService.generate_npc_ascii_art returns valid art (mocked)."""
        # Tests spec: AI service generates NPC ASCII art
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False,
        )

        with patch.object(AIService, "_call_llm") as mock_call:
            mock_call.return_value = r"""
    ___
   /   \
  | o o |
   \ = /
  /| ||\
"""
            service = AIService(config)
            art = service.generate_npc_ascii_art(
                npc_name="Merchant",
                npc_description="A friendly shopkeeper",
                npc_role="merchant",
                theme="fantasy",
            )

            # Should return non-empty art
            assert art
            # Should have multiple lines
            assert len(art.splitlines()) >= 3
            # Should be max 40 chars wide
            for line in art.splitlines():
                assert len(line) <= 40, f"Line too long: {line}"

    def test_ai_npc_ascii_art_prompt_formatting(self):
        """AI prompt includes NPC name, role, and description."""
        # Tests spec: AI prompt includes NPC details
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False,
        )

        service = AIService(config)

        prompt = service._build_npc_ascii_art_prompt(
            npc_name="Old Sage",
            npc_description="A wise elderly wizard",
            npc_role="quest_giver",
            theme="fantasy",
        )

        assert "Old Sage" in prompt
        assert "quest_giver" in prompt
        assert "wise elderly wizard" in prompt
        assert "fantasy" in prompt

    def test_ai_npc_ascii_art_too_short_raises_error(self):
        """AI-generated art that's too short raises AIGenerationError."""
        # Tests spec: AI art validation - minimum lines
        from cli_rpg.ai_service import AIService, AIGenerationError
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False,
        )

        with patch.object(AIService, "_call_llm") as mock_call:
            mock_call.return_value = "X"  # Too short

            service = AIService(config)

            with pytest.raises(AIGenerationError, match="too short"):
                service.generate_npc_ascii_art(
                    npc_name="Test",
                    npc_description="Test NPC",
                    npc_role="villager",
                    theme="fantasy",
                )

    def test_ai_npc_ascii_art_truncates_long_lines(self):
        """AI-generated art with long lines is truncated to 40 chars."""
        # Tests spec: AI art validation - line length
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False,
        )

        long_line = "X" * 50  # 50 chars, exceeds 40 limit
        with patch.object(AIService, "_call_llm") as mock_call:
            mock_call.return_value = f"{long_line}\n{long_line}\n{long_line}\n{long_line}"

            service = AIService(config)
            art = service.generate_npc_ascii_art(
                npc_name="Test",
                npc_description="Test NPC",
                npc_role="villager",
                theme="fantasy",
            )

            # All lines should be max 40 chars
            for line in art.splitlines():
                assert len(line) <= 40


class TestTalkCommandAIIntegration:
    """Test talk command AI integration - tests spec: Talk command AI integration."""

    def test_talk_generates_art_with_ai(self):
        """Talk command generates art using AI when available."""
        # Tests spec: Talk command uses AI to generate art
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1,
            gold=50,
        )

        npc = NPC(
            name="Village Elder",
            description="An ancient wise man",
            dialogue="Greetings, young one.",
            is_quest_giver=True,
        )

        location = Location(
            name="Village Center",
            description="The heart of the village",
            coordinates=(0, 0),
            npcs=[npc],
        )

        world = {"Village Center": location}
        game_state = GameState(character, world, "Village Center")
        game_state.theme = "fantasy"

        # Mock AI service
        mock_ai = Mock()
        mock_ai.generate_npc_ascii_art.return_value = r"""
     ~~~
    /   \
   | o o |
"""
        mock_ai.generate_npc_dialogue.return_value = "Wisdom awaits."
        game_state.ai_service = mock_ai

        _, output = handle_exploration_command(game_state, "talk", ["Village", "Elder"])

        # AI should have been called to generate art
        mock_ai.generate_npc_ascii_art.assert_called_once()
        # NPC should have art set
        assert npc.ascii_art
        # Greeting should be in output
        assert "Greetings" in output or "Village Elder" in output

    def test_talk_falls_back_when_ai_fails(self):
        """Talk command uses fallback when AI fails to generate art."""
        # Tests spec: Talk command falls back when AI fails
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1,
            gold=50,
        )

        npc = NPC(
            name="Town Guard",
            description="A vigilant protector",
            dialogue="Move along, citizen.",
        )

        location = Location(
            name="Town Gate",
            description="The entrance to town",
            coordinates=(0, 0),
            npcs=[npc],
        )

        world = {"Town Gate": location}
        game_state = GameState(character, world, "Town Gate")
        game_state.theme = "fantasy"

        # Mock AI service that fails
        mock_ai = Mock()
        mock_ai.generate_npc_ascii_art.side_effect = Exception("AI error")
        game_state.ai_service = mock_ai

        _, output = handle_exploration_command(game_state, "talk", ["Town", "Guard"])

        # NPC should have fallback art (guard art)
        assert npc.ascii_art
        assert len(npc.ascii_art.splitlines()) >= 3
        # Output should contain the greeting
        assert "Move along" in output or "Town Guard" in output
