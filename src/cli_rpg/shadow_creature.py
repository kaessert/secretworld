"""Shadow creature attack system for 100% dread.

When dread reaches 100%, a Shadow of Dread manifests - a terrifying
creature born from the player's accumulated fears. This provides the
gameplay consequence documented in models/dread.py for critical dread.
"""
from typing import Optional, TYPE_CHECKING

from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter
from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState

# Shadow creature constants
SHADOW_CREATURE_NAME = "Shadow of Dread"
SHADOW_CREATURE_DESCRIPTION = (
    "A writhing mass of darkness that has coalesced from your deepest fears. "
    "Its form shifts constantly, never quite solid, yet terrifyingly real."
)
SHADOW_ATTACK_FLAVOR = "lashes out with tendrils of pure terror"
SHADOW_VICTORY_DREAD_REDUCTION = 50  # Dread reduced to this value on victory

SHADOW_ASCII_ART = r"""
    .-.-.
   ( o o )
  /|  ~  |\
 / |     | \
(  |~~~~~|  )
 \ |     | /
  \|_____|/
   ~~~|~~~
"""


def spawn_shadow_creature(level: int) -> Enemy:
    """Spawn a shadow creature scaled to player level.

    Shadow creatures have:
    - Health: 30 + level * 15
    - Attack: 5 + level * 2
    - Defense: 2 + level (lower than normal - it's ethereal)
    - XP: 25 + level * 15 (rewarding for facing your fears)

    Args:
        level: Player level for scaling

    Returns:
        Enemy instance representing the shadow creature
    """
    return Enemy(
        name=SHADOW_CREATURE_NAME,
        health=30 + level * 15,
        max_health=30 + level * 15,
        attack_power=5 + level * 2,
        defense=2 + level,
        xp_reward=25 + level * 15,
        level=level,
        description=SHADOW_CREATURE_DESCRIPTION,
        attack_flavor=SHADOW_ATTACK_FLAVOR,
        ascii_art=SHADOW_ASCII_ART,
        is_boss=False,
    )


def check_and_trigger_shadow_attack(game_state: "GameState") -> Optional[str]:
    """Check for and trigger shadow creature attack at 100% dread.

    This should be called after dread is updated on movement.
    Does not trigger if already in combat.

    Args:
        game_state: The current game state

    Returns:
        Combat message if shadow attack triggered, None otherwise
    """
    # Don't trigger if not at critical dread
    if not game_state.current_character.dread_meter.is_critical():
        return None

    # Don't trigger if already in combat
    if game_state.is_in_combat():
        return None

    # Spawn shadow creature
    shadow = spawn_shadow_creature(game_state.current_character.level)

    # Create combat encounter
    game_state.current_combat = CombatEncounter(
        game_state.current_character,
        enemies=[shadow],
        companions=game_state.companions,
    )

    # Build dramatic message
    intro_lines = [
        "",
        colors.damage("=" * 50),
        colors.damage("  THE DARKNESS TAKES FORM"),
        colors.damage("=" * 50),
        "",
        "Your dread has reached its peak. The shadows around you",
        "coalesce into a terrifying manifestation of your fears.",
        "",
    ]

    combat_start = game_state.current_combat.start()

    return "\n".join(intro_lines) + "\n" + combat_start
