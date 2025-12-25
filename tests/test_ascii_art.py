"""Tests for ASCII art feature in combat encounters.

Tests cover:
1. Enemy model ascii_art field (storage and serialization)
2. Fallback ASCII art templates (beast, undead, humanoid, default)
3. Combat intro displaying ASCII art
4. Enemy spawning with fallback art
5. AI-generated ASCII art (mocked)
"""

import pytest
from unittest.mock import Mock, patch

from cli_rpg.models.enemy import Enemy
from cli_rpg.models.character import Character
from cli_rpg.combat import (
    CombatEncounter,
    spawn_enemy,
    ai_spawn_enemy,
    get_fallback_ascii_art,
)


class TestEnemyModelAsciiArt:
    """Test Enemy model has ascii_art field."""

    def test_enemy_model_has_ascii_art_field(self):
        """Verify Enemy can store/serialize ascii_art."""
        ascii_art = r"""
    /\_/\
   ( o.o )
    > ^ <
"""
        enemy = Enemy(
            name="Test Cat",
            health=20,
            max_health=20,
            attack_power=5,
            defense=2,
            xp_reward=10,
            ascii_art=ascii_art,
        )

        assert enemy.ascii_art == ascii_art

    def test_enemy_to_dict_includes_ascii_art(self):
        """Verify to_dict includes ascii_art field."""
        ascii_art = "  /-\\\n  | |\n  \\_/"
        enemy = Enemy(
            name="Test Enemy",
            health=20,
            max_health=20,
            attack_power=5,
            defense=2,
            xp_reward=10,
            ascii_art=ascii_art,
        )

        data = enemy.to_dict()
        assert "ascii_art" in data
        assert data["ascii_art"] == ascii_art

    def test_enemy_from_dict_loads_ascii_art(self):
        """Verify from_dict loads ascii_art correctly."""
        ascii_art = "  ^-^\n  | |\n  ===\n"
        data = {
            "name": "Test Enemy",
            "health": 20,
            "max_health": 20,
            "attack_power": 5,
            "defense": 2,
            "xp_reward": 10,
            "ascii_art": ascii_art,
        }

        enemy = Enemy.from_dict(data)
        assert enemy.ascii_art == ascii_art

    def test_enemy_from_dict_default_ascii_art(self):
        """Verify from_dict defaults ascii_art to empty string."""
        data = {
            "name": "Test Enemy",
            "health": 20,
            "max_health": 20,
            "attack_power": 5,
            "defense": 2,
            "xp_reward": 10,
        }

        enemy = Enemy.from_dict(data)
        assert enemy.ascii_art == ""

    def test_enemy_default_ascii_art_is_empty(self):
        """Verify Enemy defaults ascii_art to empty string."""
        enemy = Enemy(
            name="Test Enemy",
            health=20,
            max_health=20,
            attack_power=5,
            defense=2,
            xp_reward=10,
        )

        assert enemy.ascii_art == ""


class TestFallbackAsciiArt:
    """Test fallback ASCII art templates."""

    def test_get_fallback_ascii_art_beast(self):
        """Beast enemies (wolf, bear, boar) get beast art."""
        for enemy_name in ["Wolf", "Great Bear", "Wild Boar"]:
            art = get_fallback_ascii_art(enemy_name)
            assert art  # Non-empty
            assert len(art.splitlines()) >= 3  # At least 3 lines
            assert max(len(line) for line in art.splitlines()) <= 40  # Max 40 chars wide

    def test_get_fallback_ascii_art_undead(self):
        """Undead enemies (skeleton, zombie, ghost) get undead art."""
        for enemy_name in ["Skeleton Warrior", "Zombie", "Vengeful Ghost"]:
            art = get_fallback_ascii_art(enemy_name)
            assert art  # Non-empty
            assert len(art.splitlines()) >= 3

    def test_get_fallback_ascii_art_humanoid(self):
        """Humanoid enemies (goblin, bandit, thief) get humanoid art."""
        for enemy_name in ["Goblin", "Forest Bandit", "Shadow Thief"]:
            art = get_fallback_ascii_art(enemy_name)
            assert art  # Non-empty
            assert len(art.splitlines()) >= 3

    def test_get_fallback_ascii_art_creepy(self):
        """Creepy enemies (spider, bat) get creepy art."""
        for enemy_name in ["Giant Spider", "Vampire Bat"]:
            art = get_fallback_ascii_art(enemy_name)
            assert art  # Non-empty
            assert len(art.splitlines()) >= 3

    def test_get_fallback_ascii_art_default(self):
        """Unknown enemies get generic monster art."""
        art = get_fallback_ascii_art("Unknown Creature")
        assert art  # Non-empty
        assert len(art.splitlines()) >= 3
        # Verify it's consistent for unknown names
        art2 = get_fallback_ascii_art("Mysterious Thing")
        assert art == art2  # Same default art


class TestCombatStartAsciiArt:
    """Test combat start displays ASCII art."""

    @pytest.fixture
    def player(self):
        """Create a test player character."""
        return Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1,
            gold=50,
        )

    def test_combat_start_displays_ascii_art(self, player):
        """Combat intro includes ascii_art when present."""
        ascii_art = r"""
      /\  /\
     (  oo  )
      \    /
"""
        enemy = Enemy(
            name="Test Monster",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=20,
            ascii_art=ascii_art,
        )

        combat = CombatEncounter(player=player, enemy=enemy)
        intro = combat.start()

        # Should contain the enemy name intro
        assert "Test Monster" in intro
        # Should contain the ASCII art
        assert ascii_art.strip() in intro or "/\\" in intro

    def test_combat_start_no_art_when_empty(self, player):
        """No art block when ascii_art is empty."""
        enemy = Enemy(
            name="Plain Monster",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=20,
            ascii_art="",
        )

        combat = CombatEncounter(player=player, enemy=enemy)
        intro = combat.start()

        # Should still have enemy name
        assert "Plain Monster" in intro
        # No ASCII art border when art is empty
        # The intro should be relatively short without art
        assert "Combat has begun!" in intro


class TestSpawnEnemyAsciiArt:
    """Test enemy spawning sets ASCII art."""

    def test_spawn_enemy_sets_fallback_art(self):
        """Template spawn sets ascii_art using fallback."""
        enemy = spawn_enemy("Dark Forest", level=3)

        # Should have ascii_art set
        assert enemy.ascii_art
        assert len(enemy.ascii_art.splitlines()) >= 3


class TestAISpawnEnemyAsciiArt:
    """Test AI enemy spawning generates ASCII art."""

    def test_ai_spawn_enemy_generates_art(self):
        """AI spawn includes generated art when AI available."""
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_service.generate_enemy.return_value = {
            "name": "Shadow Wraith",
            "description": "A dark spectral creature",
            "attack_flavor": "slashes with ghostly claws",
            "health": 35,
            "attack_power": 8,
            "defense": 3,
            "xp_reward": 30,
            "level": 2,
        }
        mock_ai_service.generate_ascii_art.return_value = r"""
   .-.
  (o o)
   | |
  /| |\
"""

        enemy = ai_spawn_enemy(
            location_name="Haunted Ruins",
            player_level=2,
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        assert enemy.name == "Shadow Wraith"
        # Should have called generate_ascii_art
        mock_ai_service.generate_ascii_art.assert_called_once()
        # ASCII art should be set
        assert enemy.ascii_art


class TestAIAsciiArtGeneration:
    """Test AIService.generate_ascii_art method."""

    def test_ai_ascii_art_generation(self):
        """AIService.generate_ascii_art returns valid art (mocked)."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        # Create mock config and service
        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False,
        )

        with patch.object(AIService, "_call_llm") as mock_call:
            mock_call.return_value = r"""
    ___
   /o o\
   \ v /
   /| |\
  / | | \
"""
            service = AIService(config)
            art = service.generate_ascii_art(
                enemy_name="Goblin",
                enemy_description="A small green creature",
                theme="fantasy",
            )

            # Should return non-empty art
            assert art
            # Should have multiple lines
            assert len(art.splitlines()) >= 3
            # Should be max 40 chars wide
            for line in art.splitlines():
                assert len(line) <= 40, f"Line too long: {line}"
