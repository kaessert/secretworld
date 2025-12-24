"""Tests for Character leveling system."""

import pytest
from cli_rpg.models.character import Character


class TestGainXP:
    """Test gain_xp() method."""
    
    def test_gain_xp_adds_xp_correctly(self):
        """Spec: gain_xp(amount) should add XP to character."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        messages = character.gain_xp(50)
        assert character.xp == 50
    
    def test_gain_xp_triggers_level_up_at_threshold(self):
        """Spec: gain_xp() should trigger level-up when XP reaches threshold."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        # Level 1 needs 100 XP to reach level 2
        messages = character.gain_xp(100)
        assert character.level == 2
        assert len(messages) > 0
    
    def test_gain_xp_returns_level_up_messages(self):
        """Spec: gain_xp() should return messages including level-up notifications."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        messages = character.gain_xp(100)
        
        # Should have messages about XP gain and level up
        assert len(messages) >= 2
        assert any("xp" in msg.lower() for msg in messages)
        assert any("level" in msg.lower() for msg in messages)
    
    def test_gain_xp_multiple_level_ups(self):
        """Spec: gain_xp() should handle multiple level-ups from single XP gain."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        # Give enough XP for multiple levels (level 1->2 = 100, 2->3 = 200)
        messages = character.gain_xp(300)
        assert character.level == 3
        assert len(messages) >= 3  # XP gain + 2 level ups


class TestLevelUp:
    """Test level_up() method."""
    
    def test_level_up_increases_level(self):
        """Spec: level_up() should increase character level by 1."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        initial_level = character.level
        message = character.level_up()
        assert character.level == initial_level + 1
    
    def test_level_up_increases_stats(self):
        """Spec: level_up() should increase character stats."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        initial_str = character.strength
        initial_dex = character.dexterity
        initial_int = character.intelligence
        
        character.level_up()
        
        # At least one stat should increase
        assert (character.strength > initial_str or 
                character.dexterity > initial_dex or 
                character.intelligence > initial_int)
    
    def test_level_up_restores_health_to_new_max(self):
        """Spec: level_up() should restore health to new maximum."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        # Damage the character
        character.take_damage(50)
        damaged_health = character.health
        old_max_health = character.max_health
        
        character.level_up()
        
        # Health should be restored to full
        assert character.health == character.max_health
        # Max health should have increased (if strength increased)
        assert character.max_health >= old_max_health
    
    def test_level_up_resets_xp_properly(self):
        """Spec: level_up() should reset XP threshold for next level."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        # Gain XP to level up
        character.xp = 100
        old_xp = character.xp
        character.level_up()
        
        # XP should not be modified by level_up (that's handled by gain_xp)
        assert character.xp == old_xp
        # XP to next level should be higher (level 2 needs 200 XP)
        assert character.xp_to_next_level == 200
    
    def test_level_up_returns_message(self):
        """Spec: level_up() should return a message describing the level up."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        message = character.level_up()
        
        assert isinstance(message, str)
        assert len(message) > 0
        assert "level" in message.lower()


class TestXPSerialization:
    """Test XP serialization."""
    
    def test_to_dict_includes_xp(self):
        """Spec: to_dict() should include XP in serialization."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        character.xp = 75
        
        data = character.to_dict()
        assert "xp" in data
        assert data["xp"] == 75
    
    def test_from_dict_restores_xp(self):
        """Spec: from_dict() should restore XP from serialization."""
        data = {
            "name": "Hero",
            "strength": 12,
            "dexterity": 10,
            "intelligence": 10,
            "level": 2,
            "health": 100,
            "max_health": 160,
            "xp": 50
        }
        character = Character.from_dict(data)
        assert character.xp == 50
    
    def test_serialization_roundtrip_preserves_xp(self):
        """Spec: XP should survive serialization roundtrip unchanged."""
        original = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=3
        )
        original.xp = 123
        
        data = original.to_dict()
        restored = Character.from_dict(data)
        
        assert restored.xp == original.xp
        assert restored.level == original.level


class TestXPToNextLevel:
    """Test XP threshold calculation."""
    
    def test_xp_to_next_level_calculated_on_init(self):
        """Spec: xp_to_next_level should be calculated as level * 100."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=1
        )
        assert character.xp_to_next_level == 100
    
    def test_xp_to_next_level_scales_with_level(self):
        """Spec: xp_to_next_level should scale with level."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            level=5
        )
        assert character.xp_to_next_level == 500
