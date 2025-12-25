"""Tests for the light source system.

Light sources are consumable items that reduce dread buildup when entering dark areas.
When a light source is active:
- Dread increases from location category are reduced by 50%
- Night dread bonus is negated
- Light sources last for a limited number of moves (e.g., 5 moves)
- Multiple light sources stack by extending duration (not multiplying effect)
"""

import pytest
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.character import Character


# --- Item light_duration Tests ---


class TestItemLightDuration:
    """Test Item model light_duration field."""

    def test_item_light_duration_default_zero(self):
        """Item defaults to light_duration=0 (not a light source)."""
        item = Item(
            name="Potion",
            description="A healing potion",
            item_type=ItemType.CONSUMABLE,
            heal_amount=20
        )
        assert item.light_duration == 0

    def test_item_light_duration_positive(self):
        """Item can have light_duration > 0 for light sources."""
        torch = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )
        assert torch.light_duration == 5

    def test_item_light_duration_negative_rejected(self):
        """Negative light_duration raises ValueError."""
        with pytest.raises(ValueError, match="light_duration cannot be negative"):
            Item(
                name="Broken Torch",
                description="A broken torch",
                item_type=ItemType.CONSUMABLE,
                light_duration=-1
            )

    def test_item_light_duration_serialization(self):
        """to_dict/from_dict preserves light_duration."""
        torch = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )

        data = torch.to_dict()
        assert data["light_duration"] == 5

        restored = Item.from_dict(data)
        assert restored.light_duration == 5

    def test_item_str_shows_light_info(self):
        """String includes 'X moves of light' for light sources."""
        torch = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )

        result = str(torch)
        assert "5 moves of light" in result


# --- Character light_remaining Tests ---


class TestCharacterLightRemaining:
    """Test Character model light tracking."""

    def test_character_light_remaining_default_zero(self):
        """Character starts with light_remaining=0."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        assert char.light_remaining == 0

    def test_character_use_light_source(self):
        """Using light source sets light_remaining to duration."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.use_light_source(5)
        assert char.light_remaining == 5

    def test_character_light_source_stacks(self):
        """Using light when already lit extends duration additively."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.use_light_source(5)
        char.use_light_source(3)
        assert char.light_remaining == 8

    def test_character_tick_light_decrements(self):
        """tick_light() decrements light_remaining by 1."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.use_light_source(5)
        char.tick_light()
        assert char.light_remaining == 4

    def test_character_tick_light_expires_message(self):
        """tick_light() returns message when light expires (reaches 0)."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.use_light_source(1)

        message = char.tick_light()

        assert char.light_remaining == 0
        assert message is not None
        assert "fades" in message.lower() or "darkness" in message.lower()

    def test_character_tick_light_no_message_when_active(self):
        """tick_light() returns None when light still active."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.use_light_source(5)

        message = char.tick_light()

        assert char.light_remaining == 4
        assert message is None

    def test_character_tick_light_no_light(self):
        """tick_light() returns None when no light is active."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        message = char.tick_light()
        assert message is None
        assert char.light_remaining == 0

    def test_character_has_active_light(self):
        """has_active_light() returns True when light_remaining > 0."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        assert char.has_active_light() is False

        char.use_light_source(5)
        assert char.has_active_light() is True

        char.light_remaining = 0
        assert char.has_active_light() is False

    def test_character_light_serialization(self):
        """to_dict/from_dict preserves light_remaining."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.use_light_source(7)

        data = char.to_dict()
        assert data["light_remaining"] == 7

        restored = Character.from_dict(data)
        assert restored.light_remaining == 7


# --- Use Item Activation Tests ---


class TestUseLightSourceItem:
    """Test using light source items."""

    def test_use_light_source_activates_light(self):
        """Using a torch activates light on character."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        torch = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )
        char.inventory.add_item(torch)

        success, _ = char.use_item(torch)

        assert success is True
        assert char.light_remaining == 5

    def test_use_light_source_message(self):
        """Using torch shows illumination message."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        torch = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )
        char.inventory.add_item(torch)

        success, message = char.use_item(torch)

        assert success is True
        assert "light" in message.lower() or "illumin" in message.lower()

    def test_use_light_source_removes_item(self):
        """Item is removed from inventory after use."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        torch = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )
        char.inventory.add_item(torch)

        char.use_item(torch)

        assert torch not in char.inventory.items

    def test_use_light_source_extends_existing(self):
        """Using torch when already lit extends duration."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        torch1 = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )
        torch2 = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )
        char.inventory.add_item(torch1)
        char.inventory.add_item(torch2)

        char.use_item(torch1)
        assert char.light_remaining == 5

        char.use_item(torch2)
        assert char.light_remaining == 10

    def test_use_light_source_extend_message(self):
        """Using torch when already lit shows extend message."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.use_light_source(3)  # Already have some light

        torch = Item(
            name="Torch",
            description="A wooden torch",
            item_type=ItemType.CONSUMABLE,
            light_duration=5
        )
        char.inventory.add_item(torch)

        success, message = char.use_item(torch)

        assert success is True
        assert "longer" in message.lower() or "extend" in message.lower() or "add" in message.lower()
