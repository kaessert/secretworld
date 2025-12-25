"""Random encounter system for travel events.

Triggers occasional events (hostile enemies, friendly merchants, or neutral wanderers)
when the player moves between locations.
"""
import random
from typing import Optional, TYPE_CHECKING

from cli_rpg.models.random_encounter import RandomEncounter
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.combat import spawn_enemy, CombatEncounter
from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState

# Chance of random encounter per move (15%)
RANDOM_ENCOUNTER_CHANCE = 0.15

# Encounter type weights (must sum to 1.0)
ENCOUNTER_WEIGHTS = {
    "hostile": 0.60,   # 60% chance for combat encounter
    "merchant": 0.25,  # 25% chance for wandering merchant
    "wanderer": 0.15,  # 15% chance for neutral wanderer with lore
}


def _select_encounter_type() -> str:
    """Select encounter type based on weights.

    Returns:
        Encounter type: "hostile", "merchant", or "wanderer"
    """
    roll = random.random()
    cumulative = 0.0

    for encounter_type, weight in ENCOUNTER_WEIGHTS.items():
        cumulative += weight
        if roll <= cumulative:
            return encounter_type

    # Fallback (should not reach here if weights sum to 1.0)
    return "hostile"


def spawn_wandering_merchant(level: int) -> NPC:
    """Create a wandering merchant NPC with random wares.

    Args:
        level: Player level for scaling shop items

    Returns:
        NPC with is_merchant=True and a shop with 2-3 items
    """
    merchant_names = [
        "Traveling Peddler",
        "Mysterious Trader",
        "Wandering Merchant",
        "Roaming Vendor",
        "Nomadic Seller",
    ]
    merchant_descriptions = [
        "A weathered traveler with a pack full of wares",
        "A cloaked figure with goods from distant lands",
        "A friendly merchant with a cart of supplies",
        "A shrewd-looking trader with jingling pockets",
    ]

    name = random.choice(merchant_names)
    description = random.choice(merchant_descriptions)

    # Generate 2-3 random items for the shop
    num_items = random.randint(2, 3)
    shop_items = []

    for _ in range(num_items):
        item, price = _generate_shop_item(level)
        shop_items.append(ShopItem(item=item, buy_price=price))

    shop = Shop(name=f"{name}'s Wares", inventory=shop_items)

    return NPC(
        name=name,
        description=description,
        dialogue="Greetings, traveler! Care to see my wares?",
        is_merchant=True,
        shop=shop,
        greetings=[
            "Ah, a customer! What luck!",
            "Looking for supplies? I have just the thing.",
            "Fine goods for fine travelers!",
        ],
    )


def _generate_shop_item(level: int) -> tuple[Item, int]:
    """Generate a random item for a wandering merchant's shop.

    Args:
        level: Player level for scaling

    Returns:
        Tuple of (Item, buy_price)
    """
    item_type = random.choice([ItemType.WEAPON, ItemType.ARMOR, ItemType.CONSUMABLE])

    if item_type == ItemType.WEAPON:
        prefixes = ["Sturdy", "Sharp", "Fine", "Tempered"]
        names = ["Blade", "Dagger", "Mace", "Staff"]
        prefix = random.choice(prefixes)
        name = random.choice(names)
        damage_bonus = max(1, level + random.randint(0, 2))
        price = 20 + (level * 10) + (damage_bonus * 5)
        return Item(
            name=f"{prefix} {name}",
            description=f"A {prefix.lower()} {name.lower()} from distant lands",
            item_type=ItemType.WEAPON,
            damage_bonus=damage_bonus,
        ), price

    elif item_type == ItemType.ARMOR:
        prefixes = ["Padded", "Leather", "Chain", "Reinforced"]
        names = ["Vest", "Guard", "Helm", "Gloves"]
        prefix = random.choice(prefixes)
        name = random.choice(names)
        defense_bonus = max(1, level + random.randint(0, 1))
        price = 15 + (level * 8) + (defense_bonus * 5)
        return Item(
            name=f"{prefix} {name}",
            description=f"A {prefix.lower()} {name.lower()} for protection",
            item_type=ItemType.ARMOR,
            defense_bonus=defense_bonus,
        ), price

    else:  # CONSUMABLE
        heal_amount = 20 + (level * 5) + random.randint(0, 10)
        potions = [
            ("Health Potion", "A bubbling red potion"),
            ("Healing Tonic", "An herbal remedy"),
            ("Restoration Brew", "A powerful healing drink"),
        ]
        name, desc = random.choice(potions)
        price = 10 + heal_amount // 2
        return Item(
            name=name,
            description=desc,
            item_type=ItemType.CONSUMABLE,
            heal_amount=heal_amount,
        ), price


def spawn_wanderer(theme: str) -> NPC:
    """Create a neutral wanderer NPC with atmospheric dialogue.

    Args:
        theme: World theme for flavor (e.g., "fantasy", "dark")

    Returns:
        NPC with lore/hints dialogue
    """
    wanderer_types = [
        {
            "name": "Weary Traveler",
            "description": "A tired soul resting briefly on the road",
            "dialogues": [
                "These roads grow darker by the day...",
                "I've seen things out here. Things I can't explain.",
                "Be careful, friend. Not all who wander are friendly.",
            ],
        },
        {
            "name": "Hooded Stranger",
            "description": "A mysterious figure who speaks in riddles",
            "dialogues": [
                "The shadows whisper of ancient powers...",
                "Seek not what lies beneath, lest it seek you.",
                "Some doors are best left unopened.",
            ],
        },
        {
            "name": "Lost Scholar",
            "description": "A disheveled academic muttering to themselves",
            "dialogues": [
                "The texts speak of a great calamity...",
                "If my research is correct, the signs are everywhere.",
                "Knowledge can be a burden, you know.",
            ],
        },
        {
            "name": "Wandering Hermit",
            "description": "An old hermit with knowing eyes",
            "dialogues": [
                "I've lived long enough to know when trouble brews.",
                "The land itself seems... uneasy.",
                "Trust your instincts out here, stranger.",
            ],
        },
    ]

    wanderer = random.choice(wanderer_types)
    dialogue = random.choice(wanderer["dialogues"])

    return NPC(
        name=wanderer["name"],
        description=wanderer["description"],
        dialogue=dialogue,
        greetings=wanderer["dialogues"],
    )


def check_for_random_encounter(game_state: "GameState") -> Optional[str]:
    """Check for and handle a random encounter during movement.

    This function should be called from GameState.move() after successful movement.
    It checks if an encounter triggers, then handles it appropriately:
    - Hostile: Starts combat
    - Merchant: Adds NPC to current location
    - Wanderer: Adds NPC to current location

    Args:
        game_state: The current game state

    Returns:
        Formatted encounter message if triggered, None otherwise
    """
    # Don't trigger if already in combat
    if game_state.is_in_combat():
        return None

    # Roll for encounter
    if random.random() > RANDOM_ENCOUNTER_CHANCE:
        return None

    # Select encounter type
    encounter_type = _select_encounter_type()
    location = game_state.get_current_location()

    if encounter_type == "hostile":
        return _handle_hostile_encounter(game_state)

    elif encounter_type == "merchant":
        return _handle_merchant_encounter(game_state)

    else:  # wanderer
        return _handle_wanderer_encounter(game_state)


def _handle_hostile_encounter(game_state: "GameState") -> str:
    """Handle a hostile random encounter.

    Args:
        game_state: The current game state

    Returns:
        Formatted encounter message
    """
    location = game_state.get_current_location()
    level = game_state.current_character.level

    # Spawn enemy using existing system
    enemy = spawn_enemy(
        location_name=location.name,
        level=level,
        location_category=location.category,
    )

    # Create combat encounter
    game_state.current_combat = CombatEncounter(game_state.current_character, enemies=[enemy])

    # Build message
    encounter = RandomEncounter(
        encounter_type="hostile",
        entity=enemy,
        description=f"A {enemy.name} ambushes you on the road!",
    )

    combat_start = game_state.current_combat.start()

    return format_encounter_message(encounter, combat_start)


def _handle_merchant_encounter(game_state: "GameState") -> str:
    """Handle a merchant random encounter.

    Args:
        game_state: The current game state

    Returns:
        Formatted encounter message
    """
    level = game_state.current_character.level
    merchant = spawn_wandering_merchant(level)

    # Add merchant to current location
    location = game_state.get_current_location()
    location.npcs.append(merchant)

    encounter = RandomEncounter(
        encounter_type="merchant",
        entity=merchant,
        description=f"A {merchant.name} blocks your path!",
    )

    return format_encounter_message(encounter)


def _handle_wanderer_encounter(game_state: "GameState") -> str:
    """Handle a wanderer random encounter.

    Args:
        game_state: The current game state

    Returns:
        Formatted encounter message
    """
    wanderer = spawn_wanderer(game_state.theme)

    # Add wanderer to current location
    location = game_state.get_current_location()
    location.npcs.append(wanderer)

    encounter = RandomEncounter(
        encounter_type="wanderer",
        entity=wanderer,
        description=f"You encounter a {wanderer.name} on the road.",
    )

    return format_encounter_message(encounter)


def format_encounter_message(
    encounter: RandomEncounter,
    additional_text: Optional[str] = None
) -> str:
    """Format a random encounter message for display.

    Args:
        encounter: The random encounter to format
        additional_text: Optional additional text (e.g., combat start message)

    Returns:
        Formatted encounter message with [Random Encounter!] marker
    """
    lines = [
        colors.warning("[Random Encounter!]"),
        encounter.description,
    ]

    if encounter.encounter_type == "hostile":
        # Combat will show its own details
        pass
    elif encounter.encounter_type == "merchant":
        npc = encounter.entity
        if isinstance(npc, NPC):
            lines.append(f'"{npc.dialogue}"')
            lines.append(f"(Use 'talk {npc.name}' to interact)")
    elif encounter.encounter_type == "wanderer":
        npc = encounter.entity
        if isinstance(npc, NPC):
            lines.append(f'"{npc.dialogue}"')
            lines.append(f"(Use 'talk {npc.name}' to interact)")

    if additional_text:
        lines.append(additional_text)

    return "\n".join(lines)
