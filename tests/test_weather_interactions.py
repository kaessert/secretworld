"""Tests for weather interactions with combat status effects.

Spec:
- Rain extinguishes fire: When weather is "rain" or "storm", Burn status effects
  on all combatants have a 40% chance to be removed each turn (rain dampens flames)
- Cold weather enhances freeze: When weather is "storm" (cold/harsh), Freeze status
  effects on enemies have their duration extended by 1 turn when applied
"""

import random
from unittest import mock

import pytest

from cli_rpg.combat import CombatEncounter
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.status_effect import StatusEffect
from cli_rpg.models.weather import Weather


def make_test_player() -> Character:
    """Create a test player character."""
    return Character(
        name="TestHero",
        strength=10,
        dexterity=10,
        intelligence=10,
        level=1,
    )


def make_test_enemy(name: str = "TestEnemy") -> Enemy:
    """Create a test enemy."""
    return Enemy(
        name=name,
        health=50,
        max_health=50,
        attack_power=5,
        defense=2,
        xp_reward=20,
        level=1,
    )


def make_burn_effect(duration: int = 3) -> StatusEffect:
    """Create a Burn status effect."""
    return StatusEffect(
        name="Burn",
        effect_type="dot",
        damage_per_turn=5,
        duration=duration,
    )


def make_freeze_effect(duration: int = 2) -> StatusEffect:
    """Create a Freeze status effect."""
    return StatusEffect(
        name="Freeze",
        effect_type="freeze",
        damage_per_turn=0,
        duration=duration,
    )


def has_burn_effect(character: Character) -> bool:
    """Check if character has a Burn status effect."""
    return any(e.name == "Burn" for e in character.status_effects)


def has_freeze_effect(target) -> bool:
    """Check if target has a Freeze status effect."""
    if hasattr(target, "has_effect_type"):
        return target.has_effect_type("freeze")
    return any(e.effect_type == "freeze" for e in target.status_effects)


# ============================================================
# Rain Extinguishes Burn tests
# Spec: Rain/storm have 40% chance to remove Burn each turn
# ============================================================


class TestRainExtinguishesBurn:
    """Tests for rain/storm extinguishing burn effects."""

    def test_rain_can_remove_burn_from_player(self) -> None:
        """Rain has 40% chance to remove Burn from player each turn."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="rain")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to player
        burn = make_burn_effect()
        player.apply_status_effect(burn)
        assert has_burn_effect(player), "Player should have burn effect"

        # Mock random to succeed (below 0.4 threshold)
        with mock.patch("random.random", return_value=0.3):
            messages = combat._check_rain_extinguish()

        assert not has_burn_effect(player), "Burn should be removed"
        assert any("douses" in msg.lower() or "rain" in msg.lower() for msg in messages)

    def test_storm_can_remove_burn_from_player(self) -> None:
        """Storm also has rain component and can extinguish burn."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="storm")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to player
        burn = make_burn_effect()
        player.apply_status_effect(burn)

        # Mock random to succeed
        with mock.patch("random.random", return_value=0.3):
            messages = combat._check_rain_extinguish()

        assert not has_burn_effect(player), "Burn should be removed in storm"
        assert len(messages) > 0

    def test_clear_weather_does_not_remove_burn(self) -> None:
        """Clear weather doesn't affect burn - rain extinguish not called."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="clear")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to player
        burn = make_burn_effect()
        player.apply_status_effect(burn)

        # Enemy turn should not call rain extinguish for clear weather
        # Burn should remain after enemy turn (aside from normal tick)
        original_duration = burn.duration

        # Run enemy turn - burn should NOT be extinguished by rain
        with mock.patch("random.random", return_value=0.3):  # Would succeed if called
            combat.enemy_turn()

        # Effect may have ticked down duration, but should still exist
        # (unless it naturally expired, which it shouldn't with duration=3)
        # Clear weather should not trigger rain extinguish
        assert has_burn_effect(player), "Burn should NOT be removed in clear weather"

    def test_rain_removes_burn_from_enemy(self) -> None:
        """Rain also removes burn from enemies."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="rain")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to enemy
        burn = make_burn_effect()
        enemy.apply_status_effect(burn)
        assert any(e.name == "Burn" for e in enemy.status_effects), "Enemy should have burn effect"

        # Mock random to succeed
        with mock.patch("random.random", return_value=0.3):
            messages = combat._check_rain_extinguish()

        assert not any(e.name == "Burn" for e in enemy.status_effects), "Enemy burn should be removed"
        assert any("extinguish" in msg.lower() or "rain" in msg.lower() for msg in messages)

    def test_rain_extinguish_produces_message(self) -> None:
        """Extinguishing produces flavor message for atmosphere."""
        player = make_test_player()
        enemy = make_test_enemy("FireBeast")
        weather = Weather(condition="rain")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to both
        player.apply_status_effect(make_burn_effect())
        enemy.apply_status_effect(make_burn_effect())

        # Mock random to succeed
        with mock.patch("random.random", return_value=0.3):
            messages = combat._check_rain_extinguish()

        # Should have messages for both extinguished burns
        assert len(messages) == 2
        # Player message
        assert any("your" in msg.lower() for msg in messages)
        # Enemy message should include enemy name
        assert any("firebeast" in msg.lower() for msg in messages)

    def test_rain_extinguish_40_percent_chance(self) -> None:
        """Rain has exactly 40% chance - fails when random >= 0.4."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="rain")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to player
        burn = make_burn_effect()
        player.apply_status_effect(burn)

        # Mock random to fail (at threshold)
        with mock.patch("random.random", return_value=0.4):
            messages = combat._check_rain_extinguish()

        # Burn should NOT be removed (0.4 >= 0.4)
        assert has_burn_effect(player), "Burn should remain when random >= 0.4"
        assert len(messages) == 0

    def test_fog_does_not_remove_burn(self) -> None:
        """Fog weather doesn't affect burn - only rain/storm."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="fog")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to player
        burn = make_burn_effect()
        player.apply_status_effect(burn)

        # Enemy turn with fog - should not extinguish
        with mock.patch("random.random", return_value=0.3):
            combat.enemy_turn()

        # Burn should still exist (fog is not rain/storm)
        assert has_burn_effect(player), "Burn should NOT be removed in fog"


# ============================================================
# Cold Weather Enhances Freeze tests
# Spec: Storm extends Freeze duration by 1 turn when applied
# ============================================================


class TestColdWeatherEnhancesFreeze:
    """Tests for storm weather extending freeze duration."""

    def test_storm_extends_freeze_on_enemy(self) -> None:
        """Storm adds +1 duration to freeze when applied to enemy."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="storm")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Create freeze effect with base duration 2
        freeze = make_freeze_effect(duration=2)
        original_duration = freeze.duration

        # Apply via weather-aware method
        combat.apply_status_effect_with_weather(enemy, freeze)

        # Duration should be extended by 1 in storm
        assert freeze.duration == original_duration + 1
        assert has_freeze_effect(enemy)

    def test_clear_weather_no_freeze_extension(self) -> None:
        """Clear weather doesn't extend freeze duration."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="clear")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Create freeze effect with base duration 2
        freeze = make_freeze_effect(duration=2)
        original_duration = freeze.duration

        # Apply via weather-aware method
        combat.apply_status_effect_with_weather(enemy, freeze)

        # Duration should NOT be extended
        assert freeze.duration == original_duration
        assert has_freeze_effect(enemy)

    def test_rain_no_freeze_extension(self) -> None:
        """Rain doesn't extend freeze (not cold enough)."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="rain")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Create freeze effect with base duration 2
        freeze = make_freeze_effect(duration=2)
        original_duration = freeze.duration

        # Apply via weather-aware method
        combat.apply_status_effect_with_weather(enemy, freeze)

        # Duration should NOT be extended (rain is not cold enough)
        assert freeze.duration == original_duration
        assert has_freeze_effect(enemy)

    def test_fog_no_freeze_extension(self) -> None:
        """Fog doesn't extend freeze."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="fog")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        freeze = make_freeze_effect(duration=2)
        original_duration = freeze.duration

        combat.apply_status_effect_with_weather(enemy, freeze)

        assert freeze.duration == original_duration
        assert has_freeze_effect(enemy)

    def test_storm_extends_freeze_on_player_too(self) -> None:
        """Storm extends freeze on player as well (cold affects everyone)."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="storm")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        freeze = make_freeze_effect(duration=2)
        original_duration = freeze.duration

        combat.apply_status_effect_with_weather(player, freeze)

        # Duration should be extended
        assert freeze.duration == original_duration + 1
        assert has_freeze_effect(player)

    def test_storm_only_extends_freeze_not_other_effects(self) -> None:
        """Storm only extends freeze, not other status effects."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="storm")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Create a non-freeze effect (burn)
        burn = make_burn_effect(duration=3)
        original_duration = burn.duration

        combat.apply_status_effect_with_weather(enemy, burn)

        # Duration should NOT be extended for non-freeze effects
        assert burn.duration == original_duration


# ============================================================
# Integration tests - weather affects combat flow
# ============================================================


class TestWeatherCombatIntegration:
    """Integration tests for weather affecting combat."""

    def test_enemy_turn_calls_rain_extinguish_in_rain(self) -> None:
        """Enemy turn should check rain extinguish when weather is rain."""
        player = make_test_player()
        enemy = make_test_enemy()
        weather = Weather(condition="rain")

        combat = CombatEncounter(player, enemies=[enemy], weather=weather)
        combat.start()

        # Apply burn to player
        player.apply_status_effect(make_burn_effect())

        # Run enemy turn with guaranteed extinguish
        with mock.patch("random.random", return_value=0.3):
            result = combat.enemy_turn()

        # Burn should be removed and message should mention rain
        assert not has_burn_effect(player) or "rain" in result.lower()

    def test_combat_without_weather_works_normally(self) -> None:
        """Combat without weather parameter should work normally."""
        player = make_test_player()
        enemy = make_test_enemy()

        # No weather parameter
        combat = CombatEncounter(player, enemies=[enemy])
        combat.start()

        # Apply burn - should behave normally
        player.apply_status_effect(make_burn_effect())

        combat.enemy_turn()

        # Burn should still exist (no rain to extinguish)
        assert has_burn_effect(player)
