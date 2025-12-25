# Brave Player Rewards - High-Dread Area Secrets

## Summary
Add special rewards and secrets that are only accessible in high-dread areas (75%+ dread), rewarding players who venture into dangerous territory rather than always managing their dread down.

## Spec
- High-dread locations (75%+) have a chance to reveal bonus loot when player looks around
- "Dread Treasures" are special items only discoverable at high dread levels
- Thematic tie-in: the darkness reveals secrets hidden from those who fear it
- Integrate with existing layered look system (details at look 2, secrets at look 3)
- At 75%+ dread + 3rd look: chance to find "Dread Treasure" item

## Implementation Steps

### 1. Create `src/cli_rpg/brave_rewards.py` - New module for dread-based rewards

```python
"""Brave player rewards - secrets accessible only at high dread.

Players who venture into dangerous areas (75%+ dread) have a chance
to discover special treasures hidden in the darkness.
"""
import random
from typing import Optional

from cli_rpg.models.item import Item, ItemType

# Dread threshold for brave rewards (same as attack penalty threshold)
BRAVE_REWARD_DREAD_THRESHOLD = 75

# Chance to find a dread treasure when looking at high dread (30%)
DREAD_TREASURE_CHANCE = 0.30

# Dread treasure definitions - powerful items with thematic flavor
DREAD_TREASURES = [
    {
        "name": "Shadow Essence",
        "description": "A vial of crystallized darkness. Heals body and calms the mind.",
        "item_type": ItemType.CONSUMABLE,
        "heal_amount": 50,
        # Consuming this also reduces dread by 20 (handled in use logic)
    },
    {
        "name": "Veil of Courage",
        "description": "A cloak woven from conquered fears. Reduces incoming damage.",
        "item_type": ItemType.ARMOR,
        "defense_bonus": 8,
    },
    {
        "name": "Dread Blade",
        "description": "A weapon forged in nightmares. Grows stronger in darkness.",
        "item_type": ItemType.WEAPON,
        "damage_bonus": 10,
    },
    {
        "name": "Darklight Torch",
        "description": "A torch that burns with black flame. Provides light for twice as long.",
        "item_type": ItemType.CONSUMABLE,
        "light_duration": 20,  # Double normal torch
    },
]


def check_for_dread_treasure(
    dread_level: int,
    look_count: int,
    location_name: str
) -> Optional[Item]:
    """Check if player discovers a dread treasure.

    Requirements:
    - Dread at 75% or higher
    - Looking at location for 3rd+ time (exploring secrets layer)
    - 30% chance to find treasure

    Args:
        dread_level: Current dread percentage (0-100)
        look_count: Number of times player has looked at this location
        location_name: Name of current location (for flavor text)

    Returns:
        Item if treasure discovered, None otherwise
    """
    # Must be at high dread
    if dread_level < BRAVE_REWARD_DREAD_THRESHOLD:
        return None

    # Must be examining secrets (3rd+ look)
    if look_count < 3:
        return None

    # 30% chance to find treasure
    if random.random() > DREAD_TREASURE_CHANCE:
        return None

    # Select random treasure
    treasure_def = random.choice(DREAD_TREASURES)

    return Item(
        name=treasure_def["name"],
        description=treasure_def["description"],
        item_type=treasure_def["item_type"],
        damage_bonus=treasure_def.get("damage_bonus", 0),
        defense_bonus=treasure_def.get("defense_bonus", 0),
        heal_amount=treasure_def.get("heal_amount", 0),
        light_duration=treasure_def.get("light_duration", 0),
    )


def get_discovery_message(item: Item) -> str:
    """Get thematic message for discovering a dread treasure.

    Args:
        item: The discovered treasure item

    Returns:
        Formatted discovery message
    """
    return (
        f"\nThe darkness reveals its secrets to those who dare face it...\n"
        f"You discover: {item.name}!"
    )
```

### 2. Update `game_state.py` - Integrate with look command

In `GameState.look()` method (around line 245-266), add dread treasure check:

```python
def look(self) -> str:
    """Get a formatted description of the current location with progressive detail.
    ...
    """
    location = self.get_current_location()
    # Increment and get look count
    look_count = self.current_character.record_look(self.current_location)
    # Get visibility level from weather, accounting for location category
    visibility = self.weather.get_visibility_level(location.category)
    result = location.get_layered_description(look_count, visibility=visibility)

    # Check for dread treasure (brave player rewards)
    from cli_rpg.brave_rewards import check_for_dread_treasure, get_discovery_message
    treasure = check_for_dread_treasure(
        dread_level=self.current_character.dread_meter.dread,
        look_count=look_count,
        location_name=self.current_location
    )
    if treasure is not None:
        if self.current_character.inventory.add_item(treasure):
            result += get_discovery_message(treasure)
        else:
            result += f"\n{colors.warning('Your inventory is full! You cannot take the treasure.')}"

    return result
```

### 3. Add tests in `tests/test_brave_rewards.py`

```python
"""Tests for brave player rewards (dread treasures).

Spec: Players at 75%+ dread who examine locations carefully (3rd look)
have a 30% chance to discover special "dread treasures" - powerful items
only accessible to those who brave the darkness.
"""
import pytest
from unittest.mock import patch

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType
from cli_rpg.game_state import GameState
from cli_rpg.brave_rewards import (
    check_for_dread_treasure,
    get_discovery_message,
    BRAVE_REWARD_DREAD_THRESHOLD,
    DREAD_TREASURE_CHANCE,
    DREAD_TREASURES,
)


def create_test_character():
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


def create_test_world():
    cave = Location(
        name="Dark Cave",
        description="A foreboding cave.",
        connections={},
        coordinates=(0, 0),
        category="cave",
        secrets="Ancient bones litter the floor."
    )
    return {"Dark Cave": cave}


class TestCheckForDreadTreasure:
    """Test treasure discovery conditions."""

    def test_no_treasure_below_threshold(self):
        """No treasure found below 75% dread."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=74, look_count=3, location_name="Cave")
        assert result is None

    def test_no_treasure_before_3rd_look(self):
        """No treasure found on 1st or 2nd look."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=80, look_count=2, location_name="Cave")
        assert result is None

    def test_treasure_at_high_dread_3rd_look(self):
        """Treasure found at 75%+ dread on 3rd+ look when chance succeeds."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=75, look_count=3, location_name="Cave")
        assert result is not None
        assert isinstance(result, Item)

    def test_respects_30_percent_chance(self):
        """Treasure not found when chance roll fails."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.5):
            result = check_for_dread_treasure(dread_level=90, look_count=3, location_name="Cave")
        assert result is None

    def test_treasure_is_valid_item(self):
        """Discovered treasure is a valid Item with stats."""
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = check_for_dread_treasure(dread_level=80, look_count=5, location_name="Cave")
        assert result.name in [t["name"] for t in DREAD_TREASURES]


class TestDreadTreasureItems:
    """Test the treasure item definitions."""

    def test_all_treasures_have_names(self):
        """All treasures have valid names."""
        for treasure in DREAD_TREASURES:
            assert len(treasure["name"]) >= 2

    def test_all_treasures_have_descriptions(self):
        """All treasures have descriptions."""
        for treasure in DREAD_TREASURES:
            assert len(treasure["description"]) >= 1

    def test_treasures_have_stats(self):
        """Each treasure has at least one stat bonus."""
        for treasure in DREAD_TREASURES:
            has_stat = any([
                treasure.get("damage_bonus", 0) > 0,
                treasure.get("defense_bonus", 0) > 0,
                treasure.get("heal_amount", 0) > 0,
                treasure.get("light_duration", 0) > 0,
            ])
            assert has_stat, f"{treasure['name']} has no stat bonus"


class TestGameStateLookIntegration:
    """Test integration with GameState.look()."""

    def test_look_at_high_dread_can_find_treasure(self):
        """Looking at 75%+ dread on 3rd look can find treasure."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Dark Cave")
        char.dread_meter.dread = 80

        # Look twice first
        game_state.look()
        game_state.look()

        # Force treasure find on 3rd look
        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = game_state.look()

        assert "darkness reveals" in result.lower() or "discover" in result.lower()

    def test_look_at_low_dread_no_treasure(self):
        """Looking at low dread never finds treasure."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Dark Cave")
        char.dread_meter.dread = 50

        game_state.look()
        game_state.look()

        with patch("cli_rpg.brave_rewards.random.random", return_value=0.1):
            result = game_state.look()

        assert "discover" not in result.lower()


class TestDiscoveryMessage:
    """Test discovery message formatting."""

    def test_message_contains_item_name(self):
        """Discovery message includes item name."""
        item = Item(
            name="Shadow Essence",
            description="A vial of darkness",
            item_type=ItemType.CONSUMABLE,
            heal_amount=50
        )
        message = get_discovery_message(item)
        assert "Shadow Essence" in message

    def test_message_is_thematic(self):
        """Discovery message has thematic content."""
        item = Item(name="Test Item", description="Test", item_type=ItemType.MISC)
        message = get_discovery_message(item)
        assert "darkness" in message.lower()
```

## Verification

1. Run new tests: `pytest tests/test_brave_rewards.py -v`
2. Run full test suite: `pytest`
3. Manual test flow:
   - Start game, travel to dangerous area (cave/dungeon)
   - Build dread to 75%+
   - Use `look` command 3 times
   - Verify treasure discovery message and item in inventory
