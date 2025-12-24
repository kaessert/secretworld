"""Combat encounter system for CLI RPG."""

import random
from typing import Tuple
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy


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
        # Calculate damage: player strength - enemy defense, minimum 1
        damage = max(1, self.player.strength - self.enemy.defense)
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
        # Calculate damage: enemy attack - player constitution, minimum 1
        base_damage = max(1, self.enemy.calculate_damage() - self.player.constitution)
        
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
        Resolve combat and award XP on victory.
        
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
