"""Combat encounter system for CLI RPG."""

import logging
import random
from typing import Optional, Tuple, Union, TYPE_CHECKING
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.status_effect import StatusEffect
from cli_rpg.models.weather import Weather
from cli_rpg.models.companion import Companion
from cli_rpg import colors
from cli_rpg.sound_effects import sound_victory

if TYPE_CHECKING:
    from cli_rpg.ai_service import AIService

logger = logging.getLogger(__name__)

# Combo definitions: maps combo name to sequence pattern
COMBOS = {
    "frenzy": {"sequence": ["attack", "attack", "attack"], "trigger": "attack"},
    "revenge": {"sequence": ["defend", "defend", "attack"], "trigger": "attack"},
    "arcane_burst": {"sequence": ["cast", "cast", "cast"], "trigger": "cast"},
}

# Faster delay for combat (action-paced)
COMBAT_TYPEWRITER_DELAY = 0.025


def display_combat_start(intro_text: str) -> None:
    """Display combat start with typewriter effect.

    Args:
        intro_text: The combat intro text to display with typewriter effect.
    """
    from cli_rpg.text_effects import typewriter_print, pause_short
    typewriter_print(intro_text, delay=COMBAT_TYPEWRITER_DELAY)
    pause_short()  # Brief pause after combat intro


def display_combo(combo_text: str) -> None:
    """Display combo announcement with typewriter effect.

    Args:
        combo_text: The combo announcement text to display with typewriter effect.
    """
    from cli_rpg.text_effects import typewriter_print, pause_medium
    typewriter_print(combo_text, delay=COMBAT_TYPEWRITER_DELAY)
    pause_medium()  # Moderate pause after combo announcement


def display_combat_end(result_text: str) -> None:
    """Display combat end with typewriter effect.

    Handles multiline result text by printing each line with typewriter effect.

    Args:
        result_text: The combat result text to display with typewriter effect.
    """
    from cli_rpg.text_effects import typewriter_print, pause_long
    for line in result_text.split("\n"):
        typewriter_print(line, delay=COMBAT_TYPEWRITER_DELAY)
    pause_long()  # Long pause after combat resolution


def calculate_distance_from_origin(coordinates: Optional[Tuple[int, int]]) -> int:
    """Calculate Manhattan distance from origin (0,0).

    Args:
        coordinates: (x, y) coordinate tuple, or None

    Returns:
        Manhattan distance (|x| + |y|), or 0 if coordinates is None
    """
    if coordinates is None:
        return 0
    return abs(coordinates[0]) + abs(coordinates[1])


def get_distance_multiplier(distance: int) -> float:
    """Get stat scaling multiplier based on distance from origin.

    Formula: 1.0 + distance * 0.15

    Distance tiers (for reference):
    - Near (0-3): Easy (multiplier 1.0-1.45)
    - Mid (4-7): Moderate (multiplier 1.6-2.05)
    - Far (8-12): Challenging (multiplier 2.2-2.8)
    - Deep (13+): Dangerous (multiplier 2.95+)

    Args:
        distance: Manhattan distance from origin

    Returns:
        Stat multiplier (1.0 or higher)
    """
    return 1.0 + distance * 0.15


def calculate_crit_chance(stat: int, luck: int = 10) -> float:
    """Calculate critical hit chance based on a stat (DEX or INT) and luck.

    Formula: 5% base + 1% per stat point + 0.5% per luck above/below 10, capped at 25%.

    Args:
        stat: The stat value (dexterity for attacks, intelligence for cast)
        luck: The luck stat value (default 10 for backward compatibility)

    Returns:
        Critical hit chance as a decimal (varies based on stat and luck)
    """
    base_chance = 5 + stat
    luck_bonus = (luck - 10) * 0.5
    return min(base_chance + luck_bonus, 25) / 100.0


def calculate_dodge_chance(dexterity: int) -> float:
    """Calculate dodge chance based on dexterity.

    Formula: 5% base + 0.5% per DEX point (integer division), capped at 15%.

    Args:
        dexterity: Player dexterity stat

    Returns:
        Dodge chance as a decimal (0.05 to 0.15)
    """
    return min(5 + dexterity // 2, 15) / 100.0


ENEMY_CRIT_CHANCE = 0.05  # Flat 5% crit chance for enemies
CRIT_MULTIPLIER = 1.5


def strip_leading_name(enemy_name: str, attack_flavor: str) -> str:
    """Strip enemy name from start of attack flavor text if present.

    Handles cases like "The Frostbite Yeti unleashes..." → "unleashes..."

    Args:
        enemy_name: The name of the enemy
        attack_flavor: The attack flavor text that may start with the enemy name

    Returns:
        The attack flavor with leading enemy name stripped
    """
    flavor_lower = attack_flavor.lower()
    name_lower = enemy_name.lower()

    # Check for "The Enemy Name" pattern
    if flavor_lower.startswith(f"the {name_lower}"):
        return attack_flavor[len(f"the {name_lower}"):].lstrip()

    # Check for "Enemy Name" pattern
    if flavor_lower.startswith(name_lower):
        return attack_flavor[len(name_lower):].lstrip()

    return attack_flavor


# Fallback ASCII art templates for different enemy categories
_ASCII_ART_BEAST = r"""
    /\_/\
   ( o.o )
    > ^ <
   /|   |\
  (_|   |_)
"""

_ASCII_ART_UNDEAD = r"""
     .-.
    (o o)
    | O |
   /|   |\
  / |   | \
"""

_ASCII_ART_HUMANOID = r"""
     O
    /|\
    / \
   /   \
  |     |
"""

_ASCII_ART_CREEPY = r"""
   /\ /\
  (  V  )
  /|   |\
 / |   | \
(___|___|_)
"""

_ASCII_ART_DEFAULT = r"""
   .---.
  ( o o )
   \ = /
   /| |\
  / | | \
"""

# Boss-specific ASCII art templates (larger and more detailed)
_ASCII_ART_BOSS_DEMON = r"""
      /\  /\
     (  \/  )
    /|  ><  |\
   / | /||\ | \
  /  |/ || \|  \
 /   ||    ||   \
(____||    ||____)
     |________|
"""

_ASCII_ART_BOSS_UNDEAD = r"""
     .-~~~-.
    (  @  @ )
     \  <  /
   __|`---'|__
  /   |----|   \
 /  / |    | \  \
|__/  |    |  \__|
      |    |
     /|    |\
    / |____| \
"""

_ASCII_ART_BOSS_GUARDIAN = r"""
    _________
   |  ___  |
   | |   | |
   | | O | |
   | |___| |
   |_________|
   /|       |\
  / |  |||  | \
 /  |__|||__|  \
"""

_ASCII_ART_BOSS_STONE_SENTINEL = r"""
     ___________
    /  _____   \
   |  |     |  |
   |  | O O |  |
   |  |_____|  |
   |    ___    |
   |   |   |   |
  /|   |   |   |\
 / |===|   |===| \
"""

_ASCII_ART_BOSS_TREANT = r"""
     /\  ||  /\
    /  \ || /  \
   /    \||/    \
  |  O   ||   O  |
  |______||______|
      |  ||  |
     /|  ||  |\
    / |__||__| \
"""

_ASCII_ART_BOSS_DROWNED_OVERSEER = r"""
     .-~~~-.
    ( ~   ~ )
    /|  <>  |\
   / | ~~~~ | \
  |  | |==| |  |
  |  | |  | |  |
  /__| |__| |__\
"""


def get_fallback_ascii_art(enemy_name: str) -> str:
    """Get fallback ASCII art based on enemy name.

    Matches enemy name against categories and returns appropriate art.

    Args:
        enemy_name: Name of the enemy

    Returns:
        ASCII art string (5-7 lines, max 40 chars wide)
    """
    name_lower = enemy_name.lower()

    # Beast category: wolf, bear, boar, lion, etc.
    if any(term in name_lower for term in ["wolf", "bear", "boar", "lion", "cat", "dog"]):
        return _ASCII_ART_BEAST

    # Undead category: skeleton, zombie, ghost, wraith, etc.
    if any(term in name_lower for term in ["skeleton", "zombie", "ghost", "wraith", "undead"]):
        return _ASCII_ART_UNDEAD

    # Humanoid category: goblin, bandit, thief, orc, troll, etc.
    if any(term in name_lower for term in ["goblin", "bandit", "thief", "orc", "troll", "knight"]):
        return _ASCII_ART_HUMANOID

    # Creepy category: spider, bat, insect, etc.
    if any(term in name_lower for term in ["spider", "bat", "insect", "scorpion"]):
        return _ASCII_ART_CREEPY

    # Default for unknown types
    return _ASCII_ART_DEFAULT


class CombatEncounter:
    """Manages a combat encounter between player and one or more enemies."""

    def __init__(
        self,
        player: Character,
        enemies: Optional[Union[list[Enemy], Enemy]] = None,
        enemy: Optional[Enemy] = None,
        weather: Optional[Weather] = None,
        companions: Optional[list[Companion]] = None
    ):
        """
        Initialize combat encounter.

        Args:
            player: Player character
            enemies: List of enemies to fight (or single Enemy for backward compat)
            enemy: Single enemy to fight (backward compatibility keyword arg)
            weather: Optional weather for weather-combat interactions
            companions: Optional list of companions providing combat bonuses

        Note: Either enemies or enemy must be provided. If both are provided,
        enemies takes precedence. If enemy is provided, it's wrapped in a list.
        Backward compatibility: CombatEncounter(player, enemy) works as before.
        """
        self.player = player
        self.weather = weather
        self.companions = companions or []

        # Handle backward compatibility
        if enemies is not None:
            # Check if enemies is a single Enemy (legacy positional arg)
            if isinstance(enemies, Enemy):
                self.enemies = [enemies]
            else:
                self.enemies = enemies
        elif enemy is not None:
            self.enemies = [enemy]
        else:
            raise ValueError("Either enemies or enemy must be provided")

        self.turn_count = 0
        self.is_active = False
        self.defending = False

        # Combo system state
        self.action_history: list[str] = []
        self.damage_taken_while_defending: int = 0
        self.pending_combo: Optional[str] = None

    def _check_and_consume_stun(self) -> Optional[str]:
        """Check if player is stunned and consume the stun effect if so.

        Returns:
            Message about being stunned if stunned, None otherwise.
        """
        for effect in self.player.status_effects:
            if effect.effect_type == "stun":
                # Remove the stun effect (consume it)
                self.player.status_effects.remove(effect)
                return f"You are {colors.damage('stunned')} and cannot act this turn!"
        return None

    def _get_companion_bonus(self) -> float:
        """Calculate total companion attack bonus.

        Companion bonuses stack additively based on bond levels:
        - STRANGER: +0%
        - ACQUAINTANCE: +3%
        - TRUSTED: +5%
        - DEVOTED: +10%

        Returns:
            Total companion bonus as a decimal (e.g., 0.10 for +10%)
        """
        return sum(c.get_combat_bonus() for c in self.companions)

    def _check_rain_extinguish(self) -> list[str]:
        """Check if rain extinguishes burn effects (40% chance each).

        Rain/storm weather can extinguish Burn status effects on all combatants.
        Each burn effect has a 40% chance to be removed.

        Returns:
            List of flavor messages about extinguished flames.
        """
        messages = []

        # Check player burns
        for effect in list(self.player.status_effects):
            if effect.name == "Burn" and random.random() < 0.4:
                self.player.status_effects.remove(effect)
                messages.append("The rain douses your flames!")

        # Check enemy burns
        for enemy in self.get_living_enemies():
            for effect in list(enemy.status_effects):
                if effect.name == "Burn" and random.random() < 0.4:
                    enemy.status_effects.remove(effect)
                    messages.append(f"The rain extinguishes {enemy.name}'s flames!")

        return messages

    def apply_status_effect_with_weather(
        self,
        target: Union[Character, Enemy],
        effect: StatusEffect
    ) -> None:
        """Apply status effect with weather modifications.

        Storm weather extends Freeze duration by 1 turn (cold prolongs freezing).

        Args:
            target: Character or Enemy to apply effect to.
            effect: The status effect to apply.
        """
        # Storm extends freeze duration by 1 turn
        if self.weather and self.weather.condition == "storm" and effect.effect_type == "freeze":
            effect.duration += 1
        target.apply_status_effect(effect)

    @property
    def enemy(self) -> Enemy:
        """Backward compatibility: return first enemy."""
        return self.enemies[0]

    def get_living_enemies(self) -> list[Enemy]:
        """Get list of enemies that are still alive.

        Returns:
            List of living enemies
        """
        return [e for e in self.enemies if e.is_alive()]

    def find_enemy_by_name(self, name: str) -> Optional[Enemy]:
        """Find a living enemy by partial or full name match.

        Args:
            name: Name or partial name to search for (case-insensitive)

        Returns:
            Matching enemy if found, None otherwise
        """
        name_lower = name.lower()
        for enemy in self.get_living_enemies():
            if name_lower in enemy.name.lower():
                return enemy
        return None

    def _get_target(self, target: str = "") -> Tuple[Optional[Enemy], Optional[str]]:
        """Get target enemy for an attack/cast.

        Args:
            target: Target name or empty string for default target

        Returns:
            Tuple of (enemy, error_message). If enemy is None, error_message
            explains why and lists valid targets.
        """
        living = self.get_living_enemies()

        if not living:
            return None, "No living enemies to target!"

        if not target:
            # Default to first living enemy
            return living[0], None

        # Try to find by name
        enemy = self.find_enemy_by_name(target)
        if enemy:
            return enemy, None

        # Not found - build error message with valid targets
        valid_names = [e.name for e in living]
        return None, f"Target '{target}' not found. Valid targets: {', '.join(valid_names)}"

    def _record_action(self, action: str) -> None:
        """Record a combat action in history for combo detection.

        Args:
            action: Action type ('attack', 'defend', 'cast')
        """
        self.action_history.append(action)
        if len(self.action_history) > 3:
            self.action_history.pop(0)
        self._check_for_combo()

    def _check_for_combo(self) -> None:
        """Check if current action history matches a combo pattern."""
        for combo_name, combo_def in COMBOS.items():
            if self.action_history == combo_def["sequence"]:
                self.pending_combo = combo_name
                return
        self.pending_combo = None

    def get_pending_combo(self) -> Optional[str]:
        """Get the currently pending combo, if any.

        Returns:
            Combo name if pending ('frenzy', 'revenge', 'arcane_burst'), else None
        """
        return self.pending_combo

    def _clear_action_history(self) -> None:
        """Clear action history and pending combo state."""
        self.action_history.clear()
        self.pending_combo = None
        self.damage_taken_while_defending = 0

    def start(self) -> str:
        """
        Initialize combat and return intro message.

        Returns:
            Intro message describing the encounter (includes ASCII art if available)
        """
        self.is_active = True

        if len(self.enemies) == 1:
            enemy = self.enemies[0]
            # Check if this is a boss encounter
            if enemy.is_boss:
                intro = f"A {colors.damage('BOSS')} appears: {colors.enemy(enemy.name)}!"
            else:
                intro = f"A wild {colors.enemy(enemy.name)} appears!"
            # Add ASCII art if available
            if enemy.ascii_art:
                intro += "\n" + enemy.ascii_art.strip()
            intro += "\nCombat has begun!"
            return intro
        else:
            enemy_names = [colors.enemy(e.name) for e in self.enemies]
            intro = f"Enemies appear: {', '.join(enemy_names)}!"
            # Add ASCII art for first enemy if available
            if self.enemies[0].ascii_art:
                intro += "\n" + self.enemies[0].ascii_art.strip()
            intro += "\nCombat has begun!"
            return intro
    
    def player_attack(self, target: str = "") -> Tuple[bool, str]:
        """
        Player attacks an enemy.

        Args:
            target: Target enemy name (partial match). Empty = first living enemy.

        Returns:
            Tuple of (victory, message)
            - victory: True if ALL enemies defeated, False otherwise
            - message: Description of the attack
        """
        # Check if player is stunned
        stun_msg = self._check_and_consume_stun()
        if stun_msg:
            return False, stun_msg

        # Get target enemy
        enemy, error = self._get_target(target)
        if enemy is None:
            return False, error or "No target found."

        # Check if target is a hallucination
        if enemy.is_hallucination:
            self.enemies.remove(enemy)
            self.is_active = len(self.get_living_enemies()) > 0
            message = (
                f"Your attack passes through {colors.enemy(enemy.name)}!\n"
                f"The creature {colors.warning('dissipates')} like morning mist - "
                f"it was never real."
            )
            if not self.get_living_enemies():
                message += f" {colors.heal('The illusion fades.')}"
            return (not self.get_living_enemies(), message)

        # Check for Frenzy combo (Attack x3 -> triple attack, 1.5x damage)
        if self.pending_combo == "frenzy":
            base_damage = max(1, self.player.get_attack_power() - enemy.defense)
            # Triple hit: 3 smaller hits totaling 1.5x damage
            single_hit = max(1, base_damage // 2)
            total_damage = single_hit * 3
            enemy.take_damage(total_damage)
            message = (
                f"{colors.damage('FRENZY!')} You strike {colors.enemy(enemy.name)} "
                f"three times for {colors.damage(str(total_damage))} total damage!"
            )
            self._clear_action_history()

            if not enemy.is_alive():
                message += f"\n{colors.enemy(enemy.name)} has been defeated!"

            if not self.get_living_enemies():
                message += f" {colors.heal('Victory!')}"
                return True, message

            if enemy.is_alive():
                message += f"\n{colors.enemy(enemy.name)} has {enemy.health}/{enemy.max_health} HP remaining."

            return False, message

        # Check for Revenge combo (Defend x2 + Attack -> counter-attack)
        if self.pending_combo == "revenge":
            revenge_damage = max(1, self.damage_taken_while_defending)
            enemy.take_damage(revenge_damage)
            message = (
                f"{colors.damage('REVENGE!')} You channel your pain into a devastating "
                f"counter for {colors.damage(str(revenge_damage))} damage!"
            )
            self._clear_action_history()

            if not enemy.is_alive():
                message += f"\n{colors.enemy(enemy.name)} has been defeated!"

            if not self.get_living_enemies():
                message += f" {colors.heal('Victory!')}"
                return True, message

            if enemy.is_alive():
                message += f"\n{colors.enemy(enemy.name)} has {enemy.health}/{enemy.max_health} HP remaining."

            return False, message

        # Normal attack - record action for combo tracking
        self._record_action("attack")

        # Check for backstab bonus (attacking from stealth)
        is_backstab = self.player.consume_stealth()

        # Calculate damage: player attack power (strength + weapon bonus) - enemy defense, minimum 1
        dmg = max(1, self.player.get_attack_power() - enemy.defense)

        # Apply backstab bonus (1.5x damage from stealth)
        if is_backstab:
            dmg = int(dmg * 1.5)

        # Apply companion bonus
        companion_bonus = self._get_companion_bonus()
        if companion_bonus > 0:
            dmg = int(dmg * (1 + companion_bonus))

        # Check for critical hit (DEX-based + luck bonus)
        crit_chance = calculate_crit_chance(self.player.dexterity, self.player.luck)
        is_crit = random.random() < crit_chance
        if is_crit:
            dmg = int(dmg * CRIT_MULTIPLIER)

        enemy.take_damage(dmg)

        if is_backstab:
            message = (
                f"{colors.damage('BACKSTAB!')} You strike {colors.enemy(enemy.name)} "
                f"from the shadows for {colors.damage(str(dmg))} damage!"
            )
        elif is_crit:
            message = (
                f"{colors.damage('CRITICAL HIT!')} You attack {colors.enemy(enemy.name)} "
                f"for {colors.damage(str(dmg))} damage!"
            )
        else:
            message = f"You attack {colors.enemy(enemy.name)} for {colors.damage(str(dmg))} damage!"

        if not enemy.is_alive():
            message += f"\n{colors.enemy(enemy.name)} has been defeated!"

        # Check if all enemies are dead
        if not self.get_living_enemies():
            message += f" {colors.heal('Victory!')}"
            return True, message

        if enemy.is_alive():
            message += f"\n{colors.enemy(enemy.name)} has {enemy.health}/{enemy.max_health} HP remaining."

        return False, message
    
    def player_defend(self) -> Tuple[bool, str]:
        """
        Player takes defensive stance.

        Returns:
            Tuple of (victory, message)
            - victory: Always False (combat continues)
            - message: Description of defensive action
        """
        # Check if player is stunned
        stun_msg = self._check_and_consume_stun()
        if stun_msg:
            return False, stun_msg

        # Record action for combo tracking
        self._record_action("defend")

        self.defending = True
        message = "You brace yourself for the enemy's attack, taking a defensive stance!"
        return False, message

    def player_sneak(self) -> Tuple[bool, str]:
        """
        Rogue enters stealth mode for backstab opportunity.

        Only Rogues can use this ability. Applies a stealth status effect
        that provides a damage bonus on the next attack and increased
        dodge chance while in effect.

        Returns:
            Tuple of (victory, message)
            - victory: Always False (combat continues)
            - message: Description of stealth action or error message
        """
        from cli_rpg.models.character import CharacterClass

        # Check if player is stunned
        stun_msg = self._check_and_consume_stun()
        if stun_msg:
            return False, stun_msg

        # Only Rogues can sneak
        if self.player.character_class != CharacterClass.ROGUE:
            return False, "Only Rogues can sneak!"

        # Check stamina cost (10 stamina)
        if not self.player.use_stamina(10):
            return False, f"Not enough stamina! ({self.player.stamina}/{self.player.max_stamina})"

        # Record action for combo tracking
        self._record_action("sneak")

        # Apply stealth effect (duration 2: lasts through enemy turn + player's next action)
        stealth_effect = StatusEffect(
            name="Stealth",
            effect_type="stealth",
            damage_per_turn=0,
            duration=2,
            stat_modifier=0.0
        )
        self.player.apply_status_effect(stealth_effect)

        return False, "You slip into the shadows, preparing to strike..."

    def player_cast(self, target: str = "") -> Tuple[bool, str]:
        """
        Player casts a magic attack.

        Magic damage is based on intelligence and ignores enemy defense.
        Formula: intelligence * 1.5 (minimum 1)
        Costs 10 mana per cast (Arcane Burst costs 25 mana).

        Args:
            target: Target enemy name (partial match). Empty = first living enemy.

        Returns:
            Tuple of (victory, message)
            - victory: True if ALL enemies defeated, False otherwise
            - message: Description of the spell cast
        """
        # Check if player is stunned
        stun_msg = self._check_and_consume_stun()
        if stun_msg:
            return False, stun_msg

        # Get target enemy
        enemy, error = self._get_target(target)
        if enemy is None:
            return False, error or "No target found."

        # Check for Arcane Burst combo (Cast x3 -> 2x magic damage, costs 25 mana)
        if self.pending_combo == "arcane_burst":
            # Arcane Burst costs 25 mana (not 3 × 10)
            if not self.player.use_mana(25):
                return False, f"Not enough mana! ({self.player.mana}/{self.player.max_mana})"

            dmg = max(1, int(self.player.intelligence * 1.5)) * 2
            enemy.take_damage(dmg)
            message = (
                f"{colors.damage('ARCANE BURST!')} Magical energy explodes around "
                f"{colors.enemy(enemy.name)} for {colors.damage(str(dmg))} damage!"
            )
            self._clear_action_history()

            if not enemy.is_alive():
                message += f"\n{colors.enemy(enemy.name)} has been defeated!"

            if not self.get_living_enemies():
                message += f" {colors.heal('Victory!')}"
                return True, message

            if enemy.is_alive():
                message += f"\n{colors.enemy(enemy.name)} has {enemy.health}/{enemy.max_health} HP remaining."

            return False, message

        # Check mana cost for normal cast (10 mana)
        if not self.player.use_mana(10):
            return False, f"Not enough mana! ({self.player.mana}/{self.player.max_mana})"

        # Normal cast - record action for combo tracking
        self._record_action("cast")

        # Calculate magic damage: intelligence * 1.5, ignores defense
        dmg = max(1, int(self.player.intelligence * 1.5))

        # Apply companion bonus
        companion_bonus = self._get_companion_bonus()
        if companion_bonus > 0:
            dmg = int(dmg * (1 + companion_bonus))

        # Check for critical hit (INT-based for cast + luck bonus)
        crit_chance = calculate_crit_chance(self.player.intelligence, self.player.luck)
        is_crit = random.random() < crit_chance
        if is_crit:
            dmg = int(dmg * CRIT_MULTIPLIER)

        enemy.take_damage(dmg)

        if is_crit:
            message = (
                f"{colors.damage('CRITICAL HIT!')} You cast a spell at {colors.enemy(enemy.name)} "
                f"for {colors.damage(str(dmg))} magic damage!"
            )
        else:
            message = f"You cast a spell at {colors.enemy(enemy.name)} for {colors.damage(str(dmg))} magic damage!"

        if not enemy.is_alive():
            message += f"\n{colors.enemy(enemy.name)} has been defeated!"

        # Check if all enemies are dead
        if not self.get_living_enemies():
            message += f" {colors.heal('Victory!')}"
            return True, message

        if enemy.is_alive():
            message += f"\n{colors.enemy(enemy.name)} has {enemy.health}/{enemy.max_health} HP remaining."

        return False, message

    def player_flee(self) -> Tuple[bool, str]:
        """
        Attempt to flee from combat.

        Returns:
            Tuple of (success, message)
            - success: True if escape successful, False otherwise
            - message: Description of flee attempt
        """
        # Fleeing breaks combo chain
        self._clear_action_history()

        # Base 50% chance + dexterity modifier
        flee_chance = 50 + (self.player.dexterity * 2)
        roll = random.randint(1, 100)

        if roll <= flee_chance:
            return True, "You successfully flee from combat!"
        else:
            return False, "You couldn't escape! The enemy blocks your path!"
    
    def enemy_turn(self) -> str:
        """
        All living enemies attack player.

        Returns:
            Message describing the enemies' actions
        """
        living = self.get_living_enemies()

        if not living:
            return "No enemies remain to attack."

        messages = []
        total_damage = 0

        for enemy in living:
            # Check for player dodge (stealth or DEX-based)
            if self.player.is_stealthed():
                # Stealth dodge: DEX * 5%, capped at 75%
                stealth_dodge_chance = min(self.player.dexterity * 0.05, 0.75)
                if random.random() < stealth_dodge_chance:
                    # Player dodged from stealth
                    msg = (
                        f"{colors.enemy(enemy.name)} attacks, but you "
                        f"{colors.heal('dodge')} from the shadows!"
                    )
                    messages.append(msg)
                    # Still tick enemy status effects
                    enemy_status_messages = enemy.tick_status_effects()
                    messages.extend(enemy_status_messages)
                    continue
            else:
                # Normal dodge check (DEX-based)
                dodge_chance = calculate_dodge_chance(self.player.dexterity)
                if random.random() < dodge_chance:
                    # Player dodged the attack
                    msg = (
                        f"{colors.enemy(enemy.name)} attacks, but you "
                        f"{colors.heal('dodge')} out of the way!"
                    )
                    messages.append(msg)
                    # Skip damage calculation and status effects for this enemy
                    # Still tick enemy status effects
                    enemy_status_messages = enemy.tick_status_effects()
                    messages.extend(enemy_status_messages)
                    continue

            # Calculate damage: enemy attack - player defense (constitution + armor bonus), minimum 1
            # Apply freeze reduction (50%) if enemy is frozen
            attack_power = enemy.calculate_damage()
            if enemy.has_effect_type("freeze"):
                attack_power = int(attack_power * 0.5)
            base_damage = max(1, attack_power - self.player.get_defense())

            # Check for enemy critical hit (flat 5% chance)
            is_crit = random.random() < ENEMY_CRIT_CHANCE
            if is_crit:
                base_damage = int(base_damage * CRIT_MULTIPLIER)

            # Apply defense reduction if player is defending (applies to all attacks this turn)
            if self.defending:
                dmg = max(1, base_damage // 2)  # Half damage when defending
                # Track damage taken while defending for Revenge combo
                self.damage_taken_while_defending += dmg
                if is_crit:
                    msg = (
                        f"{colors.damage('CRITICAL HIT!')} {colors.enemy(enemy.name)} attacks! "
                        f"You block some of the damage, taking {colors.damage(str(dmg))} damage!"
                    )
                else:
                    msg = (
                        f"{colors.enemy(enemy.name)} attacks! You block some of the damage, "
                        f"taking {colors.damage(str(dmg))} damage!"
                    )
            else:
                dmg = base_damage
                # Use attack_flavor if available for more immersive combat
                if is_crit:
                    if enemy.attack_flavor:
                        cleaned_flavor = strip_leading_name(enemy.name, enemy.attack_flavor)
                        msg = (
                            f"{colors.damage('CRITICAL HIT!')} {colors.enemy(enemy.name)} "
                            f"{cleaned_flavor}! You take {colors.damage(str(dmg))} damage!"
                        )
                    else:
                        msg = (
                            f"{colors.damage('CRITICAL HIT!')} {colors.enemy(enemy.name)} "
                            f"attacks you for {colors.damage(str(dmg))} damage!"
                        )
                else:
                    if enemy.attack_flavor:
                        cleaned_flavor = strip_leading_name(enemy.name, enemy.attack_flavor)
                        msg = (
                            f"{colors.enemy(enemy.name)} {cleaned_flavor}! "
                            f"You take {colors.damage(str(dmg))} damage!"
                        )
                    else:
                        msg = f"{colors.enemy(enemy.name)} attacks you for {colors.damage(str(dmg))} damage!"

            self.player.take_damage(dmg)
            total_damage += dmg
            messages.append(msg)

            # Taking damage breaks stealth
            if self.player.consume_stealth():
                messages.append(f"The attack {colors.warning('breaks your stealth')}!")

            # Check if enemy can apply poison
            if enemy.poison_chance > 0 and random.random() < enemy.poison_chance:
                # Apply poison effect
                poison = StatusEffect(
                    name="Poison",
                    effect_type="dot",
                    damage_per_turn=enemy.poison_damage,
                    duration=enemy.poison_duration
                )
                self.player.apply_status_effect(poison)
                messages.append(
                    f"{colors.enemy(enemy.name)}'s attack {colors.damage('poisons')} you!"
                )

            # Check if enemy can apply burn
            if enemy.burn_chance > 0 and random.random() < enemy.burn_chance:
                # Apply burn effect
                burn = StatusEffect(
                    name="Burn",
                    effect_type="dot",
                    damage_per_turn=enemy.burn_damage,
                    duration=enemy.burn_duration
                )
                self.player.apply_status_effect(burn)
                messages.append(
                    f"{colors.enemy(enemy.name)}'s attack {colors.damage('burns')} you!"
                )

            # Check if enemy can apply stun
            if enemy.stun_chance > 0 and random.random() < enemy.stun_chance:
                # Apply stun effect
                stun = StatusEffect(
                    name="Stun",
                    effect_type="stun",
                    damage_per_turn=0,
                    duration=enemy.stun_duration
                )
                self.player.apply_status_effect(stun)
                messages.append(
                    f"{colors.enemy(enemy.name)}'s attack {colors.damage('stuns')} you!"
                )

            # Check if enemy can apply freeze (to player - ice enemies freeze the player)
            if enemy.freeze_chance > 0 and random.random() < enemy.freeze_chance:
                # Apply freeze effect to player
                freeze = StatusEffect(
                    name="Freeze",
                    effect_type="freeze",
                    damage_per_turn=0,
                    duration=enemy.freeze_duration
                )
                self.player.apply_status_effect(freeze)
                messages.append(
                    f"{colors.enemy(enemy.name)}'s attack {colors.damage('freezes')} you!"
                )

            # Check if enemy can apply bleed
            if enemy.bleed_chance > 0 and random.random() < enemy.bleed_chance:
                # Apply bleed effect to player
                bleed = StatusEffect(
                    name="Bleed",
                    effect_type="dot",
                    damage_per_turn=enemy.bleed_damage,
                    duration=enemy.bleed_duration
                )
                self.player.apply_status_effect(bleed)
                messages.append(
                    f"{colors.enemy(enemy.name)}'s attack causes you to {colors.damage('bleed')}!"
                )

            # Tick status effects on this enemy
            enemy_status_messages = enemy.tick_status_effects()
            messages.extend(enemy_status_messages)

        # Reset defensive stance after all attacks
        self.defending = False

        # Regenerate stamina (1 per enemy turn)
        self.player.regen_stamina(1)

        # Tick status effects on player (DOT damage, expiration)
        status_messages = self.player.tick_status_effects()
        messages.extend(status_messages)

        # Weather interactions: rain/storm can extinguish burn
        if self.weather and self.weather.condition in ("rain", "storm"):
            messages.extend(self._check_rain_extinguish())

        # Combine messages
        result = "\n".join(messages)
        result += f"\nYou have {self.player.health}/{self.player.max_health} HP remaining."

        return result
    
    def end_combat(self, victory: bool) -> str:
        """
        Resolve combat and award XP and loot on victory.

        XP is summed from all enemies. Loot is generated from each enemy.

        Args:
            victory: True if player won, False if player lost

        Returns:
            Message describing combat resolution
        """
        self.is_active = False

        # Clear combo state at end of combat
        self._clear_action_history()

        # Clear player status effects at end of combat
        self.player.clear_status_effects()

        # Clear enemy status effects at end of combat
        for enemy in self.enemies:
            enemy.clear_status_effects()

        if victory:
            # Play victory sound
            sound_victory()

            # Build victory message based on number of enemies
            if len(self.enemies) == 1:
                messages = [f"{colors.heal('Victory!')} You defeated {colors.enemy(self.enemies[0].name)}!"]
            else:
                enemy_names = [colors.enemy(e.name) for e in self.enemies]
                messages = [f"{colors.heal('Victory!')} You defeated {', '.join(enemy_names)}!"]

            # Sum XP from all enemies
            total_xp = sum(e.xp_reward for e in self.enemies)
            xp_messages = self.player.gain_xp(total_xp)
            messages.extend(xp_messages)

            # Award gold based on sum of enemy levels, modified by luck (±5% per luck from 10)
            total_level = sum(e.level for e in self.enemies)
            luck_modifier = 1.0 + (self.player.luck - 10) * 0.05
            gold_reward = int(random.randint(5, 15) * total_level * luck_modifier)
            self.player.add_gold(gold_reward)
            messages.append(f"You earned {colors.gold(str(gold_reward) + ' gold')}!")

            # Generate and award loot from each enemy
            for enemy in self.enemies:
                # Use boss loot for boss enemies (guaranteed drop with enhanced stats)
                if enemy.is_boss:
                    loot = generate_boss_loot(enemy, self.player.level)
                else:
                    loot = generate_loot(enemy, self.player.level, self.player.luck)
                if loot is not None:
                    if self.player.inventory.add_item(loot):
                        messages.append(f"You found: {colors.item(loot.name)}!")
                        # Track quest progress for collect objectives
                        quest_messages = self.player.record_collection(loot.name)
                        messages.extend(quest_messages)
                        # Track quest progress for drop objectives (enemy + item)
                        drop_messages = self.player.record_drop(enemy.name, loot.name)
                        messages.extend(drop_messages)
                    else:
                        messages.append(f"You found {colors.item(loot.name)} but your inventory is full!")

            return "\n".join(messages)
        else:
            if len(self.enemies) == 1:
                return f"{colors.damage('You have been defeated')} by {colors.enemy(self.enemies[0].name)}..."
            else:
                return f"{colors.damage('You have been defeated')} by the enemies..."
    
    def get_status(self) -> str:
        """
        Display current combat status.

        Returns:
            Status string showing health of player and all enemies
        """
        lines = [
            f"=== {colors.stat_header('COMBAT')} ===",
            f"Player: {self.player.name} - {self.player.health}/{self.player.max_health} HP",
        ]

        # Display active status effects on player
        if self.player.status_effects:
            effect_strs = [
                f"{e.name} ({e.duration} turns)" for e in self.player.status_effects
            ]
            lines.append(f"Status: {colors.damage(', '.join(effect_strs))}")

        for enemy in self.enemies:
            status = "DEAD" if not enemy.is_alive() else f"{enemy.health}/{enemy.max_health} HP"
            lines.append(f"Enemy: {colors.enemy(enemy.name)} - {status}")

            # Display active status effects on enemy
            if enemy.is_alive() and enemy.status_effects:
                effect_strs = [
                    f"{e.name} ({e.duration} turns)" for e in enemy.status_effects
                ]
                lines.append(f"  Status: {colors.damage(', '.join(effect_strs))}")

        # Display action history for combo tracking
        if self.action_history:
            actions_display = " → ".join(f"[{a.capitalize()}]" for a in self.action_history)
            lines.append(f"Last actions: {actions_display}")

        # Display pending combo notification
        if self.pending_combo:
            combo_name = self.pending_combo.replace("_", " ").title()
            lines.append(f"{colors.heal('COMBO AVAILABLE')}: {combo_name}!")

        # Display companion bonus if any
        companion_bonus = self._get_companion_bonus()
        if companion_bonus > 0:
            bonus_percent = int(companion_bonus * 100)
            lines.append(f"Companion Bonus: +{bonus_percent}% attack")

        return "\n".join(lines)


def generate_loot(enemy: Enemy, level: int, luck: int = 10) -> Optional[Item]:
    """Generate loot item dropped by defeated enemy.

    Args:
        enemy: The defeated enemy
        level: Player level for scaling loot stats
        luck: Player luck stat for drop rate and bonus modifiers (default 10)

    Returns:
        Item if loot dropped, None otherwise (base 50% drop rate, ±2% per luck from 10)
    """
    # Base 50% + 2% per luck above/below 10
    drop_chance = 0.50 + (luck - 10) * 0.02
    if random.random() > drop_chance:
        return None

    # Choose random item type
    item_types = [
        (ItemType.WEAPON, 0.30),
        (ItemType.ARMOR, 0.30),
        (ItemType.CONSUMABLE, 0.30),
        (ItemType.MISC, 0.10),
    ]

    roll = random.random()
    cumulative: float = 0.0
    item_type = ItemType.MISC
    for itype, prob in item_types:
        cumulative += prob
        if roll <= cumulative:
            item_type = itype
            break

    # Calculate luck bonus for equipment stats (+1 per 5 luck above 10)
    luck_bonus = max(0, (luck - 10) // 5)

    # Generate item based on type
    if item_type == ItemType.WEAPON:
        prefixes = ["Rusty", "Iron", "Steel", "Sharp", "Worn", "Old"]
        names = ["Sword", "Dagger", "Axe", "Mace", "Spear"]
        prefix = random.choice(prefixes)
        name = random.choice(names)
        damage_bonus = max(1, level + random.randint(1, 3) + luck_bonus)
        return Item(
            name=f"{prefix} {name}",
            description=f"A {prefix.lower()} {name.lower()} from {enemy.name}",
            item_type=ItemType.WEAPON,
            damage_bonus=damage_bonus
        )

    elif item_type == ItemType.ARMOR:
        prefixes = ["Worn", "Sturdy", "Leather", "Chain", "Old"]
        names = ["Armor", "Shield", "Helmet", "Gauntlets", "Boots"]
        prefix = random.choice(prefixes)
        name = random.choice(names)
        defense_bonus = max(1, level + random.randint(0, 2) + luck_bonus)
        return Item(
            name=f"{prefix} {name}",
            description=f"A {prefix.lower()} {name.lower()} from {enemy.name}",
            item_type=ItemType.ARMOR,
            defense_bonus=defense_bonus
        )

    elif item_type == ItemType.CONSUMABLE:
        # 15% chance for cure item, otherwise regular healing consumable
        if random.random() < 0.15:
            # Cure items
            cure_items = [
                ("Antidote", "A powerful cure for plagues and afflictions"),
                ("Cure Vial", "A rare remedy that can cure deadly diseases"),
                ("Purification Elixir", "Cleansing medicine from ancient recipes"),
            ]
            name, desc = random.choice(cure_items)
            return Item(
                name=name,
                description=desc,
                item_type=ItemType.CONSUMABLE,
                is_cure=True,
            )
        else:
            heal_amount = 15 + (level * 5) + random.randint(0, 10)
            potions = [
                ("Health Potion", "Restores health when consumed"),
                ("Healing Elixir", "A bubbling red liquid"),
                ("Life Draught", "Smells of herbs and magic"),
            ]
            name, desc = random.choice(potions)
            return Item(
                name=name,
                description=desc,
                item_type=ItemType.CONSUMABLE,
                heal_amount=heal_amount
            )

    else:  # MISC
        misc_items = [
            ("Gold Coin", "A shiny gold coin"),
            ("Strange Key", "An old key of unknown origin"),
            ("Monster Fang", "A trophy from battle"),
            ("Gem Stone", "A small polished gem"),
        ]
        name, desc = random.choice(misc_items)
        return Item(
            name=name,
            description=desc,
            item_type=ItemType.MISC
        )


def spawn_enemy(
    location_name: str,
    level: int,
    location_category: Optional[str] = None,
    distance: int = 0
) -> Enemy:
    """
    Spawn an enemy appropriate for the location and player level.

    Args:
        location_name: Name of the location
        level: Player level for scaling
        location_category: Optional category from Location.category field.
                          When provided, takes precedence over location name matching.
                          Valid: town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village
        distance: Manhattan distance from origin for difficulty scaling (default 0)

    Returns:
        Enemy instance with stats scaled by distance
    """
    # Enemy templates by location type
    enemy_templates = {
        "forest": ["Wolf", "Bear", "Wild Boar", "Giant Spider"],
        "cave": ["Bat", "Goblin", "Troll", "Cave Dweller"],
        "dungeon": ["Skeleton", "Zombie", "Ghost", "Dark Knight"],
        "mountain": ["Eagle", "Goat", "Mountain Lion", "Yeti"],
        "village": ["Bandit", "Thief", "Ruffian", "Outlaw"],
        "default": ["Monster", "Creature", "Beast", "Fiend"]
    }

    # Category mappings: map location categories to enemy template keys
    # This allows semantic categories like "wilderness" to map to "forest" enemies
    category_mappings = {
        "wilderness": "forest",
        "ruins": "dungeon",
        "town": "village",
        "settlement": "village",
        # Direct matches
        "forest": "forest",
        "cave": "cave",
        "dungeon": "dungeon",
        "mountain": "mountain",
        "village": "village",
    }

    # Determine location type:
    # 1. Use location_category if provided (takes precedence)
    # 2. Otherwise fall back to matching against location name
    location_type = "default"

    if location_category:
        # Use category mapping if available
        location_type = category_mappings.get(location_category.lower(), "default")
    else:
        # Fall back to name-based matching
        location_lower = location_name.lower()
        for loc_type in enemy_templates:
            if loc_type in location_lower:
                location_type = loc_type
                break

    # Select random enemy from template
    enemy_list = enemy_templates.get(location_type, enemy_templates["default"])
    enemy_name = random.choice(enemy_list)

    # Calculate base stats from level
    base_health = 20 + (level * 10)
    base_attack = 3 + (level * 2)
    base_defense = 1 + level
    base_xp = 20 + (level * 10)

    # Apply distance multiplier to scale difficulty
    multiplier = get_distance_multiplier(distance)
    scaled_health = int(base_health * multiplier)
    scaled_attack = int(base_attack * multiplier)
    scaled_defense = int(base_defense * multiplier)
    scaled_xp = int(base_xp * multiplier)

    # Get fallback ASCII art based on enemy name
    ascii_art = get_fallback_ascii_art(enemy_name)

    # Determine status effect capabilities based on enemy type
    enemy_name_lower = enemy_name.lower()

    # Spiders and snakes get 20% poison chance, 4 damage, 3 turns
    poison_chance = 0.0
    poison_damage = 0
    poison_duration = 0
    if any(term in enemy_name_lower for term in ["spider", "snake", "serpent", "viper"]):
        poison_chance = 0.2
        poison_damage = 4
        poison_duration = 3

    # Fire elementals and dragons get 20% burn chance, 5 damage, 2 turns
    burn_chance = 0.0
    burn_damage = 0
    burn_duration = 0
    if any(term in enemy_name_lower for term in ["fire", "dragon", "elemental", "flame", "inferno"]):
        burn_chance = 0.2
        burn_damage = 5
        burn_duration = 2

    # Trolls and golems get 15% stun chance, 1 turn
    stun_chance = 0.0
    stun_duration = 0
    if any(term in enemy_name_lower for term in ["troll", "golem", "hammer", "giant"]):
        stun_chance = 0.15
        stun_duration = 1

    # Yetis and ice enemies get 20% freeze chance, 2 turns
    freeze_chance = 0.0
    freeze_duration = 0
    if any(term in enemy_name_lower for term in ["yeti", "ice", "frost", "frozen", "blizzard"]):
        freeze_chance = 0.2
        freeze_duration = 2

    # Wolves, bears, lions get 20% bleed chance, 3 damage, 4 turns
    bleed_chance = 0.0
    bleed_damage = 0
    bleed_duration = 0
    if any(term in enemy_name_lower for term in ["wolf", "bear", "lion", "cat", "claw", "blade", "razor", "fang"]):
        bleed_chance = 0.2
        bleed_damage = 3
        bleed_duration = 4

    return Enemy(
        name=enemy_name,
        health=scaled_health,
        max_health=scaled_health,
        attack_power=scaled_attack,
        defense=scaled_defense,
        xp_reward=scaled_xp,
        level=level,
        ascii_art=ascii_art,
        poison_chance=poison_chance,
        poison_damage=poison_damage,
        poison_duration=poison_duration,
        burn_chance=burn_chance,
        burn_damage=burn_damage,
        burn_duration=burn_duration,
        stun_chance=stun_chance,
        stun_duration=stun_duration,
        freeze_chance=freeze_chance,
        freeze_duration=freeze_duration,
        bleed_chance=bleed_chance,
        bleed_damage=bleed_damage,
        bleed_duration=bleed_duration,
    )


def get_boss_ascii_art(boss_name: str) -> str:
    """Get ASCII art for a boss enemy.

    Args:
        boss_name: Name of the boss

    Returns:
        ASCII art string for the boss
    """
    name_lower = boss_name.lower()

    # Stone Sentinel (mine boss)
    if any(term in name_lower for term in ["stone sentinel", "sentinel"]):
        return _ASCII_ART_BOSS_STONE_SENTINEL

    # Drowned Overseer (flooded mine boss)
    if any(term in name_lower for term in ["drowned", "overseer", "flooded"]):
        return _ASCII_ART_BOSS_DROWNED_OVERSEER

    # Treant/forest bosses
    if any(term in name_lower for term in ["treant", "tree", "forest", "dryad", "grove"]):
        return _ASCII_ART_BOSS_TREANT

    # Demon/infernal bosses
    if any(term in name_lower for term in ["demon", "lord", "chaos", "overlord"]):
        return _ASCII_ART_BOSS_DEMON

    # Undead bosses
    if any(term in name_lower for term in ["lich", "pharaoh", "shadow", "cursed"]):
        return _ASCII_ART_BOSS_UNDEAD

    # Guardian/construct bosses
    if any(term in name_lower for term in ["guardian", "golem", "champion", "knight"]):
        return _ASCII_ART_BOSS_GUARDIAN

    # Default to demon art for unknown bosses
    return _ASCII_ART_BOSS_DEMON


def spawn_boss(
    location_name: str,
    level: int,
    location_category: Optional[str] = None,
    boss_type: Optional[str] = None
) -> Enemy:
    """
    Spawn a boss enemy appropriate for the location and player level.

    Bosses have 2x base stats and 4x XP reward compared to normal enemies.

    Args:
        location_name: Name of the location
        level: Player level for scaling
        location_category: Optional category for boss template selection.
                          Valid: dungeon, ruins, cave, or default for unknown.
        boss_type: Optional specific boss type to spawn (e.g., "stone_sentinel").
                   When provided, overrides category-based selection.

    Returns:
        Enemy instance with is_boss=True
    """
    # Handle specific boss types
    if boss_type == "stone_sentinel":
        # Stone Sentinel: ancient golem awakened by miners
        # Scale stats: 2x base stats for bosses
        base_health = (40 + level * 25) * 2
        base_attack = (5 + level * 3) * 2
        base_defense = (2 + level * 2) * 2
        # 4x XP reward for bosses
        base_xp = (30 + level * 20) * 4

        # Get boss ASCII art
        ascii_art = get_boss_ascii_art("The Stone Sentinel")

        return Enemy(
            name="The Stone Sentinel",
            health=base_health,
            max_health=base_health,
            attack_power=base_attack,
            defense=base_defense,
            xp_reward=base_xp,
            level=level,
            ascii_art=ascii_art,
            is_boss=True,
            description="An ancient stone guardian awakened by the miners' greed. Its eyes glow with an inner fire.",
            attack_flavor="slams down with a massive stone fist",
            stun_chance=0.20,  # Heavy stone fist can stun
            stun_duration=1,
        )

    if boss_type == "elder_treant":
        # Elder Treant: ancient tree spirit guardian of the forest
        # Scale stats: 2x base stats for bosses
        base_health = (40 + level * 25) * 2
        base_attack = (5 + level * 3) * 2
        base_defense = (2 + level * 2) * 2
        # 4x XP reward for bosses
        base_xp = (30 + level * 20) * 4

        # Get boss ASCII art
        ascii_art = get_boss_ascii_art("The Elder Treant")

        return Enemy(
            name="The Elder Treant",
            health=base_health,
            max_health=base_health,
            attack_power=base_attack,
            defense=base_defense,
            xp_reward=base_xp,
            level=level,
            ascii_art=ascii_art,
            is_boss=True,
            description="An ancient tree spirit, guardian of the forest since time immemorial. Its bark is gnarled with age, and poison sap drips from its branches.",
            attack_flavor="lashes out with gnarled branches",
            poison_chance=0.25,  # Nature's corruption
            poison_damage=5,
            poison_duration=3,
        )

    if boss_type == "drowned_overseer":
        # Drowned Overseer: undead mine foreman who drowned when the mines flooded
        # Scale stats: 2x base stats for bosses
        base_health = (40 + level * 25) * 2
        base_attack = (5 + level * 3) * 2
        base_defense = (2 + level * 2) * 2
        # 4x XP reward for bosses
        base_xp = (30 + level * 20) * 4

        # Get boss ASCII art
        ascii_art = get_boss_ascii_art("The Drowned Overseer")

        return Enemy(
            name="The Drowned Overseer",
            health=base_health,
            max_health=base_health,
            attack_power=base_attack,
            defense=base_defense,
            xp_reward=base_xp,
            level=level,
            ascii_art=ascii_art,
            is_boss=True,
            description="The former overseer of these mines, drowned when the waters rose. Now he guards the depths with rusted tools and icy hatred.",
            attack_flavor="swings a corroded pickaxe",
            bleed_chance=0.20,  # Rusted pickaxe causes bleeding
            bleed_damage=4,
            bleed_duration=3,
            freeze_chance=0.15,  # Icy water touch can freeze
            freeze_duration=2,
        )

    # Boss templates by location type
    boss_templates = {
        "dungeon": ["Lich Lord", "Dark Champion", "Demon Lord"],
        "ruins": ["Ancient Guardian", "Cursed Pharaoh", "Shadow King"],
        "cave": ["Cave Troll King", "Elder Wyrm", "Crystal Golem"],
        "forest": ["Elder Treant", "Grove Guardian", "Ancient Dryad"],
        "default": ["Archdemon", "Overlord", "Chaos Beast"]
    }

    # Determine boss type based on category
    category = location_category.lower() if location_category else "default"
    if category not in boss_templates:
        category = "default"

    # Select random boss from template
    boss_list = boss_templates[category]
    boss_name = random.choice(boss_list)

    # Scale stats: 2x base stats for bosses
    base_health = (40 + level * 25) * 2
    base_attack = (5 + level * 3) * 2
    base_defense = (2 + level * 2) * 2
    # 4x XP reward for bosses
    base_xp = (30 + level * 20) * 4

    # Get boss ASCII art
    ascii_art = get_boss_ascii_art(boss_name)

    return Enemy(
        name=boss_name,
        health=base_health,
        max_health=base_health,
        attack_power=base_attack,
        defense=base_defense,
        xp_reward=base_xp,
        level=level,
        ascii_art=ascii_art,
        is_boss=True,
    )


def generate_boss_loot(boss: Enemy, level: int) -> Item:
    """Generate guaranteed loot item dropped by defeated boss.

    Boss loot has:
    - 100% drop rate (guaranteed)
    - Enhanced stats (higher damage/defense bonuses)
    - Legendary-tier prefixes

    Args:
        boss: The defeated boss enemy
        level: Player level for scaling loot stats

    Returns:
        Item (always returns an item, guaranteed drop)
    """
    # Choose random item type (no misc for bosses)
    item_types = [
        (ItemType.WEAPON, 0.35),
        (ItemType.ARMOR, 0.35),
        (ItemType.CONSUMABLE, 0.30),
    ]

    roll = random.random()
    cumulative: float = 0.0
    item_type = ItemType.WEAPON
    for itype, prob in item_types:
        cumulative += prob
        if roll <= cumulative:
            item_type = itype
            break

    # Legendary prefixes for boss loot
    legendary_prefixes = ["Legendary", "Ancient", "Cursed", "Divine", "Epic"]

    # Generate item based on type
    if item_type == ItemType.WEAPON:
        prefix = random.choice(legendary_prefixes)
        names = ["Greatsword", "Warblade", "Doom Axe", "Soul Reaver", "Dragon Slayer"]
        name = random.choice(names)
        # Enhanced stats: level + random(5, 10)
        damage_bonus = level + random.randint(5, 10)
        return Item(
            name=f"{prefix} {name}",
            description=f"A powerful weapon dropped by {boss.name}",
            item_type=ItemType.WEAPON,
            damage_bonus=damage_bonus
        )

    elif item_type == ItemType.ARMOR:
        prefix = random.choice(legendary_prefixes)
        names = ["Platemail", "Dragon Armor", "Titan Shield", "Crown of Power", "Warlord Gauntlets"]
        name = random.choice(names)
        # Enhanced stats: level + random(4, 8)
        defense_bonus = level + random.randint(4, 8)
        return Item(
            name=f"{prefix} {name}",
            description=f"Legendary armor dropped by {boss.name}",
            item_type=ItemType.ARMOR,
            defense_bonus=defense_bonus
        )

    else:  # CONSUMABLE
        heal_amount = 50 + (level * 10) + random.randint(10, 30)
        potions = [
            ("Grand Elixir", "A powerful healing elixir of legendary quality"),
            ("Essence of Life", "Pure concentrated life energy"),
            ("Phoenix Tears", "Mystical tears that restore vitality"),
        ]
        name, desc = random.choice(potions)
        return Item(
            name=name,
            description=desc,
            item_type=ItemType.CONSUMABLE,
            heal_amount=heal_amount
        )


def ai_spawn_enemy(
    location_name: str,
    player_level: int,
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy",
    distance: int = 0
) -> Enemy:
    """Spawn enemy using AI generation with fallback to templates.

    Args:
        location_name: Name of the location for context
        player_level: Player level for scaling
        ai_service: Optional AIService for AI generation
        theme: World theme for AI generation (default: "fantasy")
        distance: Manhattan distance from origin for difficulty scaling (default 0)

    Returns:
        Enemy instance (AI-generated if available, template otherwise)
        Stats are scaled by distance multiplier.
    """
    if ai_service is not None:
        try:
            enemy_data = ai_service.generate_enemy(
                theme=theme,
                location_name=location_name,
                player_level=player_level
            )

            # Try to generate ASCII art with AI, fallback to template
            try:
                ascii_art = ai_service.generate_ascii_art(
                    enemy_name=enemy_data["name"],
                    enemy_description=enemy_data["description"],
                    theme=theme
                )
            except Exception as art_error:
                logger.warning(f"AI ASCII art generation failed, using fallback: {art_error}")
                ascii_art = get_fallback_ascii_art(enemy_data["name"])

            # Apply distance multiplier to AI-generated stats
            multiplier = get_distance_multiplier(distance)
            scaled_health = int(enemy_data["health"] * multiplier)
            scaled_attack = int(enemy_data["attack_power"] * multiplier)
            scaled_defense = int(enemy_data["defense"] * multiplier)
            scaled_xp = int(enemy_data["xp_reward"] * multiplier)

            return Enemy(
                name=enemy_data["name"],
                health=scaled_health,
                max_health=scaled_health,
                attack_power=scaled_attack,
                defense=scaled_defense,
                xp_reward=scaled_xp,
                level=enemy_data["level"],
                description=enemy_data["description"],
                attack_flavor=enemy_data["attack_flavor"],
                ascii_art=ascii_art,
            )
        except Exception as e:
            logger.warning(f"AI enemy generation failed, using fallback: {e}")
            # Fall through to template-based generation

    # Fallback to template-based spawn (with distance scaling)
    return spawn_enemy(location_name, player_level, distance=distance)


def spawn_enemies(
    location_name: str,
    level: int,
    count: Optional[int] = None,
    location_category: Optional[str] = None,
    distance: int = 0
) -> list[Enemy]:
    """
    Spawn multiple enemies appropriate for the location and player level.

    Args:
        location_name: Name of the location
        level: Player level for scaling
        count: Optional explicit enemy count. If None, random 1-2 (level 1-3)
               or 1-3 (level 4+)
        location_category: Optional category from Location.category field
        distance: Manhattan distance from origin for difficulty scaling (default 0)

    Returns:
        List of Enemy instances with stats scaled by distance
    """
    if count is None:
        # Determine count based on level
        if level < 4:
            # Lower levels: 1-2 enemies
            count = random.randint(1, 2)
        else:
            # Higher levels: 1-3 enemies
            count = random.randint(1, 3)

    enemies = []
    for _ in range(count):
        enemy = spawn_enemy(location_name, level, location_category, distance)
        enemies.append(enemy)

    return enemies
