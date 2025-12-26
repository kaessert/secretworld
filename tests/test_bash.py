"""Tests for Warrior Bash command.

Spec: Warriors can use 'bash' combat command that:
- Costs 15 stamina
- Deals 0.75x STR-based damage (reduced from normal attack)
- Applies 1-turn stun to target enemy
- Only Warriors can use this ability
"""

import pytest
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.status_effect import StatusEffect
from cli_rpg.combat import CombatEncounter


def create_warrior(strength: int = 20, stamina: int = 50) -> Character:
    """Create a Warrior character for testing."""
    warrior = Character(
        name="TestWarrior",
        strength=strength,
        dexterity=10,
        intelligence=10,
        level=1,
        character_class=CharacterClass.WARRIOR,
    )
    warrior.stamina = stamina
    warrior.max_stamina = 50
    return warrior


def create_rogue() -> Character:
    """Create a Rogue character for testing (non-Warrior)."""
    return Character(
        name="TestRogue",
        strength=10,
        dexterity=15,
        intelligence=10,
        level=1,
        character_class=CharacterClass.ROGUE,
    )


def create_mage() -> Character:
    """Create a Mage character for testing (non-Warrior)."""
    return Character(
        name="TestMage",
        strength=8,
        dexterity=10,
        intelligence=15,
        level=1,
        character_class=CharacterClass.MAGE,
    )


def create_enemy(health: int = 50, defense: int = 5) -> Enemy:
    """Create an enemy for testing."""
    return Enemy(
        name="TestEnemy",
        health=health,
        max_health=health,
        attack_power=10,
        defense=defense,
        xp_reward=50,
    )


class TestBashWarriorOnly:
    """Spec: Only Warriors can use bash."""

    def test_bash_only_available_to_warrior(self):
        """Spec: Non-warriors get 'Only Warriors can bash!' error."""
        rogue = create_rogue()
        enemy = create_enemy()
        combat = CombatEncounter(player=rogue, enemy=enemy)
        combat.start()

        victory, message = combat.player_bash()

        assert victory is False
        assert "Only Warriors can bash" in message

    def test_mage_cannot_bash(self):
        """Spec: Mages cannot use bash ability."""
        mage = create_mage()
        enemy = create_enemy()
        combat = CombatEncounter(player=mage, enemy=enemy)
        combat.start()

        victory, message = combat.player_bash()

        assert victory is False
        assert "Only Warriors can bash" in message


class TestBashStaminaCost:
    """Spec: Bash costs 15 stamina."""

    def test_bash_costs_15_stamina(self):
        """Spec: Stamina decreases by 15 after bash."""
        warrior = create_warrior(stamina=50)
        enemy = create_enemy()
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()
        initial_stamina = warrior.stamina

        combat.player_bash()

        assert warrior.stamina == initial_stamina - 15

    def test_bash_fails_without_stamina(self):
        """Spec: Returns error with <15 stamina, stamina unchanged."""
        warrior = create_warrior(stamina=10)  # Less than 15
        enemy = create_enemy()
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()
        initial_stamina = warrior.stamina

        victory, message = combat.player_bash()

        assert victory is False
        assert "Not enough stamina" in message
        assert warrior.stamina == initial_stamina  # Stamina unchanged


class TestBashDamage:
    """Spec: Bash deals 0.75x STR-based damage."""

    def test_bash_deals_reduced_damage(self):
        """Spec: Deals 0.75x STR-based damage (reduced from normal attack)."""
        warrior = create_warrior(strength=20, stamina=50)
        enemy = create_enemy(health=100, defense=5)
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()
        initial_health = enemy.health

        combat.player_bash()

        # Base damage = STR (20) - DEF (5) = 15
        # Reduced damage = 15 * 0.75 = 11.25 -> 11
        expected_damage = int((warrior.get_attack_power() - enemy.defense) * 0.75)
        expected_damage = max(1, expected_damage)
        assert enemy.health == initial_health - expected_damage

    def test_bash_minimum_damage_is_1(self):
        """Spec: Minimum damage is always 1."""
        warrior = create_warrior(strength=5, stamina=50)  # Low strength
        enemy = create_enemy(health=100, defense=10)  # High defense
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()
        initial_health = enemy.health

        combat.player_bash()

        # Even with low damage, at least 1 damage dealt
        assert enemy.health < initial_health
        assert enemy.health >= initial_health - 1

    def test_bash_can_defeat_enemy(self):
        """Spec: Returns victory=True if enemy dies from bash damage."""
        warrior = create_warrior(strength=20, stamina=50)  # Max allowed strength
        enemy = create_enemy(health=5, defense=0)  # Low health to ensure defeat
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        victory, message = combat.player_bash()

        assert victory is True
        assert not enemy.is_alive()
        assert "Victory" in message or "defeated" in message.lower()


class TestBashStunEffect:
    """Spec: Bash applies 1-turn stun to target enemy."""

    def test_bash_applies_stun_to_enemy(self):
        """Spec: Enemy has stun StatusEffect after bash."""
        warrior = create_warrior(stamina=50)
        enemy = create_enemy()
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        combat.player_bash()

        # Check enemy has stun effect
        stun_effects = [e for e in enemy.status_effects if e.effect_type == "stun"]
        assert len(stun_effects) == 1
        assert stun_effects[0].name == "Stun"

    def test_bash_stun_lasts_1_turn(self):
        """Spec: Stun duration is 1."""
        warrior = create_warrior(stamina=50)
        enemy = create_enemy()
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        combat.player_bash()

        stun_effects = [e for e in enemy.status_effects if e.effect_type == "stun"]
        assert stun_effects[0].duration == 1

    def test_bash_stun_message(self):
        """Spec: Message indicates stun was applied."""
        warrior = create_warrior(stamina=50)
        enemy = create_enemy()
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        victory, message = combat.player_bash()

        assert "stun" in message.lower()


class TestBashWhenStunned:
    """Spec: Player cannot bash while stunned."""

    def test_bash_fails_when_stunned(self):
        """Spec: Can't bash while player is stunned."""
        warrior = create_warrior(stamina=50)
        enemy = create_enemy()
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        # Apply stun to player
        stun = StatusEffect(
            name="Stun",
            effect_type="stun",
            damage_per_turn=0,
            duration=1,
        )
        warrior.apply_status_effect(stun)
        initial_stamina = warrior.stamina

        victory, message = combat.player_bash()

        assert victory is False
        assert "stunned" in message.lower()
        # Stamina should not be consumed
        assert warrior.stamina == initial_stamina


class TestBashTargeting:
    """Spec: Bash can target specific enemies."""

    def test_bash_with_target(self):
        """Spec: Bash can specify target enemy by name."""
        warrior = create_warrior(stamina=50)
        enemy1 = create_enemy(health=50)
        enemy1.name = "Goblin"
        enemy2 = create_enemy(health=50)
        enemy2.name = "Orc"
        combat = CombatEncounter(player=warrior, enemy=enemy1, enemies=[enemy1, enemy2])
        combat.start()
        initial_orc_health = enemy2.health

        combat.player_bash(target="Orc")

        # Orc should be damaged, not Goblin
        assert enemy2.health < initial_orc_health
        # Check stun was applied to Orc
        stun_effects = [e for e in enemy2.status_effects if e.effect_type == "stun"]
        assert len(stun_effects) == 1


class TestBashComboTracking:
    """Spec: Bash records action for combo tracking."""

    def test_bash_records_action_for_combo(self):
        """Spec: Action recorded as 'bash' in action_history."""
        warrior = create_warrior(stamina=50)
        enemy = create_enemy()
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        combat.player_bash()

        assert "bash" in combat.action_history
