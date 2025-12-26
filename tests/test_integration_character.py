"""Integration tests for character system."""
import pytest
from unittest.mock import patch
from cli_rpg.models.character import Character
from cli_rpg.character_creation import create_character


class TestCharacterLifecycle:
    """Test full character lifecycle."""
    
    def test_full_character_lifecycle(self):
        """Test: Create, damage, heal, check alive status (spec requirement)"""
        # Create character
        character = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        
        # Verify initial state
        assert character.is_alive() is True
        initial_max_health = character.max_health
        assert character.health == initial_max_health
        
        # Take damage
        character.take_damage(50)
        assert character.health == initial_max_health - 50
        assert character.is_alive() is True
        
        # Heal
        character.heal(20)
        assert character.health == initial_max_health - 30
        assert character.is_alive() is True
        
        # Take fatal damage
        character.take_damage(10000)
        assert character.health == 0
        assert character.is_alive() is False
    
    def test_character_persistence(self):
        """Test: Create, serialize, deserialize, verify equality (spec requirement)"""
        # Create character
        original = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        
        # Modify state
        original.take_damage(30)
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = Character.from_dict(data)
        
        # Verify all attributes match
        assert restored.name == original.name
        assert restored.strength == original.strength
        assert restored.dexterity == original.dexterity
        assert restored.intelligence == original.intelligence
        assert restored.level == original.level
        assert restored.health == original.health
        assert restored.max_health == original.max_health
        assert restored.is_alive() == original.is_alive()


class TestCharacterCreationIntegration:
    """Test character creation integration."""
    
    @patch('builtins.input', side_effect=["Hero", "1", "manual", "15", "12", "10", "10", "10", "yes"])
    def test_create_and_use_character(self, mock_input):
        """Test: Create character through creation flow and use it (spec requirement)"""
        # Create character through interactive flow
        # Flow: name -> class (warrior) -> method (manual) -> stats (str, dex, int, cha, per) -> confirm
        character = create_character()

        # Verify character was created correctly
        assert character is not None
        assert character.name == "Hero"
        # Warrior adds STR +3, DEX +1, INT 0
        assert character.strength == 18  # 15 + 3
        assert character.dexterity == 13  # 12 + 1
        assert character.intelligence == 10  # 10 + 0

        # Use character in game operations
        assert character.is_alive() is True

        # Take damage
        character.take_damage(50)
        assert character.health < character.max_health
        assert character.is_alive() is True

        # Heal
        character.heal(25)
        assert character.health > 0

        # Serialize and restore
        data = character.to_dict()
        restored = Character.from_dict(data)
        assert restored.name == character.name
        assert restored.health == character.health

    @patch('builtins.input', side_effect=["Warrior", "3", "random", "yes"])
    def test_create_random_character_and_verify_stats(self, mock_input):
        """Test: Create random character and verify stats are valid (spec requirement)"""
        # Create character with random stats
        # Flow: name -> class (rogue) -> method (random) -> confirm
        character = create_character()

        # Verify character was created
        assert character is not None
        assert character.name == "Warrior"

        # Verify stats are in valid range (8-15 base + Rogue bonuses: STR +1, DEX +3, INT 0)
        assert 9 <= character.strength <= 16  # 8-15 + 1
        assert 11 <= character.dexterity <= 18  # 8-15 + 3
        assert 8 <= character.intelligence <= 15  # 8-15 + 0
        
        # Verify health calculation is correct
        expected_max_health = 100 + character.strength * 5
        assert character.max_health == expected_max_health
        assert character.health == expected_max_health
        
        # Verify character can be used normally
        assert character.is_alive() is True
        character.take_damage(20)
        assert character.is_alive() is True
    
    def test_character_edge_cases(self):
        """Test: Character handles edge cases correctly"""
        # Minimum stats
        char_min = Character(
            name="Min",
            strength=1,
            dexterity=1,
            intelligence=1
        )
        assert char_min.max_health == 100 + 1 * 5
        assert char_min.is_alive() is True
        
        # Maximum stats
        char_max = Character(
            name="Max",
            strength=20,
            dexterity=20,
            intelligence=20
        )
        assert char_max.max_health == 100 + 20 * 5
        assert char_max.is_alive() is True
        
        # Heal when already at max health
        char_max.heal(100)
        assert char_max.health == char_max.max_health
        
        # Take damage that exceeds health
        char_min.take_damage(10000)
        assert char_min.health == 0
        assert char_min.is_alive() is False
    
    def test_character_stat_boundaries(self):
        """Test: Character respects stat boundaries"""
        # Test valid boundary values
        char = Character(
            name="Boundary",
            strength=1,
            dexterity=20,
            intelligence=10
        )
        assert char.strength == 1
        assert char.dexterity == 20
        
        # Test invalid values raise errors
        with pytest.raises(ValueError):
            Character(name="Invalid", strength=0, dexterity=10, intelligence=10)
        
        with pytest.raises(ValueError):
            Character(name="Invalid", strength=21, dexterity=10, intelligence=10)
        
        with pytest.raises(ValueError):
            Character(name="I", strength=10, dexterity=10, intelligence=10)
        
        with pytest.raises(ValueError):
            Character(name="A" * 31, strength=10, dexterity=10, intelligence=10)
