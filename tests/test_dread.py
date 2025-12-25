"""Unit tests for the DreadMeter model.

Tests cover:
1. Initialization at 0
2. Adding dread (clamped to 100)
3. Reducing dread (clamped to 0)
4. Milestone messages when crossing thresholds
5. Display bar generation
6. Attack penalty logic
7. Serialization roundtrip
8. Backward compatibility for Character without dread
"""

import pytest

from cli_rpg.models.dread import DreadMeter
from cli_rpg.models.character import Character


class TestDreadMeterInitialization:
    """Test that DreadMeter starts at 0."""

    def test_dread_meter_initialization(self):
        """Dread meter should initialize with dread=0."""
        meter = DreadMeter()
        assert meter.dread == 0


class TestAddDread:
    """Test adding dread to the meter."""

    def test_add_dread_basic(self):
        """Adding dread should increase the value."""
        meter = DreadMeter()
        meter.add_dread(10)
        assert meter.dread == 10

    def test_add_dread_clamps_to_100(self):
        """Adding dread should never exceed 100."""
        meter = DreadMeter(dread=95)
        meter.add_dread(20)  # Would be 115
        assert meter.dread == 100

    def test_add_dread_at_100(self):
        """Adding dread when already at 100 should stay at 100."""
        meter = DreadMeter(dread=100)
        meter.add_dread(10)
        assert meter.dread == 100


class TestReduceDread:
    """Test reducing dread from the meter."""

    def test_reduce_dread_basic(self):
        """Reducing dread should decrease the value."""
        meter = DreadMeter(dread=50)
        meter.reduce_dread(20)
        assert meter.dread == 30

    def test_reduce_dread_clamps_to_0(self):
        """Reducing dread should never go below 0."""
        meter = DreadMeter(dread=10)
        meter.reduce_dread(20)  # Would be -10
        assert meter.dread == 0

    def test_reduce_dread_at_0(self):
        """Reducing dread when already at 0 should stay at 0."""
        meter = DreadMeter(dread=0)
        meter.reduce_dread(10)
        assert meter.dread == 0


class TestMilestoneMessages:
    """Test milestone messages when crossing thresholds."""

    def test_crossing_25_threshold(self):
        """Crossing 25% should return a milestone message."""
        meter = DreadMeter(dread=20)
        message = meter.add_dread(10)  # 20 -> 30, crosses 25
        assert message is not None
        assert "unease" in message.lower() or "something" in message.lower()

    def test_crossing_50_threshold(self):
        """Crossing 50% should return a milestone message."""
        meter = DreadMeter(dread=45)
        message = meter.add_dread(10)  # 45 -> 55, crosses 50
        assert message is not None
        assert "paranoi" in message.lower() or "whisper" in message.lower() or "shadow" in message.lower()

    def test_crossing_75_threshold(self):
        """Crossing 75% should return a milestone message."""
        meter = DreadMeter(dread=70)
        message = meter.add_dread(10)  # 70 -> 80, crosses 75
        assert message is not None
        assert "grip" in message.lower() or "terror" in message.lower() or "attack" in message.lower()

    def test_crossing_100_threshold(self):
        """Reaching 100% should return a critical milestone message."""
        meter = DreadMeter(dread=95)
        message = meter.add_dread(10)  # 95 -> 100, crosses 100
        assert message is not None
        assert "overwhelm" in message.lower() or "consume" in message.lower() or "darkness" in message.lower()

    def test_no_message_when_not_crossing_threshold(self):
        """No message when not crossing a threshold."""
        meter = DreadMeter(dread=30)
        message = meter.add_dread(5)  # 30 -> 35, no threshold crossed
        assert message is None

    def test_no_message_on_reduce(self):
        """Reducing dread should not produce milestone messages."""
        meter = DreadMeter(dread=80)
        meter.reduce_dread(10)  # 80 -> 70, crosses below 75
        # reduce_dread doesn't return a message


class TestDreadDisplay:
    """Test the dread display bar."""

    def test_dread_display_at_0(self):
        """Display at 0% should show empty bar."""
        meter = DreadMeter(dread=0)
        display = meter.get_display()
        assert "DREAD" in display
        assert "0%" in display
        assert "█" not in display  # No filled blocks at 0%

    def test_dread_display_at_50(self):
        """Display at 50% should show half-filled bar."""
        meter = DreadMeter(dread=50)
        display = meter.get_display()
        assert "DREAD" in display
        assert "50%" in display
        # Should have roughly half filled blocks
        assert "█" in display

    def test_dread_display_at_100(self):
        """Display at 100% should show full bar."""
        meter = DreadMeter(dread=100)
        display = meter.get_display()
        assert "DREAD" in display
        assert "100%" in display
        # Bar should be fully filled
        assert "░" not in display  # No empty blocks at 100%


class TestDreadAttackPenalty:
    """Test the attack penalty at high dread levels."""

    def test_dread_attack_penalty_below_75(self):
        """No attack penalty below 75% dread."""
        meter = DreadMeter(dread=74)
        assert meter.get_penalty() == 1.0

    def test_dread_attack_penalty_at_75(self):
        """10% attack penalty at exactly 75% dread."""
        meter = DreadMeter(dread=75)
        assert meter.get_penalty() == 0.9

    def test_dread_attack_penalty_above_75(self):
        """10% attack penalty above 75% dread."""
        meter = DreadMeter(dread=90)
        assert meter.get_penalty() == 0.9

    def test_dread_attack_penalty_at_100(self):
        """10% attack penalty at 100% dread."""
        meter = DreadMeter(dread=100)
        assert meter.get_penalty() == 0.9


class TestDreadIsCritical:
    """Test the is_critical method."""

    def test_is_critical_at_100(self):
        """is_critical should be True at 100%."""
        meter = DreadMeter(dread=100)
        assert meter.is_critical() is True

    def test_is_critical_below_100(self):
        """is_critical should be False below 100%."""
        meter = DreadMeter(dread=99)
        assert meter.is_critical() is False


class TestDreadSerialization:
    """Test serialization and deserialization."""

    def test_dread_serialization_roundtrip(self):
        """to_dict and from_dict should preserve dread value."""
        meter = DreadMeter(dread=42)
        data = meter.to_dict()
        restored = DreadMeter.from_dict(data)
        assert restored.dread == 42

    def test_dread_serialization_at_0(self):
        """Serialization should work at 0%."""
        meter = DreadMeter(dread=0)
        data = meter.to_dict()
        assert data["dread"] == 0

    def test_dread_serialization_at_100(self):
        """Serialization should work at 100%."""
        meter = DreadMeter(dread=100)
        data = meter.to_dict()
        assert data["dread"] == 100


class TestCharacterDreadIntegration:
    """Test Character model integration with DreadMeter."""

    def test_character_has_dread_meter(self):
        """Character should have a dread_meter attribute."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)
        assert hasattr(char, "dread_meter")
        assert isinstance(char.dread_meter, DreadMeter)
        assert char.dread_meter.dread == 0

    def test_character_attack_power_with_high_dread(self):
        """Character attack power should be reduced at 75%+ dread."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)
        base_attack = char.get_attack_power()

        # Set dread to 75%
        char.dread_meter.dread = 75
        reduced_attack = char.get_attack_power()

        # Should be 90% of base attack
        expected = int(base_attack * 0.9)
        assert reduced_attack == expected

    def test_character_attack_power_with_low_dread(self):
        """Character attack power should not be affected below 75% dread."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)
        base_attack = char.get_attack_power()

        char.dread_meter.dread = 74
        assert char.get_attack_power() == base_attack

    def test_backward_compatibility_no_dread(self):
        """Character.from_dict should handle save files without dread_meter."""
        # Simulate an old save file format without dread
        old_save_data = {
            "name": "OldHero",
            "strength": 12,
            "dexterity": 10,
            "intelligence": 8,
            "level": 3,
            "health": 150,
            "max_health": 160,
            "xp": 50,
            "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None},
            "gold": 100,
            "quests": [],
            "bestiary": {},
            "status_effects": [],
            "look_counts": {},
            # Note: no "dread_meter" key
        }

        char = Character.from_dict(old_save_data)

        # Should have a dread_meter initialized to 0
        assert hasattr(char, "dread_meter")
        assert char.dread_meter.dread == 0

    def test_character_serialization_with_dread(self):
        """Character.to_dict should include dread_meter."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)
        char.dread_meter.dread = 55

        data = char.to_dict()

        assert "dread_meter" in data
        assert data["dread_meter"]["dread"] == 55

    def test_character_deserialization_with_dread(self):
        """Character.from_dict should restore dread_meter."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)
        char.dread_meter.dread = 67

        data = char.to_dict()
        restored = Character.from_dict(data)

        assert restored.dread_meter.dread == 67
