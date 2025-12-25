"""Tests for AI-powered item generation.

This module tests the AI item generation feature which creates contextual,
themed items (weapons, armor, consumables) for shops and loot with stats
scaled to player level.
"""

import json
import pytest
from unittest.mock import Mock, patch

from cli_rpg.models.item import Item, ItemType
from cli_rpg.ai_config import AIConfig, DEFAULT_ITEM_GENERATION_PROMPT
from cli_rpg.ai_service import AIService, AIServiceError, AIGenerationError


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def basic_config():
    """Create a basic AIConfig for testing."""
    return AIConfig(
        api_key="test-key-123",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
        max_retries=3,
        retry_delay=0.1  # Short delay for tests
    )


@pytest.fixture
def mock_weapon_response():
    """Create a valid mock AI weapon response."""
    return {
        "name": "Flame Sword",
        "description": "A blade wreathed in magical fire",
        "item_type": "weapon",
        "damage_bonus": 5,
        "defense_bonus": 0,
        "heal_amount": 0,
        "suggested_price": 150
    }


@pytest.fixture
def mock_armor_response():
    """Create a valid mock AI armor response."""
    return {
        "name": "Iron Chestplate",
        "description": "A sturdy piece of protective armor",
        "item_type": "armor",
        "damage_bonus": 0,
        "defense_bonus": 4,
        "heal_amount": 0,
        "suggested_price": 120
    }


@pytest.fixture
def mock_consumable_response():
    """Create a valid mock AI consumable response."""
    return {
        "name": "Health Potion",
        "description": "A red liquid that restores health",
        "item_type": "consumable",
        "damage_bonus": 0,
        "defense_bonus": 0,
        "heal_amount": 25,
        "suggested_price": 50
    }


# =============================================================================
# AIConfig Tests - Spec: item_generation_prompt field
# =============================================================================

class TestAIConfigItemPrompt:
    """Tests for AIConfig item generation prompt."""

    def test_ai_config_has_item_prompt(self):
        """Spec: item_generation_prompt field exists in AIConfig."""
        config = AIConfig(api_key="test-key")
        assert hasattr(config, 'item_generation_prompt')
        assert config.item_generation_prompt != ""

    def test_ai_config_item_prompt_serialization(self):
        """Spec: to_dict/from_dict handles item_generation_prompt."""
        config = AIConfig(
            api_key="test-key",
            item_generation_prompt="Custom item prompt: {theme} {location_name}"
        )

        # Serialize
        data = config.to_dict()
        assert "item_generation_prompt" in data
        assert data["item_generation_prompt"] == "Custom item prompt: {theme} {location_name}"

        # Deserialize
        restored = AIConfig.from_dict(data)
        assert restored.item_generation_prompt == "Custom item prompt: {theme} {location_name}"

    def test_default_item_prompt_contains_placeholders(self):
        """Spec: Default prompt contains required placeholders."""
        assert "{theme}" in DEFAULT_ITEM_GENERATION_PROMPT
        assert "{location_name}" in DEFAULT_ITEM_GENERATION_PROMPT
        assert "{player_level}" in DEFAULT_ITEM_GENERATION_PROMPT
        assert "{item_type_hint}" in DEFAULT_ITEM_GENERATION_PROMPT


# =============================================================================
# AIService.generate_item() Tests
# =============================================================================

class TestAIServiceGenerateItem:
    """Tests for AIService.generate_item() method."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_returns_valid_structure(
        self, mock_openai_class, basic_config, mock_weapon_response
    ):
        """Spec: Returns dict with all required fields."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_weapon_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_item(
            theme="fantasy",
            location_name="Village Shop",
            player_level=3
        )

        # Verify all required fields
        assert "name" in result
        assert "description" in result
        assert "item_type" in result
        assert "damage_bonus" in result
        assert "defense_bonus" in result
        assert "heal_amount" in result
        assert "suggested_price" in result

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_validates_name_length_too_short(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects names <2 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "X",  # Too short (< 2 chars)
            "description": "A tiny thing",
            "item_type": "misc",
            "damage_bonus": 0,
            "defense_bonus": 0,
            "heal_amount": 0,
            "suggested_price": 10
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="name"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_validates_name_length_too_long(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects names >30 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "A" * 31,  # Too long (> 30 chars)
            "description": "A very long named item",
            "item_type": "weapon",
            "damage_bonus": 5,
            "defense_bonus": 0,
            "heal_amount": 0,
            "suggested_price": 100
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="name"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_validates_description_length_too_short(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects descriptions <1 char."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Empty Item",
            "description": "",  # Too short (< 1 char)
            "item_type": "misc",
            "damage_bonus": 0,
            "defense_bonus": 0,
            "heal_amount": 0,
            "suggested_price": 10
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="description"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_validates_description_length_too_long(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects descriptions >200 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Long Described",
            "description": "A" * 201,  # Too long (> 200 chars)
            "item_type": "weapon",
            "damage_bonus": 5,
            "defense_bonus": 0,
            "heal_amount": 0,
            "suggested_price": 100
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="description"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_validates_item_type(self, mock_openai_class, basic_config):
        """Spec: Rejects invalid item types."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Unknown Thing",
            "description": "A strange item",
            "item_type": "invalid_type",  # Invalid
            "damage_bonus": 0,
            "defense_bonus": 0,
            "heal_amount": 0,
            "suggested_price": 10
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="item_type"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_validates_non_negative_stats(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects negative bonuses."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Cursed Sword",
            "description": "A blade with negative power",
            "item_type": "weapon",
            "damage_bonus": -5,  # Invalid: negative
            "defense_bonus": 0,
            "heal_amount": 0,
            "suggested_price": 50
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="non-negative"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_validates_positive_price(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects zero/negative price."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Free Item",
            "description": "A worthless trinket",
            "item_type": "misc",
            "damage_bonus": 0,
            "defense_bonus": 0,
            "heal_amount": 0,
            "suggested_price": 0  # Invalid: zero
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="price"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_respects_type_constraint(
        self, mock_openai_class, basic_config, mock_armor_response
    ):
        """Spec: Returns requested item type when provided."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_armor_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_item(
            theme="fantasy",
            location_name="Blacksmith",
            player_level=3,
            item_type=ItemType.ARMOR
        )

        # Verify item type constraint was passed to prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        assert "armor" in prompt.lower()

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_uses_context(
        self, mock_openai_class, basic_config, mock_weapon_response
    ):
        """Spec: Prompt includes theme, location, level."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_weapon_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_item(
            theme="steampunk",
            location_name="Clockwork Emporium",
            player_level=7
        )

        # Get the actual call arguments
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify context is in prompt
        assert "steampunk" in prompt.lower()
        assert "Clockwork Emporium" in prompt or "clockwork emporium" in prompt.lower()
        assert "7" in prompt  # Player level

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_handles_api_error(self, mock_openai_class, basic_config):
        """Spec: Raises AIServiceError on failure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Simulate API error
        mock_client.chat.completions.create.side_effect = Exception("API failure")

        service = AIService(basic_config)

        with pytest.raises(AIServiceError):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )


# =============================================================================
# Integration Tests - Item model compatibility
# =============================================================================

class TestGenerateItemIntegration:
    """Integration tests for generate_item with Item model."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_can_create_valid_item_instance(
        self, mock_openai_class, basic_config, mock_weapon_response
    ):
        """Spec: Result can construct Item model."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_weapon_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_item(
            theme="fantasy",
            location_name="Shop",
            player_level=3
        )

        # Should be able to create Item from result
        item = Item(
            name=result["name"],
            description=result["description"],
            item_type=ItemType(result["item_type"]),
            damage_bonus=result["damage_bonus"],
            defense_bonus=result["defense_bonus"],
            heal_amount=result["heal_amount"]
        )

        assert item.name == "Flame Sword"
        assert item.item_type == ItemType.WEAPON
        assert item.damage_bonus == 5

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_weapon_has_damage_bonus(
        self, mock_openai_class, basic_config, mock_weapon_response
    ):
        """Spec: Weapons have appropriate stats."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_weapon_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_item(
            theme="fantasy",
            location_name="Shop",
            player_level=3,
            item_type=ItemType.WEAPON
        )

        assert result["item_type"] == "weapon"
        assert result["damage_bonus"] > 0

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_armor_has_defense_bonus(
        self, mock_openai_class, basic_config, mock_armor_response
    ):
        """Spec: Armor has appropriate stats."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_armor_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_item(
            theme="fantasy",
            location_name="Armory",
            player_level=3,
            item_type=ItemType.ARMOR
        )

        assert result["item_type"] == "armor"
        assert result["defense_bonus"] > 0

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_item_consumable_has_heal_amount(
        self, mock_openai_class, basic_config, mock_consumable_response
    ):
        """Spec: Consumables have appropriate stats."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_consumable_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_item(
            theme="fantasy",
            location_name="Apothecary",
            player_level=3,
            item_type=ItemType.CONSUMABLE
        )

        assert result["item_type"] == "consumable"
        assert result["heal_amount"] > 0


# =============================================================================
# Item Response Parsing Error Tests (Coverage for lines 1063-1064, 1071)
# =============================================================================

class TestParseItemResponseErrors:
    """Tests for _parse_item_response error handling."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_parse_item_response_invalid_json(self, mock_openai_class, basic_config):
        """Spec: Invalid JSON raises AIGenerationError.

        Covers lines 1063-1064: json.JSONDecodeError handling in _parse_item_response.
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Return invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON { bad syntax"
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="parse.*JSON"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_parse_item_response_missing_field(self, mock_openai_class, basic_config):
        """Spec: Missing required field raises AIGenerationError.

        Covers line 1071: raise AIGenerationError(f"Response missing required field: {field}")
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Response missing 'suggested_price' field
        incomplete_response = {
            "name": "Test Item",
            "description": "A test item",
            "item_type": "weapon",
            "damage_bonus": 5,
            "defense_bonus": 0,
            "heal_amount": 0
            # Missing 'suggested_price'
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(incomplete_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="missing required field.*suggested_price"):
            service.generate_item(
                theme="fantasy",
                location_name="Shop",
                player_level=1
            )
