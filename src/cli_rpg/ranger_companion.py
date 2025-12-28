"""Ranger animal companion command functions.

Spec: Rangers can have animal companions with combat and utility bonuses.

Commands:
- `companion` - View companion status
- `summon` - Call companion if dismissed (costs 10 stamina)
- `dismiss` - Send companion away temporarily
- `feed <item>` - Feed companion to heal and increase bond
- `tame <animal>` - Tame a wild animal (one-time)
"""

from typing import TYPE_CHECKING, Tuple, Optional

from cli_rpg import colors
from cli_rpg.models.animal_companion import AnimalCompanion, AnimalType
from cli_rpg.models.character import CharacterClass
from cli_rpg.models.item import ItemType

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


# Summon stamina cost (Spec: costs 10 stamina)
SUMMON_STAMINA_COST = 10

# Feed healing amount per consumable
FEED_HEAL_AMOUNT = 15

# Feed bond increase per consumable
FEED_BOND_AMOUNT = 5

# Track bonus with animal companion present (Spec: +15%)
TRACK_COMPANION_BONUS = 15


def execute_companion_status(game_state: "GameState") -> str:
    """Display the Ranger's animal companion status.

    Args:
        game_state: Current game state

    Returns:
        Formatted string with companion status, or error message
    """
    player = game_state.current_character

    # Check if player is a Ranger
    if player.character_class != CharacterClass.RANGER:
        return "Only Rangers can have animal companions."

    # Check if player has a companion
    if player.animal_companion is None:
        return (
            "You don't have an animal companion yet.\n"
            "Use 'tame' when you encounter a wild animal to befriend one."
        )

    return player.animal_companion.get_status_display()


def execute_summon(game_state: "GameState") -> Tuple[bool, str]:
    """Summon a dismissed animal companion.

    Costs 10 stamina to summon.

    Args:
        game_state: Current game state

    Returns:
        Tuple of (success, message)
    """
    player = game_state.current_character

    # Check if player is a Ranger
    if player.character_class != CharacterClass.RANGER:
        return (False, "Only Rangers can summon animal companions.")

    # Check if player has a companion
    if player.animal_companion is None:
        return (False, "You don't have an animal companion to summon.")

    # Check if already present
    if player.animal_companion.is_present:
        return (False, f"{player.animal_companion.name} is already at your side.")

    # Check stamina
    if player.stamina < SUMMON_STAMINA_COST:
        return (
            False,
            f"Not enough stamina to summon your companion! "
            f"({player.stamina}/{player.max_stamina})",
        )

    # Summon the companion
    player.use_stamina(SUMMON_STAMINA_COST)
    player.animal_companion.summon()

    companion = player.animal_companion
    return (
        True,
        f"You whistle and {colors.npc(companion.name)} the {companion.animal_type.value} "
        f"comes bounding to your side!",
    )


def execute_dismiss(game_state: "GameState") -> Tuple[bool, str]:
    """Dismiss the animal companion temporarily.

    Args:
        game_state: Current game state

    Returns:
        Tuple of (success, message)
    """
    player = game_state.current_character

    # Check if player is a Ranger
    if player.character_class != CharacterClass.RANGER:
        return (False, "Only Rangers have animal companions to dismiss.")

    # Check if player has a companion
    if player.animal_companion is None:
        return (False, "You don't have an animal companion to dismiss.")

    # Check if already dismissed
    if not player.animal_companion.is_present:
        return (
            False,
            f"{player.animal_companion.name} is already away. Use 'summon' to call them back.",
        )

    # Dismiss the companion
    player.animal_companion.dismiss()

    companion = player.animal_companion
    return (
        True,
        f"You signal {colors.npc(companion.name)} to go. "
        f"The {companion.animal_type.value} trots off into the wilderness, "
        f"ready to return when called.",
    )


def execute_feed(game_state: "GameState", item_name: str) -> Tuple[bool, str]:
    """Feed the animal companion a consumable item.

    Feeding heals the companion and increases bond.

    Args:
        game_state: Current game state
        item_name: Name of the item to feed

    Returns:
        Tuple of (success, message)
    """
    player = game_state.current_character

    # Check if player is a Ranger
    if player.character_class != CharacterClass.RANGER:
        return (False, "Only Rangers have animal companions to feed.")

    # Check if player has a companion
    if player.animal_companion is None:
        return (False, "You don't have an animal companion to feed.")

    companion = player.animal_companion

    # Check if companion is present
    if not companion.is_present:
        return (
            False,
            f"{companion.name} is not here. Summon them first to feed them.",
        )

    # Find the item in inventory (case-insensitive)
    item = None
    item_name_lower = item_name.lower()
    for inv_item in player.inventory.items:
        if inv_item.name.lower() == item_name_lower:
            item = inv_item
            break

    if item is None:
        return (False, f"You don't have '{item_name}' in your inventory.")

    # Check if item is consumable
    if item.item_type != ItemType.CONSUMABLE:
        return (False, f"You can only feed consumable items to {companion.name}.")

    # Remove item and feed companion
    player.inventory.remove_item(item)

    # Heal the companion
    healed = companion.heal(FEED_HEAL_AMOUNT)

    # Increase bond
    bond_message = companion.add_bond(FEED_BOND_AMOUNT)

    messages = [
        f"You feed {colors.item(item.name)} to {colors.npc(companion.name)}.",
    ]

    if healed > 0:
        messages.append(f"{companion.name} heals {colors.heal(str(healed))} health!")

    messages.append(f"Bond increased by {FEED_BOND_AMOUNT}.")

    if bond_message:
        messages.append(colors.heal(bond_message))

    return (True, " ".join(messages))


def execute_tame(game_state: "GameState", animal_name: str) -> Tuple[bool, str]:
    """Tame a wild animal to become the Ranger's companion.

    Can only be done once - Rangers have a single animal companion.

    Args:
        game_state: Current game state
        animal_name: Name/type of the animal to tame

    Returns:
        Tuple of (success, message)
    """
    player = game_state.current_character

    # Check if player is a Ranger
    if player.character_class != CharacterClass.RANGER:
        return (False, "Only Rangers can tame animal companions.")

    # Check if player already has a companion
    if player.animal_companion is not None:
        return (
            False,
            f"You already have {player.animal_companion.name} as your companion. "
            f"Rangers bond with a single animal for life.",
        )

    # Check for valid animal type
    animal_name_lower = animal_name.lower()
    animal_type: Optional[AnimalType] = None

    for at in AnimalType:
        if at.value.lower() == animal_name_lower:
            animal_type = at
            break

    if animal_type is None:
        available = ", ".join([at.value for at in AnimalType])
        return (
            False,
            f"You can't tame a '{animal_name}'. Available animal types: {available}",
        )

    # Check if there's a compatible animal in the current location
    # For now, we'll be lenient and allow taming anywhere (could be enhanced later)
    location = game_state.get_current_location()

    # Create the companion
    # Generate a default name based on animal type
    default_names = {
        AnimalType.WOLF: "Fang",
        AnimalType.HAWK: "Talon",
        AnimalType.BEAR: "Brutus",
    }
    companion_name = default_names.get(animal_type, animal_type.value)

    companion = AnimalCompanion.create(companion_name, animal_type)
    player.animal_companion = companion

    # Get type-specific bonuses for display
    bonuses = []
    flank_pct = int(companion.get_flank_bonus() * 100)
    bonuses.append(f"+{flank_pct}% flank damage")

    per_bonus = companion.get_perception_bonus()
    if per_bonus > 0:
        bonuses.append(f"+{per_bonus} PER for tracking/secrets")

    if animal_type == AnimalType.BEAR:
        bonuses.append("2x health (can tank hits)")

    bonus_str = ", ".join(bonuses)

    return (
        True,
        f"You approach the wild {animal_type.value} slowly, hand outstretched...\n"
        f"After a tense moment, it accepts you as its companion!\n\n"
        f"{colors.npc(companion_name)} the {animal_type.value} has joined you!\n"
        f"Bonuses: {bonus_str}",
    )


def get_companion_flank_bonus(game_state: "GameState") -> float:
    """Get the animal companion's flank bonus for combat.

    Args:
        game_state: Current game state

    Returns:
        Flank bonus as a decimal (0.0 to 0.15), or 0.0 if no companion/not present
    """
    player = game_state.current_character

    if player.character_class != CharacterClass.RANGER:
        return 0.0

    if player.animal_companion is None:
        return 0.0

    return player.animal_companion.get_flank_bonus()


def get_companion_perception_bonus(game_state: "GameState") -> int:
    """Get the animal companion's perception bonus.

    Args:
        game_state: Current game state

    Returns:
        PER bonus (0 to 3), or 0 if no companion/not present
    """
    player = game_state.current_character

    if player.character_class != CharacterClass.RANGER:
        return 0

    if player.animal_companion is None:
        return 0

    return player.animal_companion.get_perception_bonus()


def companion_attack(
    game_state: "GameState",
    enemy_defense: int,
) -> Tuple[int, str]:
    """Execute the animal companion's attack.

    Companion deals 50% of Ranger's base strength minus enemy defense.

    Args:
        game_state: Current game state
        enemy_defense: The target enemy's defense value

    Returns:
        Tuple of (damage dealt, message describing the attack)
    """
    player = game_state.current_character

    if player.character_class != CharacterClass.RANGER:
        return (0, "")

    if player.animal_companion is None:
        return (0, "")

    companion = player.animal_companion

    if not companion.is_present or not companion.is_alive():
        return (0, "")

    # Calculate companion damage (50% of strength, minus enemy defense, min 1)
    base_damage = companion.get_attack_damage(player.strength)
    damage = max(1, base_damage - enemy_defense)

    # Type-specific attack descriptions
    attack_verbs = {
        AnimalType.WOLF: "lunges and bites",
        AnimalType.HAWK: "swoops down and claws",
        AnimalType.BEAR: "swipes with massive paws at",
    }
    attack_verb = attack_verbs.get(companion.animal_type, "attacks")

    message = (
        f"{colors.npc(companion.name)} {attack_verb} the enemy "
        f"for {colors.damage(str(damage))} damage!"
    )

    return (damage, message)


def get_track_companion_bonus(game_state: "GameState") -> int:
    """Get tracking bonus from animal companion.

    Args:
        game_state: Current game state

    Returns:
        Track success bonus percentage (0 or 15)
    """
    player = game_state.current_character

    if player.character_class != CharacterClass.RANGER:
        return 0

    if player.animal_companion is None:
        return 0

    if not player.animal_companion.is_present:
        return 0

    return TRACK_COMPANION_BONUS
