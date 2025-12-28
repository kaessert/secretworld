"""HumanLikeAgent - Agent with personality, class behaviors, and memory.

Extends the base Agent class to integrate:
- Personality traits that modify decision thresholds
- Class-specific combat and exploration commands
- Memory system for learning from experience
- Environmental awareness (time, weather, tiredness)
"""

from typing import Optional

from scripts.ai_agent import Agent, AgentGoal
from scripts.agent import (
    PersonalityType,
    PersonalityTraits,
    CharacterClassName,
    ClassBehavior,
    AgentMemory,
    get_personality_traits,
    get_class_behavior,
)
from scripts.state_parser import AgentState


class HumanLikeAgent(Agent):
    """Agent with personality, class behaviors, and memory for human-like play.

    Extends the base Agent with:
    - Personality traits that modify flee thresholds, social engagement, etc.
    - Class-specific combat commands (bash, cast, sneak, smite, etc.)
    - Memory of past failures, dangerous enemies, and NPC interactions
    - Environmental awareness affecting decision-making
    """

    def __init__(
        self,
        personality: PersonalityType = PersonalityType.CAUTIOUS_EXPLORER,
        character_class: CharacterClassName = CharacterClassName.WARRIOR,
        verbose: bool = False,
    ):
        """Initialize HumanLikeAgent.

        Args:
            personality: Personality type preset (default: CAUTIOUS_EXPLORER)
            character_class: Character class for behavior (default: WARRIOR)
            verbose: If True, print decision reasoning
        """
        super().__init__(verbose=verbose)

        # Personality system
        self.personality_type = personality
        self.traits = get_personality_traits(personality)

        # Class behavior system
        self.character_class = character_class
        self.class_behavior = get_class_behavior(character_class)

        # Memory system
        self.memory = AgentMemory()

        # Scale max_sub_location_moves by exploration_drive
        # Higher exploration drive = more willing to explore deeply
        base_moves = 50
        self.max_sub_location_moves = int(base_moves * (0.5 + self.traits.exploration_drive))

    def _combat_decision(self, state: AgentState) -> str:
        """Make combat decision incorporating class behavior and personality.

        Priority order:
        1. Check for combat end conditions
        2. Flee if conditions met (modified by personality and memory)
        3. Use class-specific combat command if available
        4. Use healing if needed
        5. Default to attack

        Args:
            state: Current game state

        Returns:
            Combat command
        """
        hp_pct = state.health_percent

        # Check if combat has ended (from parent class logic)
        narrative_lower = state.last_narrative.lower()
        combat_ended_indicators = [
            "defeated", "slain", "you killed", "you have slain",
            "fled successfully", "you escaped", "combat ends",
            "victory", "enemy fell", "you won",
        ]
        if any(indicator in narrative_lower for indicator in combat_ended_indicators):
            self._reset_combat_state(state)
            if self.verbose:
                print("[AGENT] Combat ended, returning to exploration")
            self.needs_look = True
            self.last_command = "look"
            return "look"

        # Check if enemy health is 0 (we won)
        if state.enemy_health <= 0 and state.enemy:
            self._reset_combat_state(state)
            if self.verbose:
                print("[AGENT] Enemy defeated, returning to exploration")
            self.needs_look = True
            self.last_command = "look"
            return "look"

        # === FLEE DECISION ===
        # Check if we should flee based on:
        # 1. Memory of dangerous enemies
        # 2. Class-specific flee threshold
        # 3. Personality risk tolerance
        # 4. Environmental factors (night time)

        # Check memory for dangerous enemies
        if self.memory.is_enemy_dangerous(state.enemy):
            if self.verbose:
                print(f"[AGENT] Enemy {state.enemy} killed us before - fleeing!")
            self.last_command = "flee"
            return "flee"

        # Calculate effective flee threshold
        base_threshold = self.class_behavior.config.flee_health_threshold

        # Personality modifies threshold: high risk_tolerance = lower flee threshold
        # risk_tolerance 0.2 -> +0.1 threshold (flee sooner)
        # risk_tolerance 0.9 -> -0.05 threshold (flee later)
        personality_modifier = (0.5 - self.traits.risk_tolerance) * 0.15
        effective_threshold = base_threshold + personality_modifier

        # Night time increases caution (add 0.1 to threshold)
        if state.is_night():
            effective_threshold += 0.10

        # Flee if below threshold
        if hp_pct < effective_threshold:
            if self.verbose:
                print(f"[AGENT] Fleeing - HP {hp_pct:.0%} < threshold {effective_threshold:.0%}")
            self.last_command = "flee"
            return "flee"

        # Check class-specific flee suggestion
        if self.class_behavior.should_flee(state, self.memory):
            if self.verbose:
                print("[AGENT] Class behavior suggests fleeing")
            self.last_command = "flee"
            return "flee"

        # === CLASS-SPECIFIC COMBAT ===
        class_command = self.class_behavior.get_combat_command(state, self.memory)
        if class_command:
            if self.verbose:
                print(f"[AGENT] Using class command: {class_command}")
            self.last_command = class_command
            return class_command

        # === HEALING ===
        heal_threshold = self.class_behavior.config.heal_health_threshold
        # Personality modifies: high resource_conservation = heal sooner
        heal_threshold += (self.traits.resource_conservation - 0.5) * 0.1

        if hp_pct < heal_threshold and state.has_healing_item():
            potion_name = state.get_healing_item_name()
            if potion_name:
                if self.verbose:
                    print(f"[AGENT] Using {potion_name} - HP low ({hp_pct:.0%})")
                self.last_command = f"use {potion_name}"
                return f"use {potion_name}"

        # === DEFAULT ATTACK ===
        # Track attack progress (from parent)
        if state.enemy_health > 0:
            if state.enemy_health == self.last_enemy_health:
                self.consecutive_attacks += 1
            else:
                self.consecutive_attacks = 0
            self.last_enemy_health = state.enemy_health

        if self.verbose:
            print(f"[AGENT] Attacking {state.enemy or 'enemy'} - HP {hp_pct:.0%}")
        self.last_command = "attack"
        return "attack"

    def _explore_decision(self, state: AgentState) -> str:
        """Make exploration decision incorporating personality and class.

        Modifications from base Agent:
        - Social engagement affects NPC talk priority
        - Exploration drive affects dungeon entry willingness
        - Class-specific exploration commands
        - Environmental awareness (tiredness, weather)

        Args:
            state: Current game state

        Returns:
            Exploration command
        """
        hp_pct = state.health_percent

        # === TIREDNESS CHECK ===
        # High tiredness triggers rest (environmental awareness)
        if state.should_rest() and self.traits.resource_conservation > 0.4:
            if self.verbose:
                print(f"[AGENT] Resting - tiredness {state.tiredness}%")
            self.last_command = "rest"
            return "rest"

        # === CLASS-SPECIFIC EXPLORATION ===
        class_command = self.class_behavior.get_exploration_command(state, self.memory)
        if class_command:
            if self.verbose:
                print(f"[AGENT] Using class exploration command: {class_command}")
            self.last_command = class_command
            return class_command

        # === HEALING PRIORITY ===
        if self.current_goal == AgentGoal.HEAL_UP or hp_pct < 0.50:
            return self._healing_decision(state)

        # === QUEST TURN-IN ===
        if self.current_goal == AgentGoal.TURN_IN_QUEST:
            return self._turn_in_quest_decision(state)

        # === DUNGEON EXPLORATION ===
        if self.current_goal == AgentGoal.EXPLORE_DUNGEON:
            return self._dungeon_exploration_decision(state)

        # === QUEST COMPLETION ===
        if self.current_goal == AgentGoal.COMPLETE_QUEST:
            return self._quest_driven_decision(state)

        # === OVERWORLD EXPLORATION WITH PERSONALITY ===
        return self._personality_aware_exploration(state)

    def _personality_aware_exploration(self, state: AgentState) -> str:
        """Overworld exploration modified by personality traits.

        Args:
            state: Current game state

        Returns:
            Exploration command
        """
        hp_pct = state.health_percent

        # Detect if we're in a conversation and need to say bye
        in_conversation = (
            "type 'bye' to leave" in state.last_narrative.lower() or
            "(continue chatting" in state.last_narrative.lower() or
            "how do you respond?" in state.last_narrative.lower() or
            self.last_command.startswith("talk ")
        )
        if in_conversation and self.last_command != "bye":
            if self.verbose:
                print("[AGENT] Saying bye to leave conversation")
            self.last_command = "bye"
            return "bye"

        # Accept quests ONLY if we have NPCs and likely in a quest dialog
        if "accept" in state.commands and state.npcs and self.stuck_counter == 0:
            if not hasattr(self, "_accept_attempts"):
                self._accept_attempts = 0
            if self._accept_attempts < 3:
                self._accept_attempts += 1
                if self.verbose:
                    print("[AGENT] Accepting quest")
                self.last_command = "accept"
                return "accept"
        else:
            self._accept_attempts = 0

        # === SOCIAL ENGAGEMENT: Talk to NPCs based on personality ===
        # High social_engagement = always talk, low = skip unless quest-related
        social_threshold = 1.0 - self.traits.social_engagement  # Invert: high engagement = low threshold
        if self.traits.social_engagement > social_threshold:
            for npc in state.npcs:
                if npc not in self.talked_this_location:
                    self.talked_this_location.add(npc)
                    if self.verbose:
                        print(f"[AGENT] Talking to {npc} (social_engagement={self.traits.social_engagement})")
                    self.last_command = f"talk {npc}"
                    return f"talk {npc}"

        # === ENTER SUB-LOCATIONS based on exploration_drive and risk ===
        if state.enterables and hp_pct > 0.70 and self.failed_enter_attempts < 3:
            # Check location danger from memory
            enterable = state.enterables[0]
            location_danger = self.memory.get_location_danger(enterable)

            # Enter if exploration_drive > danger_threshold
            # Higher exploration_drive = willing to enter more dangerous places
            danger_threshold = 1.0 - self.traits.exploration_drive
            should_enter = location_danger < (1.0 - danger_threshold * 0.5)

            # Also check risk_tolerance
            if self.traits.risk_tolerance > 0.5 or location_danger < 0.3:
                should_enter = True

            if should_enter:
                if self.verbose:
                    print(f"[AGENT] Entering sub-location: {enterable} (danger={location_danger})")
                self.failed_enter_attempts = 0
                self.last_command = f"enter {enterable}"
                return f"enter {enterable}"

        # Only try generic enter ONCE per location
        if ("enter" in state.commands and state.enterables and
                self.failed_enter_attempts < 1 and self.last_command != "enter"):
            self.failed_enter_attempts += 1
            if self.verbose:
                print("[AGENT] Entering location")
            self.last_command = "enter"
            return "enter"

        # Low social engagement: skip NPCs we haven't talked to
        # (already handled above by social_threshold check)

        # === MOVEMENT ===
        if state.exits:
            direction = self._get_smart_direction(state)

            # Track direction for smart exploration
            if direction == self.last_direction:
                self.consecutive_same_dir += 1
            else:
                self.consecutive_same_dir = 0
            self.last_direction = direction
            self.direction_history.append(direction)
            if len(self.direction_history) > 20:
                self.direction_history.pop(0)

            # Update coordinates
            self._update_coordinates_for_direction(direction)

            if self.verbose:
                unexplored = self._count_unexplored_adjacent()
                print(f"[AGENT] Moving {direction} @ {self.current_coords} (unexplored: {unexplored})")

            self.last_command = f"go {direction}"
            return f"go {direction}"

        # Shop interaction
        if "shop" in state.commands and state.gold > 50:
            if not state.has_healing_item():
                if self.verbose:
                    print("[AGENT] Buying potion at shop")
                self.last_command = "buy health potion"
                return "buy health potion"

        # Reset failed attempts if we've moved on
        if state.exits:
            self.failed_enter_attempts = 0

        # Stuck detection
        if self.stuck_counter > 3:
            self.stuck_counter = 0
            if state.npcs and "talk" in state.commands:
                import random
                npc = random.choice(state.npcs)
                if self.verbose:
                    print(f"[AGENT] Stuck - trying to talk to {npc}")
                self.last_command = f"talk {npc}"
                return f"talk {npc}"

            # Try an unexplored direction
            for dir_name in ["east", "west", "north", "south"]:
                dx, dy = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}[dir_name]
                target = (self.current_coords[0] + dx, self.current_coords[1] + dy)
                if target not in self.visited_coordinates:
                    if self.verbose:
                        print(f"[AGENT] Stuck - trying unexplored direction: {dir_name}")
                    self.last_direction = dir_name
                    self.last_command = f"go {dir_name}"
                    return f"go {dir_name}"

        # Fallback: look
        if self.verbose:
            print("[AGENT] Looking around (fallback)")
        self.last_command = "look"
        return "look"

    def to_checkpoint_dict(self) -> dict:
        """Serialize agent state to dictionary for checkpointing.

        Extends base Agent serialization with personality, class, and memory.

        Returns:
            Dictionary with all serializable agent state.
        """
        # Get base checkpoint data
        base_data = super().to_checkpoint_dict()

        # Add HumanLikeAgent-specific fields
        base_data["personality_type"] = self.personality_type.name
        base_data["character_class"] = self.character_class.name
        base_data["memory"] = self.memory.to_dict()

        return base_data

    def restore_from_checkpoint(self, data: dict) -> None:
        """Restore agent state from checkpoint dictionary.

        Extends base Agent restoration with personality, class, and memory.

        Args:
            data: Dictionary containing serialized agent state.
        """
        # Restore base Agent state
        super().restore_from_checkpoint(data)

        # Restore personality
        if "personality_type" in data:
            personality_name = data["personality_type"]
            self.personality_type = PersonalityType[personality_name]
            self.traits = get_personality_traits(self.personality_type)

        # Restore character class
        if "character_class" in data:
            class_name = data["character_class"]
            self.character_class = CharacterClassName[class_name]
            self.class_behavior = get_class_behavior(self.character_class)

        # Restore memory
        if "memory" in data:
            self.memory = AgentMemory.from_dict(data["memory"])

        # Recalculate max_sub_location_moves
        base_moves = 50
        self.max_sub_location_moves = int(base_moves * (0.5 + self.traits.exploration_drive))
