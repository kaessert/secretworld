"""Tests for gold system.

Tests the Character gold attribute and add_gold/remove_gold methods.
"""
from cli_rpg.models.character import Character


class TestGold:
    """Tests for gold system on Character model - tests spec: Gold System (Character Enhancement)."""

    def test_character_starts_with_zero_gold(self):
        """Character starts with 0 gold by default."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        assert char.gold == 0

    def test_add_gold(self):
        """add_gold() increases character gold."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(100)
        assert char.gold == 100

    def test_add_gold_multiple(self):
        """add_gold() accumulates gold."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(100)
        char.add_gold(50)
        assert char.gold == 150

    def test_remove_gold_success(self):
        """remove_gold() returns True and removes gold when sufficient."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(100)
        success = char.remove_gold(50)
        assert success is True
        assert char.gold == 50

    def test_remove_gold_insufficient(self):
        """remove_gold() returns False and doesn't change gold when insufficient."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(30)
        success = char.remove_gold(50)
        assert success is False
        assert char.gold == 30  # Unchanged

    def test_gold_serialization(self):
        """Gold is included in to_dict() serialization."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(250)
        data = char.to_dict()
        assert data["gold"] == 250

    def test_gold_deserialization(self):
        """Gold is restored from from_dict() deserialization."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.add_gold(250)
        data = char.to_dict()
        restored = Character.from_dict(data)
        assert restored.gold == 250

    def test_gold_backward_compatibility(self):
        """from_dict() defaults to 0 gold for old saves without gold field."""
        data = {
            "name": "OldHero",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
            "health": 150,
            "max_health": 150,
            "xp": 0,
            "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None}
        }
        char = Character.from_dict(data)
        assert char.gold == 0
