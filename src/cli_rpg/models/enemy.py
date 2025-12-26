"""Enemy model for combat encounters."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.status_effect import StatusEffect


class ElementType(Enum):
    """Element types for elemental damage system.

    Elements interact with each other according to weaknesses and resistances:
    - FIRE is strong vs ICE, resists FIRE
    - ICE is strong vs FIRE, resists ICE
    - POISON resists POISON
    - PHYSICAL is neutral to all
    """
    PHYSICAL = "physical"  # Default - no elemental affinity
    FIRE = "fire"          # Fire creatures, dragons, flame elementals
    ICE = "ice"            # Yetis, frost creatures, ice elementals
    POISON = "poison"      # Spiders, snakes, serpents, vipers


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
    bleed_chance: float = 0.0  # Chance (0.0-1.0) to apply bleed on attack
    bleed_damage: int = 0  # Damage per turn if bleed is applied
    bleed_duration: int = 0  # Duration of bleed in turns
    is_hallucination: bool = False  # True if this is a dread-induced hallucination
    element_type: ElementType = ElementType.PHYSICAL  # Elemental affinity for damage modifiers
    status_effects: List = field(default_factory=list)  # Active status effects on this enemy
    faction_affiliation: Optional[str] = None  # Faction this enemy belongs to (for reputation effects)

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
    
    def _get_stat_modifier(self, buff_type: str, debuff_type: str) -> float:
        """Calculate the total stat modifier from buffs and debuffs.

        Args:
            buff_type: Effect type for buffs (e.g., "buff_attack")
            debuff_type: Effect type for debuffs (e.g., "debuff_attack")

        Returns:
            Combined modifier (e.g., 1.25 for +25% buff, 0.75 for -25% debuff)
        """
        modifier = 1.0
        for effect in self.status_effects:
            if effect.effect_type == buff_type:
                modifier += effect.stat_modifier
            elif effect.effect_type == debuff_type:
                modifier -= effect.stat_modifier
        return modifier

    def calculate_damage(self) -> int:
        """
        Compute attack damage, including buff/debuff modifiers.

        Returns:
            Attack power value modified by attack buffs/debuffs
        """
        modifier = self._get_stat_modifier("buff_attack", "debuff_attack")
        return int(self.attack_power * modifier)

    def get_defense(self) -> int:
        """
        Get defense value, including buff/debuff modifiers.

        Returns:
            Defense value modified by defense buffs/debuffs
        """
        modifier = self._get_stat_modifier("buff_defense", "debuff_defense")
        return int(self.defense * modifier)

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
            "bleed_chance": self.bleed_chance,
            "bleed_damage": self.bleed_damage,
            "bleed_duration": self.bleed_duration,
            "is_hallucination": self.is_hallucination,
            "element_type": self.element_type.value,
            "status_effects": [e.to_dict() for e in self.status_effects],
            "faction_affiliation": self.faction_affiliation,
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

        # Deserialize element type with backward compatibility
        element_type_str = data.get("element_type", "physical")
        element_type = ElementType(element_type_str)

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
            bleed_chance=data.get("bleed_chance", 0.0),
            bleed_damage=data.get("bleed_damage", 0),
            bleed_duration=data.get("bleed_duration", 0),
            is_hallucination=data.get("is_hallucination", False),
            element_type=element_type,
            status_effects=status_effects,
            faction_affiliation=data.get("faction_affiliation"),
        )
