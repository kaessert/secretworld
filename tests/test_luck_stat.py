"""Tests for Luck (LCK) stat on Character model."""
import pytest
from cli_rpg.models.character import Character, CharacterClass, CLASS_BONUSES


class TestLuckStatBasics:
    """Test basic luck stat functionality on Character."""

    def test_character_has_luck_stat(self):
        """Character has `luck` attribute defaulting to 10."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        assert hasattr(char, "luck")
        assert char.luck == 10

    def test_luck_stat_validation_min(self):
        """LCK validates minimum 1 like other stats."""
        with pytest.raises(ValueError, match="luck must be at least 1"):
            Character(name="Test", strength=10, dexterity=10, intelligence=10, luck=0)

    def test_luck_stat_validation_max(self):
        """LCK validates maximum 20 like other stats."""
        with pytest.raises(ValueError, match="luck must be at most 20"):
            Character(name="Test", strength=10, dexterity=10, intelligence=10, luck=21)

    def test_luck_stat_valid_range(self):
        """LCK accepts values within 1-20 range."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10, luck=15)
        assert char.luck == 15


class TestLuckClassBonuses:
    """Test class bonuses for luck stat."""

    def test_rogue_gets_luck_bonus(self):
        """Rogue class gets +2 LCK bonus."""
        # Base luck 10 + Rogue bonus 2 = 12
        char = Character(
            name="Test", strength=10, dexterity=10, intelligence=10,
            character_class=CharacterClass.ROGUE
        )
        assert char.luck == 12

    def test_ranger_gets_luck_bonus(self):
        """Ranger class gets +1 LCK bonus."""
        # Base luck 10 + Ranger bonus 1 = 11
        char = Character(
            name="Test", strength=10, dexterity=10, intelligence=10,
            character_class=CharacterClass.RANGER
        )
        assert char.luck == 11

    def test_warrior_no_luck_bonus(self):
        """Warrior class gets +0 LCK bonus."""
        char = Character(
            name="Test", strength=10, dexterity=10, intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        assert char.luck == 10

    def test_mage_no_luck_bonus(self):
        """Mage class gets +0 LCK bonus."""
        char = Character(
            name="Test", strength=10, dexterity=10, intelligence=10,
            character_class=CharacterClass.MAGE
        )
        assert char.luck == 10

    def test_cleric_no_luck_bonus(self):
        """Cleric class gets +0 LCK bonus."""
        char = Character(
            name="Test", strength=10, dexterity=10, intelligence=10,
            character_class=CharacterClass.CLERIC
        )
        assert char.luck == 10

    def test_class_bonuses_dict_includes_luck(self):
        """CLASS_BONUSES dict includes luck for each class."""
        for char_class in CharacterClass:
            assert "luck" in CLASS_BONUSES[char_class], f"Missing luck in {char_class}"


class TestLuckLevelUp:
    """Test luck increases on level up."""

    def test_level_up_increases_luck(self):
        """LCK increases by +1 on level up."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10, luck=10)
        initial_luck = char.luck
        char.level_up()
        assert char.luck == initial_luck + 1

    def test_level_up_message_includes_luck(self):
        """Level up message includes LCK stat increase."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        message = char.level_up()
        assert "LCK +1" in message


class TestLuckSerialization:
    """Test luck stat serialization/deserialization."""

    def test_to_dict_includes_luck(self):
        """to_dict() includes luck field."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10, luck=15)
        data = char.to_dict()
        assert "luck" in data
        assert data["luck"] == 15

    def test_from_dict_restores_luck(self):
        """from_dict() restores luck value."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10, luck=15)
        data = char.to_dict()
        restored = Character.from_dict(data)
        assert restored.luck == 15

    def test_from_dict_backward_compat_defaults_to_10(self):
        """from_dict() defaults luck to 10 if missing (backward compat)."""
        # Simulate old save data without luck field
        old_data = {
            "name": "OldChar",
            "strength": 12,
            "dexterity": 14,
            "intelligence": 11,
            "charisma": 10,
            "perception": 10,
            "level": 1,
        }
        char = Character.from_dict(old_data)
        assert char.luck == 10


class TestLuckDisplay:
    """Test luck stat display in character string representation."""

    def test_character_str_includes_luck(self):
        """__str__() displays LCK stat."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10, luck=15)
        char_str = str(char)
        assert "Luck" in char_str
        assert "15" in char_str
