"""Tests for Ranger class abilities: track command and wilderness bonus.

Spec: Ranger class abilities to bring parity with Warrior (bash), Mage (fireball/ice_bolt/heal), and Rogue (sneak):
- `track` command for detecting enemies in adjacent locations
- Wilderness bonus for combat damage in forest/wilderness locations
"""

import random
from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState
from cli_rpg.combat import CombatEncounter


class TestTrackCommand:
    """Test cases for Ranger track command."""

    def _create_ranger(self, perception: int = 10, stamina: int = 100) -> Character:
        """Create a Ranger character with specified stats."""
        char = Character(
            name="Ranger",
            strength=10,
            dexterity=10,
            intelligence=10,
            perception=perception,
            character_class=CharacterClass.RANGER,
        )
        char.stamina = stamina
        return char

    def _create_game_state_with_world(self, character: Character) -> GameState:
        """Create a game state with a test world."""
        town = Location(
            name="Town Square",
            description="A peaceful town square.",
            coordinates=(0, 0),
            category="town",
        )
        forest = Location(
            name="Dark Forest",
            description="A dark forest with enemies lurking.",
            coordinates=(0, 1),
            category="forest",
        )
        # Add bidirectional connections
        town.add_connection("north", "Dark Forest")
        forest.add_connection("south", "Town Square")

        world = {"Town Square": town, "Dark Forest": forest}
        return GameState(character=character, world=world, starting_location="Town Square")

    def test_track_only_available_to_ranger(self):
        """Spec: Only Rangers can use track - other classes get 'Only Rangers can track!'"""
        from cli_rpg.ranger import execute_track

        # Test with Warrior
        warrior = Character(
            name="Warrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        world = {"Town": Location(name="Town", description="A town.", coordinates=(0, 0))}
        game_state = GameState(character=warrior, world=world, starting_location="Town")

        success, message = execute_track(game_state)

        assert success is False
        assert "Only Rangers can track" in message

    def test_track_costs_10_stamina(self):
        """Spec: Track costs 10 stamina."""
        from cli_rpg.ranger import execute_track

        ranger = self._create_ranger(stamina=100)
        game_state = self._create_game_state_with_world(ranger)

        initial_stamina = ranger.stamina

        # Force success by mocking random
        with patch("random.random", return_value=0.0):  # Always succeed
            execute_track(game_state)

        assert ranger.stamina == initial_stamina - 10

    def test_track_fails_without_stamina(self):
        """Spec: Track fails with <10 stamina and returns error."""
        from cli_rpg.ranger import execute_track

        ranger = self._create_ranger(stamina=5)
        game_state = self._create_game_state_with_world(ranger)

        success, message = execute_track(game_state)

        assert success is False
        assert "stamina" in message.lower()
        # Stamina should not be consumed on failure
        assert ranger.stamina == 5

    def test_track_detects_enemies_in_adjacent_locations(self):
        """Spec: Track reports enemy types and counts in connected locations."""
        from cli_rpg.ranger import execute_track

        ranger = self._create_ranger(perception=15)

        # Create world with enemies in adjacent location
        town = Location(
            name="Town Square",
            description="A town.",
            coordinates=(0, 0),
            category="town",
        )
        forest = Location(
            name="Dark Forest",
            description="A forest.",
            coordinates=(0, 1),
            category="forest",
        )
        town.add_connection("north", "Dark Forest")
        forest.add_connection("south", "Town Square")

        world = {"Town Square": town, "Dark Forest": forest}
        game_state = GameState(character=ranger, world=world, starting_location="Town Square")

        # Mock the tracking roll to succeed and simulate enemies in forest
        with patch("random.random", return_value=0.0):  # Always succeed
            with patch("cli_rpg.ranger._get_location_enemies") as mock_enemies:
                mock_enemies.return_value = [("Dark Forest", [("Wolf", 2), ("Bear", 1)])]
                success, message = execute_track(game_state)

        assert success is True
        assert "Dark Forest" in message or "north" in message.lower()

    def test_track_fails_during_combat(self):
        """Spec: Cannot use track while in combat."""
        from cli_rpg.ranger import execute_track

        ranger = self._create_ranger()
        game_state = self._create_game_state_with_world(ranger)

        # Start combat
        enemy = Enemy(
            name="Wolf",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        game_state.current_combat = CombatEncounter(player=ranger, enemy=enemy)
        game_state.current_combat.start()

        success, message = execute_track(game_state)

        assert success is False
        assert "combat" in message.lower()

    def test_track_reports_safe_when_no_enemies(self):
        """Spec: Track reports 'No enemies detected nearby' when no enemies."""
        from cli_rpg.ranger import execute_track

        ranger = self._create_ranger(perception=15)
        game_state = self._create_game_state_with_world(ranger)

        # Mock to succeed and return no enemies
        with patch("random.random", return_value=0.0):  # Always succeed
            with patch("cli_rpg.ranger._get_location_enemies") as mock_enemies:
                mock_enemies.return_value = []
                success, message = execute_track(game_state)

        assert success is True
        assert "no enemies" in message.lower() or "safe" in message.lower()

    def test_track_success_scales_with_perception(self):
        """Spec: Higher PER = higher success rate (base 50% + 3% per PER)."""
        from cli_rpg.ranger import TRACK_BASE_CHANCE, TRACK_PER_BONUS

        # Base chance is 50%, +3% per PER
        # PER 10 = 50 + 30 = 80%
        # PER 15 = 50 + 45 = 95%
        # PER 5 = 50 + 15 = 65%

        # Verify constants are as specified
        assert TRACK_BASE_CHANCE == 50
        assert TRACK_PER_BONUS == 3

        # Test that higher PER gives higher calculated chance
        per_10_chance = TRACK_BASE_CHANCE + (10 * TRACK_PER_BONUS)
        per_15_chance = TRACK_BASE_CHANCE + (15 * TRACK_PER_BONUS)

        assert per_15_chance > per_10_chance
        assert per_10_chance == 80  # 50 + 30
        assert per_15_chance == 95  # 50 + 45


class TestWildernessBonus:
    """Test cases for Ranger wilderness combat bonus."""

    def _create_character(self, character_class: CharacterClass) -> Character:
        """Create a character with specified class."""
        return Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=character_class,
        )

    def _create_combat(
        self,
        player: Character,
        enemy: Enemy,
        location_category: str = None,
    ) -> CombatEncounter:
        """Create a combat encounter with optional location category."""
        combat = CombatEncounter(player=player, enemy=enemy, location_category=location_category)
        combat.start()
        return combat

    def test_ranger_wilderness_bonus_in_forest(self):
        """Spec: Ranger gets +15% damage in forest category locations."""
        ranger = self._create_character(CharacterClass.RANGER)
        enemy = Enemy(
            name="Wolf",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,  # No defense for easy damage calc
            xp_reward=25,
        )

        # Create combat with forest category
        combat = self._create_combat(ranger, enemy, location_category="forest")

        # Mock random to avoid critical hits
        with patch("random.random", return_value=1.0):  # No crit
            _, _ = combat.player_attack()

        # Base damage = strength (10), with 15% bonus = 11.5 -> 11 (int)
        # Enemy took 11 damage (100 - 89)
        expected_damage = int(ranger.strength * 1.15)
        assert enemy.health == 100 - expected_damage

    def test_ranger_wilderness_bonus_in_wilderness(self):
        """Spec: Ranger gets +15% damage in wilderness category locations."""
        ranger = self._create_character(CharacterClass.RANGER)
        enemy = Enemy(
            name="Bear",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=25,
        )

        combat = self._create_combat(ranger, enemy, location_category="wilderness")

        with patch("random.random", return_value=1.0):
            _, _ = combat.player_attack()

        expected_damage = int(ranger.strength * 1.15)
        assert enemy.health == 100 - expected_damage

    def test_ranger_no_bonus_in_dungeon(self):
        """Spec: Ranger does not get wilderness bonus in dungeon category."""
        ranger = self._create_character(CharacterClass.RANGER)
        enemy = Enemy(
            name="Skeleton",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=25,
        )

        combat = self._create_combat(ranger, enemy, location_category="dungeon")

        with patch("random.random", return_value=1.0):
            _, _ = combat.player_attack()

        # No bonus - base damage = strength (10)
        expected_damage = ranger.strength
        assert enemy.health == 100 - expected_damage

    def test_ranger_no_bonus_in_town(self):
        """Spec: Ranger does not get wilderness bonus in town category."""
        ranger = self._create_character(CharacterClass.RANGER)
        enemy = Enemy(
            name="Bandit",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=25,
        )

        combat = self._create_combat(ranger, enemy, location_category="town")

        with patch("random.random", return_value=1.0):
            _, _ = combat.player_attack()

        expected_damage = ranger.strength
        assert enemy.health == 100 - expected_damage

    def test_non_ranger_no_wilderness_bonus(self):
        """Spec: Warriors/Mages/Rogues don't get wilderness bonus."""
        for char_class in [CharacterClass.WARRIOR, CharacterClass.MAGE, CharacterClass.ROGUE]:
            character = self._create_character(char_class)
            enemy = Enemy(
                name="Wolf",
                health=100,
                max_health=100,
                attack_power=5,
                defense=0,
                xp_reward=25,
            )

            combat = self._create_combat(character, enemy, location_category="forest")

            with patch("random.random", return_value=1.0):
                _, _ = combat.player_attack()

            # Calculate expected damage (base strength + class bonuses)
            expected_damage = character.strength  # Just strength, no bonus
            assert enemy.health == 100 - expected_damage, f"{char_class.value} should not get wilderness bonus"

            # Reset for next iteration
            enemy.health = 100
