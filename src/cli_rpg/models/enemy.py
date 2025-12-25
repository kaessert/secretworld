"""Enemy model for combat encounters."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Enemy:
    """Represents an enemy/NPC in combat."""

    name: str
    health: int
    max_health: int
    attack_power: int
    defense: int
    xp_reward: int
    level: int = 1
    description: str = ""  # e.g., "A snarling beast with glowing red eyes"
    attack_flavor: str = ""  # e.g., "lunges with razor-sharp claws"
    ascii_art: str = ""  # ASCII art representation of the enemy
    is_boss: bool = False  # True if this is a boss enemy
    poison_chance: float = 0.0  # Chance (0.0-1.0) to apply poison on attack
    poison_damage: int = 0  # Damage per turn if poison is applied
    poison_duration: int = 0  # Duration of poison in turns
    
    def __post_init__(self):
        """Validate enemy attributes."""
        if self.health < 0:
            raise ValueError("health cannot be negative")
        if self.max_health <= 0:
            raise ValueError("max_health must be positive")
        if self.health > self.max_health:
            raise ValueError("health cannot exceed max_health")
        if self.attack_power < 0:
            raise ValueError("attack_power cannot be negative")
        if self.defense < 0:
            raise ValueError("defense cannot be negative")
        if self.xp_reward < 0:
            raise ValueError("xp_reward cannot be negative")
    
    def take_damage(self, amount: int) -> None:
        """
        Reduce health by amount, floored at 0.
        
        Args:
            amount: Damage to take
        """
        self.health = max(0, self.health - amount)
    
    def is_alive(self) -> bool:
        """
        Check if enemy is still alive.
        
        Returns:
            True if health > 0, False otherwise
        """
        return self.health > 0
    
    def calculate_damage(self) -> int:
        """
        Compute attack damage.
        
        Returns:
            Attack power value
        """
        return self.attack_power
    
    def to_dict(self) -> Dict:
        """
        Serialize enemy to dictionary.

        Returns:
            Dictionary representation of enemy
        """
        return {
            "name": self.name,
            "health": self.health,
            "max_health": self.max_health,
            "attack_power": self.attack_power,
            "defense": self.defense,
            "xp_reward": self.xp_reward,
            "level": self.level,
            "description": self.description,
            "attack_flavor": self.attack_flavor,
            "ascii_art": self.ascii_art,
            "is_boss": self.is_boss,
            "poison_chance": self.poison_chance,
            "poison_damage": self.poison_damage,
            "poison_duration": self.poison_duration,
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Enemy':
        """
        Deserialize enemy from dictionary.

        Args:
            data: Dictionary containing enemy data

        Returns:
            Enemy instance
        """
        return Enemy(
            name=data["name"],
            health=data["health"],
            max_health=data["max_health"],
            attack_power=data["attack_power"],
            defense=data["defense"],
            xp_reward=data["xp_reward"],
            level=data.get("level", 1),
            description=data.get("description", ""),
            attack_flavor=data.get("attack_flavor", ""),
            ascii_art=data.get("ascii_art", ""),
            is_boss=data.get("is_boss", False),
            poison_chance=data.get("poison_chance", 0.0),
            poison_damage=data.get("poison_damage", 0),
            poison_duration=data.get("poison_duration", 0),
        )
