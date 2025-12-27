"""Environmental storytelling for dungeon/cave/ruins/temple interiors.

This module provides environmental storytelling elements (corpses, bloodstains,
journals) that appear in SubGrid location descriptions to add atmosphere and
hint at the dangers that lie ahead.
"""

import random
from typing import List


# Categories that receive environmental storytelling elements
STORYTELLING_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple"})

# Base chance (40%) for environmental details to appear
BASE_STORYTELLING_CHANCE = 0.40

# Environmental detail pools by category
# Each entry has 'type' (corpse/bloodstain/journal) and 'desc' (description text)
ENVIRONMENTAL_DETAILS: dict[str, list[dict[str, str]]] = {
    "dungeon": [
        # Corpses
        {"type": "corpse", "desc": "A skeleton slumps against the wall, rusted chains still binding its wrists."},
        {"type": "corpse", "desc": "The remains of an adventurer lie here, their sword still gripped in bony fingers."},
        {"type": "corpse", "desc": "A skeletal prisoner reaches toward the door, frozen in their final escape attempt."},
        {"type": "corpse", "desc": "Bones scattered across the floor tell of a violent end."},
        # Bloodstains
        {"type": "bloodstain", "desc": "Dark stains splatter across the floor, long since dried."},
        {"type": "bloodstain", "desc": "A trail of dried blood leads to a dark corner."},
        {"type": "bloodstain", "desc": "Rust-colored smears mark the walls at chest height."},
        # Journals
        {"type": "journal", "desc": "A torn page reads: 'The deeper we go, the worse the whispers get...'"},
        {"type": "journal", "desc": "Scratched into the stone: 'DON'T TRUST THE SHADOWS'"},
        {"type": "journal", "desc": "A faded note warns: 'The torch went out on level three. We're not alone.'"},
    ],
    "cave": [
        # Corpses
        {"type": "corpse", "desc": "A mauled hunter lies among scattered supplies, claw marks scoring the walls."},
        {"type": "corpse", "desc": "Bones bleached white by dripping mineral water rest in a shallow pool."},
        {"type": "corpse", "desc": "A trapped explorer's skeleton is wedged between rocks, their pack just out of reach."},
        # Bloodstains
        {"type": "bloodstain", "desc": "Dark stains on the cave floor suggest something was dragged deeper inside."},
        {"type": "bloodstain", "desc": "Splashes of old blood mark the crystal formations."},
        # Journals
        {"type": "journal", "desc": "Carved into the rock: 'TURN BACK - SOMETHING LIVES IN THE DEEP'"},
        {"type": "journal", "desc": "A tattered journal page mentions strange echoes that shouldn't exist."},
    ],
    "ruins": [
        # Corpses
        {"type": "corpse", "desc": "An ancient corpse lies preserved in the dry air, clutching a golden amulet."},
        {"type": "corpse", "desc": "Skeletal remains in ornate robes suggest this was once a person of importance."},
        {"type": "corpse", "desc": "A petrified figure stands frozen mid-stride, expression locked in terror."},
        # Bloodstains
        {"type": "bloodstain", "desc": "Faded rust-colored stains mar the ancient stonework."},
        {"type": "bloodstain", "desc": "The floor bears the marks of an ancient massacre."},
        # Journals
        {"type": "journal", "desc": "A stone tablet warns: 'THE SEAL MUST NEVER BE BROKEN'"},
        {"type": "journal", "desc": "Faded inscriptions describe a great cataclysm that ended this civilization."},
        {"type": "journal", "desc": "Carved glyphs tell of treasures guarded by things that do not sleep."},
    ],
    "temple": [
        # Corpses
        {"type": "corpse", "desc": "A sacrificial victim lies on the altar, ancient ceremonial wounds still visible."},
        {"type": "corpse", "desc": "A corrupted priest's remains are twisted into an unnatural pose."},
        {"type": "corpse", "desc": "Skeletal acolytes kneel before the defiled shrine, forever in prayer."},
        # Bloodstains
        {"type": "bloodstain", "desc": "Dried blood pools around the altar in ritualistic patterns."},
        {"type": "bloodstain", "desc": "Dark stains run down the temple steps like frozen tears."},
        # Journals
        {"type": "journal", "desc": "Profane scripture scrawled in blood covers the walls."},
        {"type": "journal", "desc": "A priest's final confession: 'We summoned something we cannot send back...'"},
        {"type": "journal", "desc": "Sacred texts have been defaced with blasphemous symbols."},
    ],
}


def get_environmental_details(category: str, distance: int = 0, z_level: int = 0) -> List[str]:
    """Generate 0-2 environmental storytelling elements for a location.

    Environmental details are category-specific atmospheric descriptions that
    hint at previous explorers' fates and dangers ahead. Chance increases with
    distance from entry and depth (z-level).

    Args:
        category: Location category (dungeon, cave, ruins, temple, etc.)
        distance: Manhattan distance from entry point (higher = more chance)
        z_level: Vertical level (negative = deeper underground, more chance)

    Returns:
        List of 0-2 environmental detail description strings.
        Returns empty list for non-storytelling categories.
    """
    # Only storytelling categories get environmental details
    if category not in STORYTELLING_CATEGORIES:
        return []

    # Get detail pool for this category
    details_pool = ENVIRONMENTAL_DETAILS.get(category)
    if not details_pool:
        return []

    # Calculate chance based on base + distance/depth scaling
    # Each unit of distance adds 5%, each unit of depth adds 8%
    depth = abs(z_level)  # z_level is negative for deeper levels
    chance = BASE_STORYTELLING_CHANCE + (distance * 0.05) + (depth * 0.08)
    chance = min(chance, 0.95)  # Cap at 95%

    # Roll for whether to add details
    if random.random() > chance:
        return []

    # Determine how many details (1-2)
    # Deeper/further = more likely to get 2
    if random.random() < 0.3 + (distance * 0.05) + (depth * 0.05):
        num_details = 2
    else:
        num_details = 1

    # Select random details from pool
    num_details = min(num_details, len(details_pool))
    selected = random.sample(details_pool, num_details)

    return [detail["desc"] for detail in selected]
