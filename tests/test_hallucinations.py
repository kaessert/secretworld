"""Tests for hallucination system at high dread levels (75%+)."""
import pytest
from unittest.mock import patch

from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState
from cli_rpg.hallucinations import (
    spawn_hallucination,
    check_for_hallucination,
    HALLUCINATION_DREAD_THRESHOLD,
    HALLUCINATION_CHANCE,
    DREAD_REDUCTION_ON_DISPEL,
)


def create_test_character():
    """Create a test character."""
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


def create_test_world():
    """Create a test world with dungeon."""
    town = Location(
        name="Town Square",
        description="A town.",
        coordinates=(0, 0),
        category="town"
    )
    cave = Location(
        name="Dark Cave",
        description="A cave.",
        coordinates=(0, 1),
        category="cave"
    )
    return {"Town Square": town, "Dark Cave": cave}


class TestSpawnHallucination:
    """Test hallucination spawning."""

    def test_spawn_returns_enemy(self):
        """spawn_hallucination returns an Enemy instance."""
        enemy = spawn_hallucination(level=5)
        assert isinstance(enemy, Enemy)

    def test_spawn_is_hallucination_flag(self):
        """Hallucination has is_hallucination=True."""
        enemy = spawn_hallucination(level=1)
        assert enemy.is_hallucination is True

    def test_spawn_has_themed_name(self):
        """Hallucination has one of the themed names."""
        enemy = spawn_hallucination(level=1)
        valid_names = ["Shadow Mimic", "Phantom Shade", "Nightmare Echo"]
        assert enemy.name in valid_names

    def test_spawn_scales_with_level(self):
        """Hallucination stats scale with player level."""
        enemy_low = spawn_hallucination(level=1)
        enemy_high = spawn_hallucination(level=10)
        assert enemy_high.health > enemy_low.health

    def test_spawn_has_description(self):
        """Hallucination has a description."""
        enemy = spawn_hallucination(level=1)
        assert enemy.description != ""

    def test_spawn_has_ascii_art(self):
        """Hallucination has ASCII art."""
        enemy = spawn_hallucination(level=1)
        assert enemy.ascii_art != ""


class TestCheckForHallucination:
    """Test hallucination trigger logic."""

    def test_triggers_at_75_dread(self):
        """Hallucination can trigger at exactly 75% dread."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 75

        # Force trigger (30% chance)
        with patch("cli_rpg.hallucinations.random.random", return_value=0.1):
            result = check_for_hallucination(game_state)

        assert result is not None
        assert game_state.is_in_combat()
        assert game_state.current_combat.enemy.is_hallucination

    def test_no_trigger_below_75(self):
        """Hallucination does not trigger below 75% dread."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 74

        with patch("cli_rpg.hallucinations.random.random", return_value=0.1):
            result = check_for_hallucination(game_state)

        assert result is None
        assert not game_state.is_in_combat()

    def test_no_trigger_at_100_dread(self):
        """Hallucination does not trigger at 100% (shadow creature priority)."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 100

        with patch("cli_rpg.hallucinations.random.random", return_value=0.1):
            result = check_for_hallucination(game_state)

        assert result is None

    def test_no_trigger_if_already_in_combat(self):
        """Hallucination does not trigger if already in combat."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 80

        # Start combat first
        from cli_rpg.combat import CombatEncounter
        dummy = Enemy(name="Goblin", health=10, max_health=10, attack_power=5, defense=1, xp_reward=10)
        game_state.current_combat = CombatEncounter(char, enemies=[dummy])
        game_state.current_combat.is_active = True

        with patch("cli_rpg.hallucinations.random.random", return_value=0.1):
            result = check_for_hallucination(game_state)

        assert result is None

    def test_respects_30_percent_chance(self):
        """Hallucination respects 30% trigger chance."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 80

        # Roll above 30% threshold
        with patch("cli_rpg.hallucinations.random.random", return_value=0.5):
            result = check_for_hallucination(game_state)

        assert result is None


class TestHallucinationCombat:
    """Test hallucination behavior in combat."""

    def test_attacking_hallucination_dispels_it(self):
        """Attacking a hallucination dispels it with special message."""
        char = create_test_character()
        from cli_rpg.combat import CombatEncounter

        hallucination = spawn_hallucination(level=1)
        combat = CombatEncounter(char, enemies=[hallucination])
        combat.start()

        victory, message = combat.player_attack()

        # Hallucination should be removed and combat should end
        assert victory is True  # No enemies left = victory
        assert "dissipate" in message.lower() or "illusion" in message.lower() or "vanish" in message.lower()
        # No damage should be dealt (hallucination just disappears)

    def test_hallucination_dispel_ends_combat(self):
        """Dispelling hallucination ends combat (no enemy turn)."""
        char = create_test_character()
        from cli_rpg.combat import CombatEncounter

        hallucination = spawn_hallucination(level=1)
        combat = CombatEncounter(char, enemies=[hallucination])
        combat.start()

        victory, _ = combat.player_attack()

        assert victory is True
        assert len(combat.get_living_enemies()) == 0


class TestEnemyHallucinationFlag:
    """Test Enemy model hallucination field."""

    def test_enemy_default_not_hallucination(self):
        """Normal enemies have is_hallucination=False by default."""
        enemy = Enemy(name="Wolf", health=20, max_health=20, attack_power=5, defense=2, xp_reward=10)
        assert enemy.is_hallucination is False

    def test_enemy_serialization_roundtrip(self):
        """is_hallucination survives serialization."""
        enemy = Enemy(
            name="Phantom", health=20, max_health=20, attack_power=5,
            defense=2, xp_reward=10, is_hallucination=True
        )
        data = enemy.to_dict()
        restored = Enemy.from_dict(data)
        assert restored.is_hallucination is True

    def test_backward_compat_no_hallucination_field(self):
        """Old saves without is_hallucination load correctly."""
        old_data = {
            "name": "Wolf", "health": 20, "max_health": 20,
            "attack_power": 5, "defense": 2, "xp_reward": 10
        }
        enemy = Enemy.from_dict(old_data)
        assert enemy.is_hallucination is False


class TestDreadReductionOnDispel:
    """Test that dispelling hallucination reduces dread."""

    def test_dread_reduction_constant(self):
        """Verify dread reduction constant is set."""
        assert DREAD_REDUCTION_ON_DISPEL == 5
