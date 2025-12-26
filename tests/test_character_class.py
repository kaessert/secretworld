"""Tests for Character Class system (Spec: Character Class System MVP)."""
import pytest
from cli_rpg.models.character import Character, CharacterClass, CLASS_BONUSES


class TestCharacterClassEnum:
    """Spec: CharacterClass enum exists with 5 values."""

    def test_character_class_enum_has_five_values(self):
        """Spec: CharacterClass enum has WARRIOR, MAGE, ROGUE, RANGER, CLERIC."""
        assert len(CharacterClass) == 5
        assert CharacterClass.WARRIOR.value == "Warrior"
        assert CharacterClass.MAGE.value == "Mage"
        assert CharacterClass.ROGUE.value == "Rogue"
        assert CharacterClass.RANGER.value == "Ranger"
        assert CharacterClass.CLERIC.value == "Cleric"


class TestClassBonuses:
    """Spec: CLASS_BONUSES dict maps each class to stat bonuses."""

    def test_class_bonuses_has_all_classes(self):
        """Spec: CLASS_BONUSES contains all 5 classes."""
        assert len(CLASS_BONUSES) == 5
        for char_class in CharacterClass:
            assert char_class in CLASS_BONUSES

    def test_warrior_bonuses(self):
        """Spec: Warrior has STR +3, DEX +1, INT 0."""
        bonuses = CLASS_BONUSES[CharacterClass.WARRIOR]
        assert bonuses["strength"] == 3
        assert bonuses["dexterity"] == 1
        assert bonuses["intelligence"] == 0

    def test_mage_bonuses(self):
        """Spec: Mage has STR 0, DEX +1, INT +3."""
        bonuses = CLASS_BONUSES[CharacterClass.MAGE]
        assert bonuses["strength"] == 0
        assert bonuses["dexterity"] == 1
        assert bonuses["intelligence"] == 3

    def test_rogue_bonuses(self):
        """Spec: Rogue has STR +1, DEX +3, INT 0."""
        bonuses = CLASS_BONUSES[CharacterClass.ROGUE]
        assert bonuses["strength"] == 1
        assert bonuses["dexterity"] == 3
        assert bonuses["intelligence"] == 0

    def test_ranger_bonuses(self):
        """Spec: Ranger has STR +1, DEX +2, INT +1."""
        bonuses = CLASS_BONUSES[CharacterClass.RANGER]
        assert bonuses["strength"] == 1
        assert bonuses["dexterity"] == 2
        assert bonuses["intelligence"] == 1

    def test_cleric_bonuses(self):
        """Spec: Cleric has STR +1, DEX 0, INT +2."""
        bonuses = CLASS_BONUSES[CharacterClass.CLERIC]
        assert bonuses["strength"] == 1
        assert bonuses["dexterity"] == 0
        assert bonuses["intelligence"] == 2


class TestCharacterWithClass:
    """Spec: Character model accepts optional character_class field."""

    def test_character_with_no_class_defaults_to_none(self):
        """Spec: Character without class defaults to None (backward compat)."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        assert character.character_class is None

    def test_character_with_warrior_class(self):
        """Spec: Character with Warrior class stores class identity."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        assert character.character_class == CharacterClass.WARRIOR

    def test_character_with_class_applies_stat_bonuses(self):
        """Spec: Stats apply bonuses - Warrior with base STR 10 has effective STR 13."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Warrior bonuses: STR +3, DEX +1, INT 0
        assert character.strength == 13  # 10 + 3
        assert character.dexterity == 11  # 10 + 1
        assert character.intelligence == 10  # 10 + 0

    def test_mage_applies_stat_bonuses(self):
        """Spec: Mage bonuses applied correctly."""
        character = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Mage bonuses: STR 0, DEX +1, INT +3
        assert character.strength == 10
        assert character.dexterity == 11
        assert character.intelligence == 13

    def test_rogue_applies_stat_bonuses(self):
        """Spec: Rogue bonuses applied correctly."""
        character = Character(
            name="Thief",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.ROGUE,
        )
        # Rogue bonuses: STR +1, DEX +3, INT 0
        assert character.strength == 11
        assert character.dexterity == 13
        assert character.intelligence == 10

    def test_ranger_applies_stat_bonuses(self):
        """Spec: Ranger bonuses applied correctly."""
        character = Character(
            name="Archer",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.RANGER,
        )
        # Ranger bonuses: STR +1, DEX +2, INT +1
        assert character.strength == 11
        assert character.dexterity == 12
        assert character.intelligence == 11

    def test_cleric_applies_stat_bonuses(self):
        """Spec: Cleric bonuses applied correctly."""
        character = Character(
            name="Priest",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        # Cleric bonuses: STR +1, DEX 0, INT +2
        assert character.strength == 11
        assert character.dexterity == 10
        assert character.intelligence == 12

    def test_class_bonuses_affect_derived_stats(self):
        """Spec: Class bonuses affect derived stats (max_health from strength)."""
        base_char = Character(
            name="Base",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        warrior = Character(
            name="Warrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Warrior has +3 STR, so max_health should be higher
        # max_health = 100 + strength * 5
        assert base_char.max_health == 100 + 10 * 5  # 150
        assert warrior.max_health == 100 + 13 * 5  # 165


class TestCharacterClassSerialization:
    """Spec: Character.from_dict/to_dict serialize class correctly."""

    def test_to_dict_includes_class(self):
        """Spec: to_dict includes character_class as string."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        data = character.to_dict()
        assert "character_class" in data
        assert data["character_class"] == "Warrior"

    def test_to_dict_with_no_class(self):
        """Spec: to_dict with None class serializes as None."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        data = character.to_dict()
        assert "character_class" in data
        assert data["character_class"] is None

    def test_from_dict_restores_class(self):
        """Spec: from_dict restores character_class correctly."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        data = character.to_dict()
        restored = Character.from_dict(data)
        assert restored.character_class == CharacterClass.MAGE

    def test_from_dict_without_class_defaults_to_none(self):
        """Spec: from_dict without character_class key defaults to None (backward compat)."""
        data = {
            "name": "Hero",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
            "health": 150,
            "max_health": 150,
            "xp": 0,
            "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None},
            "gold": 0,
        }
        character = Character.from_dict(data)
        assert character.character_class is None

    def test_from_dict_preserves_stats_with_bonuses(self):
        """Spec: from_dict preserves bonused stats from saved game."""
        warrior = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        data = warrior.to_dict()
        # Stats in dict should include bonuses
        assert data["strength"] == 13

        restored = Character.from_dict(data)
        assert restored.strength == 13
        assert restored.character_class == CharacterClass.WARRIOR


class TestCharacterClassDisplay:
    """Spec: Character.__str__() displays class name."""

    def test_str_includes_class_name(self):
        """Spec: __str__ shows class when present."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        output = str(character)
        assert "Warrior" in output

    def test_str_without_class_still_works(self):
        """Spec: __str__ works when class is None."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        output = str(character)
        assert "Hero" in output
        # Should not crash, just not include class
