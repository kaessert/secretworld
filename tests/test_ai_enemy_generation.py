"""Tests for AI-powered enemy generation.

This module tests the AI enemy generation feature which creates contextual,
themed enemies with descriptions, stats scaling, and encounter flavor text.
"""

import json
import pytest
from unittest.mock import Mock, patch

from cli_rpg.models.enemy import Enemy
from cli_rpg.ai_config import AIConfig, DEFAULT_ENEMY_GENERATION_PROMPT
from cli_rpg.ai_service import AIService, AIServiceError, AIGenerationError
from cli_rpg.combat import ai_spawn_enemy, CombatEncounter
from cli_rpg.models.character import Character


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
def mock_enemy_response():
    """Create a valid mock AI enemy response."""
    return {
        "name": "Shadow Wolf",
        "description": "A snarling beast with glowing red eyes",
        "attack_flavor": "lunges with razor-sharp claws",
        "health": 50,
        "attack_power": 8,
        "defense": 3,
        "xp_reward": 40
    }


@pytest.fixture
def test_character():
    """Create a test character for combat tests."""
    return Character(
        name="TestHero",
        strength=15,
        dexterity=10,
        intelligence=8,
        level=3
    )


# =============================================================================
# Enemy Model Tests - Spec: description and attack_flavor fields
# =============================================================================

class TestEnemyDescriptionField:
    """Tests for Enemy description field."""

    def test_enemy_description_serializes_correctly(self):
        """Spec: to_dict/from_dict includes description field."""
        enemy = Enemy(
            name="Shadow Wolf",
            health=50,
            max_health=50,
            attack_power=8,
            defense=3,
            xp_reward=40,
            level=2,
            description="A snarling beast with glowing red eyes"
        )

        # Serialize
        data = enemy.to_dict()
        assert "description" in data
        assert data["description"] == "A snarling beast with glowing red eyes"

        # Deserialize
        restored = Enemy.from_dict(data)
        assert restored.description == "A snarling beast with glowing red eyes"

    def test_enemy_attack_flavor_serializes_correctly(self):
        """Spec: to_dict/from_dict includes attack_flavor field."""
        enemy = Enemy(
            name="Shadow Wolf",
            health=50,
            max_health=50,
            attack_power=8,
            defense=3,
            xp_reward=40,
            level=2,
            attack_flavor="lunges with razor-sharp claws"
        )

        # Serialize
        data = enemy.to_dict()
        assert "attack_flavor" in data
        assert data["attack_flavor"] == "lunges with razor-sharp claws"

        # Deserialize
        restored = Enemy.from_dict(data)
        assert restored.attack_flavor == "lunges with razor-sharp claws"

    def test_enemy_default_description_empty(self):
        """Spec: description defaults to empty string."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        assert enemy.description == ""

    def test_enemy_default_attack_flavor_empty(self):
        """Spec: attack_flavor defaults to empty string."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        assert enemy.attack_flavor == ""

    def test_enemy_serialization_roundtrip_with_description(self):
        """Spec: Enemy with description survives serialization roundtrip."""
        original = Enemy(
            name="Fire Drake",
            health=100,
            max_health=100,
            attack_power=15,
            defense=8,
            xp_reward=150,
            level=5,
            description="A small dragon wreathed in flames",
            attack_flavor="breathes a cone of fire"
        )

        data = original.to_dict()
        restored = Enemy.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.attack_flavor == original.attack_flavor


# =============================================================================
# AIConfig Tests - Spec: enemy_generation_prompt field
# =============================================================================

class TestAIConfigEnemyPrompt:
    """Tests for AIConfig enemy generation prompt."""

    def test_ai_config_has_enemy_prompt(self):
        """Spec: enemy_generation_prompt field exists in AIConfig."""
        config = AIConfig(api_key="test-key")
        assert hasattr(config, 'enemy_generation_prompt')
        assert config.enemy_generation_prompt != ""

    def test_ai_config_enemy_prompt_serialization(self):
        """Spec: to_dict/from_dict handles enemy_generation_prompt."""
        config = AIConfig(
            api_key="test-key",
            enemy_generation_prompt="Custom enemy prompt: {theme} {location_name}"
        )

        # Serialize
        data = config.to_dict()
        assert "enemy_generation_prompt" in data
        assert data["enemy_generation_prompt"] == "Custom enemy prompt: {theme} {location_name}"

        # Deserialize
        restored = AIConfig.from_dict(data)
        assert restored.enemy_generation_prompt == "Custom enemy prompt: {theme} {location_name}"

    def test_default_enemy_prompt_contains_placeholders(self):
        """Spec: Default prompt contains required placeholders."""
        assert "{theme}" in DEFAULT_ENEMY_GENERATION_PROMPT
        assert "{location_name}" in DEFAULT_ENEMY_GENERATION_PROMPT
        assert "{player_level}" in DEFAULT_ENEMY_GENERATION_PROMPT


# =============================================================================
# AIService.generate_enemy() Tests
# =============================================================================

class TestAIServiceGenerateEnemy:
    """Tests for AIService.generate_enemy() method."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_enemy_returns_valid_structure(
        self, mock_openai_class, basic_config, mock_enemy_response
    ):
        """Spec: Returns dict with all required fields."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_enemy_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_enemy(
            theme="fantasy",
            location_name="Dark Forest",
            player_level=3
        )

        # Verify all required fields
        assert "name" in result
        assert "description" in result
        assert "attack_flavor" in result
        assert "health" in result
        assert "attack_power" in result
        assert "defense" in result
        assert "xp_reward" in result
        assert "level" in result

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_enemy_validates_name_length(self, mock_openai_class, basic_config):
        """Spec: Rejects names <2 or >30 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Name too short
        invalid_response = {
            "name": "X",  # Too short (< 2 chars)
            "description": "A tiny creature",
            "attack_flavor": "bites weakly",
            "health": 10,
            "attack_power": 2,
            "defense": 1,
            "xp_reward": 5
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="name"):
            service.generate_enemy(
                theme="fantasy",
                location_name="Forest",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_enemy_validates_name_too_long(self, mock_openai_class, basic_config):
        """Spec: Rejects names >30 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Name too long
        invalid_response = {
            "name": "A" * 31,  # Too long (> 30 chars)
            "description": "A very long named creature",
            "attack_flavor": "attacks viciously",
            "health": 50,
            "attack_power": 5,
            "defense": 3,
            "xp_reward": 30
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="name"):
            service.generate_enemy(
                theme="fantasy",
                location_name="Forest",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_enemy_validates_description_length(self, mock_openai_class, basic_config):
        """Spec: Rejects descriptions <10 or >150 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Description too short
        invalid_response = {
            "name": "Goblin",
            "description": "Short",  # Too short (< 10 chars)
            "attack_flavor": "stabs with a dagger",
            "health": 30,
            "attack_power": 5,
            "defense": 2,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="description"):
            service.generate_enemy(
                theme="fantasy",
                location_name="Cave",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_enemy_validates_positive_stats(self, mock_openai_class, basic_config):
        """Spec: Rejects negative health/attack/defense."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Negative health
        invalid_response = {
            "name": "Broken Skeleton",
            "description": "A shambling pile of bones",
            "attack_flavor": "swipes with bony claws",
            "health": -10,  # Invalid
            "attack_power": 5,
            "defense": 2,
            "xp_reward": 20
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="positive"):
            service.generate_enemy(
                theme="fantasy",
                location_name="Dungeon",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_enemy_uses_context(self, mock_openai_class, basic_config, mock_enemy_response):
        """Spec: Prompt includes location_name and player_level."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_enemy_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_enemy(
            theme="cyberpunk",
            location_name="Neon District",
            player_level=5
        )

        # Get the actual call arguments
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify context is in prompt
        assert "cyberpunk" in prompt.lower()
        assert "Neon District" in prompt or "neon district" in prompt.lower()
        assert "5" in prompt  # Player level

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_enemy_handles_api_error(self, mock_openai_class, basic_config):
        """Spec: Raises AIServiceError on failure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Simulate API error
        mock_client.chat.completions.create.side_effect = Exception("API failure")

        service = AIService(basic_config)

        with pytest.raises(AIServiceError):
            service.generate_enemy(
                theme="fantasy",
                location_name="Forest",
                player_level=1
            )


# =============================================================================
# ai_spawn_enemy() Tests
# =============================================================================

class TestAISpawnEnemy:
    """Tests for ai_spawn_enemy() function."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_ai_spawn_enemy_uses_ai_service(
        self, mock_openai_class, basic_config, mock_enemy_response
    ):
        """Spec: Calls AIService when provided."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_enemy_response)
        mock_client.chat.completions.create.return_value = mock_response

        ai_service = AIService(basic_config)

        enemy = ai_spawn_enemy(
            location_name="Dark Forest",
            player_level=3,
            ai_service=ai_service,
            theme="fantasy"
        )

        # Verify AI was called
        assert mock_client.chat.completions.create.called

        # Verify enemy has AI-generated attributes
        assert enemy.name == "Shadow Wolf"
        assert enemy.description == "A snarling beast with glowing red eyes"
        assert enemy.attack_flavor == "lunges with razor-sharp claws"

    @patch('cli_rpg.ai_service.OpenAI')
    def test_ai_spawn_enemy_fallback_on_error(self, mock_openai_class, basic_config):
        """Spec: Falls back to spawn_enemy() on AI failure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Make AI fail
        mock_client.chat.completions.create.side_effect = Exception("AI error")

        ai_service = AIService(basic_config)

        # Should not raise, should fallback
        enemy = ai_spawn_enemy(
            location_name="Dark Forest",
            player_level=3,
            ai_service=ai_service,
            theme="fantasy"
        )

        # Verify we got a valid enemy from fallback
        assert isinstance(enemy, Enemy)
        assert enemy.name != ""
        assert enemy.health > 0

    def test_ai_spawn_enemy_fallback_when_no_service(self):
        """Spec: Falls back when ai_service=None."""
        enemy = ai_spawn_enemy(
            location_name="Dark Forest",
            player_level=3,
            ai_service=None,
            theme="fantasy"
        )

        # Verify we got a valid enemy from fallback
        assert isinstance(enemy, Enemy)
        assert enemy.name != ""
        assert enemy.health > 0

    @patch('cli_rpg.ai_service.OpenAI')
    def test_ai_spawn_enemy_returns_valid_enemy(
        self, mock_openai_class, basic_config, mock_enemy_response
    ):
        """Spec: Returns Enemy instance with correct fields."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_enemy_response)
        mock_client.chat.completions.create.return_value = mock_response

        ai_service = AIService(basic_config)

        enemy = ai_spawn_enemy(
            location_name="Dark Forest",
            player_level=3,
            ai_service=ai_service,
            theme="fantasy"
        )

        # Verify Enemy instance with correct values
        assert isinstance(enemy, Enemy)
        assert enemy.name == "Shadow Wolf"
        assert enemy.health == 50
        assert enemy.max_health == 50
        assert enemy.attack_power == 8
        assert enemy.defense == 3
        assert enemy.xp_reward == 40
        assert enemy.level == 3  # Should match player level


# =============================================================================
# Combat Integration Tests - attack_flavor in messages
# =============================================================================

class TestCombatAttackFlavor:
    """Tests for attack_flavor usage in combat messages."""

    def test_enemy_turn_uses_attack_flavor(self, test_character):
        """Spec: Message includes attack_flavor when present."""
        enemy = Enemy(
            name="Shadow Wolf",
            health=50,
            max_health=50,
            attack_power=8,
            defense=3,
            xp_reward=40,
            level=2,
            attack_flavor="lunges with razor-sharp claws"
        )

        combat = CombatEncounter(test_character, enemy)
        combat.start()

        message = combat.enemy_turn()

        # Should use attack_flavor in message
        assert "lunges with razor-sharp claws" in message

    def test_enemy_turn_default_message_without_flavor(self, test_character):
        """Spec: Uses default message when no flavor."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )

        combat = CombatEncounter(test_character, enemy)
        combat.start()

        message = combat.enemy_turn()

        # Should use default attack message
        assert "attacks you" in message


# =============================================================================
# GameState Integration Tests
# =============================================================================

class TestGameStateEncounterIntegration:
    """Tests for GameState.trigger_encounter() with AI."""

    @patch('cli_rpg.ai_service.OpenAI')
    @patch('random.random')
    def test_trigger_encounter_uses_ai_when_available(
        self, mock_random, mock_openai_class, basic_config, mock_enemy_response
    ):
        """Spec: Uses ai_spawn_enemy with service when available."""
        # Force encounter to happen
        mock_random.return_value = 0.1  # < 0.3 threshold

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_enemy_response)
        mock_client.chat.completions.create.return_value = mock_response

        from cli_rpg.models.location import Location
        from cli_rpg.game_state import GameState

        ai_service = AIService(basic_config)
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=3
        )
        location = Location(
            name="Dark Forest",
            description="A dark and mysterious forest.",
            coordinates=(0, 0)
        )

        game_state = GameState(
            character=character,
            world={"Dark Forest": location},
            starting_location="Dark Forest",
            ai_service=ai_service,
            theme="fantasy"
        )

        # Trigger encounter
        message = game_state.trigger_encounter("Dark Forest")

        # Should have triggered an encounter
        assert message is not None
        assert game_state.current_combat is not None

        # Should have used AI-generated enemy
        assert game_state.current_combat.enemy.name == "Shadow Wolf"

    @patch('random.random')
    def test_trigger_encounter_works_without_ai(self, mock_random):
        """Spec: Works correctly without AI service."""
        # Force encounter to happen
        mock_random.return_value = 0.1  # < 0.3 threshold

        from cli_rpg.models.location import Location
        from cli_rpg.game_state import GameState

        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=3
        )
        location = Location(
            name="Dark Forest",
            description="A dark and mysterious forest.",
            coordinates=(0, 0)
        )

        game_state = GameState(
            character=character,
            world={"Dark Forest": location},
            starting_location="Dark Forest",
            ai_service=None,  # No AI
            theme="fantasy"
        )

        # Trigger encounter
        message = game_state.trigger_encounter("Dark Forest")

        # Should still work with fallback
        assert message is not None
        assert game_state.current_combat is not None
        assert isinstance(game_state.current_combat.enemy, Enemy)
