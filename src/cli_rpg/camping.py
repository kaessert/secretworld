"""Camping, foraging, and hunting wilderness survival mechanics.

Provides camp, forage, and hunt commands that integrate with dread, inventory,
random encounters, and day/night systems.
"""

import random
from typing import TYPE_CHECKING, Optional, Tuple

from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.location import Location

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


# =============================================================================
# Constants
# =============================================================================

# Location categories where camping is allowed
CAMPABLE_CATEGORIES = {"forest", "wilderness", "cave", "ruins"}

# Location categories where foraging/hunting is allowed (wilderness only, not dungeons)
FORAGEABLE_CATEGORIES = {"forest", "wilderness"}
HUNTABLE_CATEGORIES = {"forest", "wilderness"}

# Camping mechanics
CAMP_HEAL_PERCENT = 50  # Heal 50% of max HP
CAMP_DREAD_REDUCTION = 30  # Base dread reduction
CAMP_CAMPFIRE_BONUS = 10  # Extra dread reduction with campfire
CAMP_TIME_HOURS = 8  # Time advance for camping
CAMP_DREAM_CHANCE = 0.40  # 40% chance of dream during camp
CAMP_VISITOR_CHANCE = 0.20  # 20% chance of campfire visitor

# Forage mechanics
FORAGE_BASE_CHANCE = 40  # Base 40% success
FORAGE_PER_BONUS = 2  # +2% per perception
FORAGE_COOLDOWN = 1  # 1 hour cooldown
FORAGE_TIME_HOURS = 1  # Advances 1 hour

# Hunt mechanics
HUNT_BASE_CHANCE = 30  # Base 30% success
HUNT_DEX_BONUS = 2  # +2% per dexterity
HUNT_PER_BONUS = 1  # +1% per perception
HUNT_COOLDOWN = 2  # 2 hours cooldown
HUNT_TIME_HOURS = 2  # Advances 2 hours
HUNT_CRITICAL_PERCENT = 10  # Critical success is 10% of success chance


# =============================================================================
# Forage item templates
# =============================================================================

FORAGE_ITEMS = [
    {
        "name": "Herbs",
        "description": "A bundle of healing herbs found in the wild",
        "heal_amount": 10,
        "weight": 3,  # Higher weight = more common
        "night_only": False,
    },
    {
        "name": "Wild Berries",
        "description": "Sweet berries that provide minor healing",
        "heal_amount": 15,
        "weight": 3,
        "night_only": False,
    },
    {
        "name": "Medicinal Root",
        "description": "A potent root with healing properties",
        "heal_amount": 20,
        "weight": 2,
        "night_only": False,
    },
    {
        "name": "Moonpetal Flower",
        "description": "A rare flower that glows softly in moonlight. Restores mana.",
        "mana_restore": 20,
        "weight": 1,  # Rare
        "night_only": True,  # Spec: only at night
    },
]


# =============================================================================
# Hunt result templates
# =============================================================================

HUNT_RESULTS = {
    "success_items": [
        {
            "name": "Raw Meat",
            "description": "Raw meat from a hunted animal. Best cooked over a campfire.",
            "heal_amount": 30,
        }
    ],
    "critical_items": [
        {
            "name": "Animal Pelt",
            "description": "A quality animal pelt. Can be sold for gold.",
            "sell_value": 25,
        }
    ],
}


# =============================================================================
# Campfire visitor templates
# =============================================================================

CAMPFIRE_VISITORS = [
    {
        "name": "Wandering Storyteller",
        "type": "storyteller",
        "description": "An old traveler with tales to share",
        "dread_reduction": 5,
    },
    {
        "name": "Traveling Merchant",
        "type": "merchant",
        "description": "A merchant passing through with discounted wares",
        "discount": 0.20,  # 20% discount
    },
    {
        "name": "Lost Traveler",
        "type": "traveler",
        "description": "A weary traveler seeking warmth by your fire",
    },
]


# =============================================================================
# Helper functions
# =============================================================================

def is_campable_location(location: Location) -> bool:
    """Check if a location is suitable for camping.

    Camping is allowed in wilderness areas (forest, wilderness, cave, ruins)
    but NOT in safe zones (towns, villages) where 'rest' should be used.

    Args:
        location: The location to check

    Returns:
        True if camping is allowed, False otherwise
    """
    # Safe zones cannot be camped in (use rest instead)
    if location.is_safe_zone:
        return False

    # Check if category is in campable list
    category = location.category or ""
    return category.lower() in CAMPABLE_CATEGORIES


def is_forageable_location(location: Location) -> bool:
    """Check if a location is suitable for foraging.

    Foraging is allowed in wilderness/forest areas but NOT in towns or dungeons.

    Args:
        location: The location to check

    Returns:
        True if foraging is allowed, False otherwise
    """
    if location.is_safe_zone:
        return False

    category = location.category or ""
    return category.lower() in FORAGEABLE_CATEGORIES


def is_huntable_location(location: Location) -> bool:
    """Check if a location is suitable for hunting.

    Hunting is allowed in wilderness/forest areas but NOT in towns or dungeons.

    Args:
        location: The location to check

    Returns:
        True if hunting is allowed, False otherwise
    """
    if location.is_safe_zone:
        return False

    category = location.category or ""
    return category.lower() in HUNTABLE_CATEGORIES


def decrement_cooldowns(game_state: "GameState", hours: int = 1) -> None:
    """Decrement forage, hunt, and gather cooldowns by the specified hours.

    Args:
        game_state: The current game state
        hours: Number of hours to decrement (default 1)
    """
    game_state.forage_cooldown = max(0, game_state.forage_cooldown - hours)
    game_state.hunt_cooldown = max(0, game_state.hunt_cooldown - hours)
    game_state.gather_cooldown = max(0, game_state.gather_cooldown - hours)


def _generate_forage_item(is_night: bool) -> Item:
    """Generate a random forage item based on time of day.

    Args:
        is_night: Whether it's currently night time

    Returns:
        An Item instance representing the found item
    """
    # Filter items by night availability
    available = [
        item for item in FORAGE_ITEMS
        if not item.get("night_only", False) or is_night
    ]

    # Weight-based random selection
    weights = [item.get("weight", 1) for item in available]
    chosen = random.choices(available, weights=weights, k=1)[0]

    # Create the item
    return Item(
        name=chosen["name"],
        description=chosen["description"],
        item_type=ItemType.CONSUMABLE,
        heal_amount=chosen.get("heal_amount", 0),
        mana_restore=chosen.get("mana_restore", 0),
    )


def _generate_hunt_result(is_critical: bool) -> list[Item]:
    """Generate hunt result items.

    Args:
        is_critical: Whether this was a critical success

    Returns:
        List of Item instances (Raw Meat, and optionally Animal Pelt)
    """
    items = []

    # Always give Raw Meat on success
    meat_data = HUNT_RESULTS["success_items"][0]
    meat = Item(
        name=meat_data["name"],
        description=meat_data["description"],
        item_type=ItemType.CONSUMABLE,
        heal_amount=meat_data.get("heal_amount", 0),
    )
    items.append(meat)

    # Critical success also gives Animal Pelt
    if is_critical:
        pelt_data = HUNT_RESULTS["critical_items"][0]
        pelt = Item(
            name=pelt_data["name"],
            description=pelt_data["description"],
            item_type=ItemType.MISC,
        )
        items.append(pelt)

    return items


def _cook_raw_meat(game_state: "GameState") -> Optional[str]:
    """Cook any Raw Meat in inventory to Cooked Meat.

    Args:
        game_state: The current game state

    Returns:
        Message about cooking if meat was cooked, None otherwise
    """
    inventory = game_state.current_character.inventory
    raw_meat = inventory.find_item_by_name("Raw Meat")

    if raw_meat is None:
        return None

    # Remove raw meat and add cooked meat
    inventory.remove_item(raw_meat)
    cooked_meat = Item(
        name="Cooked Meat",
        description="Deliciously cooked meat. Provides excellent healing.",
        item_type=ItemType.CONSUMABLE,
        heal_amount=40,  # Spec: 40 HP vs 30 for raw
    )
    inventory.add_item(cooked_meat)

    return "You cook your Raw Meat over the campfire. It smells delicious!"


def _spawn_campfire_visitor() -> Optional[dict]:
    """Potentially spawn a campfire visitor.

    Returns:
        Visitor dict if spawned, None otherwise
    """
    if random.random() < CAMP_VISITOR_CHANCE:
        return random.choice(CAMPFIRE_VISITORS)
    return None


# =============================================================================
# Main command functions
# =============================================================================

def execute_camp(game_state: "GameState") -> Tuple[bool, str]:
    """Execute the camp command.

    Camping in the wilderness allows recovery and reduces dread. Requires
    Camping Supplies item. With an active light source (campfire), provides
    extra dread reduction and can cook Raw Meat.

    Args:
        game_state: The current game state

    Returns:
        Tuple of (success, message)
    """
    from cli_rpg import colors
    from cli_rpg.dreams import maybe_trigger_dream, display_dream

    location = game_state.get_current_location()
    character = game_state.current_character

    # Check location suitability
    if not is_campable_location(location):
        if location.is_safe_zone:
            return (False, "You're in a safe zone. Use 'rest' command here instead.")
        return (False, "You can't camp here. Find a wilderness location.")

    # Check for Camping Supplies
    supplies = character.inventory.find_item_by_name("Camping Supplies")
    if supplies is None:
        return (False, "You need Camping Supplies to make camp. Buy some from a merchant.")

    # Check if already at full health and no dread
    at_full = character.health >= character.max_health
    no_dread = character.dread_meter.dread == 0

    if at_full and no_dread:
        return (False, "You're already well-rested. No need to camp.")

    # Consume supplies
    character.inventory.remove_item(supplies)

    messages = []

    # Heal 50% of max HP
    heal_amount = character.max_health // 2
    actual_heal = min(heal_amount, character.max_health - character.health)
    if actual_heal > 0:
        character.heal(actual_heal)
        messages.append(f"You set up camp and rest. Recovered {actual_heal} health.")
    else:
        messages.append("You set up camp and rest comfortably.")

    # Check for campfire (active light source)
    has_campfire = character.has_active_light()

    # Reduce dread
    dread_reduction = CAMP_DREAD_REDUCTION
    if has_campfire:
        dread_reduction += CAMP_CAMPFIRE_BONUS
        messages.append("The warm campfire eases your mind.")

    if character.dread_meter.dread > 0:
        old_dread = character.dread_meter.dread
        character.dread_meter.reduce_dread(dread_reduction)
        dread_reduced = old_dread - character.dread_meter.dread
        if dread_reduced > 0:
            messages.append(f"Dread -{dread_reduced}%.")

    # Cook raw meat if campfire present
    if has_campfire:
        cook_msg = _cook_raw_meat(game_state)
        if cook_msg:
            messages.append(cook_msg)

    # Advance time
    game_state.game_time.advance(CAMP_TIME_HOURS)
    messages.append(f"Time passes... ({CAMP_TIME_HOURS} hours)")

    # Check for campfire visitor
    if has_campfire:
        visitor = _spawn_campfire_visitor()
        if visitor:
            visitor_msg = f"\nA {visitor['name']} approaches your campfire!"
            messages.append(visitor_msg)
            if visitor.get("dread_reduction"):
                character.dread_meter.reduce_dread(visitor["dread_reduction"])
                messages.append(f"Their stories calm your nerves. (Dread -{visitor['dread_reduction']}%)")

    # Check for dream
    result_message = "\n".join(messages)
    dream = maybe_trigger_dream(
        dread=character.dread_meter.dread,
        choices=getattr(game_state, 'choices', None),
        theme=getattr(game_state, 'theme', 'fantasy'),
        ai_service=getattr(game_state, 'ai_service', None),
        location_name=game_state.current_location
    )
    if dream:
        # Display dream immediately with typewriter effect
        print("\n" + result_message)
        display_dream(dream)
        return (True, "")

    return (True, result_message)


def execute_forage(game_state: "GameState") -> Tuple[bool, str]:
    """Execute the forage command.

    Search the area for herbs, berries, and other useful plants.
    Success chance based on perception. Has a 1-hour cooldown.

    Args:
        game_state: The current game state

    Returns:
        Tuple of (success, message)
    """
    location = game_state.get_current_location()
    character = game_state.current_character

    # Check location suitability
    if not is_forageable_location(location):
        if location.is_safe_zone:
            return (False, "You can't forage here. Visit the wilderness instead.")
        category = location.category or "this area"
        return (False, f"You can't forage in {category}. Find a forest or wilderness.")

    # Check cooldown
    if game_state.forage_cooldown > 0:
        return (False, f"You've recently foraged. Wait {game_state.forage_cooldown} hour(s).")

    # Calculate success chance
    success_chance = FORAGE_BASE_CHANCE + (character.perception * FORAGE_PER_BONUS)
    success_chance = min(95, success_chance)  # Cap at 95%

    # Advance time (always, whether success or failure)
    game_state.game_time.advance(FORAGE_TIME_HOURS)

    # Set cooldown
    game_state.forage_cooldown = FORAGE_COOLDOWN

    # Roll for success
    roll = random.random() * 100
    if roll < success_chance:
        # Success - find item
        is_night = game_state.game_time.is_night()
        item = _generate_forage_item(is_night)

        if character.inventory.is_full():
            return (True, f"You found {item.name}, but your inventory is full!")

        character.inventory.add_item(item)
        return (True, f"You search the area and found {item.name}!")
    else:
        # Failure
        return (True, "You search but find nothing useful.")


def execute_hunt(game_state: "GameState") -> Tuple[bool, str]:
    """Execute the hunt command.

    Hunt for game in the wilderness. Success chance based on dexterity
    and perception. Has a 2-hour cooldown.

    Args:
        game_state: The current game state

    Returns:
        Tuple of (success, message)
    """
    location = game_state.get_current_location()
    character = game_state.current_character

    # Check location suitability
    if not is_huntable_location(location):
        if location.is_safe_zone:
            return (False, "You can't hunt here. Visit the wilderness instead.")
        category = location.category or "this area"
        return (False, f"You can't hunt in {category}. Find a forest or wilderness.")

    # Check cooldown
    if game_state.hunt_cooldown > 0:
        return (False, f"You've recently hunted. Wait {game_state.hunt_cooldown} hour(s).")

    # Calculate success chance
    success_chance = HUNT_BASE_CHANCE
    success_chance += character.dexterity * HUNT_DEX_BONUS
    success_chance += character.perception * HUNT_PER_BONUS
    success_chance = min(95, success_chance)  # Cap at 95%

    # Advance time (always, whether success or failure)
    game_state.game_time.advance(HUNT_TIME_HOURS)

    # Set cooldown
    game_state.hunt_cooldown = HUNT_COOLDOWN

    # Roll for success
    roll = random.random() * 100
    if roll < success_chance:
        # Check for critical success (10% of success chance)
        critical_threshold = success_chance * (HUNT_CRITICAL_PERCENT / 100)
        is_critical = roll < critical_threshold

        # Generate items
        items = _generate_hunt_result(is_critical)

        if character.inventory.is_full():
            return (True, "You caught something, but your inventory is full!")

        # Add items to inventory
        item_names = []
        for item in items:
            if not character.inventory.is_full():
                character.inventory.add_item(item)
                item_names.append(item.name)

        items_str = " and ".join(item_names)
        if is_critical:
            return (True, f"Excellent hunt! You caught {items_str}!")
        return (True, f"Successful hunt! You obtained {items_str}.")
    else:
        # Failure
        return (True, "The prey escapes before you can catch it.")
