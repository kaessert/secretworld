"""Character model for CLI RPG."""
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Dict, List, Optional, Tuple, TYPE_CHECKING

from cli_rpg import colors
from cli_rpg.sound_effects import sound_level_up

from cli_rpg.models.dread import DreadMeter


class CharacterClass(Enum):
    """Character class enum (Spec: 5 classes with unique stat bonuses)."""

    WARRIOR = "Warrior"
    MAGE = "Mage"
    ROGUE = "Rogue"
    RANGER = "Ranger"
    CLERIC = "Cleric"


# Spec: CLASS_BONUSES dict maps each class to stat bonuses
# Includes CHA bonuses: Cleric +2, Rogue +1, others 0
# Includes PER bonuses: Rogue +2, Ranger +1, others 0
CLASS_BONUSES: Dict["CharacterClass", Dict[str, int]] = {
    CharacterClass.WARRIOR: {
        "strength": 3, "dexterity": 1, "intelligence": 0, "charisma": 0, "perception": 0
    },
    CharacterClass.MAGE: {
        "strength": 0, "dexterity": 1, "intelligence": 3, "charisma": 0, "perception": 0
    },
    CharacterClass.ROGUE: {
        "strength": 1, "dexterity": 3, "intelligence": 0, "charisma": 1, "perception": 2
    },
    CharacterClass.RANGER: {
        "strength": 1, "dexterity": 2, "intelligence": 1, "charisma": 0, "perception": 1
    },
    CharacterClass.CLERIC: {
        "strength": 1, "dexterity": 0, "intelligence": 2, "charisma": 2, "perception": 0
    },
}

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
        charisma: Charisma stat (1-20) - affects social skills and shop prices
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
    charisma: int = 10  # Default charisma for backward compatibility
    perception: int = 10  # Default perception for backward compatibility
    character_class: Optional[CharacterClass] = None
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
    look_counts: Dict[str, int] = field(default_factory=dict)
    dread_meter: DreadMeter = field(default_factory=DreadMeter)
    light_remaining: int = 0

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
            ("charisma", self.charisma),
            ("perception", self.perception),
            ("level", self.level)
        ]:
            if not isinstance(stat_value, int):
                raise ValueError(f"{stat_name} must be an integer")
            if stat_value < self.MIN_STAT:
                raise ValueError(f"{stat_name} must be at least {self.MIN_STAT}")
            if stat_name != "level" and stat_value > self.MAX_STAT:
                raise ValueError(f"{stat_name} must be at most {self.MAX_STAT}")

        # Apply class bonuses if a class is selected (Spec: unique starting stat bonuses)
        if self.character_class is not None:
            bonuses = CLASS_BONUSES[self.character_class]
            self.strength += bonuses["strength"]
            self.dexterity += bonuses["dexterity"]
            self.intelligence += bonuses["intelligence"]
            self.charisma += bonuses["charisma"]
            self.perception += bonuses.get("perception", 0)

        # Calculate derived stats (after bonuses applied)
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

    def get_attack_power(self) -> int:
        """Get total attack power including equipped weapon bonus and buffs/debuffs.

        Returns:
            Strength plus weapon damage bonus, modified by attack buffs/debuffs and dread
        """
        base_attack = self.strength + self.inventory.get_damage_bonus()
        modifier = self._get_stat_modifier("buff_attack", "debuff_attack")
        # Apply dread penalty (0.9 at 75%+ dread)
        dread_penalty = self.dread_meter.get_penalty()
        return int(base_attack * modifier * dread_penalty)

    def get_defense(self) -> int:
        """Get total defense including equipped armor bonus and buffs/debuffs.

        Returns:
            Constitution plus armor defense bonus, modified by defense buffs/debuffs
        """
        base_defense = self.constitution + self.inventory.get_defense_bonus()
        modifier = self._get_stat_modifier("buff_defense", "debuff_defense")
        return int(base_defense * modifier)

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

        # Handle light source items
        if item.light_duration > 0:
            had_light = self.light_remaining > 0
            self.use_light_source(item.light_duration)
            self.inventory.remove_item(item)
            if had_light:
                message = f"You add the {item.name} to your light. Your light will last longer."
            else:
                message = f"You light the {item.name}. It illuminates your surroundings."
            quest_messages = self.record_use(item.name)
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

    def is_stealthed(self) -> bool:
        """Check if character has an active stealth effect.

        Returns:
            True if character has a stealth effect, False otherwise.
        """
        return any(e.effect_type == "stealth" for e in self.status_effects)

    def consume_stealth(self) -> bool:
        """Remove stealth effect if present.

        Returns:
            True if stealth was removed, False if character wasn't stealthed.
        """
        for effect in self.status_effects:
            if effect.effect_type == "stealth":
                self.status_effects.remove(effect)
                return True
        return False

    def tick_status_effects(self) -> List[str]:
        """Process one turn of all status effects.

        Applies damage from DOT effects and removes expired effects.
        Stun effects are NOT ticked here - they are consumed when player acts.

        Returns:
            List of messages describing what happened
        """
        messages = []
        expired_effects = []

        for effect in self.status_effects:
            # Skip stun effects - they are consumed when player tries to act
            if effect.effect_type == "stun":
                continue

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

    def use_light_source(self, duration: int) -> None:
        """Activate or extend light source duration.

        Args:
            duration: Number of moves the light will last
        """
        self.light_remaining += duration

    def tick_light(self) -> Optional[str]:
        """Tick down light remaining. Returns message if light expires.

        Returns:
            Message if light expires, None otherwise
        """
        if self.light_remaining > 0:
            self.light_remaining -= 1
            if self.light_remaining == 0:
                return "Your light source fades into darkness..."
        return None

    def has_active_light(self) -> bool:
        """Check if character has an active light source.

        Returns:
            True if character has light_remaining > 0
        """
        return self.light_remaining > 0

    def record_look(self, location_name: str) -> int:
        """Record a look at a location and return the new count.

        Args:
            location_name: Name of the location being looked at

        Returns:
            The new look count for that location
        """
        self.look_counts[location_name] = self.look_counts.get(location_name, 0) + 1
        return self.look_counts[location_name]

    def get_look_count(self, location_name: str) -> int:
        """Get the number of times player has looked at a location.

        Args:
            location_name: Name of the location

        Returns:
            Number of looks at that location (0 if never looked)
        """
        return self.look_counts.get(location_name, 0)

    def reset_look_count(self, location_name: str) -> None:
        """Reset the look count for a location.

        Args:
            location_name: Name of the location to reset
        """
        self.look_counts.pop(location_name, None)

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
                    "ascii_art": enemy.ascii_art,
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

        # Play level up sound
        sound_level_up()

        # Increase stats (including charisma and perception)
        self.strength += 1
        self.dexterity += 1
        self.intelligence += 1
        self.charisma += 1
        self.perception += 1

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
                f"Stats increased: STR +1, DEX +1, INT +1, CHA +1, PER +1\n"
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
            "charisma": self.charisma,
            "perception": self.perception,
            "character_class": self.character_class.value if self.character_class else None,
            "level": self.level,
            "health": self.health,
            "max_health": self.max_health,
            "xp": self.xp,
            "inventory": self.inventory.to_dict(),
            "gold": self.gold,
            "quests": [quest.to_dict() for quest in self.quests],
            "bestiary": self.bestiary,
            "status_effects": [effect.to_dict() for effect in self.status_effects],
            "look_counts": self.look_counts,
            "dread_meter": self.dread_meter.to_dict(),
            "light_remaining": self.light_remaining,
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
        # Charisma defaults to 10 for backward compatibility with old saves
        capped_charisma = min(data.get("charisma", 10), cls.MAX_STAT)
        # Perception defaults to 10 for backward compatibility with old saves
        capped_perception = min(data.get("perception", 10), cls.MAX_STAT)

        # Create character with capped stats to pass validation
        # Note: We pass character_class=None here to avoid re-applying bonuses
        # (bonuses are already baked into the saved stats)
        character = cls(
            name=data["name"],
            strength=capped_strength,
            dexterity=capped_dexterity,
            intelligence=capped_intelligence,
            charisma=capped_charisma,
            perception=capped_perception,
            level=data.get("level", 1),
            character_class=None,  # Don't apply bonuses on load
        )

        # Restore character class from save (backward compat: defaults to None)
        class_value = data.get("character_class")
        if class_value:
            # Convert string value to CharacterClass enum
            for char_class in CharacterClass:
                if char_class.value == class_value:
                    character.character_class = char_class
                    break

        # Restore actual stats from save (may be > 20 from level-ups)
        character.strength = data["strength"]
        character.dexterity = data["dexterity"]
        character.intelligence = data["intelligence"]
        # Charisma defaults to 10 for backward compatibility
        character.charisma = data.get("charisma", 10)
        # Perception defaults to 10 for backward compatibility
        character.perception = data.get("perception", 10)

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
        # Restore look counts (with backward compatibility, defaults to empty dict)
        character.look_counts = data.get("look_counts", {})
        # Restore dread meter (with backward compatibility, defaults to 0)
        if "dread_meter" in data:
            character.dread_meter = DreadMeter.from_dict(data["dread_meter"])
        else:
            character.dread_meter = DreadMeter()
        # Restore light_remaining (with backward compatibility, defaults to 0)
        character.light_remaining = data.get("light_remaining", 0)
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

        # Include class in title line if present
        class_str = f" {self.character_class.value}" if self.character_class else ""

        return (
            f"{self.name}{class_str} (Level {self.level}) - {status}\n"
            f"{colors.stat_header('Health')}: {health_str} | "
            f"{colors.stat_header('Gold')}: {gold_str} | "
            f"{colors.stat_header('XP')}: {xp_str}\n"
            f"{colors.stat_header('Strength')}: {self.strength} | "
            f"{colors.stat_header('Dexterity')}: {self.dexterity} | "
            f"{colors.stat_header('Intelligence')}: {self.intelligence} | "
            f"{colors.stat_header('Charisma')}: {self.charisma} | "
            f"{colors.stat_header('Perception')}: {self.perception}"
        )
