"""Combat encounter system for CLI RPG."""

import random
from typing import Optional, Tuple
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.item import Item, ItemType


class CombatEncounter:
    """Manages a combat encounter between player and enemy."""
    
    def __init__(self, player: Character, enemy: Enemy):
        """
        Initialize combat encounter.
        
        Args:
            player: Player character
            enemy: Enemy to fight
        """
        self.player = player
        self.enemy = enemy
        self.turn_count = 0
        self.is_active = False
        self.defending = False
    
    def start(self) -> str:
        """
        Initialize combat and return intro message.
        
        Returns:
            Intro message describing the encounter
        """
        self.is_active = True
        return f"A wild {self.enemy.name} appears! Combat has begun!"
    
    def player_attack(self) -> Tuple[bool, str]:
        """
        Player attacks enemy.

        Returns:
            Tuple of (victory, message)
            - victory: True if enemy defeated, False otherwise
            - message: Description of the attack
        """
        # Calculate damage: player attack power (strength + weapon bonus) - enemy defense, minimum 1
        damage = max(1, self.player.get_attack_power() - self.enemy.defense)
        self.enemy.take_damage(damage)
        
        message = f"You attack {self.enemy.name} for {damage} damage!"
        
        if not self.enemy.is_alive():
            message += f"\n{self.enemy.name} has been defeated! Victory!"
            return True, message
        
        message += f"\n{self.enemy.name} has {self.enemy.health}/{self.enemy.max_health} HP remaining."
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

    def player_cast(self) -> Tuple[bool, str]:
        """
        Player casts a magic attack.

        Magic damage is based on intelligence and ignores enemy defense.
        Formula: intelligence * 1.5 (minimum 1)

        Returns:
            Tuple of (victory, message)
            - victory: True if enemy defeated, False otherwise
            - message: Description of the spell cast
        """
        # Calculate magic damage: intelligence * 1.5, ignores defense
        damage = max(1, int(self.player.intelligence * 1.5))
        self.enemy.take_damage(damage)

        message = f"You cast a spell at {self.enemy.name} for {damage} magic damage!"

        if not self.enemy.is_alive():
            message += f"\n{self.enemy.name} has been defeated! Victory!"
            return True, message

        message += f"\n{self.enemy.name} has {self.enemy.health}/{self.enemy.max_health} HP remaining."
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
        Enemy attacks player.

        Returns:
            Message describing the enemy's action
        """
        # Calculate damage: enemy attack - player defense (constitution + armor bonus), minimum 1
        base_damage = max(1, self.enemy.calculate_damage() - self.player.get_defense())
        
        # Apply defense reduction if player is defending
        if self.defending:
            damage = max(1, base_damage // 2)  # Half damage when defending
            message = f"{self.enemy.name} attacks! You block some of the damage, taking {damage} damage!"
            self.defending = False  # Reset defensive stance
        else:
            damage = base_damage
            message = f"{self.enemy.name} attacks you for {damage} damage!"
        
        self.player.take_damage(damage)
        message += f"\nYou have {self.player.health}/{self.player.max_health} HP remaining."
        
        return message
    
    def end_combat(self, victory: bool) -> str:
        """
        Resolve combat and award XP and loot on victory.

        Args:
            victory: True if player won, False if player lost

        Returns:
            Message describing combat resolution
        """
        self.is_active = False

        if victory:
            messages = [f"Victory! You defeated {self.enemy.name}!"]
            xp_messages = self.player.gain_xp(self.enemy.xp_reward)
            messages.extend(xp_messages)

            # Generate and award loot
            loot = generate_loot(self.enemy, self.player.level)
            if loot is not None:
                if self.player.inventory.add_item(loot):
                    messages.append(f"You found: {loot.name}!")
                else:
                    messages.append(f"You found {loot.name} but your inventory is full!")

            return "\n".join(messages)
        else:
            return f"You have been defeated by {self.enemy.name}..."
    
    def get_status(self) -> str:
        """
        Display current combat status.
        
        Returns:
            Status string showing health of both combatants
        """
        return (
            f"=== COMBAT ===\n"
            f"Player: {self.player.name} - {self.player.health}/{self.player.max_health} HP\n"
            f"Enemy: {self.enemy.name} - {self.enemy.health}/{self.enemy.max_health} HP"
        )


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
    cumulative = 0
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


def spawn_enemy(location_name: str, level: int) -> Enemy:
    """
    Spawn an enemy appropriate for the location and player level.
    
    Args:
        location_name: Name of the location
        level: Player level for scaling
        
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
    
    # Determine location type from location name
    location_type = "default"
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
    
    return Enemy(
        name=enemy_name,
        health=base_health,
        max_health=base_health,
        attack_power=base_attack,
        defense=base_defense,
        xp_reward=base_xp
    )
