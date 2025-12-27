"""Secret discovery mechanics using Perception stat."""
import random
from enum import Enum
from typing import List, Optional, Tuple, TYPE_CHECKING

from cli_rpg.models.character import Character
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.location import Location

if TYPE_CHECKING:
    from cli_rpg.world_grid import SubGrid


class SecretType(Enum):
    """Types of secrets that can be discovered."""

    HIDDEN_DOOR = "hidden_door"
    HIDDEN_TREASURE = "hidden_treasure"
    TRAP = "trap"
    LORE_HINT = "lore_hint"


# Bonuses for active search
SEARCH_BONUS = 5  # Bonus to PER when actively searching
LIGHT_BONUS = 2  # Additional bonus when character has active light

# Hidden room templates by parent category
HIDDEN_ROOM_TEMPLATES = {
    "dungeon": [
        ("Hidden Chamber", "A dusty chamber concealed behind the wall. Cobwebs drape ancient shelves."),
        ("Secret Vault", "A small vault with iron-banded chests. Someone hid their treasures here."),
        ("Forgotten Cell", "A cramped cell, long abandoned. Scratch marks cover the walls."),
    ],
    "cave": [
        ("Crystal Grotto", "A natural hollow where crystals glitter in the darkness."),
        ("Hidden Cavern", "A secluded cave with a still pool of water."),
        ("Secret Pool", "An underground spring hidden from view."),
    ],
    "forest": [
        ("Hidden Glade", "A peaceful clearing hidden by dense undergrowth."),
        ("Secret Hollow", "A concealed hollow within a massive ancient tree."),
        ("Fairy Circle", "A mystical circle of mushrooms in a hidden clearing."),
    ],
    "temple": [
        ("Hidden Shrine", "A secret shrine to a forgotten deity."),
        ("Secret Crypt", "An unmarked crypt beneath the floor."),
        ("Sacred Chamber", "A chamber of meditation hidden from worldly eyes."),
    ],
    "default": [
        ("Hidden Room", "A secret room concealed behind a false wall."),
        ("Secret Alcove", "A small alcove hidden from casual view."),
        ("Concealed Chamber", "A chamber that has been carefully hidden."),
    ],
}


def generate_hidden_room(
    location: Location,
    sub_grid: "SubGrid",
    direction: str,
    parent_category: Optional[str] = None,
) -> Optional[Location]:
    """Generate a hidden room in the SubGrid at an empty adjacent coordinate.

    Args:
        location: Current location where door was found
        sub_grid: The SubGrid to add the room to
        direction: Direction the hidden door leads (north, south, east, west, up, down)
        parent_category: Category of parent location for theming

    Returns:
        The new Location if created, None if no valid position found
    """
    from cli_rpg.world_grid import SUBGRID_DIRECTION_OFFSETS

    # Get current location's 3D coordinates
    if location.coordinates is None:
        return None

    x, y = location.coordinates[:2]
    z = location.coordinates[2] if len(location.coordinates) > 2 else 0

    # Get direction offset
    if direction not in SUBGRID_DIRECTION_OFFSETS:
        return None

    dx, dy, dz = SUBGRID_DIRECTION_OFFSETS[direction]
    target_x, target_y, target_z = x + dx, y + dy, z + dz

    # Check if target is within bounds
    if not sub_grid.is_within_bounds(target_x, target_y, target_z):
        return None

    # Check if target is already occupied
    if sub_grid.get_by_coordinates(target_x, target_y, target_z) is not None:
        return None

    # Get templates for this category
    category_key = parent_category.lower() if parent_category else "default"
    templates = HIDDEN_ROOM_TEMPLATES.get(category_key, HIDDEN_ROOM_TEMPLATES["default"])

    # Pick a random template
    name, description = random.choice(templates)

    # Create the hidden room
    hidden_room = Location(
        name=name,
        description=description,
        category="hidden_room",
    )

    # Add to SubGrid (this sets coordinates and parent_location)
    sub_grid.add_location(hidden_room, target_x, target_y, target_z)

    # 50% chance to add treasure
    if random.random() < 0.5:
        hidden_room.hidden_secrets.append({
            "type": SecretType.HIDDEN_TREASURE.value,
            "description": "A cache left by whoever built this secret room.",
            "threshold": 8,  # Easy to find once you're in
            "discovered": False,
            "reward_gold": random.randint(20, 50),
        })

    return hidden_room


def check_passive_detection(char: Character, location: Location) -> List[dict]:
    """Check for automatic secret detection based on PER when entering a location.

    Secrets with threshold <= character's perception are automatically detected
    and marked as discovered. Already discovered secrets are skipped.

    Args:
        char: The player character with perception stat
        location: The location being entered/examined

    Returns:
        List of secrets that were newly detected (dicts with type, description, threshold)
    """
    detected = []
    for secret in location.hidden_secrets:
        # Skip already discovered secrets
        if secret.get("discovered"):
            continue
        # Check if perception meets threshold
        if char.perception >= secret.get("threshold", 15):
            secret["discovered"] = True
            detected.append(secret)
    return detected


def perform_active_search(
    char: Character,
    location: Location,
    sub_grid: Optional["SubGrid"] = None,
) -> Tuple[bool, str]:
    """Perform active search for hidden secrets using the 'search' command.

    Active search grants a +5 bonus to perception, plus +2 if the character
    has an active light source. Secrets found are marked as discovered.

    Args:
        char: The player character performing the search
        location: The location being searched
        sub_grid: Optional SubGrid for creating hidden rooms when hidden_door found

    Returns:
        Tuple of (found_something, message):
        - found_something: True if any secrets were discovered
        - message: Description of what was found or a message if nothing found
    """
    # Calculate effective perception with bonuses
    effective_per = char.perception + SEARCH_BONUS
    if char.has_active_light():
        effective_per += LIGHT_BONUS

    # Get undiscovered secrets
    undiscovered = [s for s in location.hidden_secrets if not s.get("discovered")]

    if not undiscovered:
        return (False, "You search carefully but find nothing hidden.")

    # Check each secret against effective perception
    found = []
    for secret in undiscovered:
        if effective_per >= secret.get("threshold", 15):
            secret["discovered"] = True
            found.append(secret)

    if not found:
        return (False, "You search but don't notice anything unusual.")

    # Build discovery message with reward details
    messages = []
    for secret in found:
        desc = secret["description"]
        success, reward_msg = apply_secret_rewards(char, location, secret, sub_grid)
        if reward_msg:
            messages.append(f"{desc} - {reward_msg}")
        else:
            messages.append(desc)

    return (True, f"You discover: {', '.join(messages)}")


# Default trap disarm XP reward
TRAP_DISARM_XP = 10
# Default lore hint XP reward
LORE_HINT_XP = 5
# DEX threshold for trap disarm
TRAP_DEX_THRESHOLD = 12


def apply_secret_rewards(
    char: Character,
    location: Location,
    secret: dict,
    sub_grid: Optional["SubGrid"] = None,
) -> Tuple[bool, str]:
    """Apply rewards/effects for a discovered secret.

    Args:
        char: Player character
        location: Current location
        secret: The secret dict with type, description, etc.
        sub_grid: Optional SubGrid for creating hidden rooms when hidden_door found

    Returns:
        (success, message) describing what happened
    """
    # Check if reward was already applied
    if secret.get("reward_applied"):
        return (False, "")

    secret_type = secret.get("type", "")
    messages = []

    if secret_type == SecretType.HIDDEN_TREASURE.value:
        messages.extend(_apply_treasure_reward(char, secret))
    elif secret_type == SecretType.TRAP.value:
        messages.append(_apply_trap_effect(char, secret))
    elif secret_type == SecretType.LORE_HINT.value:
        messages.append(_apply_lore_reward(char, secret))
    elif secret_type == SecretType.HIDDEN_DOOR.value:
        messages.append(_apply_hidden_door(location, secret, sub_grid))

    # Mark reward as applied so it won't be re-applied
    secret["reward_applied"] = True

    return (True, " ".join(messages)) if messages else (True, "")


def _apply_treasure_reward(char: Character, secret: dict) -> List[str]:
    """Apply treasure rewards (gold and/or items).

    Args:
        char: Player character
        secret: The secret dict with reward_gold and/or reward_item

    Returns:
        List of reward messages
    """
    messages = []

    # Grant gold if specified
    gold_reward = secret.get("reward_gold", 0)
    if gold_reward > 0:
        char.add_gold(gold_reward)
        messages.append(f"Found {gold_reward} gold!")

    # Grant item if specified
    item_name = secret.get("reward_item")
    if item_name:
        # Create item based on name - try to match known consumables
        item = _create_treasure_item(item_name)
        char.inventory.add_item(item)
        messages.append(f"Found {item_name}!")

    return messages


def _create_treasure_item(item_name: str) -> Item:
    """Create an item for treasure rewards.

    Args:
        item_name: Name of the item to create

    Returns:
        Item instance
    """
    # Check for known consumable types
    name_lower = item_name.lower()

    if "health potion" in name_lower or "healing" in name_lower:
        return Item(
            name=item_name,
            description="A potion that restores health.",
            item_type=ItemType.CONSUMABLE,
            heal_amount=25,
        )
    elif "mana potion" in name_lower:
        return Item(
            name=item_name,
            description="A potion that restores mana.",
            item_type=ItemType.CONSUMABLE,
            mana_restore=25,
        )
    elif "dagger" in name_lower:
        return Item(
            name=item_name,
            description="A small, sharp blade.",
            item_type=ItemType.WEAPON,
            damage_bonus=3,
        )
    elif "sword" in name_lower:
        return Item(
            name=item_name,
            description="A sturdy sword.",
            item_type=ItemType.WEAPON,
            damage_bonus=5,
        )
    elif "shield" in name_lower:
        return Item(
            name=item_name,
            description="A protective shield.",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
        )
    elif "torch" in name_lower:
        return Item(
            name=item_name,
            description="A light source that illuminates dark places.",
            item_type=ItemType.CONSUMABLE,
            light_duration=10,
        )
    else:
        # Default to misc item
        return Item(
            name=item_name,
            description=f"A mysterious {item_name}.",
            item_type=ItemType.MISC,
        )


def _apply_trap_effect(char: Character, secret: dict) -> str:
    """Apply trap effect based on DEX check.

    Args:
        char: Player character
        secret: The secret dict with trap_damage

    Returns:
        Message describing what happened
    """
    trap_damage = secret.get("trap_damage", 10)

    if char.dexterity >= TRAP_DEX_THRESHOLD:
        # Disarm trap and gain XP
        char.xp += TRAP_DISARM_XP
        return f"You deftly disarm the trap! Gained {TRAP_DISARM_XP} XP."
    else:
        # Triggered trap - take damage
        char.take_damage(trap_damage)
        return f"The trap triggers! You take {trap_damage} damage."


def _apply_lore_reward(char: Character, secret: dict) -> str:
    """Apply lore discovery reward (XP).

    Args:
        char: Player character
        secret: The secret dict

    Returns:
        Message describing what happened
    """
    char.xp += LORE_HINT_XP
    return f"Gained {LORE_HINT_XP} XP for the discovery."


def _apply_hidden_door(
    location: Location,
    secret: dict,
    sub_grid: Optional["SubGrid"] = None,
) -> str:
    """Reveal a hidden exit direction and create a room if in SubGrid.

    Args:
        location: Current location
        secret: The secret dict with exit_direction
        sub_grid: Optional SubGrid for creating the hidden room

    Returns:
        Message describing what happened
    """
    exit_direction = secret.get("exit_direction", "north")

    # Try to generate actual hidden room in SubGrid
    if sub_grid is not None:
        hidden_room = generate_hidden_room(
            location, sub_grid, exit_direction, location.category
        )
        if hidden_room is not None:
            return f"A hidden passage to the {exit_direction} reveals {hidden_room.name}!"

    # Fallback: just add temporary exit (cosmetic)
    if exit_direction not in location.temporary_exits:
        location.temporary_exits.append(exit_direction)

    return f"A hidden passage to the {exit_direction} is revealed!"
