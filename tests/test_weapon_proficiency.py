"""Tests for weapon proficiency system.

Spec tests:
- Test XP gain and level transitions (0→25→50→75→100)
- Test damage bonus returns correct values for each level
- Test can_use_special() at each level
- Test serialization/deserialization
"""
import pytest
from cli_rpg.models.weapon_proficiency import (
    WeaponType,
    ProficiencyLevel,
    WeaponProficiency,
)


class TestWeaponType:
    """Test WeaponType enum."""

    def test_weapon_types_exist(self):
        """Spec: All weapon types must be defined."""
        assert WeaponType.SWORD.value == "sword"
        assert WeaponType.AXE.value == "axe"
        assert WeaponType.DAGGER.value == "dagger"
        assert WeaponType.MACE.value == "mace"
        assert WeaponType.BOW.value == "bow"
        assert WeaponType.STAFF.value == "staff"
        assert WeaponType.UNKNOWN.value == "unknown"


class TestProficiencyLevel:
    """Test ProficiencyLevel enum."""

    def test_proficiency_levels_exist(self):
        """Spec: All proficiency levels must be defined."""
        assert ProficiencyLevel.NOVICE.value == "Novice"
        assert ProficiencyLevel.APPRENTICE.value == "Apprentice"
        assert ProficiencyLevel.JOURNEYMAN.value == "Journeyman"
        assert ProficiencyLevel.EXPERT.value == "Expert"
        assert ProficiencyLevel.MASTER.value == "Master"


class TestWeaponProficiency:
    """Test WeaponProficiency dataclass."""

    def test_new_proficiency_starts_at_novice(self):
        """Spec: New proficiency starts at 0 XP (Novice)."""
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD)
        assert prof.xp == 0
        assert prof.get_level() == ProficiencyLevel.NOVICE

    def test_get_level_thresholds(self):
        """Spec: Test level transitions at 0→25→50→75→100 XP."""
        # Novice: 0-24 XP
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=0)
        assert prof.get_level() == ProficiencyLevel.NOVICE

        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=24)
        assert prof.get_level() == ProficiencyLevel.NOVICE

        # Apprentice: 25-49 XP
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=25)
        assert prof.get_level() == ProficiencyLevel.APPRENTICE

        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=49)
        assert prof.get_level() == ProficiencyLevel.APPRENTICE

        # Journeyman: 50-74 XP
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=50)
        assert prof.get_level() == ProficiencyLevel.JOURNEYMAN

        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=74)
        assert prof.get_level() == ProficiencyLevel.JOURNEYMAN

        # Expert: 75-99 XP
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=75)
        assert prof.get_level() == ProficiencyLevel.EXPERT

        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=99)
        assert prof.get_level() == ProficiencyLevel.EXPERT

        # Master: 100+ XP
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=100)
        assert prof.get_level() == ProficiencyLevel.MASTER

    def test_get_damage_bonus(self):
        """Spec: Test damage bonus for each level (0%, 5%, 10%, 15%, 20%)."""
        # Novice: +0%
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=0)
        assert prof.get_damage_bonus() == 1.0

        # Apprentice: +5%
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=25)
        assert prof.get_damage_bonus() == 1.05

        # Journeyman: +10%
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=50)
        assert prof.get_damage_bonus() == 1.10

        # Expert: +15%
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=75)
        assert prof.get_damage_bonus() == 1.15

        # Master: +20%
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=100)
        assert prof.get_damage_bonus() == 1.20

    def test_can_use_special(self):
        """Spec: Special moves unlocked at Journeyman (50 XP)."""
        # Novice: no special
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=0)
        assert prof.can_use_special() is False

        # Apprentice: no special
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=25)
        assert prof.can_use_special() is False

        # Journeyman: has special
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=50)
        assert prof.can_use_special() is True

        # Expert: has special
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=75)
        assert prof.can_use_special() is True

        # Master: has special
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=100)
        assert prof.can_use_special() is True

    def test_is_special_enhanced(self):
        """Spec: Special move enhanced at Master (100 XP)."""
        # Non-master levels: not enhanced
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=0)
        assert prof.is_special_enhanced() is False

        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=50)
        assert prof.is_special_enhanced() is False

        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=99)
        assert prof.is_special_enhanced() is False

        # Master: enhanced
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=100)
        assert prof.is_special_enhanced() is True

    def test_gain_xp(self):
        """Spec: Test XP gain and level-up message."""
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=0)

        # Gain XP without level-up
        message = prof.gain_xp(10)
        assert prof.xp == 10
        assert message is None  # No level up

        # Gain XP with level-up to Apprentice
        message = prof.gain_xp(15)  # 10 + 15 = 25
        assert prof.xp == 25
        assert message is not None
        assert "Apprentice" in message
        assert "sword" in message.lower()

        # Gain XP with level-up to Journeyman
        message = prof.gain_xp(25)  # 25 + 25 = 50
        assert prof.xp == 50
        assert "Journeyman" in message

        # Gain XP with level-up to Expert
        message = prof.gain_xp(25)  # 50 + 25 = 75
        assert prof.xp == 75
        assert "Expert" in message

        # Gain XP with level-up to Master
        message = prof.gain_xp(25)  # 75 + 25 = 100
        assert prof.xp == 100
        assert "Master" in message

    def test_xp_caps_at_100(self):
        """Spec: XP should cap at 100."""
        prof = WeaponProficiency(weapon_type=WeaponType.SWORD, xp=95)
        prof.gain_xp(10)  # 95 + 10 = 105, should cap at 100
        assert prof.xp == 100

    def test_serialization(self):
        """Spec: Test to_dict() and from_dict() for persistence."""
        prof = WeaponProficiency(weapon_type=WeaponType.DAGGER, xp=50)

        # Serialize
        data = prof.to_dict()
        assert data["weapon_type"] == "dagger"
        assert data["xp"] == 50

        # Deserialize
        restored = WeaponProficiency.from_dict(data)
        assert restored.weapon_type == WeaponType.DAGGER
        assert restored.xp == 50
        assert restored.get_level() == ProficiencyLevel.JOURNEYMAN


class TestCharacterProficiencies:
    """Test Character weapon proficiency tracking."""

    def test_get_weapon_proficiency_default_novice(self):
        """Spec: get_weapon_proficiency returns Novice for new weapon types."""
        from cli_rpg.models.character import Character

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        prof = char.get_weapon_proficiency(WeaponType.SWORD)

        assert prof.weapon_type == WeaponType.SWORD
        assert prof.xp == 0
        assert prof.get_level() == ProficiencyLevel.NOVICE

    def test_gain_weapon_xp_creates_and_updates_proficiency(self):
        """Spec: gain_weapon_xp creates proficiency if not exists, then updates."""
        from cli_rpg.models.character import Character

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

        # First gain should create proficiency
        message = char.gain_weapon_xp(WeaponType.SWORD, 10)
        assert message is None  # No level up yet

        prof = char.get_weapon_proficiency(WeaponType.SWORD)
        assert prof.xp == 10

        # Additional gain should update
        message = char.gain_weapon_xp(WeaponType.SWORD, 15)  # 10 + 15 = 25
        assert message is not None  # Level up to Apprentice
        assert "Apprentice" in message

        prof = char.get_weapon_proficiency(WeaponType.SWORD)
        assert prof.xp == 25

    def test_proficiencies_persist_through_serialization(self):
        """Spec: weapon_proficiencies serialize/deserialize correctly."""
        from cli_rpg.models.character import Character

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.gain_weapon_xp(WeaponType.SWORD, 50)  # Journeyman
        char.gain_weapon_xp(WeaponType.DAGGER, 25)  # Apprentice

        # Serialize
        data = char.to_dict()

        # Check serialized data
        assert "weapon_proficiencies" in data
        assert len(data["weapon_proficiencies"]) == 2

        # Deserialize
        restored = Character.from_dict(data)

        # Check restored proficiencies
        sword_prof = restored.get_weapon_proficiency(WeaponType.SWORD)
        assert sword_prof.xp == 50
        assert sword_prof.get_level() == ProficiencyLevel.JOURNEYMAN

        dagger_prof = restored.get_weapon_proficiency(WeaponType.DAGGER)
        assert dagger_prof.xp == 25
        assert dagger_prof.get_level() == ProficiencyLevel.APPRENTICE

    def test_backward_compatible_load_without_proficiencies(self):
        """Spec: Old saves without proficiencies should load correctly."""
        from cli_rpg.models.character import Character

        # Simulate old save data without weapon_proficiencies
        old_save = {
            "name": "OldChar",
            "strength": 12,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
        }

        char = Character.from_dict(old_save)

        # Should work without errors, proficiencies start empty
        prof = char.get_weapon_proficiency(WeaponType.SWORD)
        assert prof.xp == 0


class TestProficiencyCommand:
    """Test proficiency command display."""

    def test_proficiency_command_empty(self):
        """Spec: Show message when no proficiencies."""
        from cli_rpg.game_state import parse_command

        cmd, args = parse_command("proficiency")
        assert cmd == "proficiency"
        assert args == []

    def test_proficiency_command_alias(self):
        """Spec: 'prof' should be an alias for 'proficiency'."""
        from cli_rpg.game_state import parse_command

        cmd, args = parse_command("prof")
        assert cmd == "proficiency"

    def test_proficiency_command_shows_proficiencies(self):
        """Spec: Command shows proficiencies with progress bars."""
        from cli_rpg.models.character import Character

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.gain_weapon_xp(WeaponType.SWORD, 50)

        # Verify proficiency exists and has correct data
        prof = char.get_weapon_proficiency(WeaponType.SWORD)
        assert prof.xp == 50


class TestWeaponTypeInference:
    """Test inferring weapon type from item names."""

    def test_infer_sword_types(self):
        """Test that sword-like names infer to SWORD."""
        from cli_rpg.models.weapon_proficiency import infer_weapon_type

        assert infer_weapon_type("Iron Sword") == WeaponType.SWORD
        assert infer_weapon_type("Rusty Blade") == WeaponType.SWORD
        assert infer_weapon_type("Steel Rapier") == WeaponType.SWORD
        assert infer_weapon_type("Great Claymore") == WeaponType.SWORD
        assert infer_weapon_type("Longsword") == WeaponType.SWORD

    def test_infer_axe_types(self):
        """Test that axe-like names infer to AXE."""
        from cli_rpg.models.weapon_proficiency import infer_weapon_type

        assert infer_weapon_type("Iron Axe") == WeaponType.AXE
        assert infer_weapon_type("Battle Hatchet") == WeaponType.AXE
        assert infer_weapon_type("War Axe") == WeaponType.AXE

    def test_infer_dagger_types(self):
        """Test that dagger-like names infer to DAGGER."""
        from cli_rpg.models.weapon_proficiency import infer_weapon_type

        assert infer_weapon_type("Iron Dagger") == WeaponType.DAGGER
        assert infer_weapon_type("Poison Knife") == WeaponType.DAGGER
        assert infer_weapon_type("Stiletto") == WeaponType.DAGGER
        assert infer_weapon_type("Throwing Shiv") == WeaponType.DAGGER

    def test_infer_mace_types(self):
        """Test that mace-like names infer to MACE."""
        from cli_rpg.models.weapon_proficiency import infer_weapon_type

        assert infer_weapon_type("Iron Mace") == WeaponType.MACE
        assert infer_weapon_type("War Hammer") == WeaponType.MACE
        assert infer_weapon_type("Morning Star") == WeaponType.MACE
        assert infer_weapon_type("Flail of Doom") == WeaponType.MACE
        assert infer_weapon_type("Iron Club") == WeaponType.MACE

    def test_infer_bow_types(self):
        """Test that bow-like names infer to BOW."""
        from cli_rpg.models.weapon_proficiency import infer_weapon_type

        assert infer_weapon_type("Longbow") == WeaponType.BOW
        assert infer_weapon_type("Hunter's Bow") == WeaponType.BOW
        assert infer_weapon_type("Crossbow") == WeaponType.BOW
        assert infer_weapon_type("Short Bow") == WeaponType.BOW

    def test_infer_staff_types(self):
        """Test that staff-like names infer to STAFF."""
        from cli_rpg.models.weapon_proficiency import infer_weapon_type

        assert infer_weapon_type("Oak Staff") == WeaponType.STAFF
        assert infer_weapon_type("Wizard's Wand") == WeaponType.STAFF
        assert infer_weapon_type("Magic Rod") == WeaponType.STAFF
        assert infer_weapon_type("Scepter of Power") == WeaponType.STAFF

    def test_infer_unknown_types(self):
        """Test that unrecognized names default to UNKNOWN."""
        from cli_rpg.models.weapon_proficiency import infer_weapon_type

        assert infer_weapon_type("Mysterious Object") == WeaponType.UNKNOWN
        assert infer_weapon_type("Random Thing") == WeaponType.UNKNOWN
        assert infer_weapon_type("Gold Coin") == WeaponType.UNKNOWN
