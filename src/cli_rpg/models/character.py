"""Character model for CLI RPG."""
from dataclasses import dataclass, field
from typing import ClassVar, List


@dataclass
class Character:
    """Represents a player character in the RPG.
    
    Attributes:
        name: Character's name (2-30 characters)
        strength: Strength stat (1-20)
        dexterity: Dexterity stat (1-20)
        intelligence: Intelligence stat (1-20)
        level: Character level (default 1)
        health: Current health points
        max_health: Maximum health points (calculated from strength)
        xp: Current experience points
        xp_to_next_level: XP needed for next level
        constitution: Constitution stat for damage reduction (derived from strength)
    """
    
    MIN_STAT: ClassVar[int] = 1
    MAX_STAT: ClassVar[int] = 20
    MIN_NAME_LENGTH: ClassVar[int] = 2
    MAX_NAME_LENGTH: ClassVar[int] = 30
    BASE_HEALTH: ClassVar[int] = 100
    HEALTH_PER_STRENGTH: ClassVar[int] = 5
    
    name: str
    strength: int
    dexterity: int
    intelligence: int
    level: int = 1
    health: int = field(init=False)
    max_health: int = field(init=False)
    xp: int = 0
    xp_to_next_level: int = field(init=False)
    constitution: int = field(init=False)
    
    def __post_init__(self):
        """Validate attributes and calculate derived stats."""
        # Validate name
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")
        if len(self.name) < self.MIN_NAME_LENGTH:
            raise ValueError(f"Name must be at least {self.MIN_NAME_LENGTH} characters")
        if len(self.name) > self.MAX_NAME_LENGTH:
            raise ValueError(f"Name must be at most {self.MAX_NAME_LENGTH} characters")
        
        # Validate stats
        for stat_name, stat_value in [
            ("strength", self.strength),
            ("dexterity", self.dexterity),
            ("intelligence", self.intelligence),
            ("level", self.level)
        ]:
            if not isinstance(stat_value, int):
                raise ValueError(f"{stat_name} must be an integer")
            if stat_value < self.MIN_STAT:
                raise ValueError(f"{stat_name} must be at least {self.MIN_STAT}")
            if stat_name != "level" and stat_value > self.MAX_STAT:
                raise ValueError(f"{stat_name} must be at most {self.MAX_STAT}")
        
        # Calculate derived stats
        self.max_health = self.BASE_HEALTH + self.strength * self.HEALTH_PER_STRENGTH
        self.health = self.max_health
        self.xp_to_next_level = self.level * 100
        self.constitution = self.strength  # Constitution based on strength
    
    def take_damage(self, amount: int) -> None:
        """Reduce health by damage amount, minimum 0.
        
        Args:
            amount: Amount of damage to take
        """
        self.health = max(0, self.health - amount)
    
    def heal(self, amount: int) -> None:
        """Increase health by heal amount, maximum max_health.
        
        Args:
            amount: Amount of health to restore
        """
        self.health = min(self.max_health, self.health + amount)
    
    def is_alive(self) -> bool:
        """Check if character is alive.
        
        Returns:
            True if health > 0, False otherwise
        """
        return self.health > 0
    
    def gain_xp(self, amount: int) -> List[str]:
        """
        Add XP and handle level-ups.
        
        Args:
            amount: Amount of XP to gain
            
        Returns:
            List of messages describing XP gain and any level-ups
        """
        messages = [f"Gained {amount} XP!"]
        self.xp += amount
        
        # Check for level-ups
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            level_up_message = self.level_up()
            messages.append(level_up_message)
        
        return messages
    
    def level_up(self) -> str:
        """
        Increase level and boost stats.
        
        Returns:
            Message describing level up
        """
        self.level += 1
        
        # Increase stats
        self.strength += 1
        self.dexterity += 1
        self.intelligence += 1
        
        # Recalculate derived stats
        old_max_health = self.max_health
        self.max_health = self.BASE_HEALTH + self.strength * self.HEALTH_PER_STRENGTH
        self.constitution = self.strength
        
        # Restore health to new maximum
        self.health = self.max_health
        
        # Update XP threshold
        self.xp_to_next_level = self.level * 100
        
        health_increase = self.max_health - old_max_health
        return (f"Level Up! You are now level {self.level}!\n"
                f"Stats increased: STR +1, DEX +1, INT +1\n"
                f"Max HP increased by {health_increase}! Health fully restored!")
    
    def to_dict(self) -> dict:
        """Serialize character to dictionary.
        
        Returns:
            Dictionary containing all character attributes
        """
        return {
            "name": self.name,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "intelligence": self.intelligence,
            "level": self.level,
            "health": self.health,
            "max_health": self.max_health,
            "xp": self.xp
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """Deserialize character from dictionary.
        
        Args:
            data: Dictionary containing character attributes
            
        Returns:
            Character instance
        """
        # Create character with base stats
        character = cls(
            name=data["name"],
            strength=data["strength"],
            dexterity=data["dexterity"],
            intelligence=data["intelligence"],
            level=data.get("level", 1)
        )
        # Override health if different from calculated max
        if "health" in data:
            character.health = data["health"]
        # Restore XP
        if "xp" in data:
            character.xp = data["xp"]
        return character
    
    def __str__(self) -> str:
        """String representation of character.
        
        Returns:
            Formatted string with character details
        """
        status = "Alive" if self.is_alive() else "Dead"
        return (
            f"{self.name} (Level {self.level}) - {status}\n"
            f"Health: {self.health}/{self.max_health}\n"
            f"Strength: {self.strength} | Dexterity: {self.dexterity} | Intelligence: {self.intelligence}"
        )
