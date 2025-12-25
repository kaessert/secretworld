"""Tests for Character model."""
import pytest
from cli_rpg.models.character import Character


class TestCharacterCreation:
    """Test character creation and validation."""
    
    def test_character_creation_valid(self):
        """Test: Create character with valid attributes (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        assert character.name == "Hero"
        assert character.strength == 10
        assert character.dexterity == 12
        assert character.intelligence == 8
        assert character.level == 1
        assert character.health > 0
        assert character.max_health > 0
    
    def test_character_creation_with_defaults(self):
        """Test: Verify level defaults to 1 (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        assert character.level == 1
    
    def test_character_health_calculation(self):
        """Test: Verify max_health = 100 + strength * 5 (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        expected_max_health = 100 + 10 * 5
        assert character.max_health == expected_max_health
        assert character.health == expected_max_health
    
    def test_character_name_validation_too_short(self):
        """Test: Reject name < 2 chars (spec requirement)"""
        with pytest.raises(ValueError, match="at least 2 characters"):
            Character(
                name="H",
                strength=10,
                dexterity=10,
                intelligence=10
            )
    
    def test_character_name_validation_too_long(self):
        """Test: Reject name > 30 chars (spec requirement)"""
        with pytest.raises(ValueError, match="at most 30 characters"):
            Character(
                name="A" * 31,
                strength=10,
                dexterity=10,
                intelligence=10
            )
    
    def test_character_name_validation_empty(self):
        """Test: Reject empty name (spec requirement)"""
        with pytest.raises(ValueError, match="cannot be empty"):
            Character(
                name="",
                strength=10,
                dexterity=10,
                intelligence=10
            )
    
    def test_character_stat_validation_below_min(self):
        """Test: Reject stats < 1 (spec requirement)"""
        with pytest.raises(ValueError, match="at least 1"):
            Character(
                name="Hero",
                strength=0,
                dexterity=10,
                intelligence=10
            )
    
    def test_character_stat_validation_above_max(self):
        """Test: Reject stats > 20 (spec requirement)"""
        with pytest.raises(ValueError, match="at most 20"):
            Character(
                name="Hero",
                strength=21,
                dexterity=10,
                intelligence=10
            )


class TestCharacterMethods:
    """Test character methods."""
    
    def test_character_take_damage(self):
        """Test: Reduce health by damage amount (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        initial_health = character.health
        character.take_damage(20)
        assert character.health == initial_health - 20
    
    def test_character_take_damage_cannot_go_negative(self):
        """Test: Health floors at 0 (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        character.take_damage(10000)
        assert character.health == 0
    
    def test_character_heal(self):
        """Test: Increase health by heal amount (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        character.take_damage(30)
        damaged_health = character.health
        character.heal(15)
        assert character.health == damaged_health + 15
    
    def test_character_heal_cannot_exceed_max(self):
        """Test: Health caps at max_health (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        character.take_damage(10)
        character.heal(1000)
        assert character.health == character.max_health
    
    def test_character_is_alive_when_healthy(self):
        """Test: Returns True when health > 0 (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        assert character.is_alive() is True
    
    def test_character_is_alive_when_dead(self):
        """Test: Returns False when health = 0 (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10
        )
        character.take_damage(10000)
        assert character.is_alive() is False


class TestCharacterSerialization:
    """Test character serialization."""
    
    def test_character_to_dict(self):
        """Test: Serializes all attributes correctly (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8,
            level=1
        )
        data = character.to_dict()
        assert data["name"] == "Hero"
        assert data["strength"] == 10
        assert data["dexterity"] == 12
        assert data["intelligence"] == 8
        assert data["level"] == 1
        assert data["health"] == character.health
        assert data["max_health"] == character.max_health
    
    def test_character_from_dict(self):
        """Test: Deserializes to equivalent Character instance (spec requirement)"""
        original = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        data = original.to_dict()
        restored = Character.from_dict(data)
        
        assert restored.name == original.name
        assert restored.strength == original.strength
        assert restored.dexterity == original.dexterity
        assert restored.intelligence == original.intelligence
        assert restored.level == original.level
        assert restored.health == original.health
        assert restored.max_health == original.max_health
    
    def test_character_from_dict_with_damage(self):
        """Test: Deserializes character with reduced health correctly"""
        original = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        original.take_damage(50)
        data = original.to_dict()
        restored = Character.from_dict(data)
        
        assert restored.health == original.health
        assert restored.health < restored.max_health
    
    def test_character_str_representation(self):
        """Test: Verify __str__ method output (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        str_repr = str(character)
        assert "Hero" in str_repr
        assert "Level 1" in str_repr
        assert "Alive" in str_repr
        assert str(character.health) in str_repr
        assert str(character.max_health) in str_repr
        assert "Strength: 10" in str_repr
        assert "Dexterity: 12" in str_repr
        assert "Intelligence: 8" in str_repr
        # Verify XP progress is displayed (spec: XP progress display)
        assert "XP:" in str_repr
        assert f"{character.xp}/{character.xp_to_next_level}" in str_repr
