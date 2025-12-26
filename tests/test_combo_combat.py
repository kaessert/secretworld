"""Tests for Combo Combat System.

These tests verify the combo system that tracks player actions and unlocks
special combo moves when specific action sequences are performed.

Combos:
- Frenzy: Attack -> Attack -> Attack = Triple attack (1.5x damage)
- Revenge: Defend -> Defend -> Attack = Counter-attack (damage = damage taken while defending)
- Arcane Burst: Cast -> Cast -> Cast = Empowered spell (2x magic damage)
"""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter


def create_test_player(strength: int = 10, intelligence: int = 10) -> Character:
    """Create a test player character with known stats."""
    return Character(
        name="Hero",
        strength=strength,
        dexterity=10,
        intelligence=intelligence,
        level=1
    )


def create_test_enemy(
    health: int = 100,
    defense: int = 0,
    attack_power: int = 10
) -> Enemy:
    """Create a test enemy with known stats."""
    return Enemy(
        name="Test Goblin",
        health=health,
        max_health=health,
        attack_power=attack_power,
        defense=defense,
        xp_reward=25
    )


class TestActionHistoryTracking:
    """Test action history tracking in CombatEncounter.

    Tests verify that combat actions are recorded for combo detection.
    """

    def test_combat_encounter_has_action_history(self):
        """Spec: CombatEncounter has action_history attribute (empty list)."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)

        assert hasattr(combat, "action_history")
        assert combat.action_history == []

    def test_attack_records_action(self):
        """Spec: player_attack() adds 'attack' to action_history."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_attack()

        assert "attack" in combat.action_history

    def test_defend_records_action(self):
        """Spec: player_defend() adds 'defend' to action_history."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_defend()

        assert "defend" in combat.action_history

    def test_cast_records_action(self):
        """Spec: player_cast() adds 'cast' to action_history."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_cast()

        assert "cast" in combat.action_history

    def test_flee_clears_history(self):
        """Spec: player_flee() clears action_history (breaks combo)."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up some history
        combat.player_attack()
        combat.player_attack()
        assert len(combat.action_history) == 2

        # Flee should clear history
        combat.player_flee()

        assert combat.action_history == []

    def test_action_history_max_length(self):
        """Spec: History never exceeds 3 entries (oldest dropped)."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Perform 4 attacks
        combat.player_attack()
        combat.player_attack()
        combat.player_attack()
        # History should be at 3, pending combo cleared on next action
        # Clear pending combo to allow recording
        combat.pending_combo = None
        combat.player_defend()

        # History should never exceed 3
        assert len(combat.action_history) <= 3

    def test_end_combat_clears_history(self):
        """Spec: end_combat() clears action_history."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up some history
        combat.player_attack()
        combat.player_attack()

        # End combat
        combat.end_combat(victory=True)

        assert combat.action_history == []


class TestComboDetection:
    """Test combo detection from action sequences.

    Tests verify that the system correctly detects when combo conditions are met.
    """

    def test_detect_frenzy_combo(self):
        """Spec: After Attack->Attack->Attack, get_pending_combo() returns 'frenzy'."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_attack()
        combat.player_attack()
        combat.player_attack()

        assert combat.get_pending_combo() == "frenzy"

    def test_detect_revenge_combo(self):
        """Spec: After Defend->Defend->Attack, get_pending_combo() returns 'revenge'."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_defend()
        combat.player_defend()
        combat.player_attack()

        assert combat.get_pending_combo() == "revenge"

    def test_detect_arcane_burst_combo(self):
        """Spec: After Cast->Cast->Cast, get_pending_combo() returns 'arcane_burst'."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_cast()
        combat.player_cast()
        combat.player_cast()

        assert combat.get_pending_combo() == "arcane_burst"

    def test_no_combo_partial_sequence(self):
        """Spec: After Attack->Attack, get_pending_combo() returns None."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_attack()
        combat.player_attack()

        assert combat.get_pending_combo() is None

    def test_no_combo_broken_sequence(self):
        """Spec: After Attack->Defend->Attack, get_pending_combo() returns None."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_attack()
        combat.player_defend()
        combat.player_attack()

        assert combat.get_pending_combo() is None


class TestFrenzyCombo:
    """Test Frenzy combo execution (Attack x3 = triple attack, 1.5x damage).

    Tests verify that Frenzy deals bonus damage via multiple hits.
    """

    def test_frenzy_deals_bonus_damage(self):
        """Spec: Frenzy attack deals 1.5x total damage via 3 hits."""
        player = create_test_player(strength=20)  # High strength for clear damage
        enemy = create_test_enemy(health=200, defense=0)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up Frenzy combo
        combat.player_attack()
        combat.player_attack()
        combat.player_attack()
        assert combat.get_pending_combo() == "frenzy"

        initial_health = enemy.health

        # Next attack triggers Frenzy
        victory, message = combat.player_attack()

        # Normal damage would be strength - defense = 20 - 0 = 20
        # Frenzy should deal 1.5x = 30 total
        normal_damage = player.get_attack_power() - enemy.defense
        expected_damage = int(normal_damage * 1.5)
        actual_damage = initial_health - enemy.health

        # Frenzy damage should be roughly 1.5x normal (allow for rounding)
        assert actual_damage >= expected_damage - 1
        assert actual_damage <= expected_damage + 1

    def test_frenzy_clears_after_trigger(self):
        """Spec: After Frenzy triggers, action_history is cleared."""
        player = create_test_player(strength=10)
        enemy = create_test_enemy(health=200, defense=0)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up Frenzy combo
        combat.player_attack()
        combat.player_attack()
        combat.player_attack()

        # Trigger Frenzy
        combat.player_attack()

        assert combat.action_history == []
        assert combat.get_pending_combo() is None

    def test_frenzy_message_shows_triple_hit(self):
        """Spec: Frenzy attack message mentions 'three' or 'triple'."""
        player = create_test_player(strength=10)
        enemy = create_test_enemy(health=200, defense=0)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up and trigger Frenzy
        combat.player_attack()
        combat.player_attack()
        combat.player_attack()
        victory, message = combat.player_attack()

        message_lower = message.lower()
        assert "frenzy" in message_lower or "three" in message_lower


class TestRevengeCombo:
    """Test Revenge combo execution (Defend x2 + Attack = counter-attack).

    Tests verify that Revenge deals damage based on damage taken while defending.
    """

    def test_revenge_tracks_damage_taken(self):
        """Spec: Damage taken during defend actions is tracked."""
        player = create_test_player()
        enemy = create_test_enemy(attack_power=20)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        assert hasattr(combat, "damage_taken_while_defending")
        assert combat.damage_taken_while_defending == 0

        # Defend and take enemy turn
        combat.player_defend()
        combat.enemy_turn()

        # Should have tracked damage taken while defending
        assert combat.damage_taken_while_defending > 0

    def test_revenge_deals_damage_equal_to_taken(self):
        """Spec: Revenge attack deals damage = damage taken while defending."""
        player = create_test_player(strength=5)  # Low strength so revenge is clearly different
        enemy = create_test_enemy(health=200, defense=0, attack_power=20)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up Revenge combo and accumulate damage
        combat.player_defend()
        combat.enemy_turn()  # Enemy attacks, damage tracked
        combat.player_defend()
        combat.enemy_turn()  # More damage tracked
        combat.player_attack()

        # Now we have pending Revenge combo
        assert combat.get_pending_combo() == "revenge"

        # Get the damage tracked
        tracked_damage = combat.damage_taken_while_defending
        assert tracked_damage > 0

        initial_health = enemy.health

        # Trigger Revenge
        combat.player_attack()

        actual_damage = initial_health - enemy.health
        # Revenge should deal damage equal to what we tracked
        assert actual_damage == max(1, tracked_damage)

    def test_revenge_resets_damage_counter(self):
        """Spec: After Revenge triggers, damage counter resets."""
        player = create_test_player()
        enemy = create_test_enemy(health=200, attack_power=20)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up Revenge combo and take damage
        combat.player_defend()
        combat.enemy_turn()
        combat.player_defend()
        combat.enemy_turn()
        combat.player_attack()

        # Trigger Revenge
        combat.player_attack()

        assert combat.damage_taken_while_defending == 0


class TestArcaneBurstCombo:
    """Test Arcane Burst combo execution (Cast x3 = 2x magic damage).

    Tests verify that Arcane Burst deals double magic damage.
    """

    def test_arcane_burst_double_damage(self):
        """Spec: Arcane Burst cast deals 2x magic damage."""
        player = create_test_player(intelligence=20)
        # Ensure player has enough mana for 3 casts (10 each) + Arcane Burst (25)
        player.mana = 100
        enemy = create_test_enemy(health=200, defense=0)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up Arcane Burst combo
        combat.player_cast()
        combat.player_cast()
        combat.player_cast()
        assert combat.get_pending_combo() == "arcane_burst"

        initial_health = enemy.health

        # Trigger Arcane Burst
        combat.player_cast()

        # Normal cast damage = intelligence * 1.5 = 20 * 1.5 = 30
        # Arcane Burst = 2x = 60
        normal_damage = int(player.intelligence * 1.5)
        expected_damage = normal_damage * 2
        actual_damage = initial_health - enemy.health

        assert actual_damage == expected_damage

    def test_arcane_burst_message(self):
        """Spec: Message mentions 'arcane' or 'burst' or 'explodes'."""
        player = create_test_player(intelligence=10)
        # Ensure player has enough mana for 3 casts (10 each) + Arcane Burst (25)
        player.mana = 100
        enemy = create_test_enemy(health=200)
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up and trigger Arcane Burst
        combat.player_cast()
        combat.player_cast()
        combat.player_cast()
        victory, message = combat.player_cast()

        message_lower = message.lower()
        assert "arcane" in message_lower or "burst" in message_lower or "explodes" in message_lower


class TestComboUINotifications:
    """Test combo notifications in combat status.

    Tests verify that players are notified when combos are available.
    """

    def test_combo_available_notification(self):
        """Spec: When combo is pending, status shows 'COMBO AVAILABLE: ...'."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Build up a combo
        combat.player_attack()
        combat.player_attack()
        combat.player_attack()

        status = combat.get_status()

        assert "COMBO AVAILABLE" in status
        assert "Frenzy" in status

    def test_get_status_shows_action_history(self):
        """Spec: Combat status shows 'Last actions: [Attack] -> [Defend]'."""
        player = create_test_player()
        enemy = create_test_enemy()
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_attack()
        combat.player_defend()

        status = combat.get_status()

        # Should show action history in status
        assert "Last actions" in status or "Attack" in status
