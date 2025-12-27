"""Environmental hazards system for dungeon interiors (Issue #26).

This module provides non-combat environmental challenges:
- Poison Gas: DOT damage per move, mitigated by antidotes
- Darkness: Reduces perception by 50%, requires active light
- Unstable Ground: DEX check or take fall damage (5-15 HP)
- Extreme Cold/Heat: +5 tiredness per move in hazard room
- Flooded Rooms: 50% chance to fail movement (slowed)

Hazards are assigned during SubGrid room generation based on location category.
"""

import random
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from cli_rpg.models.character import Character
    from cli_rpg.models.location import Location
    from cli_rpg.game_state import GameState

# All valid hazard types
HAZARD_TYPES = {
    "poison_gas",
    "darkness",
    "unstable_ground",
    "extreme_cold",
    "extreme_heat",
    "flooded",
}

# Category-specific hazard pools
CATEGORY_HAZARDS = {
    "dungeon": ["poison_gas", "darkness", "unstable_ground"],
    "cave": ["darkness", "flooded", "extreme_cold"],
    "ruins": ["unstable_ground", "darkness"],
    "temple": ["poison_gas", "darkness"],
}

# Hazards that Ranger class can mitigate (wilderness affinity)
RANGER_MITIGATED_HAZARDS = {"unstable_ground", "extreme_cold", "extreme_heat"}

# Poison gas damage range
POISON_GAS_MIN_DAMAGE = 3
POISON_GAS_MAX_DAMAGE = 6

# Unstable ground fall damage range
FALL_DAMAGE_MIN = 5
FALL_DAMAGE_MAX = 15

# Temperature hazard tiredness increase
TEMPERATURE_TIREDNESS = 5


def apply_poison_gas(character: "Character") -> str:
    """Apply poison gas damage to character.

    Deals 3-6 damage per move in poisonous area.

    Args:
        character: The player character

    Returns:
        Message describing the effect
    """
    damage = random.randint(POISON_GAS_MIN_DAMAGE, POISON_GAS_MAX_DAMAGE)
    character.take_damage(damage)
    return f"The poison gas burns your lungs! You take {damage} damage."


def check_darkness_penalty(character: "Character") -> float:
    """Calculate perception penalty from darkness.

    Args:
        character: The player character

    Returns:
        Perception multiplier (0.5 if dark, 1.0 if lit)
    """
    if character.light_remaining > 0:
        return 1.0  # No penalty with active light
    return 0.5  # 50% perception penalty in darkness


def check_unstable_ground(character: "Character") -> Tuple[bool, int]:
    """Check if character falls on unstable ground.

    Uses DEX check: d20 + DEX modifier vs DC 12.
    Higher DEX = less likely to fall.

    Args:
        character: The player character

    Returns:
        Tuple of (fell: bool, damage: int)
    """
    # DEX modifier is (DEX - 10) // 2 (D&D-style)
    dex_modifier = (character.dexterity - 10) // 2
    roll = random.randint(1, 20) + dex_modifier
    dc = 12  # Difficulty check

    if roll >= dc:
        return (False, 0)  # Passed check, no fall

    # Failed check - take fall damage
    damage = random.randint(FALL_DAMAGE_MIN, FALL_DAMAGE_MAX)
    return (True, damage)


def apply_temperature_effect(character: "Character", hazard_type: str) -> str:
    """Apply temperature hazard effect.

    Increases tiredness by 5.

    Args:
        character: The player character
        hazard_type: "extreme_cold" or "extreme_heat"

    Returns:
        Message describing the effect
    """
    character.tiredness.increase(TEMPERATURE_TIREDNESS)

    if hazard_type == "extreme_cold":
        return "The extreme cold saps your energy! Tiredness +5."
    else:  # extreme_heat
        return "The extreme heat is exhausting! Tiredness +5."


def check_flooded_movement(character: "Character") -> bool:
    """Check if movement fails in flooded room.

    50% chance to fail movement (slowed by water).

    Args:
        character: The player character

    Returns:
        True if movement fails, False if successful
    """
    return random.random() < 0.5


def can_mitigate_hazard(character: "Character", hazard_type: str) -> bool:
    """Check if character can mitigate a specific hazard.

    Mitigation rules:
    - Ranger: Ignores unstable_ground, extreme_cold, extreme_heat
    - Light source: Negates darkness penalty
    - Flooded: No mitigation available
    - Poison gas: No class-based mitigation (requires antidote item use)

    Args:
        character: The player character
        hazard_type: Type of hazard to check

    Returns:
        True if hazard can be mitigated, False otherwise
    """
    from cli_rpg.models.character import CharacterClass

    # Ranger mitigates wilderness hazards
    if (
        character.character_class == CharacterClass.RANGER
        and hazard_type in RANGER_MITIGATED_HAZARDS
    ):
        return True

    # Light source mitigates darkness
    if hazard_type == "darkness" and character.light_remaining > 0:
        return True

    # Flooded and poison_gas have no class-based mitigation
    return False


def get_hazards_for_category(category: str, distance: int = 0) -> List[str]:
    """Get random hazards appropriate for a location category.

    Hazard chance increases with distance from entry:
    - Distance 0-1: 10% chance for 1 hazard
    - Distance 2-3: 25% chance for 1 hazard, 10% for 2
    - Distance 4+: 40% chance for 1 hazard, 20% for 2

    Args:
        category: Location category (dungeon, cave, etc.)
        distance: Manhattan distance from entry point

    Returns:
        List of hazard type strings (0-2 hazards)
    """
    if category not in CATEGORY_HAZARDS:
        return []

    pool = CATEGORY_HAZARDS[category]
    hazards = []

    # Calculate chance based on distance
    if distance <= 1:
        single_chance = 0.10
        double_chance = 0.0
    elif distance <= 3:
        single_chance = 0.25
        double_chance = 0.10
    else:
        single_chance = 0.40
        double_chance = 0.20

    roll = random.random()
    if roll < double_chance:
        # Two hazards
        hazards = random.sample(pool, min(2, len(pool)))
    elif roll < single_chance + double_chance:
        # One hazard
        hazards = [random.choice(pool)]

    return hazards


def check_hazards_on_entry(
    game_state: "GameState", location: "Location"
) -> List[str]:
    """Process all hazards when entering a location.

    Applies effects for each hazard, checking for mitigation first.

    Args:
        game_state: Current game state
        location: Location being entered

    Returns:
        List of messages describing hazard effects
    """
    if not location.hazards:
        return []

    messages = []
    character = game_state.current_character

    for hazard in location.hazards:
        # Check for mitigation
        if can_mitigate_hazard(character, hazard):
            # Add mitigation message based on hazard type
            if hazard in RANGER_MITIGATED_HAZARDS:
                messages.append(
                    f"Your Ranger skills help you avoid the {hazard.replace('_', ' ')}."
                )
            elif hazard == "darkness":
                messages.append("Your light source illuminates the darkness.")
            continue  # Skip effect application

        # Apply hazard effect
        if hazard == "poison_gas":
            msg = apply_poison_gas(character)
            messages.append(msg)

        elif hazard == "darkness":
            penalty = check_darkness_penalty(character)
            if penalty < 1.0:
                messages.append(
                    "The darkness here is oppressive. Your perception is reduced."
                )

        elif hazard == "unstable_ground":
            fell, damage = check_unstable_ground(character)
            if fell:
                character.take_damage(damage)
                messages.append(
                    f"The ground crumbles beneath you! You fall and take {damage} damage."
                )
            else:
                messages.append("You carefully navigate the unstable ground.")

        elif hazard in ("extreme_cold", "extreme_heat"):
            msg = apply_temperature_effect(character, hazard)
            messages.append(msg)

        elif hazard == "flooded":
            # Flooded effect is handled at movement time, not entry
            # Just add flavor message here
            messages.append("The room is partially flooded. Movement may be slowed.")

    return messages
