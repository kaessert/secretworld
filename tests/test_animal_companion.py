"""Tests for Ranger Animal Companion system.

Tests verify the spec:
- Ranger-Only: Only Rangers can have an animal companion
- One Companion: Rangers have a single animal companion
- Bond Level: Uses existing BondLevel enum (0-100 points)
- Combat: Flank Bonus (+10-15%), Companion Attack (50% of Ranger strength)
- Out-of-Combat: Track Bonus (+15%), Perception Bonus (+3 for hawk)
"""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.models.animal_companion import (
    AnimalCompanion,
    AnimalType,
    ANIMAL_TYPE_BONUSES,
    BASE_COMPANION_HEALTH,
)
from cli_rpg.models.companion import BondLevel
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.item import Item, ItemType


class TestAnimalCompanionCreation:
    """Tests for AnimalCompanion creation and types."""

    def test_create_wolf_companion(self):
        """Test Wolf type creation with correct stats. (Spec: Wolf +15% flank bonus)"""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        assert companion.name == "Fang"
        assert companion.animal_type == AnimalType.WOLF
        assert companion.health == BASE_COMPANION_HEALTH  # 1.0x multiplier
        assert companion.max_health == BASE_COMPANION_HEALTH
        assert companion.bond_points == 0
        assert companion.is_present is True

    def test_create_hawk_companion(self):
        """Test Hawk type creation with 0.5x health. (Spec: Hawk +3 PER, lower health)"""
        companion = AnimalCompanion.create("Sky", AnimalType.HAWK)

        assert companion.animal_type == AnimalType.HAWK
        assert companion.health == int(BASE_COMPANION_HEALTH * 0.5)
        assert companion.max_health == int(BASE_COMPANION_HEALTH * 0.5)

    def test_create_bear_companion(self):
        """Test Bear type creation with 2x health. (Spec: Bear has 2x health)"""
        companion = AnimalCompanion.create("Brutus", AnimalType.BEAR)

        assert companion.animal_type == AnimalType.BEAR
        assert companion.health == int(BASE_COMPANION_HEALTH * 2.0)
        assert companion.max_health == int(BASE_COMPANION_HEALTH * 2.0)

    def test_animal_type_bonuses_defined(self):
        """Test that all animal types have defined bonuses."""
        for animal_type in AnimalType:
            assert animal_type in ANIMAL_TYPE_BONUSES
            bonuses = ANIMAL_TYPE_BONUSES[animal_type]
            assert "flank_bonus" in bonuses
            assert "perception_bonus" in bonuses
            assert "health_multiplier" in bonuses


class TestAnimalCompanionCombatBonuses:
    """Tests for combat-related bonuses."""

    def test_wolf_flank_bonus(self):
        """Test Wolf gives +15% flank bonus. (Spec: Wolf +15% pack tactics)"""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        assert companion.get_flank_bonus() == 0.15

    def test_hawk_flank_bonus(self):
        """Test Hawk gives +10% flank bonus. (Spec: Default +10%)"""
        companion = AnimalCompanion.create("Sky", AnimalType.HAWK)

        assert companion.get_flank_bonus() == 0.10

    def test_bear_flank_bonus(self):
        """Test Bear gives +10% flank bonus. (Spec: Default +10%)"""
        companion = AnimalCompanion.create("Brutus", AnimalType.BEAR)

        assert companion.get_flank_bonus() == 0.10

    def test_flank_bonus_zero_when_dismissed(self):
        """Test no flank bonus when companion is dismissed. (Spec: must be present)"""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.dismiss()

        assert companion.get_flank_bonus() == 0.0

    def test_companion_attack_damage(self):
        """Test companion attack deals 50% of Ranger strength. (Spec: 50% base damage)"""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        ranger_strength = 10

        damage = companion.get_attack_damage(ranger_strength)

        assert damage == 5  # 50% of 10

    def test_companion_attack_minimum_damage(self):
        """Test companion attack has minimum 1 damage."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        ranger_strength = 1

        damage = companion.get_attack_damage(ranger_strength)

        assert damage == 1  # Minimum damage

    def test_companion_attack_zero_when_dismissed(self):
        """Test no attack when companion is dismissed."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.dismiss()

        damage = companion.get_attack_damage(10)

        assert damage == 0

    def test_companion_attack_zero_when_dead(self):
        """Test no attack when companion is dead."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.take_damage(companion.max_health)  # Kill companion

        damage = companion.get_attack_damage(10)

        assert damage == 0


class TestAnimalCompanionPerception:
    """Tests for perception bonuses."""

    def test_hawk_perception_bonus(self):
        """Test Hawk gives +3 PER bonus. (Spec: Hawk +3 PER)"""
        companion = AnimalCompanion.create("Sky", AnimalType.HAWK)

        assert companion.get_perception_bonus() == 3

    def test_wolf_perception_bonus(self):
        """Test Wolf gives +0 PER bonus."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        assert companion.get_perception_bonus() == 0

    def test_bear_perception_bonus(self):
        """Test Bear gives +0 PER bonus."""
        companion = AnimalCompanion.create("Brutus", AnimalType.BEAR)

        assert companion.get_perception_bonus() == 0

    def test_perception_bonus_zero_when_dismissed(self):
        """Test no PER bonus when companion is dismissed."""
        companion = AnimalCompanion.create("Sky", AnimalType.HAWK)
        companion.dismiss()

        assert companion.get_perception_bonus() == 0


class TestAnimalCompanionBond:
    """Tests for bond level progression."""

    def test_initial_bond_stranger(self):
        """Test newly tamed companion starts as STRANGER."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        assert companion.get_bond_level() == BondLevel.STRANGER
        assert companion.bond_points == 0

    def test_bond_acquaintance_threshold(self):
        """Test bond level becomes ACQUAINTANCE at 25 points."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 25

        assert companion.get_bond_level() == BondLevel.ACQUAINTANCE

    def test_bond_trusted_threshold(self):
        """Test bond level becomes TRUSTED at 50 points."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 50

        assert companion.get_bond_level() == BondLevel.TRUSTED

    def test_bond_devoted_threshold(self):
        """Test bond level becomes DEVOTED at 75 points."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 75

        assert companion.get_bond_level() == BondLevel.DEVOTED

    def test_add_bond_progression(self):
        """Test add_bond increases bond points."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        companion.add_bond(10)

        assert companion.bond_points == 10

    def test_add_bond_capped_at_100(self):
        """Test bond points cannot exceed 100."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 95

        companion.add_bond(20)

        assert companion.bond_points == 100

    def test_add_bond_level_up_message(self):
        """Test add_bond returns level-up message when crossing threshold."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 24

        message = companion.add_bond(1)

        assert message is not None
        assert "Fang" in message
        assert "Acquaintance" in message

    def test_add_bond_no_message_within_level(self):
        """Test add_bond returns None when not crossing threshold."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        message = companion.add_bond(10)

        assert message is None

    def test_reduce_bond(self):
        """Test reduce_bond decreases bond points."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 50

        companion.reduce_bond(10)

        assert companion.bond_points == 40

    def test_reduce_bond_clamped_at_zero(self):
        """Test bond points cannot go below 0."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 5

        companion.reduce_bond(10)

        assert companion.bond_points == 0


class TestAnimalCompanionHealth:
    """Tests for companion health mechanics."""

    def test_companion_alive_initially(self):
        """Test companion starts alive."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        assert companion.is_alive() is True

    def test_take_damage(self):
        """Test companion can take damage."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        initial_health = companion.health

        companion.take_damage(10)

        assert companion.health == initial_health - 10

    def test_take_damage_clamped_at_zero(self):
        """Test health cannot go below 0."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        companion.take_damage(companion.max_health + 50)

        assert companion.health == 0

    def test_companion_dead_at_zero_health(self):
        """Test companion is dead when health reaches 0."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.take_damage(companion.max_health)

        assert companion.is_alive() is False

    def test_heal_companion(self):
        """Test companion can be healed."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.take_damage(20)
        old_health = companion.health

        healed = companion.heal(10)

        assert companion.health == old_health + 10
        assert healed == 10

    def test_heal_clamped_at_max(self):
        """Test healing cannot exceed max_health."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.take_damage(5)

        healed = companion.heal(20)

        assert companion.health == companion.max_health
        assert healed == 5

    def test_bear_higher_health_pool(self):
        """Test Bear companion has 2x health pool. (Spec: Bear can tank hits)"""
        bear = AnimalCompanion.create("Brutus", AnimalType.BEAR)
        wolf = AnimalCompanion.create("Fang", AnimalType.WOLF)

        assert bear.max_health == wolf.max_health * 2

    def test_hawk_lower_health_pool(self):
        """Test Hawk companion has 0.5x health pool."""
        hawk = AnimalCompanion.create("Sky", AnimalType.HAWK)
        wolf = AnimalCompanion.create("Fang", AnimalType.WOLF)

        assert hawk.max_health == wolf.max_health // 2


class TestAnimalCompanionSummonDismiss:
    """Tests for summon/dismiss mechanics."""

    def test_dismiss_companion(self):
        """Test dismissing companion sets is_present to False."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        result = companion.dismiss()

        assert result is True
        assert companion.is_present is False

    def test_dismiss_already_dismissed(self):
        """Test dismissing already dismissed companion returns False."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.dismiss()

        result = companion.dismiss()

        assert result is False
        assert companion.is_present is False

    def test_summon_companion(self):
        """Test summoning companion sets is_present to True."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.dismiss()

        result = companion.summon()

        assert result is True
        assert companion.is_present is True

    def test_summon_already_present(self):
        """Test summoning already present companion returns False."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        result = companion.summon()

        assert result is False
        assert companion.is_present is True


class TestAnimalCompanionSerialization:
    """Tests for save/load serialization."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 50
        companion.take_damage(10)
        companion.dismiss()

        data = companion.to_dict()

        assert data["name"] == "Fang"
        assert data["animal_type"] == "Wolf"
        assert data["health"] == companion.health
        assert data["max_health"] == companion.max_health
        assert data["bond_points"] == 50
        assert data["is_present"] is False

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "Sky",
            "animal_type": "Hawk",
            "health": 10,
            "max_health": 15,
            "bond_points": 75,
            "is_present": True,
        }

        companion = AnimalCompanion.from_dict(data)

        assert companion.name == "Sky"
        assert companion.animal_type == AnimalType.HAWK
        assert companion.health == 10
        assert companion.max_health == 15
        assert companion.bond_points == 75
        assert companion.is_present is True

    def test_from_dict_backward_compat(self):
        """Test deserialization with missing optional fields."""
        data = {
            "name": "Fang",
            "animal_type": "Wolf",
            "health": 30,
            "max_health": 30,
        }

        companion = AnimalCompanion.from_dict(data)

        assert companion.bond_points == 0
        assert companion.is_present is True

    def test_round_trip_serialization(self):
        """Test that to_dict -> from_dict preserves all data."""
        original = AnimalCompanion.create("Brutus", AnimalType.BEAR)
        original.bond_points = 42
        original.take_damage(15)
        original.dismiss()

        data = original.to_dict()
        restored = AnimalCompanion.from_dict(data)

        assert restored.name == original.name
        assert restored.animal_type == original.animal_type
        assert restored.health == original.health
        assert restored.max_health == original.max_health
        assert restored.bond_points == original.bond_points
        assert restored.is_present == original.is_present


class TestRangerOnlyCompanion:
    """Tests that only Rangers can have animal companions."""

    def test_ranger_can_have_companion(self):
        """Test Ranger class is valid for animal companions. (Spec: Ranger-only)"""
        # This test verifies the class is correct
        ranger = Character(
            name="Ranger Test",
            strength=10,
            dexterity=12,
            intelligence=8,
            character_class=CharacterClass.RANGER,
        )

        assert ranger.character_class == CharacterClass.RANGER


class TestCharacterIntegration:
    """Tests for Character model integration with animal companion."""

    def test_character_animal_companion_serialization(self):
        """Test Character with animal companion serializes correctly."""
        ranger = Character(
            name="Ranger Test",
            strength=10,
            dexterity=12,
            intelligence=8,
            character_class=CharacterClass.RANGER,
        )
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 50
        ranger.animal_companion = companion

        data = ranger.to_dict()
        assert data["animal_companion"] is not None
        assert data["animal_companion"]["name"] == "Fang"
        assert data["animal_companion"]["animal_type"] == "Wolf"
        assert data["animal_companion"]["bond_points"] == 50

    def test_character_animal_companion_deserialization(self):
        """Test Character with animal companion deserializes correctly."""
        ranger = Character(
            name="Ranger Test",
            strength=10,
            dexterity=12,
            intelligence=8,
            character_class=CharacterClass.RANGER,
        )
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 50
        ranger.animal_companion = companion

        data = ranger.to_dict()
        restored = Character.from_dict(data)

        assert restored.animal_companion is not None
        assert restored.animal_companion.name == "Fang"
        assert restored.animal_companion.animal_type == AnimalType.WOLF
        assert restored.animal_companion.bond_points == 50

    def test_character_no_companion_backward_compat(self):
        """Test Character deserializes without animal_companion for old saves."""
        data = {
            "name": "Old Hero",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None},
        }

        character = Character.from_dict(data)

        assert character.animal_companion is None


class TestStatusDisplay:
    """Tests for companion status display."""

    def test_status_display_contains_name(self):
        """Test status display includes companion name."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        display = companion.get_status_display()

        assert "Fang" in display
        assert "Wolf" in display

    def test_status_display_shows_health(self):
        """Test status display shows health."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.take_damage(10)

        display = companion.get_status_display()

        assert f"{companion.health}" in display

    def test_status_display_shows_bond_level(self):
        """Test status display shows bond level."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)
        companion.bond_points = 50

        display = companion.get_status_display()

        assert "Trusted" in display

    def test_status_display_shows_flank_bonus(self):
        """Test status display shows flank bonus percentage."""
        companion = AnimalCompanion.create("Fang", AnimalType.WOLF)

        display = companion.get_status_display()

        assert "15%" in display  # Wolf has 15% flank bonus


class TestRangerCompanionCommands:
    """Tests for ranger_companion command functions."""

    @pytest.fixture
    def ranger_game_state(self):
        """Create a mock game state with a Ranger character."""
        from unittest.mock import MagicMock
        game_state = MagicMock()
        ranger = Character(
            name="Test Ranger",
            strength=12,
            dexterity=14,
            intelligence=10,
            character_class=CharacterClass.RANGER,
        )
        game_state.current_character = ranger
        game_state.get_current_location.return_value = MagicMock()
        return game_state

    @pytest.fixture
    def warrior_game_state(self):
        """Create a mock game state with a Warrior character."""
        from unittest.mock import MagicMock
        game_state = MagicMock()
        warrior = Character(
            name="Test Warrior",
            strength=14,
            dexterity=10,
            intelligence=8,
            character_class=CharacterClass.WARRIOR,
        )
        game_state.current_character = warrior
        return game_state

    def test_only_ranger_can_tame(self, warrior_game_state):
        """Test non-Rangers cannot tame companions. (Spec: Ranger-only)"""
        from cli_rpg.ranger_companion import execute_tame

        success, message = execute_tame(warrior_game_state, "wolf")

        assert success is False
        assert "Only Rangers" in message

    def test_tame_creates_companion(self, ranger_game_state):
        """Test tame command creates animal companion."""
        from cli_rpg.ranger_companion import execute_tame

        success, message = execute_tame(ranger_game_state, "wolf")

        assert success is True
        assert ranger_game_state.current_character.animal_companion is not None
        assert ranger_game_state.current_character.animal_companion.animal_type == AnimalType.WOLF

    def test_tame_only_once(self, ranger_game_state):
        """Test Rangers can only tame one companion. (Spec: One companion)"""
        from cli_rpg.ranger_companion import execute_tame

        execute_tame(ranger_game_state, "wolf")
        success, message = execute_tame(ranger_game_state, "bear")

        assert success is False
        assert "already have" in message

    def test_tame_invalid_animal(self, ranger_game_state):
        """Test taming invalid animal type fails."""
        from cli_rpg.ranger_companion import execute_tame

        success, message = execute_tame(ranger_game_state, "dragon")

        assert success is False
        assert "can't tame" in message

    def test_summon_requires_dismissed_companion(self, ranger_game_state):
        """Test summon fails if companion already present."""
        from cli_rpg.ranger_companion import execute_tame, execute_summon

        execute_tame(ranger_game_state, "wolf")
        success, message = execute_summon(ranger_game_state)

        assert success is False
        assert "already at your side" in message

    def test_summon_costs_stamina(self, ranger_game_state):
        """Test summon costs 10 stamina. (Spec: costs 10 stamina)"""
        from cli_rpg.ranger_companion import execute_tame, execute_dismiss, execute_summon

        execute_tame(ranger_game_state, "wolf")
        execute_dismiss(ranger_game_state)
        initial_stamina = ranger_game_state.current_character.stamina

        success, _ = execute_summon(ranger_game_state)

        assert success is True
        assert ranger_game_state.current_character.stamina == initial_stamina - 10

    def test_summon_fails_insufficient_stamina(self, ranger_game_state):
        """Test summon fails with insufficient stamina."""
        from cli_rpg.ranger_companion import execute_tame, execute_dismiss, execute_summon

        execute_tame(ranger_game_state, "wolf")
        execute_dismiss(ranger_game_state)
        ranger_game_state.current_character.stamina = 5

        success, message = execute_summon(ranger_game_state)

        assert success is False
        assert "Not enough stamina" in message

    def test_dismiss_works(self, ranger_game_state):
        """Test dismiss command works."""
        from cli_rpg.ranger_companion import execute_tame, execute_dismiss

        execute_tame(ranger_game_state, "wolf")
        success, message = execute_dismiss(ranger_game_state)

        assert success is True
        assert not ranger_game_state.current_character.animal_companion.is_present

    def test_dismiss_already_dismissed(self, ranger_game_state):
        """Test dismiss fails if already dismissed."""
        from cli_rpg.ranger_companion import execute_tame, execute_dismiss

        execute_tame(ranger_game_state, "wolf")
        execute_dismiss(ranger_game_state)
        success, message = execute_dismiss(ranger_game_state)

        assert success is False
        assert "already away" in message

    def test_feed_heals_and_bonds(self, ranger_game_state):
        """Test feed heals companion and increases bond. (Spec: feed heals + bond)"""
        from cli_rpg.ranger_companion import execute_tame, execute_feed, FEED_BOND_AMOUNT

        execute_tame(ranger_game_state, "wolf")
        companion = ranger_game_state.current_character.animal_companion
        companion.take_damage(20)
        old_health = companion.health
        old_bond = companion.bond_points

        # Add a consumable to inventory
        food = Item(name="Meat", description="Raw meat", item_type=ItemType.CONSUMABLE)
        ranger_game_state.current_character.inventory.add_item(food)

        success, message = execute_feed(ranger_game_state, "meat")

        assert success is True
        assert companion.health > old_health
        assert companion.bond_points == old_bond + FEED_BOND_AMOUNT

    def test_feed_non_consumable_fails(self, ranger_game_state):
        """Test feeding non-consumable fails."""
        from cli_rpg.ranger_companion import execute_tame, execute_feed

        execute_tame(ranger_game_state, "wolf")

        # Add a weapon to inventory
        sword = Item(name="Sword", description="A sword", item_type=ItemType.WEAPON)
        ranger_game_state.current_character.inventory.add_item(sword)

        success, message = execute_feed(ranger_game_state, "sword")

        assert success is False
        assert "only feed consumable" in message

    def test_companion_status_display(self, ranger_game_state):
        """Test companion status command."""
        from cli_rpg.ranger_companion import execute_tame, execute_companion_status

        execute_tame(ranger_game_state, "wolf")
        status = execute_companion_status(ranger_game_state)

        assert "Wolf" in status
        assert "Present" in status or "Alive" in status

    def test_companion_status_no_companion(self, ranger_game_state):
        """Test companion status when no companion."""
        from cli_rpg.ranger_companion import execute_companion_status

        status = execute_companion_status(ranger_game_state)

        assert "don't have" in status

    def test_track_bonus_with_companion(self, ranger_game_state):
        """Test +15% track bonus with companion present. (Spec: Track Bonus +15%)"""
        from cli_rpg.ranger_companion import execute_tame, get_track_companion_bonus

        execute_tame(ranger_game_state, "wolf")

        bonus = get_track_companion_bonus(ranger_game_state)

        assert bonus == 15

    def test_track_bonus_no_companion(self, ranger_game_state):
        """Test no track bonus without companion."""
        from cli_rpg.ranger_companion import get_track_companion_bonus

        bonus = get_track_companion_bonus(ranger_game_state)

        assert bonus == 0

    def test_track_bonus_companion_dismissed(self, ranger_game_state):
        """Test no track bonus when companion dismissed."""
        from cli_rpg.ranger_companion import execute_tame, execute_dismiss, get_track_companion_bonus

        execute_tame(ranger_game_state, "wolf")
        execute_dismiss(ranger_game_state)

        bonus = get_track_companion_bonus(ranger_game_state)

        assert bonus == 0

    def test_flank_bonus_with_companion(self, ranger_game_state):
        """Test flank bonus is retrieved correctly."""
        from cli_rpg.ranger_companion import execute_tame, get_companion_flank_bonus

        execute_tame(ranger_game_state, "wolf")

        bonus = get_companion_flank_bonus(ranger_game_state)

        assert bonus == 0.15  # Wolf flank bonus

    def test_perception_bonus_hawk(self, ranger_game_state):
        """Test hawk perception bonus. (Spec: Hawk +3 PER)"""
        from cli_rpg.ranger_companion import execute_tame, get_companion_perception_bonus

        execute_tame(ranger_game_state, "hawk")

        bonus = get_companion_perception_bonus(ranger_game_state)

        assert bonus == 3

    def test_perception_bonus_non_hawk(self, ranger_game_state):
        """Test non-hawk has no perception bonus."""
        from cli_rpg.ranger_companion import execute_tame, get_companion_perception_bonus

        execute_tame(ranger_game_state, "wolf")

        bonus = get_companion_perception_bonus(ranger_game_state)

        assert bonus == 0

    def test_companion_attack(self, ranger_game_state):
        """Test companion attack damage calculation. (Spec: 50% of Ranger strength)"""
        from cli_rpg.ranger_companion import execute_tame, companion_attack

        execute_tame(ranger_game_state, "wolf")
        strength = ranger_game_state.current_character.strength  # 12 + 1 (class bonus) = 13

        damage, message = companion_attack(ranger_game_state, enemy_defense=0)

        # 50% of strength (13) = 6 (integer division)
        expected_damage = 13 // 2  # 6
        assert damage == expected_damage
        assert "Fang" in message  # Default wolf name

    def test_companion_attack_dismissed_no_damage(self, ranger_game_state):
        """Test dismissed companion does no damage."""
        from cli_rpg.ranger_companion import execute_tame, execute_dismiss, companion_attack

        execute_tame(ranger_game_state, "wolf")
        execute_dismiss(ranger_game_state)

        damage, message = companion_attack(ranger_game_state, enemy_defense=0)

        assert damage == 0
        assert message == ""
