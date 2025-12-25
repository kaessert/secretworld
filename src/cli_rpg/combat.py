"""Combat encounter system for CLI RPG."""

import logging
import random
from typing import Optional, Tuple, Union, TYPE_CHECKING
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.item import Item, ItemType
from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.ai_service import AIService

logger = logging.getLogger(__name__)


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
        enemy: Optional[Enemy] = None
    ):
        """
        Initialize combat encounter.

        Args:
            player: Player character
            enemies: List of enemies to fight (or single Enemy for backward compat)
            enemy: Single enemy to fight (backward compatibility keyword arg)

        Note: Either enemies or enemy must be provided. If both are provided,
        enemies takes precedence. If enemy is provided, it's wrapped in a list.
        Backward compatibility: CombatEncounter(player, enemy) works as before.
        """
        self.player = player

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
    
    def start(self) -> str:
        """
        Initialize combat and return intro message.

        Returns:
            Intro message describing the encounter (includes ASCII art if available)
        """
        self.is_active = True

        if len(self.enemies) == 1:
            intro = f"A wild {colors.enemy(self.enemies[0].name)} appears!"
            # Add ASCII art if available
            if self.enemies[0].ascii_art:
                intro += "\n" + self.enemies[0].ascii_art.strip()
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
        # Get target enemy
        enemy, error = self._get_target(target)
        if enemy is None:
            return False, error or "No target found."

        # Calculate damage: player attack power (strength + weapon bonus) - enemy defense, minimum 1
        dmg = max(1, self.player.get_attack_power() - enemy.defense)
        enemy.take_damage(dmg)

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
        self.defending = True
        message = "You brace yourself for the enemy's attack, taking a defensive stance!"
        return False, message

    def player_cast(self, target: str = "") -> Tuple[bool, str]:
        """
        Player casts a magic attack.

        Magic damage is based on intelligence and ignores enemy defense.
        Formula: intelligence * 1.5 (minimum 1)

        Args:
            target: Target enemy name (partial match). Empty = first living enemy.

        Returns:
            Tuple of (victory, message)
            - victory: True if ALL enemies defeated, False otherwise
            - message: Description of the spell cast
        """
        # Get target enemy
        enemy, error = self._get_target(target)
        if enemy is None:
            return False, error or "No target found."

        # Calculate magic damage: intelligence * 1.5, ignores defense
        dmg = max(1, int(self.player.intelligence * 1.5))
        enemy.take_damage(dmg)

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
            # Calculate damage: enemy attack - player defense (constitution + armor bonus), minimum 1
            base_damage = max(1, enemy.calculate_damage() - self.player.get_defense())

            # Apply defense reduction if player is defending (applies to all attacks this turn)
            if self.defending:
                dmg = max(1, base_damage // 2)  # Half damage when defending
                msg = (
                    f"{colors.enemy(enemy.name)} attacks! You block some of the damage, "
                    f"taking {colors.damage(str(dmg))} damage!"
                )
            else:
                dmg = base_damage
                # Use attack_flavor if available for more immersive combat
                if enemy.attack_flavor:
                    msg = (
                        f"{colors.enemy(enemy.name)} {enemy.attack_flavor}! "
                        f"You take {colors.damage(str(dmg))} damage!"
                    )
                else:
                    msg = f"{colors.enemy(enemy.name)} attacks you for {colors.damage(str(dmg))} damage!"

            self.player.take_damage(dmg)
            total_damage += dmg
            messages.append(msg)

        # Reset defensive stance after all attacks
        self.defending = False

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

        if victory:
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

            # Award gold based on sum of enemy levels
            total_level = sum(e.level for e in self.enemies)
            gold_reward = random.randint(5, 15) * total_level
            self.player.add_gold(gold_reward)
            messages.append(f"You earned {colors.gold(str(gold_reward) + ' gold')}!")

            # Generate and award loot from each enemy
            for enemy in self.enemies:
                loot = generate_loot(enemy, self.player.level)
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

        for enemy in self.enemies:
            status = "DEAD" if not enemy.is_alive() else f"{enemy.health}/{enemy.max_health} HP"
            lines.append(f"Enemy: {colors.enemy(enemy.name)} - {status}")

        return "\n".join(lines)


def generate_loot(enemy: Enemy, level: int) -> Optional[Item]:
    """Generate loot item dropped by defeated enemy.

    Args:
        enemy: The defeated enemy
        level: Player level for scaling loot stats

    Returns:
        Item if loot dropped, None otherwise (50% drop rate)
    """
    # 50% chance to drop loot
    if random.random() > 0.5:
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

    # Generate item based on type
    if item_type == ItemType.WEAPON:
        prefixes = ["Rusty", "Iron", "Steel", "Sharp", "Worn", "Old"]
        names = ["Sword", "Dagger", "Axe", "Mace", "Spear"]
        prefix = random.choice(prefixes)
        name = random.choice(names)
        damage_bonus = max(1, level + random.randint(1, 3))
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
        defense_bonus = max(1, level + random.randint(0, 2))
        return Item(
            name=f"{prefix} {name}",
            description=f"A {prefix.lower()} {name.lower()} from {enemy.name}",
            item_type=ItemType.ARMOR,
            defense_bonus=defense_bonus
        )

    elif item_type == ItemType.CONSUMABLE:
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
    location_category: Optional[str] = None
) -> Enemy:
    """
    Spawn an enemy appropriate for the location and player level.

    Args:
        location_name: Name of the location
        level: Player level for scaling
        location_category: Optional category from Location.category field.
                          When provided, takes precedence over location name matching.
                          Valid: town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village

    Returns:
        Enemy instance
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
    
    # Scale stats based on level
    base_health = 20 + (level * 10)
    base_attack = 3 + (level * 2)
    base_defense = 1 + level
    base_xp = 20 + (level * 10)

    # Get fallback ASCII art based on enemy name
    ascii_art = get_fallback_ascii_art(enemy_name)

    return Enemy(
        name=enemy_name,
        health=base_health,
        max_health=base_health,
        attack_power=base_attack,
        defense=base_defense,
        xp_reward=base_xp,
        level=level,
        ascii_art=ascii_art,
    )


def ai_spawn_enemy(
    location_name: str,
    player_level: int,
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy"
) -> Enemy:
    """Spawn enemy using AI generation with fallback to templates.

    Args:
        location_name: Name of the location for context
        player_level: Player level for scaling
        ai_service: Optional AIService for AI generation
        theme: World theme for AI generation (default: "fantasy")

    Returns:
        Enemy instance (AI-generated if available, template otherwise)
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

            return Enemy(
                name=enemy_data["name"],
                health=enemy_data["health"],
                max_health=enemy_data["health"],
                attack_power=enemy_data["attack_power"],
                defense=enemy_data["defense"],
                xp_reward=enemy_data["xp_reward"],
                level=enemy_data["level"],
                description=enemy_data["description"],
                attack_flavor=enemy_data["attack_flavor"],
                ascii_art=ascii_art,
            )
        except Exception as e:
            logger.warning(f"AI enemy generation failed, using fallback: {e}")
            # Fall through to template-based generation

    # Fallback to template-based spawn
    return spawn_enemy(location_name, player_level)


def spawn_enemies(
    location_name: str,
    level: int,
    count: Optional[int] = None,
    location_category: Optional[str] = None
) -> list[Enemy]:
    """
    Spawn multiple enemies appropriate for the location and player level.

    Args:
        location_name: Name of the location
        level: Player level for scaling
        count: Optional explicit enemy count. If None, random 1-2 (level 1-3)
               or 1-3 (level 4+)
        location_category: Optional category from Location.category field

    Returns:
        List of Enemy instances
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
        enemy = spawn_enemy(location_name, level, location_category)
        enemies.append(enemy)

    return enemies
