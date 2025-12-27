"""Hallucination system for high dread levels (75%+).

At high dread, the player may encounter fake enemies that appear real
but dissipate when attacked. This adds psychological horror depth.
"""
import random
from typing import Optional, TYPE_CHECKING

from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter
from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState

HALLUCINATION_DREAD_THRESHOLD = 75
HALLUCINATION_CHANCE = 0.30
DREAD_REDUCTION_ON_DISPEL = 5

HALLUCINATION_TEMPLATES = [
    {
        "name": "Shadow Mimic",
        "description": "A shifting, indistinct form that flickers between shapes you almost recognize.",
        "attack_flavor": "lunges with shadowy claws",
    },
    {
        "name": "Phantom Shade",
        "description": "An ethereal apparition with hollow, staring eyes that seem to look through you.",
        "attack_flavor": "reaches toward you with spectral hands",
    },
    {
        "name": "Nightmare Echo",
        "description": "A creature born from your deepest fears, yet somehow hauntingly familiar.",
        "attack_flavor": "strikes with remembered terror",
    },
]

# Category-specific hallucination templates (Issue 22)
# Pattern follows encounter_tables.py (Issue 21)
CATEGORY_HALLUCINATION_TEMPLATES: dict[str, list[dict]] = {
    "dungeon": [
        {
            "name": "Ghostly Prisoner",
            "description": "A spectral figure bound in phantom chains, moaning of eternal torment.",
            "attack_flavor": "reaches through you with incorporeal hands",
        },
        {
            "name": "Skeletal Warrior",
            "description": "An animated skeleton in rusted armor, its eye sockets burning with cold fire.",
            "attack_flavor": "swings a corroded blade",
        },
    ],
    "forest": [
        {
            "name": "Twisted Treant",
            "description": "A gnarled tree creature with branches that writhe like grasping fingers.",
            "attack_flavor": "lashes with thorned limbs",
        },
        {
            "name": "Shadow Wolf",
            "description": "A wolf-shaped mass of darkness with eyes that gleam like dying embers.",
            "attack_flavor": "lunges with fangs of shadow",
        },
    ],
    "temple": [
        {
            "name": "Fallen Priest",
            "description": "A robed figure with a face of hollow despair, whispering blasphemous prayers.",
            "attack_flavor": "invokes corrupted blessings",
        },
        {
            "name": "Dark Angel",
            "description": "A winged being of terrible beauty, its halo cracked and bleeding shadow.",
            "attack_flavor": "strikes with wings of black flame",
        },
    ],
    "cave": [
        {
            "name": "Eyeless Horror",
            "description": "A pale, eyeless creature that navigates by sensing your heartbeat.",
            "attack_flavor": "claws blindly toward your chest",
        },
        {
            "name": "Dripping Shadow",
            "description": "A formless mass of darkness that drips like tar from the ceiling.",
            "attack_flavor": "engulfs you in suffocating darkness",
        },
    ],
}


def get_hallucination_templates(category: Optional[str]) -> list[dict]:
    """Get hallucination templates for a location category.

    Args:
        category: Location category (dungeon, forest, temple, cave) or None

    Returns:
        List of hallucination templates for the category, or defaults if unknown
    """
    if category is None:
        return HALLUCINATION_TEMPLATES
    return CATEGORY_HALLUCINATION_TEMPLATES.get(category, HALLUCINATION_TEMPLATES)

HALLUCINATION_ASCII_ART = r"""
   .~.~.
  ( ? ? )
   \~~~/
  /|   |\
 ~ |   | ~
   ~~~~~
"""


def spawn_hallucination(level: int, category: Optional[str] = None) -> Enemy:
    """Spawn a hallucination enemy.

    Args:
        level: Player level for stat scaling
        category: Location category for themed hallucinations (dungeon, forest, etc.)

    Returns:
        Enemy with is_hallucination=True
    """
    templates = get_hallucination_templates(category)
    template = random.choice(templates)

    return Enemy(
        name=template["name"],
        health=20 + level * 10,
        max_health=20 + level * 10,
        attack_power=3 + level * 2,
        defense=1 + level,
        xp_reward=0,  # No XP for hallucinations
        level=level,
        description=template["description"],
        attack_flavor=template["attack_flavor"],
        ascii_art=HALLUCINATION_ASCII_ART,
        is_hallucination=True,
    )


def check_for_hallucination(game_state: "GameState") -> Optional[str]:
    """Check for and trigger hallucination at high dread.

    Triggers with 30% chance when dread is 75-99%.
    Does not trigger at 100% (shadow creature priority) or if in combat.

    Args:
        game_state: Current game state

    Returns:
        Combat start message if hallucination triggered, None otherwise
    """
    dread = game_state.current_character.dread_meter.dread

    # Only trigger at 75-99% dread
    if dread < HALLUCINATION_DREAD_THRESHOLD or dread >= 100:
        return None

    # Don't trigger if already in combat
    if game_state.is_in_combat():
        return None

    # 30% chance to trigger
    if random.random() > HALLUCINATION_CHANCE:
        return None

    # Get location for category-themed hallucinations
    location = game_state.get_current_location()

    # Spawn hallucination using location category for themed templates
    hallucination = spawn_hallucination(
        game_state.current_character.level,
        category=location.category if location else None,
    )

    # Create combat encounter
    game_state.current_combat = CombatEncounter(
        game_state.current_character,
        enemies=[hallucination],
        companions=game_state.companions,
        location_category=location.category if location else None,
        game_state=game_state,
    )

    # Build eerie message
    intro_lines = [
        "",
        colors.warning("[Your mind plays tricks on you...]"),
        "",
    ]

    combat_start = game_state.current_combat.start()

    return "\n".join(intro_lines) + combat_start
