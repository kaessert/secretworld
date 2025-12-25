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
