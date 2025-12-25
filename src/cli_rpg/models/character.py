"""Character model for CLI RPG."""
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Tuple, TYPE_CHECKING

from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.models.item import Item
    from cli_rpg.models.inventory import Inventory
    from cli_rpg.models.quest import Quest
    from cli_rpg.models.enemy import Enemy
    from cli_rpg.models.status_effect import StatusEffect


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
    quests: List["Quest"] = field(default_factory=list)
    bestiary: Dict[str, dict] = field(default_factory=dict)
    status_effects: List["StatusEffect"] = field(default_factory=list)

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
            # Record item use for quest progress
            quest_messages = self.record_use(item.name)
            message = f"You used {item.name} and healed {healed} health!"
            if quest_messages:
                message += "\n" + "\n".join(quest_messages)
            return (True, message)

        # Generic consumable without heal effect
        self.inventory.remove_item(item)
        # Record item use for quest progress
        quest_messages = self.record_use(item.name)
        message = f"You used {item.name}."
        if quest_messages:
            message += "\n" + "\n".join(quest_messages)
        return (True, message)

    def has_quest(self, quest_name: str) -> bool:
        """Check if character has a quest by name.

        Args:
            quest_name: Name of the quest to check for (case-insensitive)

        Returns:
            True if character has the quest, False otherwise
        """
        return any(q.name.lower() == quest_name.lower() for q in self.quests)

    def record_kill(self, enemy_name: str) -> List[str]:
        """Record an enemy kill for quest progress.

        Args:
            enemy_name: Name of the defeated enemy

        Returns:
            List of notification messages for quest progress/completion
        """
        from cli_rpg.models.quest import QuestStatus, ObjectiveType

        messages = []
        for quest in self.quests:
            if (
                quest.status == QuestStatus.ACTIVE
                and quest.objective_type == ObjectiveType.KILL
                and quest.target.lower() == enemy_name.lower()
            ):
                completed = quest.progress()
                if completed:
                    quest.status = QuestStatus.READY_TO_TURN_IN
                    if quest.quest_giver:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            f"Return to {quest.quest_giver} to claim your reward."
                        )
                    else:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            "Return to the quest giver to claim your reward."
                        )
                else:
                    messages.append(
                        f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                    )
        return messages

    def record_collection(self, item_name: str) -> List[str]:
        """Record an item collection for quest progress.

        Args:
            item_name: Name of the collected item

        Returns:
            List of notification messages for quest progress/completion
        """
        from cli_rpg.models.quest import QuestStatus, ObjectiveType

        messages = []
        for quest in self.quests:
            if (
                quest.status == QuestStatus.ACTIVE
                and quest.objective_type == ObjectiveType.COLLECT
                and quest.target.lower() == item_name.lower()
            ):
                completed = quest.progress()
                if completed:
                    quest.status = QuestStatus.READY_TO_TURN_IN
                    if quest.quest_giver:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            f"Return to {quest.quest_giver} to claim your reward."
                        )
                    else:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            "Return to the quest giver to claim your reward."
                        )
                else:
                    messages.append(
                        f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                    )
        return messages

    def record_drop(self, enemy_name: str, item_name: str) -> List[str]:
        """Record an item drop from an enemy for DROP quest progress.

        Args:
            enemy_name: Name of the defeated enemy
            item_name: Name of the dropped item

        Returns:
            List of notification messages for quest progress/completion
        """
        from cli_rpg.models.quest import QuestStatus, ObjectiveType

        messages = []
        for quest in self.quests:
            if (
                quest.status == QuestStatus.ACTIVE
                and quest.objective_type == ObjectiveType.DROP
                and quest.target.lower() == enemy_name.lower()
                and quest.drop_item
                and quest.drop_item.lower() == item_name.lower()
            ):
                completed = quest.progress()
                if completed:
                    quest.status = QuestStatus.READY_TO_TURN_IN
                    if quest.quest_giver:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            f"Return to {quest.quest_giver} to claim your reward."
                        )
                    else:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            "Return to the quest giver to claim your reward."
                        )
                else:
                    messages.append(
                        f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                    )
        return messages

    def record_explore(self, location_name: str) -> List[str]:
        """Record exploring a location for quest progress.

        Args:
            location_name: Name of the explored location

        Returns:
            List of notification messages for quest progress/completion
        """
        from cli_rpg.models.quest import QuestStatus, ObjectiveType

        messages = []
        for quest in self.quests:
            if (
                quest.status == QuestStatus.ACTIVE
                and quest.objective_type == ObjectiveType.EXPLORE
                and quest.target.lower() == location_name.lower()
            ):
                completed = quest.progress()
                if completed:
                    quest.status = QuestStatus.READY_TO_TURN_IN
                    if quest.quest_giver:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            f"Return to {quest.quest_giver} to claim your reward."
                        )
                    else:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            "Return to the quest giver to claim your reward."
                        )
                else:
                    messages.append(
                        f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                    )
        return messages

    def record_talk(self, npc_name: str) -> List[str]:
        """Record talking to an NPC for quest progress.

        Args:
            npc_name: Name of the NPC spoken to

        Returns:
            List of notification messages for quest progress/completion
        """
        from cli_rpg.models.quest import QuestStatus, ObjectiveType

        messages = []
        for quest in self.quests:
            if (
                quest.status == QuestStatus.ACTIVE
                and quest.objective_type == ObjectiveType.TALK
                and quest.target.lower() == npc_name.lower()
            ):
                completed = quest.progress()
                if completed:
                    quest.status = QuestStatus.READY_TO_TURN_IN
                    if quest.quest_giver:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            f"Return to {quest.quest_giver} to claim your reward."
                        )
                    else:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            "Return to the quest giver to claim your reward."
                        )
                else:
                    messages.append(
                        f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                    )
        return messages

    def record_use(self, item_name: str) -> List[str]:
        """Record using an item for quest progress.

        Args:
            item_name: Name of the item used

        Returns:
            List of notification messages for quest progress/completion
        """
        from cli_rpg.models.quest import QuestStatus, ObjectiveType

        messages = []
        for quest in self.quests:
            if (
                quest.status == QuestStatus.ACTIVE
                and quest.objective_type == ObjectiveType.USE
                and quest.target.lower() == item_name.lower()
            ):
                completed = quest.progress()
                if completed:
                    quest.status = QuestStatus.READY_TO_TURN_IN
                    if quest.quest_giver:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            f"Return to {quest.quest_giver} to claim your reward."
                        )
                    else:
                        messages.append(
                            f"Quest objectives complete: {quest.name}! "
                            "Return to the quest giver to claim your reward."
                        )
                else:
                    messages.append(
                        f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                    )
        return messages

    def abandon_quest(self, quest_name: str) -> Tuple[bool, str]:
        """Abandon an active quest by name.

        Args:
            quest_name: Name or partial name of the quest to abandon (case-insensitive)

        Returns:
            Tuple of (success, message) - success is True if quest was abandoned
        """
        from cli_rpg.models.quest import QuestStatus

        quest_name_lower = quest_name.lower()

        # Find matching quest by partial name match
        matching_quest = None
        for q in self.quests:
            if quest_name_lower in q.name.lower():
                matching_quest = q
                break

        if matching_quest is None:
            return (False, f"No quest found matching '{quest_name}'.")

        # Only allow abandoning ACTIVE quests
        if matching_quest.status != QuestStatus.ACTIVE:
            status_name = matching_quest.status.name.replace("_", " ").title()
            return (
                False,
                f"Can't abandon '{matching_quest.name}' - "
                f"only active quests can be abandoned (current status: {status_name})."
            )

        # Remove quest from list
        self.quests.remove(matching_quest)
        return (True, f"Quest abandoned: {matching_quest.name}")

    def apply_status_effect(self, effect: "StatusEffect") -> None:
        """Apply a status effect to the character.

        Args:
            effect: StatusEffect to apply
        """
        self.status_effects.append(effect)

    def tick_status_effects(self) -> List[str]:
        """Process one turn of all status effects.

        Applies damage from DOT effects and removes expired effects.

        Returns:
            List of messages describing what happened
        """
        messages = []
        expired_effects = []

        for effect in self.status_effects:
            damage, expired = effect.tick()

            if damage > 0:
                self.take_damage(damage)
                messages.append(f"{effect.name} deals {damage} damage!")

            if expired:
                expired_effects.append(effect)
                messages.append(f"{effect.name} has worn off.")

        # Remove expired effects
        for effect in expired_effects:
            self.status_effects.remove(effect)

        return messages

    def clear_status_effects(self) -> None:
        """Clear all status effects from the character.

        Called when combat ends.
        """
        self.status_effects.clear()

    def record_enemy_defeat(self, enemy: "Enemy") -> None:
        """Record a defeated enemy in the bestiary.

        Stores enemy data on first defeat and increments kill count on subsequent defeats.

        Args:
            enemy: The defeated enemy to record
        """
        key = enemy.name.lower()

        if key in self.bestiary:
            # Increment count for existing enemy
            self.bestiary[key]["count"] += 1
        else:
            # Store first-seen enemy data
            self.bestiary[key] = {
                "count": 1,
                "enemy_data": {
                    "name": enemy.name,
                    "level": enemy.level,
                    "attack_power": enemy.attack_power,
                    "defense": enemy.defense,
                    "description": enemy.description,
                    "is_boss": enemy.is_boss,
                }
            }

    def claim_quest_rewards(self, quest: "Quest") -> List[str]:
        """Claim rewards from a quest ready to turn in.

        Args:
            quest: The quest to claim rewards from (must be READY_TO_TURN_IN)

        Returns:
            List of reward notification messages

        Raises:
            ValueError: If quest is not in READY_TO_TURN_IN status
        """
        from cli_rpg.models.quest import QuestStatus
        from cli_rpg.models.item import Item, ItemType

        if quest.status != QuestStatus.READY_TO_TURN_IN:
            raise ValueError("Quest must be ready to turn in to claim rewards")

        messages = []

        # Grant gold reward
        if quest.gold_reward > 0:
            self.add_gold(quest.gold_reward)
            messages.append(f"Received {quest.gold_reward} gold!")

        # Grant XP reward
        if quest.xp_reward > 0:
            xp_messages = self.gain_xp(quest.xp_reward)
            messages.extend(xp_messages)

        # Grant item rewards
        for item_name in quest.item_rewards:
            # Create a basic misc item with the given name
            item = Item(
                name=item_name,
                description=f"A reward from the quest '{quest.name}'",
                item_type=ItemType.MISC,
            )
            self.inventory.add_item(item)
            messages.append(f"Received item: {item_name}!")

        return messages

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
            "gold": self.gold,
            "quests": [quest.to_dict() for quest in self.quests],
            "bestiary": self.bestiary,
            "status_effects": [effect.to_dict() for effect in self.status_effects],
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
        # Restore quests (with backward compatibility, defaults to empty list)
        if "quests" in data:
            from cli_rpg.models.quest import Quest
            character.quests = [Quest.from_dict(q) for q in data["quests"]]
        # Restore bestiary (with backward compatibility, defaults to empty dict)
        character.bestiary = data.get("bestiary", {})
        # Restore status effects (with backward compatibility, defaults to empty list)
        if "status_effects" in data:
            from cli_rpg.models.status_effect import StatusEffect
            character.status_effects = [
                StatusEffect.from_dict(e) for e in data["status_effects"]
            ]
        return character
    
    def __str__(self) -> str:
        """String representation of character.

        Returns:
            Formatted string with character details
        """
        status = colors.heal("Alive") if self.is_alive() else colors.damage("Dead")
        gold_str = colors.gold(str(self.gold))

        # Color health based on percentage
        health_pct = self.health / self.max_health if self.max_health > 0 else 0
        if health_pct > 0.5:
            health_str = colors.heal(f"{self.health}/{self.max_health}")
        elif health_pct > 0.25:
            health_str = colors.gold(f"{self.health}/{self.max_health}")
        else:
            health_str = colors.damage(f"{self.health}/{self.max_health}")

        xp_str = colors.location(f"{self.xp}/{self.xp_to_next_level}")

        return (
            f"{self.name} (Level {self.level}) - {status}\n"
            f"{colors.stat_header('Health')}: {health_str} | "
            f"{colors.stat_header('Gold')}: {gold_str} | "
            f"{colors.stat_header('XP')}: {xp_str}\n"
            f"{colors.stat_header('Strength')}: {self.strength} | "
            f"{colors.stat_header('Dexterity')}: {self.dexterity} | "
            f"{colors.stat_header('Intelligence')}: {self.intelligence}"
        )
