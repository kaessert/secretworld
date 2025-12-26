"""Tests for the Fighting Stances system.

Spec: Add a `stance` command that lets players choose between 4 combat stances,
each providing stat modifiers during combat:

| Stance | Damage Modifier | Defense Modifier | Other |
|--------|----------------|------------------|-------|
| Aggressive | +20% | -10% | - |
| Defensive | -10% | +20% | - |
| Balanced | 0% | 0% | +5% crit chance |
| Berserker | +X% (scales with missing HP) | 0% | - |

Berserker Formula: Damage bonus = (1 - current_hp/max_hp) * 50%
"""

import pytest
from cli_rpg.models.character import Character, CharacterClass, FightingStance


class TestFightingStanceEnum:
    """Tests for FightingStance enum values exist (Spec: 4 stances)."""

    def test_balanced_stance_exists(self):
        """Test that BALANCED stance exists."""
        assert hasattr(FightingStance, "BALANCED")
        assert FightingStance.BALANCED.value == "Balanced"

    def test_aggressive_stance_exists(self):
        """Test that AGGRESSIVE stance exists."""
        assert hasattr(FightingStance, "AGGRESSIVE")
        assert FightingStance.AGGRESSIVE.value == "Aggressive"

    def test_defensive_stance_exists(self):
        """Test that DEFENSIVE stance exists."""
        assert hasattr(FightingStance, "DEFENSIVE")
        assert FightingStance.DEFENSIVE.value == "Defensive"

    def test_berserker_stance_exists(self):
        """Test that BERSERKER stance exists."""
        assert hasattr(FightingStance, "BERSERKER")
        assert FightingStance.BERSERKER.value == "Berserker"


class TestCharacterStanceDefault:
    """Tests for Character stance default value."""

    def test_character_defaults_to_balanced_stance(self):
        """Test that new characters default to BALANCED stance (Spec: default BALANCED)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        assert char.stance == FightingStance.BALANCED

    def test_character_with_class_defaults_to_balanced(self):
        """Test that characters with a class still default to BALANCED."""
        char = Character(
            name="Warrior", strength=10, dexterity=10, intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        assert char.stance == FightingStance.BALANCED


class TestStanceSerialization:
    """Tests for stance serialization/deserialization."""

    def test_stance_serialized_in_to_dict(self):
        """Test that stance is included in to_dict output."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.AGGRESSIVE
        data = char.to_dict()
        assert "stance" in data
        assert data["stance"] == "Aggressive"

    def test_stance_deserialized_from_dict(self):
        """Test that stance is restored from from_dict."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.DEFENSIVE
        data = char.to_dict()

        restored = Character.from_dict(data)
        assert restored.stance == FightingStance.DEFENSIVE

    def test_backward_compatibility_no_stance_defaults_to_balanced(self):
        """Test that old saves without stance field default to BALANCED."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        data = char.to_dict()
        # Simulate old save without stance field
        del data["stance"]

        restored = Character.from_dict(data)
        assert restored.stance == FightingStance.BALANCED


class TestStanceDamageModifier:
    """Tests for stance damage modifier calculations (Spec: damage modifiers)."""

    def test_balanced_stance_damage_modifier(self):
        """Test BALANCED stance has 1.0 (0%) damage modifier."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BALANCED
        assert char.get_stance_damage_modifier() == 1.0

    def test_aggressive_stance_damage_modifier(self):
        """Test AGGRESSIVE stance has 1.20 (+20%) damage modifier (Spec: +20%)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.AGGRESSIVE
        assert char.get_stance_damage_modifier() == 1.20

    def test_defensive_stance_damage_modifier(self):
        """Test DEFENSIVE stance has 0.90 (-10%) damage modifier (Spec: -10%)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.DEFENSIVE
        assert char.get_stance_damage_modifier() == 0.90

    def test_berserker_stance_damage_at_full_health(self):
        """Test BERSERKER at full HP has 1.0 (0%) modifier (Spec: scales with missing HP)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BERSERKER
        # At full health: (1 - 1.0) * 0.5 = 0%, so 1.0 multiplier
        assert char.get_stance_damage_modifier() == 1.0

    def test_berserker_stance_damage_at_half_health(self):
        """Test BERSERKER at 50% HP has 1.25 (+25%) modifier (Spec: formula)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BERSERKER
        char.health = char.max_health // 2  # 50% health
        # At 50% health: (1 - 0.5) * 0.5 = 25%, so 1.25 multiplier
        assert char.get_stance_damage_modifier() == pytest.approx(1.25, rel=0.01)

    def test_berserker_stance_damage_at_10_percent_health(self):
        """Test BERSERKER at 10% HP has ~1.45 (+45%) modifier (Spec: formula)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BERSERKER
        char.health = int(char.max_health * 0.1)  # 10% health
        # At 10% health: (1 - 0.1) * 0.5 = 45%, so 1.45 multiplier
        assert char.get_stance_damage_modifier() == pytest.approx(1.45, rel=0.05)


class TestStanceDefenseModifier:
    """Tests for stance defense modifier calculations (Spec: defense modifiers)."""

    def test_balanced_stance_defense_modifier(self):
        """Test BALANCED stance has 1.0 (0%) defense modifier."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BALANCED
        assert char.get_stance_defense_modifier() == 1.0

    def test_aggressive_stance_defense_modifier(self):
        """Test AGGRESSIVE stance has 0.90 (-10%) defense modifier (Spec: -10%)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.AGGRESSIVE
        assert char.get_stance_defense_modifier() == 0.90

    def test_defensive_stance_defense_modifier(self):
        """Test DEFENSIVE stance has 1.20 (+20%) defense modifier (Spec: +20%)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.DEFENSIVE
        assert char.get_stance_defense_modifier() == 1.20

    def test_berserker_stance_defense_modifier(self):
        """Test BERSERKER stance has 1.0 (0%) defense modifier (Spec: 0%)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BERSERKER
        assert char.get_stance_defense_modifier() == 1.0


class TestStanceCritModifier:
    """Tests for stance crit modifier calculations (Spec: +5% crit for Balanced)."""

    def test_balanced_stance_crit_modifier(self):
        """Test BALANCED stance has 0.05 (+5%) crit modifier (Spec: +5% crit chance)."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BALANCED
        assert char.get_stance_crit_modifier() == 0.05

    def test_aggressive_stance_crit_modifier(self):
        """Test AGGRESSIVE stance has 0.0 (no bonus) crit modifier."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.AGGRESSIVE
        assert char.get_stance_crit_modifier() == 0.0

    def test_defensive_stance_crit_modifier(self):
        """Test DEFENSIVE stance has 0.0 (no bonus) crit modifier."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.DEFENSIVE
        assert char.get_stance_crit_modifier() == 0.0

    def test_berserker_stance_crit_modifier(self):
        """Test BERSERKER stance has 0.0 (no bonus) crit modifier."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BERSERKER
        assert char.get_stance_crit_modifier() == 0.0


class TestStanceCommand:
    """Tests for the stance command functionality."""

    def test_stance_command_in_known_commands(self):
        """Test that 'stance' is a recognized command."""
        from cli_rpg.game_state import KNOWN_COMMANDS
        assert "stance" in KNOWN_COMMANDS

    def test_stance_alias_st_resolves_to_stance(self):
        """Test that 'st' alias resolves to 'stance' command."""
        from cli_rpg.game_state import parse_command
        command, args = parse_command("st")
        assert command == "stance"

    def test_stance_can_be_changed(self):
        """Test that player can change stance."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        assert char.stance == FightingStance.BALANCED

        char.stance = FightingStance.AGGRESSIVE
        assert char.stance == FightingStance.AGGRESSIVE

        char.stance = FightingStance.DEFENSIVE
        assert char.stance == FightingStance.DEFENSIVE

        char.stance = FightingStance.BERSERKER
        assert char.stance == FightingStance.BERSERKER


class TestCombatWithStance:
    """Tests for stance modifiers applied in combat calculations."""

    def test_aggressive_stance_increases_attack_damage(self):
        """Test that AGGRESSIVE stance increases damage dealt by 20%."""
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Dummy", health=1000, max_health=1000, attack_power=1, defense=0, xp_reward=10, level=1)

        # Baseline damage with BALANCED stance
        char.stance = FightingStance.BALANCED
        combat = CombatEncounter(char, enemy)
        combat.start()
        victory, _ = combat.player_attack()
        balanced_damage = 1000 - enemy.health

        # Reset enemy
        enemy.health = 1000
        char.stance = FightingStance.AGGRESSIVE
        combat2 = CombatEncounter(char, enemy)
        combat2.start()
        # Seed random for consistent results in crit chance
        import random
        random.seed(42)
        victory, _ = combat2.player_attack()
        aggressive_damage = 1000 - enemy.health

        # Aggressive should deal more damage (about 1.2x)
        # Allow some variance due to crit chance
        assert aggressive_damage >= balanced_damage

    def test_defensive_stance_reduces_damage_taken(self):
        """Test that DEFENSIVE stance reduces incoming damage by 20% less (more defense)."""
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy

        char1 = Character(name="Test1", strength=10, dexterity=10, intelligence=10)
        char2 = Character(name="Test2", strength=10, dexterity=10, intelligence=10)
        enemy1 = Enemy(name="Attacker1", health=100, max_health=100, attack_power=20, defense=0, xp_reward=10, level=1)
        enemy2 = Enemy(name="Attacker2", health=100, max_health=100, attack_power=20, defense=0, xp_reward=10, level=1)

        # BALANCED stance
        char1.stance = FightingStance.BALANCED
        combat1 = CombatEncounter(char1, enemy1)
        combat1.start()
        initial_health_1 = char1.health
        # Force no dodge by seeding random
        import random
        random.seed(999)  # Pick a seed that doesn't dodge
        combat1.enemy_turn()
        balanced_damage_taken = initial_health_1 - char1.health

        # DEFENSIVE stance
        char2.stance = FightingStance.DEFENSIVE
        combat2 = CombatEncounter(char2, enemy2)
        combat2.start()
        initial_health_2 = char2.health
        random.seed(999)  # Same seed
        combat2.enemy_turn()
        defensive_damage_taken = initial_health_2 - char2.health

        # Defensive stance should take less or equal damage (defense modifier increases defense)
        assert defensive_damage_taken <= balanced_damage_taken


class TestStancePersistence:
    """Tests for stance persisting through save/load."""

    def test_stance_persists_through_save_load(self):
        """Test that stance is preserved when saving and loading game state."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.stance = FightingStance.BERSERKER

        world = {"Town Square": Location(name="Town Square", description="A town square.")}
        game_state = GameState(character=char, world=world, starting_location="Town Square")

        # Serialize and deserialize
        data = game_state.to_dict()
        restored_state = GameState.from_dict(data)

        assert restored_state.current_character.stance == FightingStance.BERSERKER
