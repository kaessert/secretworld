"""Ranger class abilities: track command and wilderness bonuses.

Spec: Ranger class abilities to bring parity with other classes:
- `track` command: Rangers can detect enemies in adjacent locations
- Wilderness bonus: Rangers get +15% attack damage in wilderness/forest locations
"""

from typing import TYPE_CHECKING, Tuple, List
import random

from cli_rpg import colors
from cli_rpg.models.character import CharacterClass

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState

# Track command constants (Spec: costs 10 stamina, base 50% + 3% per PER)
TRACK_STAMINA_COST = 10
TRACK_BASE_CHANCE = 50
TRACK_PER_BONUS = 3

# Wilderness bonus constants (Spec: +15% damage in forest/wilderness)
WILDERNESS_DAMAGE_BONUS = 0.15
WILDERNESS_CATEGORIES = {"forest", "wilderness"}


def _get_location_enemies(
    game_state: "GameState",
) -> List[Tuple[str, List[Tuple[str, int]]]]:
    """Get enemies in adjacent locations (simulated based on location category).

    In a real implementation, this would check actual spawned enemies.
    For tracking purposes, we simulate potential threats based on location type.

    Args:
        game_state: Current game state

    Returns:
        List of (location_name, [(enemy_type, count), ...]) tuples
    """
    current_location = game_state.get_current_location()
    results = []

    # Check each connected location
    for direction in current_location.get_available_directions():
        connected_name = current_location.get_connection(direction)
        if connected_name and connected_name in game_state.world:
            connected_loc = game_state.world[connected_name]

            # Determine potential enemies based on category
            category = connected_loc.category or "default"
            enemies = _get_enemies_for_category(category)

            if enemies:
                results.append((connected_name, enemies))

    return results


def _get_enemies_for_category(category: str) -> List[Tuple[str, int]]:
    """Get potential enemies for a location category.

    Args:
        category: Location category

    Returns:
        List of (enemy_type, count) tuples
    """
    enemy_mapping = {
        "forest": [("Wolf", random.randint(1, 2)), ("Bear", random.randint(0, 1))],
        "wilderness": [("Wild Boar", random.randint(1, 2))],
        "cave": [("Goblin", random.randint(1, 3)), ("Bat", random.randint(2, 4))],
        "dungeon": [("Skeleton", random.randint(1, 2)), ("Zombie", random.randint(0, 1))],
        "mountain": [("Eagle", random.randint(1, 2)), ("Mountain Lion", random.randint(0, 1))],
    }

    enemies = enemy_mapping.get(category, [])
    # Filter out zero counts
    return [(name, count) for name, count in enemies if count > 0]


def execute_track(game_state: "GameState") -> Tuple[bool, str]:
    """Execute the track command for Rangers.

    Rangers can detect enemies in adjacent locations.
    - Costs 10 stamina
    - Success: base 50% + 3% per PER
    - Returns enemy types/counts in connected locations
    - Cannot be used during combat

    Args:
        game_state: Current game state

    Returns:
        Tuple of (success, message)
    """
    player = game_state.current_character

    # Check if player is a Ranger (Spec: Only Rangers can track)
    if player.character_class != CharacterClass.RANGER:
        return (False, "Only Rangers can track!")

    # Check if in combat (Spec: Can only be used outside combat)
    if game_state.is_in_combat():
        return (False, "You can't track while in combat!")

    # Check stamina (Spec: Costs 10 stamina)
    if player.stamina < TRACK_STAMINA_COST:
        return (
            False,
            f"Not enough stamina to track! ({player.stamina}/{player.max_stamina})",
        )

    # Consume stamina
    player.use_stamina(TRACK_STAMINA_COST)

    # Calculate success chance (Spec: base 50% + 3% per PER)
    # Add +15% bonus from animal companion if present
    from cli_rpg.ranger_companion import get_track_companion_bonus
    companion_bonus = get_track_companion_bonus(game_state)
    success_chance = min(
        100, TRACK_BASE_CHANCE + (player.perception * TRACK_PER_BONUS) + companion_bonus
    )
    roll = random.random() * 100

    if roll > success_chance:
        return (
            True,
            "You crouch down and study the tracks... but the trail is too cold to follow.",
        )

    # Success! Get enemies in adjacent locations
    enemy_data = _get_location_enemies(game_state)

    if not enemy_data:
        return (
            True,
            "You crouch down and study the tracks... "
            f"{colors.heal('No enemies detected nearby.')} The area seems safe.",
        )

    # Format the tracking results
    lines = ["You crouch down and study the tracks..."]
    for location_name, enemies in enemy_data:
        enemy_strs = [f"{count} {name}" for name, count in enemies]
        lines.append(
            f"  {colors.location(location_name)}: {', '.join(enemy_strs)} detected"
        )

    return (True, "\n".join(lines))


def calculate_wilderness_bonus(
    character_class: CharacterClass,
    location_category: str,
) -> float:
    """Calculate wilderness damage bonus for Rangers.

    Args:
        character_class: The character's class
        location_category: The location's category

    Returns:
        Damage multiplier (1.0 for no bonus, 1.15 for wilderness bonus)
    """
    if character_class != CharacterClass.RANGER:
        return 1.0

    if location_category and location_category.lower() in WILDERNESS_CATEGORIES:
        return 1.0 + WILDERNESS_DAMAGE_BONUS

    return 1.0
