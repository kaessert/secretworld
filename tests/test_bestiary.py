"""Tests for the bestiary feature - tracking defeated enemies."""
import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.location import Location


class TestRecordEnemyDefeat:
    """Tests for Character.record_enemy_defeat() method.

    Spec: First kill stores enemy data with count=1
    """

    def test_record_first_enemy_defeat(self):
        """First kill stores enemy data with count=1."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(
            name="Goblin Scout",
            health=20,
            max_health=20,
            attack_power=8,
            defense=3,
            xp_reward=25,
            level=2,
            description="A small, green-skinned creature with beady eyes"
        )

        character.record_enemy_defeat(enemy)

        assert "goblin scout" in character.bestiary
        entry = character.bestiary["goblin scout"]
        assert entry["count"] == 1
        assert entry["enemy_data"]["name"] == "Goblin Scout"
        assert entry["enemy_data"]["level"] == 2
        assert entry["enemy_data"]["attack_power"] == 8
        assert entry["enemy_data"]["defense"] == 3
        assert entry["enemy_data"]["description"] == "A small, green-skinned creature with beady eyes"

    def test_record_enemy_defeat_stores_ascii_art(self):
        """Spec: First kill stores enemy ascii_art in bestiary."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        ascii_art = """
   /\\
  /  \\
 / oo \\
 \\    /
  \\  /
   \\/
"""
        enemy = Enemy(
            name="Triangle Monster",
            health=30,
            max_health=30,
            attack_power=10,
            defense=5,
            xp_reward=30,
            level=3,
            description="A bizarre triangular creature",
            ascii_art=ascii_art
        )

        character.record_enemy_defeat(enemy)

        assert "triangle monster" in character.bestiary
        entry = character.bestiary["triangle monster"]
        assert entry["enemy_data"]["ascii_art"] == ascii_art

    def test_record_repeated_enemy_defeat(self):
        """Spec: Repeated kills increment count."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(
            name="Goblin Scout",
            health=20,
            max_health=20,
            attack_power=8,
            defense=3,
            xp_reward=25,
            level=2,
            description="A small, green-skinned creature"
        )

        character.record_enemy_defeat(enemy)
        character.record_enemy_defeat(enemy)
        character.record_enemy_defeat(enemy)

        entry = character.bestiary["goblin scout"]
        assert entry["count"] == 3

    def test_record_different_enemies(self):
        """Spec: Multiple enemy types tracked separately."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        goblin = Enemy(
            name="Goblin Scout",
            health=20,
            max_health=20,
            attack_power=8,
            defense=3,
            xp_reward=25,
            level=2,
            description="A small green creature"
        )
        wolf = Enemy(
            name="Shadow Wolf",
            health=40,
            max_health=40,
            attack_power=12,
            defense=5,
            xp_reward=50,
            level=4,
            description="A spectral wolf"
        )

        character.record_enemy_defeat(goblin)
        character.record_enemy_defeat(goblin)
        character.record_enemy_defeat(wolf)

        assert len(character.bestiary) == 2
        assert character.bestiary["goblin scout"]["count"] == 2
        assert character.bestiary["shadow wolf"]["count"] == 1
        assert character.bestiary["shadow wolf"]["enemy_data"]["level"] == 4


class TestBestiarySerialization:
    """Tests for bestiary serialization in to_dict/from_dict.

    Spec: to_dict/from_dict preserves bestiary
    """

    def test_bestiary_serialization(self):
        """Bestiary is preserved through to_dict/from_dict cycle."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(
            name="Goblin Scout",
            health=20,
            max_health=20,
            attack_power=8,
            defense=3,
            xp_reward=25,
            level=2,
            description="A small green creature"
        )

        character.record_enemy_defeat(enemy)
        character.record_enemy_defeat(enemy)

        # Serialize and deserialize
        data = character.to_dict()
        restored = Character.from_dict(data)

        assert "goblin scout" in restored.bestiary
        assert restored.bestiary["goblin scout"]["count"] == 2
        assert restored.bestiary["goblin scout"]["enemy_data"]["name"] == "Goblin Scout"
        assert restored.bestiary["goblin scout"]["enemy_data"]["level"] == 2

    def test_bestiary_empty_serialization(self):
        """Empty bestiary is preserved through serialization."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        data = character.to_dict()
        restored = Character.from_dict(data)

        assert restored.bestiary == {}

    def test_bestiary_backward_compatibility(self):
        """Old saves without bestiary field should work (default to empty dict)."""
        # Simulate old save data without bestiary field
        old_save_data = {
            "name": "OldHero",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
            "health": 150,
            "max_health": 150,
            "xp": 0,
            "gold": 0,
            "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None},
            "quests": []
        }

        restored = Character.from_dict(old_save_data)

        assert hasattr(restored, "bestiary")
        assert restored.bestiary == {}


class TestBestiaryCommand:
    """Tests for the bestiary command handler.

    Spec: bestiary command shows formatted enemy list
    """

    def test_bestiary_command_empty(self):
        """Shows 'No enemies defeated yet' when bestiary is empty."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Test Location": Location(
                name="Test Location",
                description="A test place"
            )
        }
        game_state = GameState(character, world, starting_location="Test Location")

        continue_game, message = handle_exploration_command(game_state, "bestiary", [])

        assert continue_game is True
        assert "Bestiary" in message
        assert "No enemies defeated yet" in message

    def test_bestiary_command_with_kills(self):
        """Shows formatted enemy list with kills."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        goblin = Enemy(
            name="Goblin Scout",
            health=20,
            max_health=20,
            attack_power=8,
            defense=3,
            xp_reward=25,
            level=2,
            description="A small, green-skinned creature"
        )
        wolf = Enemy(
            name="Shadow Wolf",
            health=40,
            max_health=40,
            attack_power=12,
            defense=5,
            xp_reward=50,
            level=4,
            description="A spectral wolf"
        )

        character.record_enemy_defeat(goblin)
        character.record_enemy_defeat(goblin)
        character.record_enemy_defeat(goblin)
        character.record_enemy_defeat(wolf)

        world = {
            "Test Location": Location(
                name="Test Location",
                description="A test place"
            )
        }
        game_state = GameState(character, world, starting_location="Test Location")

        continue_game, message = handle_exploration_command(game_state, "bestiary", [])

        assert continue_game is True
        assert "Bestiary" in message
        assert "Goblin Scout" in message
        assert "x3" in message
        assert "Shadow Wolf" in message
        assert "x1" in message
        assert "Level 2" in message
        assert "Level 4" in message
        assert "ATK: 8" in message
        assert "DEF: 3" in message
        assert "Total enemies defeated: 4" in message

    def test_bestiary_command_shows_ascii_art(self):
        """Spec: Bestiary command displays ASCII art for discovered enemies."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        ascii_art = """  /\\_/\\
 ( o.o )
  > ^ <"""
        enemy = Enemy(
            name="Cat Monster",
            health=20,
            max_health=20,
            attack_power=8,
            defense=3,
            xp_reward=25,
            level=2,
            description="A ferocious feline"
        )
        enemy.ascii_art = ascii_art

        character.record_enemy_defeat(enemy)

        world = {
            "Test Location": Location(
                name="Test Location",
                description="A test place"
            )
        }
        game_state = GameState(character, world, starting_location="Test Location")

        continue_game, message = handle_exploration_command(game_state, "bestiary", [])

        assert continue_game is True
        assert "Cat Monster" in message
        # Check that ASCII art lines are in the output
        assert "/\\_/\\" in message
        assert "( o.o )" in message
        assert "> ^ <" in message

    def test_bestiary_backward_compat_no_ascii_art(self):
        """Spec: Old saves without ascii_art in bestiary entries still work."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        # Manually create bestiary entry without ascii_art (simulating old save)
        character.bestiary["old goblin"] = {
            "count": 5,
            "enemy_data": {
                "name": "Old Goblin",
                "level": 3,
                "attack_power": 10,
                "defense": 4,
                "description": "An old-style goblin from an old save",
                "is_boss": False,
                # No ascii_art field - simulating old save format
            }
        }

        world = {
            "Test Location": Location(
                name="Test Location",
                description="A test place"
            )
        }
        game_state = GameState(character, world, starting_location="Test Location")

        # This should not crash, even without ascii_art
        continue_game, message = handle_exploration_command(game_state, "bestiary", [])

        assert continue_game is True
        assert "Old Goblin" in message
        assert "x5" in message
        assert "Level 3" in message

    def test_bestiary_alias(self):
        """'b' works as alias for 'bestiary'."""
        command, args = parse_command("b")
        assert command == "bestiary"
        assert args == []


class TestCombatBestiaryIntegration:
    """Tests for combat integration with bestiary tracking."""

    def test_combat_victory_records_enemy(self):
        """Combat victory calls record_enemy_defeat via handle_combat_command."""
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.main import handle_combat_command

        character = Character(name="Hero", strength=20, dexterity=10, intelligence=10)
        enemy = Enemy(
            name="Test Goblin",
            health=1,  # Very low health so attack kills it
            max_health=20,
            attack_power=5,
            defense=0,
            xp_reward=25,
            level=1,
            description="A test enemy"
        )

        world = {
            "Test Location": Location(
                name="Test Location",
                description="A test place"
            )
        }
        game_state = GameState(character, world, starting_location="Test Location")

        # Start combat
        combat = CombatEncounter(character, enemy)
        combat.start()
        game_state.current_combat = combat

        # Attack should defeat enemy (1 HP)
        continue_game, message = handle_combat_command(game_state, "attack", [])

        # Verify combat ended
        assert game_state.current_combat is None
        assert "Victory" in message or "defeated" in message

        # Verify enemy was recorded in bestiary
        assert "test goblin" in character.bestiary
        assert character.bestiary["test goblin"]["count"] == 1
        assert character.bestiary["test goblin"]["enemy_data"]["name"] == "Test Goblin"

    def test_cast_victory_records_enemy(self):
        """Cast victory also records enemy in bestiary."""
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.main import handle_combat_command

        character = Character(name="Mage", strength=5, dexterity=5, intelligence=20)
        enemy = Enemy(
            name="Weak Slime",
            health=1,
            max_health=10,
            attack_power=2,
            defense=0,
            xp_reward=10,
            level=1,
            description="A wobbly slime"
        )

        world = {
            "Test Location": Location(
                name="Test Location",
                description="A test place"
            )
        }
        game_state = GameState(character, world, starting_location="Test Location")

        # Start combat
        combat = CombatEncounter(character, enemy)
        combat.start()
        game_state.current_combat = combat

        # Cast should defeat enemy
        continue_game, message = handle_combat_command(game_state, "cast", [])

        # Verify enemy was recorded in bestiary
        assert "weak slime" in character.bestiary
        assert character.bestiary["weak slime"]["count"] == 1
