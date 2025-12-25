"""Tests for distance-based enemy difficulty scaling.

Spec: Scale enemy stats based on Manhattan distance from origin (0,0).
Formula: base_stat * (1 + distance * 0.15)

Distance tiers:
- Near (0-3): Easy (multiplier 1.0-1.45)
- Mid (4-7): Moderate (multiplier 1.6-2.05)
- Far (8-12): Challenging (multiplier 2.2-2.8)
- Deep (13+): Dangerous (multiplier 2.95+)
"""

from typing import Optional, Tuple
import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.combat import (
    calculate_distance_from_origin,
    get_distance_multiplier,
    spawn_enemy,
    spawn_enemies,
    ai_spawn_enemy,
)
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState


class TestDistanceCalculation:
    """Tests for calculate_distance_from_origin utility function."""

    def test_distance_from_origin_at_origin(self):
        """Distance at (0,0) should be 0."""
        # Spec: Distance at origin is 0
        assert calculate_distance_from_origin((0, 0)) == 0

    def test_distance_from_origin_manhattan(self):
        """Distance should be Manhattan distance: |x| + |y|."""
        # Spec: Manhattan distance formula
        assert calculate_distance_from_origin((3, 4)) == 7
        assert calculate_distance_from_origin((-2, 5)) == 7
        assert calculate_distance_from_origin((5, -5)) == 10
        assert calculate_distance_from_origin((-3, -4)) == 7

    def test_distance_from_origin_single_axis(self):
        """Distance along single axis should be absolute value."""
        # Spec: Manhattan distance on single axis
        assert calculate_distance_from_origin((5, 0)) == 5
        assert calculate_distance_from_origin((0, 3)) == 3
        assert calculate_distance_from_origin((-7, 0)) == 7

    def test_distance_from_origin_none(self):
        """None coordinates should return 0 (fallback for legacy locations)."""
        # Spec: None coordinates default to distance 0
        assert calculate_distance_from_origin(None) == 0


class TestDistanceMultiplier:
    """Tests for get_distance_multiplier utility function."""

    def test_multiplier_at_origin(self):
        """At distance 0, multiplier is 1.0."""
        # Spec: multiplier = 1 + distance * 0.15 = 1 + 0 = 1.0
        assert get_distance_multiplier(0) == 1.0

    def test_multiplier_scales_linearly(self):
        """Multiplier follows formula: 1 + distance * 0.15"""
        # Spec: multiplier = 1 + distance * 0.15
        assert get_distance_multiplier(1) == 1.15
        assert get_distance_multiplier(10) == 2.5
        assert get_distance_multiplier(20) == 4.0

    def test_multiplier_near_tier(self):
        """Near tier (0-3) gives multipliers 1.0-1.45."""
        # Spec: Near tier multipliers
        assert get_distance_multiplier(0) == 1.0
        assert get_distance_multiplier(3) == 1.45

    def test_multiplier_mid_tier(self):
        """Mid tier (4-7) gives multipliers 1.6-2.05."""
        # Spec: Mid tier multipliers
        assert get_distance_multiplier(4) == 1.6
        assert get_distance_multiplier(7) == 2.05

    def test_multiplier_far_tier(self):
        """Far tier (8-12) gives multipliers 2.2-2.8."""
        # Spec: Far tier multipliers
        assert get_distance_multiplier(8) == 2.2
        assert get_distance_multiplier(12) == 2.8

    def test_multiplier_deep_tier(self):
        """Deep tier (13+) gives multipliers 2.95+."""
        # Spec: Deep tier multipliers
        assert get_distance_multiplier(13) == 2.95
        assert get_distance_multiplier(20) == 4.0


class TestEnemyDistanceScaling:
    """Tests for spawn_enemy distance-based stat scaling."""

    def test_spawn_enemy_stats_scale_with_distance(self):
        """Enemies at greater distance have higher stats."""
        # Spec: Stats scale with distance multiplier
        near = spawn_enemy("forest", level=1, distance=0)
        far = spawn_enemy("forest", level=1, distance=10)

        # At distance 10, multiplier is 2.5
        assert far.max_health > near.max_health
        assert far.attack_power > near.attack_power
        assert far.xp_reward > near.xp_reward

    def test_spawn_enemy_distance_zero_unchanged(self):
        """At distance 0, stats match original formulas."""
        # Spec: At distance 0, multiplier is 1.0 (no change)
        # Base formulas: health=20+(level*10), attack=3+(level*2), defense=1+level, xp=20+(level*10)
        enemy = spawn_enemy("forest", level=3, distance=0)
        assert enemy.max_health == 20 + (3 * 10)  # 50
        assert enemy.attack_power == 3 + (3 * 2)  # 9
        assert enemy.defense == 1 + 3  # 4
        assert enemy.xp_reward == 20 + (3 * 10)  # 50

    def test_spawn_enemy_distance_scaling_formula(self):
        """Stats follow formula: base_stat * (1 + distance * 0.15)."""
        # Spec: multiplier = 1 + distance * 0.15
        # At distance 10, multiplier = 2.5
        enemy = spawn_enemy("forest", level=1, distance=10)

        # Base values at level 1: health=30, attack=5, defense=2, xp=30
        base_health = 20 + (1 * 10)  # 30
        base_attack = 3 + (1 * 2)  # 5
        base_defense = 1 + 1  # 2
        base_xp = 20 + (1 * 10)  # 30

        multiplier = 2.5
        assert enemy.max_health == int(base_health * multiplier)  # 75
        assert enemy.attack_power == int(base_attack * multiplier)  # 12
        assert enemy.defense == int(base_defense * multiplier)  # 5
        assert enemy.xp_reward == int(base_xp * multiplier)  # 75

    def test_spawn_enemy_default_distance_zero(self):
        """When distance not provided, defaults to 0 (original behavior)."""
        # Spec: Backward compatibility - distance defaults to 0
        enemy_no_distance = spawn_enemy("forest", level=1)
        enemy_zero_distance = spawn_enemy("forest", level=1, distance=0)

        # Should have same stats (both use multiplier 1.0)
        assert enemy_no_distance.max_health == enemy_zero_distance.max_health
        assert enemy_no_distance.attack_power == enemy_zero_distance.attack_power


class TestSpawnEnemiesDistanceScaling:
    """Tests for spawn_enemies distance parameter propagation."""

    def test_spawn_enemies_passes_distance(self):
        """spawn_enemies should pass distance to spawn_enemy."""
        # Spec: spawn_enemies propagates distance parameter
        enemies_near = spawn_enemies("forest", level=1, count=1, distance=0)
        enemies_far = spawn_enemies("forest", level=1, count=1, distance=10)

        assert enemies_far[0].max_health > enemies_near[0].max_health
        assert enemies_far[0].attack_power > enemies_near[0].attack_power

    def test_spawn_enemies_default_distance_zero(self):
        """When distance not provided, defaults to 0."""
        # Spec: Backward compatibility
        enemies = spawn_enemies("forest", level=1, count=1)
        # At distance 0, base health at level 1 = 30
        assert enemies[0].max_health == 30


class TestAISpawnEnemyDistanceScaling:
    """Tests for ai_spawn_enemy distance-based scaling."""

    def test_ai_spawn_enemy_fallback_uses_distance(self):
        """When AI unavailable, fallback spawn uses distance."""
        # Spec: AI fallback uses distance parameter
        near = ai_spawn_enemy("forest", player_level=1, ai_service=None, distance=0)
        far = ai_spawn_enemy("forest", player_level=1, ai_service=None, distance=10)

        assert far.max_health > near.max_health
        assert far.attack_power > near.attack_power

    def test_ai_spawn_enemy_default_distance_zero(self):
        """When distance not provided, defaults to 0."""
        # Spec: Backward compatibility
        enemy = ai_spawn_enemy("forest", player_level=1, ai_service=None)
        # At distance 0, base health at level 1 = 30
        assert enemy.max_health == 30

    def test_ai_spawn_enemy_scales_ai_generated_stats(self):
        """AI-generated enemy stats should be scaled by distance."""
        # Spec: AI enemy stats scaled by distance multiplier
        mock_ai = MagicMock()
        mock_ai.generate_enemy.return_value = {
            "name": "Dark Wolf",
            "description": "A shadowy wolf",
            "health": 30,
            "attack_power": 5,
            "defense": 2,
            "xp_reward": 30,
            "level": 1,
            "attack_flavor": "lunges",
        }
        mock_ai.generate_ascii_art.side_effect = Exception("Skip art")

        # At distance 10, multiplier = 2.5
        enemy = ai_spawn_enemy("forest", player_level=1, ai_service=mock_ai, distance=10)

        # Stats should be scaled
        assert enemy.max_health == int(30 * 2.5)  # 75
        assert enemy.attack_power == int(5 * 2.5)  # 12
        assert enemy.defense == int(2 * 2.5)  # 5
        assert enemy.xp_reward == int(30 * 2.5)  # 75


class TestGameStateEncounterDistance:
    """Tests for trigger_encounter using location coordinates for distance."""

    def _create_game_state(self, location_coords: Optional[Tuple[int, int]]) -> GameState:
        """Helper to create a GameState with a location at given coordinates."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Location",
            description="A test location",
            coordinates=location_coords,
        )
        world = {"Test Location": location}
        return GameState(character, world, starting_location="Test Location")

    def _create_mock_enemy(self):
        """Helper to create a mock enemy for testing."""
        from cli_rpg.models.enemy import Enemy
        return Enemy(
            name="Test Enemy",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=30,
        )

    @patch("cli_rpg.game_state.spawn_enemies")
    @patch("cli_rpg.game_state.random.random", return_value=0.1)  # Force encounter
    def test_trigger_encounter_uses_location_coordinates(
        self, mock_random, mock_spawn_enemies
    ):
        """Encounters should spawn enemies scaled by location distance."""
        # Spec: Location coordinates determine distance for enemy scaling
        mock_spawn_enemies.return_value = [self._create_mock_enemy()]

        # Location at (5, 5) = distance 10
        gs = self._create_game_state((5, 5))
        gs.trigger_encounter("Test Location")

        # Verify spawn_enemies called with distance=10
        mock_spawn_enemies.assert_called_once()
        call_kwargs = mock_spawn_enemies.call_args.kwargs
        assert call_kwargs.get("distance") == 10

    @patch("cli_rpg.game_state.spawn_enemies")
    @patch("cli_rpg.game_state.random.random", return_value=0.1)
    def test_trigger_encounter_origin_location(self, mock_random, mock_spawn_enemies):
        """Encounters at origin should use distance 0."""
        # Spec: Origin coordinates give distance 0
        mock_spawn_enemies.return_value = [self._create_mock_enemy()]

        gs = self._create_game_state((0, 0))
        gs.trigger_encounter("Test Location")

        call_kwargs = mock_spawn_enemies.call_args.kwargs
        assert call_kwargs.get("distance") == 0

    @patch("cli_rpg.game_state.spawn_enemies")
    @patch("cli_rpg.game_state.random.random", return_value=0.1)
    def test_trigger_encounter_none_coordinates(self, mock_random, mock_spawn_enemies):
        """Locations without coordinates should use distance 0."""
        # Spec: None coordinates default to distance 0
        mock_spawn_enemies.return_value = [self._create_mock_enemy()]

        gs = self._create_game_state(None)
        gs.trigger_encounter("Test Location")

        call_kwargs = mock_spawn_enemies.call_args.kwargs
        assert call_kwargs.get("distance") == 0

    @patch("cli_rpg.game_state.ai_spawn_enemy")
    @patch("cli_rpg.game_state.random.random", return_value=0.1)
    def test_trigger_encounter_ai_uses_distance(self, mock_random, mock_ai_spawn):
        """AI-powered encounters should pass distance parameter."""
        # Spec: AI spawn also uses distance
        from cli_rpg.models.enemy import Enemy

        mock_ai_spawn.return_value = Enemy(
            name="Test",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=30,
        )

        gs = self._create_game_state((3, 4))  # distance = 7
        gs.ai_service = MagicMock()  # Enable AI mode
        gs.trigger_encounter("Test Location")

        call_kwargs = mock_ai_spawn.call_args.kwargs
        assert call_kwargs.get("distance") == 7
