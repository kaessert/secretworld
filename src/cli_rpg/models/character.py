"""Character model for CLI RPG."""
from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.item import Item


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
    inventory: "Inventory" = field(init=False)
    gold: int = 0

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

        # Initialize inventory
        from cli_rpg.models.inventory import Inventory
        self.inventory = Inventory()

    def add_gold(self, amount: int) -> None:
        """Add gold to character.

        Args:
            amount: Amount of gold to add (must be non-negative)

        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Amount must be non-negative")
        self.gold += amount

    def remove_gold(self, amount: int) -> bool:
        """Remove gold from character.

        Args:
            amount: Amount of gold to remove (must be non-negative)

        Returns:
            True if successful, False if insufficient gold

        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Amount must be non-negative")
        if self.gold < amount:
            return False
        self.gold -= amount
        return True
    
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

    def get_attack_power(self) -> int:
        """Get total attack power including equipped weapon bonus.

        Returns:
            Strength plus weapon damage bonus
        """
        return self.strength + self.inventory.get_damage_bonus()

    def get_defense(self) -> int:
        """Get total defense including equipped armor bonus.

        Returns:
            Constitution plus armor defense bonus
        """
        return self.constitution + self.inventory.get_defense_bonus()

    def equip_item(self, item: "Item") -> bool:
        """Equip an item from inventory.

        Args:
            item: Item to equip (must be weapon or armor in inventory)

        Returns:
            True if equipped successfully, False otherwise
        """
        return self.inventory.equip(item)

    def use_item(self, item: "Item") -> Tuple[bool, str]:
        """Use an item from inventory.

        Args:
            item: Item to use (consumables only)

        Returns:
            Tuple of (success, message)
        """
        from cli_rpg.models.item import ItemType

        # Check if item is in inventory
        if item not in self.inventory.items:
            return (False, f"You don't have {item.name} in your inventory.")

        # Only consumables can be used
        if item.item_type != ItemType.CONSUMABLE:
            return (False, f"You can't use {item.name} - it's not a consumable item.")

        # Apply effect
        if item.heal_amount > 0:
            # Check if already at full health
            if self.health >= self.max_health:
                return (False, "You're already at full health!")
            old_health = self.health
            self.heal(item.heal_amount)
            healed = self.health - old_health
            self.inventory.remove_item(item)
            return (True, f"You used {item.name} and healed {healed} health!")

        # Generic consumable without heal effect
        self.inventory.remove_item(item)
        return (True, f"You used {item.name}.")

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
            "xp": self.xp,
            "inventory": self.inventory.to_dict(),
            "gold": self.gold
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """Deserialize character from dictionary.

        Args:
            data: Dictionary containing character attributes

        Returns:
            Character instance
        """
        from cli_rpg.models.inventory import Inventory

        # Cap stats for initial validation (stats may be > 20 from level-ups)
        # The 1-20 limit is for character creation, not saved game state
        capped_strength = min(data["strength"], cls.MAX_STAT)
        capped_dexterity = min(data["dexterity"], cls.MAX_STAT)
        capped_intelligence = min(data["intelligence"], cls.MAX_STAT)

        # Create character with capped stats to pass validation
        character = cls(
            name=data["name"],
            strength=capped_strength,
            dexterity=capped_dexterity,
            intelligence=capped_intelligence,
            level=data.get("level", 1),
        )

        # Restore actual stats from save (may be > 20 from level-ups)
        character.strength = data["strength"]
        character.dexterity = data["dexterity"]
        character.intelligence = data["intelligence"]

        # Recalculate derived stats based on actual strength
        character.max_health = cls.BASE_HEALTH + character.strength * cls.HEALTH_PER_STRENGTH
        character.constitution = character.strength

        # Override with saved health if provided (capped at max_health)
        if "health" in data:
            character.health = min(data["health"], character.max_health)

        # Restore XP
        if "xp" in data:
            character.xp = data["xp"]
        # Restore inventory (with backward compatibility)
        if "inventory" in data:
            character.inventory = Inventory.from_dict(data["inventory"])
        # Restore gold (with backward compatibility, defaults to 0)
        character.gold = data.get("gold", 0)
        return character
    
    def __str__(self) -> str:
        """String representation of character.
        
        Returns:
            Formatted string with character details
        """
        status = "Alive" if self.is_alive() else "Dead"
        return (
            f"{self.name} (Level {self.level}) - {status}\n"
            f"Health: {self.health}/{self.max_health} | Gold: {self.gold}\n"
            f"Strength: {self.strength} | Dexterity: {self.dexterity} | Intelligence: {self.intelligence}"
        )
