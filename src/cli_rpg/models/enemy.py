"""Enemy model for combat encounters."""

from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.status_effect import StatusEffect


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
    burn_chance: float = 0.0  # Chance (0.0-1.0) to apply burn on attack
    burn_damage: int = 0  # Damage per turn if burn is applied
    burn_duration: int = 0  # Duration of burn in turns
    stun_chance: float = 0.0  # Chance (0.0-1.0) to apply stun on attack
    stun_duration: int = 0  # Duration of stun in turns
    freeze_chance: float = 0.0  # Chance (0.0-1.0) to apply freeze on attack
    freeze_duration: int = 0  # Duration of freeze in turns
    status_effects: List = field(default_factory=list)  # Active status effects on this enemy

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

    def apply_status_effect(self, effect: "StatusEffect") -> None:
        """Apply a status effect to this enemy.

        Args:
            effect: The status effect to apply
        """
        self.status_effects.append(effect)

    def tick_status_effects(self) -> List[str]:
        """Process all status effects for one turn.

        Returns:
            List of messages describing what happened
        """
        messages = []
        expired_effects = []

        for effect in self.status_effects:
            damage, expired = effect.tick()
            if damage > 0:
                self.take_damage(damage)
                messages.append(f"{self.name} takes {damage} damage from {effect.name}!")
            if expired:
                expired_effects.append(effect)
                messages.append(f"{effect.name} has worn off from {self.name}.")

        # Remove expired effects
        for effect in expired_effects:
            self.status_effects.remove(effect)

        return messages

    def clear_status_effects(self) -> None:
        """Remove all status effects from this enemy."""
        self.status_effects.clear()

    def has_effect_type(self, effect_type: str) -> bool:
        """Check if enemy has a specific effect type.

        Args:
            effect_type: The effect type to check for (e.g., "freeze", "stun")

        Returns:
            True if enemy has an effect of that type, False otherwise
        """
        return any(e.effect_type == effect_type for e in self.status_effects)

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
            "burn_chance": self.burn_chance,
            "burn_damage": self.burn_damage,
            "burn_duration": self.burn_duration,
            "stun_chance": self.stun_chance,
            "stun_duration": self.stun_duration,
            "freeze_chance": self.freeze_chance,
            "freeze_duration": self.freeze_duration,
            "status_effects": [e.to_dict() for e in self.status_effects],
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
        from cli_rpg.models.status_effect import StatusEffect

        # Deserialize status effects
        status_effects = [
            StatusEffect.from_dict(e) for e in data.get("status_effects", [])
        ]

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
            burn_chance=data.get("burn_chance", 0.0),
            burn_damage=data.get("burn_damage", 0),
            burn_duration=data.get("burn_duration", 0),
            stun_chance=data.get("stun_chance", 0.0),
            stun_duration=data.get("stun_duration", 0),
            freeze_chance=data.get("freeze_chance", 0.0),
            freeze_duration=data.get("freeze_duration", 0),
            status_effects=status_effects,
        )
