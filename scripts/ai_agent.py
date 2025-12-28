"""AI Agent for autonomous CLI-RPG gameplay.

Uses heuristic-based decision making to play the game via JSON mode.
Supports sophisticated exploration including dungeons, sub-locations,
and quest-driven behavior.
"""
import os
import queue
import random
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from scripts.state_parser import AgentState, parse_line, update_state


class AgentGoal(Enum):
    """High-level goal states for the agent."""
    EXPLORE_OVERWORLD = auto()  # Exploring the main world
    EXPLORE_DUNGEON = auto()    # Exploring inside a sub-location
    COMPLETE_QUEST = auto()     # Working on a specific quest
    HEAL_UP = auto()            # Finding safety to heal
    TURN_IN_QUEST = auto()      # Returning to quest giver


@dataclass
class SessionStats:
    """Statistics collected during an agent session.

    Attributes:
        commands_issued: Total commands sent to game
        locations_visited: Set of unique location names visited
        enemies_defeated: Count of enemies killed
        deaths: Count of player deaths
        potions_used: Count of healing items consumed
        gold_earned: Net gold change during session
        fled_count: Number of times agent fled combat
        rested_count: Number of rest commands issued
        errors_encountered: Count of error messages received
        sub_locations_entered: Count of dungeons/caves entered
        quests_accepted: Count of quests accepted
        quests_completed: Count of quests turned in
        bosses_defeated: Count of boss enemies defeated
        npcs_talked_to: Set of unique NPCs talked to
    """
    commands_issued: int = 0
    locations_visited: set[str] = field(default_factory=set)
    enemies_defeated: int = 0
    deaths: int = 0
    potions_used: int = 0
    gold_earned: int = 0
    fled_count: int = 0
    rested_count: int = 0
    errors_encountered: int = 0
    sub_locations_entered: int = 0
    quests_accepted: int = 0
    quests_completed: int = 0
    bosses_defeated: int = 0
    npcs_talked_to: set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        """Serialize stats to dictionary."""
        return {
            "commands_issued": self.commands_issued,
            "locations_visited": list(self.locations_visited),
            "unique_locations": len(self.locations_visited),
            "enemies_defeated": self.enemies_defeated,
            "deaths": self.deaths,
            "potions_used": self.potions_used,
            "gold_earned": self.gold_earned,
            "fled_count": self.fled_count,
            "rested_count": self.rested_count,
            "errors_encountered": self.errors_encountered,
            "sub_locations_entered": self.sub_locations_entered,
            "quests_accepted": self.quests_accepted,
            "quests_completed": self.quests_completed,
            "bosses_defeated": self.bosses_defeated,
            "npcs_talked_to": list(self.npcs_talked_to),
        }


class Agent:
    """Sophisticated heuristic-based decision engine for CLI-RPG.

    Makes contextual decisions based on game state using priority rules.
    Supports dungeon exploration, quest fulfillment, and strategic gameplay.
    """

    def __init__(self, verbose: bool = False):
        """Initialize agent.

        Args:
            verbose: If True, print decision reasoning
        """
        self.verbose = verbose
        self.current_goal = AgentGoal.EXPLORE_OVERWORLD
        self.talked_this_location: set[str] = set()
        self.exploration_depth: int = 0  # Tracks depth in sub-location
        self.failed_enter_attempts: int = 0  # Avoid infinite enter loops
        self.last_command: str = ""
        self.stuck_counter: int = 0  # Detect stuck states
        self.last_location: str = ""
        self.sub_location_moves: int = 0  # Moves since entering sub-location
        self.max_sub_location_moves: int = 50  # Exit after this many moves

        # Smart exploration tracking
        self.visited_coordinates: set[tuple[int, int]] = set()  # Track (x,y) coords
        self.current_coords: tuple[int, int] = (0, 0)  # Current position estimate
        self.direction_history: list[str] = []  # Recent directions taken
        self.needs_look: bool = True  # Should look before next action
        self.consecutive_same_dir: int = 0  # How many times same dir was taken
        self.last_direction: str = ""

        # Combat state tracking for better detection
        self.in_combat_override: bool = False  # Manual combat detection
        self.commands_since_combat_check: int = 0
        self.consecutive_attacks: int = 0  # Track attacks without progress
        self.last_enemy_health: int = 0  # Detect if attacks are working
        self.max_consecutive_attacks: int = 10  # Bail out after this many

    def _detect_combat_from_narrative(self, state: AgentState) -> bool:
        """Detect if we're in combat from narrative text.

        Args:
            state: Current game state

        Returns:
            True if combat is detected
        """
        narrative = state.last_narrative.lower()
        combat_indicators = [
            "combat has begun",
            "appears!",
            "ambush",
            "attacks you",
            "enemy hp:",
            "=== combat",
            "a wild",
            "creature lunges",
            "you are attacked",
        ]
        return any(indicator in narrative for indicator in combat_indicators)

    def _is_in_combat(self, state: AgentState) -> bool:
        """Check if we're in combat using multiple detection methods.

        Args:
            state: Current game state

        Returns:
            True if in combat
        """
        # FIRST: Check for too many consecutive attacks (stuck in combat loop)
        if self.consecutive_attacks >= self.max_consecutive_attacks:
            if self.verbose:
                print(f"[AGENT] Bailing out of combat - {self.consecutive_attacks} attacks with no progress")
            self._reset_combat_state(state)
            return False

        # If we have exits, we're not in active combat - reset and return
        if state.exits and len(state.exits) > 0:
            self._reset_combat_state(state)
            return False

        # Direct state check - primary source of truth
        if state.in_combat:
            return True

        # Check narrative for combat indicators
        if self._detect_combat_from_narrative(state):
            return True

        # Check last narrative for "Can't do that during combat"
        if "can't do that during combat" in state.last_narrative.lower():
            return True

        # Check if commands indicate combat (only combat commands available)
        combat_only_commands = {"attack", "defend", "flee", "block", "parry"}
        if state.commands:
            available = set(state.commands)
            # Only if we ONLY have combat commands and no movement
            non_combat = {"go", "look", "enter", "exit", "talk", "shop", "inventory"}
            if combat_only_commands & available and not (non_combat & available):
                return True

        return False

    def _reset_combat_state(self, state: AgentState) -> None:
        """Reset all combat-related tracking.

        Args:
            state: Game state to update
        """
        self.in_combat_override = False
        self.consecutive_attacks = 0
        self.last_enemy_health = 0
        state.enemy = ""
        state.enemy_health = 0
        state.in_combat = False

    def decide(self, state: AgentState) -> str:
        """Determine next command based on current state.

        Args:
            state: Current game state

        Returns:
            Command string to send to game
        """
        self.commands_since_combat_check += 1

        # Detect stuck state (same location, no progress)
        if state.location == self.last_location:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
            self.last_location = state.location
            self.needs_look = True  # Look when entering new location
            # Reset talked set when location changes
            self.talked_this_location.clear()
            # Update coordinate tracking
            self._update_coordinates()

        # Mark current position as visited
        self.visited_coordinates.add(self.current_coords)

        # PRIORITY 1: Combat detection with multiple methods
        if self._is_in_combat(state):
            if self.verbose:
                print(f"[AGENT] Combat detected (in_combat={state.in_combat}, override={self.in_combat_override})")
            return self._combat_decision(state)

        # PRIORITY 2: Look before taking major actions (new location or unclear state)
        # But don't look repeatedly if we just looked
        if self.needs_look and self.last_command != "look":
            self.needs_look = False
            if self.verbose:
                print("[AGENT] Looking to assess surroundings")
            self.last_command = "look"
            return "look"

        # If we have no exits and just looked, wait for state update
        if not state.exits and self.last_command == "look":
            # Try dump-state to get full state
            if self.verbose:
                print("[AGENT] No exits after look, requesting dump-state")
            self.last_command = "dump-state"
            return "dump-state"

        # Update goal based on state
        self._update_goal(state)

        return self._explore_decision(state)

    def _update_coordinates(self) -> None:
        """Update estimated coordinates based on last direction."""
        self._update_coordinates_for_direction(self.last_direction)

    def _update_coordinates_for_direction(self, direction: str) -> None:
        """Update estimated coordinates for a given direction.

        Args:
            direction: Direction being moved
        """
        direction_map = {
            "north": (0, 1),
            "south": (0, -1),
            "east": (1, 0),
            "west": (-1, 0),
        }
        if direction in direction_map:
            dx, dy = direction_map[direction]
            x, y = self.current_coords
            self.current_coords = (x + dx, y + dy)
            # Mark new position as visited
            self.visited_coordinates.add(self.current_coords)

    def _update_goal(self, state: AgentState) -> None:
        """Update the current high-level goal based on state.

        Args:
            state: Current game state
        """
        hp_pct = state.health_percent

        # Priority 1: Heal if critically low
        if hp_pct < 0.40:
            self.current_goal = AgentGoal.HEAL_UP
            return

        # Priority 2: Turn in completed quests
        if state.has_quest_ready_to_turn_in():
            self.current_goal = AgentGoal.TURN_IN_QUEST
            return

        # Priority 3: In sub-location = explore dungeon
        if state.in_sub_location:
            self.current_goal = AgentGoal.EXPLORE_DUNGEON
            self.sub_location_moves += 1
            return

        # Priority 4: Have active quest = work on it
        if state.quest_details:
            self.current_goal = AgentGoal.COMPLETE_QUEST
            return

        # Default: explore overworld
        self.current_goal = AgentGoal.EXPLORE_OVERWORLD
        self.sub_location_moves = 0

    def _combat_decision(self, state: AgentState) -> str:
        """Make combat decision.

        Priority:
        1. Flee if HP < 20% (critical)
        2. Use potion if HP < 40% and has healing item
        3. Attack (checking if target matches quest)

        Args:
            state: Current game state

        Returns:
            Combat command
        """
        hp_pct = state.health_percent

        # Check if combat has ended (victory or fled)
        narrative_lower = state.last_narrative.lower()
        combat_ended_indicators = [
            "defeated",
            "slain",
            "you killed",
            "you have slain",
            "fled successfully",
            "you escaped",
            "combat ends",
            "victory",
            "enemy fell",
            "you won",
        ]
        if any(indicator in narrative_lower for indicator in combat_ended_indicators):
            self._reset_combat_state(state)
            if self.verbose:
                print("[AGENT] Combat ended, returning to exploration")
            self.needs_look = True
            self.last_command = "look"
            return "look"

        # Also check if enemy health is 0 (we won)
        if state.enemy_health <= 0 and state.enemy:
            self._reset_combat_state(state)
            if self.verbose:
                print("[AGENT] Enemy defeated, returning to exploration")
            self.needs_look = True
            self.last_command = "look"
            return "look"

        # Flee at critical health
        if hp_pct < 0.20:
            if self.verbose:
                print(f"[AGENT] Fleeing - HP critical ({hp_pct:.0%})")
            self.last_command = "flee"
            return "flee"

        # Use healing if hurt and have potion
        if hp_pct < 0.40 and state.has_healing_item():
            potion_name = state.get_healing_item_name()
            if potion_name:
                if self.verbose:
                    print(f"[AGENT] Using {potion_name} - HP low ({hp_pct:.0%})")
                self.last_command = f"use {potion_name}"
                return f"use {potion_name}"

        # Check if this enemy matches a kill quest target
        quest_target = state.get_kill_quest_target()
        if quest_target and state.enemy and quest_target.lower() in state.enemy.lower():
            if self.verbose:
                print(f"[AGENT] Attacking quest target: {state.enemy}")

        # Default: attack
        enemy_name = state.enemy or "enemy"

        # Track attack progress - are we actually doing damage?
        if state.enemy_health > 0:
            if state.enemy_health == self.last_enemy_health:
                self.consecutive_attacks += 1
            else:
                self.consecutive_attacks = 0
            self.last_enemy_health = state.enemy_health

        if self.verbose:
            print(f"[AGENT] Attacking {enemy_name} - HP {hp_pct:.0%}")
        self.last_command = "attack"
        return "attack"

    def _explore_decision(self, state: AgentState) -> str:
        """Make exploration decision based on current goal.

        Args:
            state: Current game state

        Returns:
            Exploration command
        """
        hp_pct = state.health_percent

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

        # === DEFAULT: OVERWORLD EXPLORATION ===
        return self._overworld_exploration_decision(state)

    def _healing_decision(self, state: AgentState) -> str:
        """Decision when agent needs to heal.

        Args:
            state: Current game state

        Returns:
            Healing-related command
        """
        hp_pct = state.health_percent

        # Use potion if available and hurt
        if hp_pct < 0.60 and state.has_healing_item():
            potion_name = state.get_healing_item_name()
            if potion_name:
                if self.verbose:
                    print(f"[AGENT] Using {potion_name} for healing ({hp_pct:.0%})")
                return f"use {potion_name}"

        # Rest if HP < 50% or dread high
        if hp_pct < 0.50 or state.dread > 60:
            if self.verbose:
                reason = f"HP {hp_pct:.0%}" if hp_pct < 0.50 else f"dread {state.dread}%"
                print(f"[AGENT] Resting - {reason}")
            return "rest"

        # Exit sub-location if low health and at exit point
        if state.in_sub_location and state.is_exit_point and hp_pct < 0.60:
            if self.verbose:
                print("[AGENT] Exiting sub-location to heal")
            return "exit"

        # Otherwise try to move toward safety (prefer exits that lead away)
        if state.exits:
            direction = random.choice(state.exits)
            if self.verbose:
                print(f"[AGENT] Moving {direction} while healing")
            return f"go {direction}"

        return "rest"

    def _turn_in_quest_decision(self, state: AgentState) -> str:
        """Decision when agent has a quest ready to turn in.

        Args:
            state: Current game state

        Returns:
            Quest turn-in related command
        """
        # Check if quest giver is present
        quest_giver = state.get_quest_giver_for_turnin()

        if quest_giver and quest_giver in state.npcs:
            # Talk to quest giver to turn in
            if quest_giver not in self.talked_this_location:
                self.talked_this_location.add(quest_giver)
                if self.verbose:
                    print(f"[AGENT] Talking to {quest_giver} to turn in quest")
                return f"talk {quest_giver}"

        # Try complete command if available
        if "complete" in state.commands:
            if self.verbose:
                print("[AGENT] Completing quest")
            return "complete"

        # Must exit sub-location first
        if state.in_sub_location and state.is_exit_point:
            if self.verbose:
                print("[AGENT] Exiting to turn in quest")
            return "exit"

        # Move toward quest giver (explore to find them)
        return self._overworld_exploration_decision(state)

    def _dungeon_exploration_decision(self, state: AgentState) -> str:
        """Decision for exploring inside a dungeon/sub-location.

        Args:
            state: Current game state

        Returns:
            Dungeon exploration command
        """
        hp_pct = state.health_percent

        # Check if we should exit (too many moves, low health, or explored enough)
        should_exit = (
            self.sub_location_moves > self.max_sub_location_moves
            or hp_pct < 0.35
            or state.dread > 70
        )

        if should_exit and state.is_exit_point:
            if self.verbose:
                reason = "max moves" if self.sub_location_moves > self.max_sub_location_moves else "low HP/dread"
                print(f"[AGENT] Exiting sub-location ({reason})")
            self.sub_location_moves = 0
            return "exit"

        # Talk to NPCs for quests (if not already talked)
        for npc in state.npcs:
            if npc not in self.talked_this_location:
                self.talked_this_location.add(npc)
                if self.verbose:
                    print(f"[AGENT] Talking to {npc} in dungeon")
                return f"talk {npc}"

        # Say bye if in conversation
        if "bye" in state.commands:
            if self.verbose:
                print("[AGENT] Saying bye in dungeon")
            return "bye"

        # Accept quests if offered (and have NPCs - means we're in a dialog)
        if "accept" in state.commands and state.npcs:
            if self.verbose:
                print("[AGENT] Accepting quest in dungeon")
            return "accept"

        # Try to open chests/treasures
        if "open" in state.commands:
            if self.verbose:
                print("[AGENT] Opening treasure")
            return "open"

        # Search for secrets
        if "search" in state.commands and random.random() < 0.3:
            if self.verbose:
                print("[AGENT] Searching for secrets")
            return "search"

        # Explore deeper - prioritize unexplored directions
        if state.exits:
            # Prefer down (deeper into dungeon) when healthy
            if "down" in state.exits and hp_pct > 0.60:
                if self.verbose:
                    print("[AGENT] Going down (deeper)")
                return "go down"

            # Then try other directions
            direction = random.choice(state.exits)
            if self.verbose:
                print(f"[AGENT] Exploring dungeon: {direction}")
            return f"go {direction}"

        # If at exit point with no other options, exit
        if state.is_exit_point:
            if self.verbose:
                print("[AGENT] No more exits, leaving dungeon")
            return "exit"

        # Fallback: look
        return "look"

    def _quest_driven_decision(self, state: AgentState) -> str:
        """Decision when working on active quests.

        Args:
            state: Current game state

        Returns:
            Quest-related command
        """
        # Check quest objectives and try to fulfill them

        # TALK quest: Find and talk to target NPC
        talk_target = state.get_talk_quest_target()
        if talk_target:
            # Check if target is present
            for npc in state.npcs:
                if talk_target.lower() in npc.lower():
                    if npc not in self.talked_this_location:
                        self.talked_this_location.add(npc)
                        if self.verbose:
                            print(f"[AGENT] Talking to quest target: {npc}")
                        return f"talk {npc}"

        # EXPLORE quest: Look for target location
        explore_target = state.get_explore_quest_target()
        if explore_target:
            # Check if we're at the target
            if explore_target.lower() in state.location.lower():
                if self.verbose:
                    print(f"[AGENT] Reached explore target: {state.location}")
                # Look around to register the visit
                return "look"

        # KILL quest: Explore to find enemies (combat handles killing)
        # Just explore - combat will happen naturally

        # Say bye if in conversation
        if "bye" in state.commands:
            if self.verbose:
                print("[AGENT] Saying bye")
            return "bye"

        # Accept available quests (only if NPCs present - means in dialog)
        if "accept" in state.commands and state.npcs:
            if self.verbose:
                print("[AGENT] Accepting quest")
            return "accept"

        # Default to exploration to find quest objectives
        return self._overworld_exploration_decision(state)

    def _get_smart_direction(self, state: AgentState) -> str:
        """Choose direction intelligently based on exploration history.

        Prioritizes:
        1. Directions leading to unexplored coordinates
        2. Directions not recently taken
        3. East/West to expand exploration (avoid north/south ping-pong)

        Args:
            state: Current game state

        Returns:
            Direction to move
        """
        if not state.exits:
            return "north"  # Fallback

        direction_map = {
            "north": (0, 1),
            "south": (0, -1),
            "east": (1, 0),
            "west": (-1, 0),
        }

        # Score each available exit
        exit_scores: dict[str, float] = {}
        for exit_dir in state.exits:
            if exit_dir not in direction_map:
                continue  # Skip up/down for overworld

            dx, dy = direction_map[exit_dir]
            target_coords = (self.current_coords[0] + dx, self.current_coords[1] + dy)

            score = 0.0

            # Heavily prefer unexplored coordinates
            if target_coords not in self.visited_coordinates:
                score += 100.0

            # Prefer east/west to expand horizontally
            if exit_dir in ("east", "west"):
                score += 20.0

            # Penalize going same direction too many times
            if exit_dir == self.last_direction:
                # Increasing penalty for consecutive same direction
                score -= 10.0 * (1 + self.consecutive_same_dir)

            # Avoid reversing immediately (but less penalty if we've been going one way for a while)
            opposites = {"north": "south", "south": "north", "east": "west", "west": "east"}
            if exit_dir == opposites.get(self.last_direction):
                if self.consecutive_same_dir < 3:
                    score -= 30.0
                else:
                    # After going one direction for a while, reversing is ok
                    score += 10.0

            # Slight randomness to avoid deterministic loops
            score += random.uniform(0, 15)

            exit_scores[exit_dir] = score

        if not exit_scores:
            return random.choice(state.exits)

        # Pick highest scoring direction
        best_dir = max(exit_scores, key=lambda d: exit_scores[d])
        return best_dir

    def _overworld_exploration_decision(self, state: AgentState) -> str:
        """Default exploration decision for overworld.

        Args:
            state: Current game state

        Returns:
            Exploration command
        """
        hp_pct = state.health_percent

        # Detect if we're in a conversation and need to say bye
        # Check narrative for conversation indicators since "bye" isn't in commands
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
        # (accept should only be used when actually offered a quest)
        if "accept" in state.commands and state.npcs and self.stuck_counter == 0:
            # Limit accept attempts to avoid infinite loops
            if not hasattr(self, "_accept_attempts"):
                self._accept_attempts = 0
            if self._accept_attempts < 3:
                self._accept_attempts += 1
                if self.verbose:
                    print("[AGENT] Accepting quest")
                self.last_command = "accept"
                return "accept"
        else:
            # Reset accept attempts when we move to a new context
            self._accept_attempts = 0

        # PRIORITY: Enter sub-locations (dungeons, caves) when healthy - before moving!
        if state.enterables and hp_pct > 0.70 and self.failed_enter_attempts < 3:
            enterable = state.enterables[0]
            if self.verbose:
                print(f"[AGENT] Entering sub-location: {enterable}")
            self.failed_enter_attempts = 0
            self.last_command = f"enter {enterable}"
            return f"enter {enterable}"

        # Only try generic enter ONCE per location, and only if we have enterables
        if ("enter" in state.commands and state.enterables and
                self.failed_enter_attempts < 1 and self.last_command != "enter"):
            self.failed_enter_attempts += 1
            if self.verbose:
                print("[AGENT] Entering location")
            self.last_command = "enter"
            return "enter"

        # Talk to NPCs to get quests (if not already talked)
        for npc in state.npcs:
            if npc not in self.talked_this_location:
                self.talked_this_location.add(npc)
                if self.verbose:
                    print(f"[AGENT] Talking to {npc}")
                self.last_command = f"talk {npc}"
                return f"talk {npc}"

        # Explore: use SMART direction selection
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

            # Update coordinates BEFORE moving (since state update is delayed)
            self._update_coordinates_for_direction(direction)

            if self.verbose:
                unexplored = self._count_unexplored_adjacent()
                print(f"[AGENT] Moving {direction} @ {self.current_coords} (unexplored: {unexplored})")

            self.last_command = f"go {direction}"
            return f"go {direction}"

        # Buy potions at shop if needed
        if "shop" in state.commands and state.gold > 50:
            if not state.has_healing_item():
                if self.verbose:
                    print("[AGENT] Buying potion at shop")
                self.last_command = "buy health potion"
                return "buy health potion"

        # Reset failed attempts if we've moved on
        if state.exits:
            self.failed_enter_attempts = 0

        # Stuck detection: if we've been stuck, try different commands
        if self.stuck_counter > 3:
            self.stuck_counter = 0
            if state.npcs and "talk" in state.commands:
                npc = random.choice(state.npcs)
                if self.verbose:
                    print(f"[AGENT] Stuck - trying to talk to {npc}")
                self.last_command = f"talk {npc}"
                return f"talk {npc}"
            # Try an unexplored direction
            for dir in ["east", "west", "north", "south"]:
                dx, dy = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}[dir]
                target = (self.current_coords[0] + dx, self.current_coords[1] + dy)
                if target not in self.visited_coordinates:
                    if self.verbose:
                        print(f"[AGENT] Stuck - trying unexplored direction: {dir}")
                    self.last_direction = dir
                    self.last_command = f"go {dir}"
                    return f"go {dir}"

        # Fallback: if we've been looking too much, try a random direction
        if self.last_command in ("look", "dump-state"):
            # Force a move in any direction
            for dir in ["north", "south", "east", "west"]:
                if self.verbose:
                    print(f"[AGENT] Fallback - forcing move {dir}")
                self.last_direction = dir
                self.last_command = f"go {dir}"
                return f"go {dir}"

        # Look around to refresh state
        if self.verbose:
            print("[AGENT] Looking around (fallback)")
        self.last_command = "look"
        return "look"

    def _count_unexplored_adjacent(self) -> int:
        """Count unexplored adjacent tiles."""
        count = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            target = (self.current_coords[0] + dx, self.current_coords[1] + dy)
            if target not in self.visited_coordinates:
                count += 1
        return count

    def to_checkpoint_dict(self) -> dict:
        """Serialize agent state to dictionary for checkpointing.

        Returns:
            Dictionary with all serializable agent state.
        """
        return {
            "current_goal": self.current_goal.name,
            "visited_coordinates": list(self.visited_coordinates),
            "current_coords": self.current_coords,
            "direction_history": list(self.direction_history),
            "talked_this_location": list(self.talked_this_location),
            "sub_location_moves": self.sub_location_moves,
            "exploration_depth": self.exploration_depth,
            "failed_enter_attempts": self.failed_enter_attempts,
            "last_command": self.last_command,
            "stuck_counter": self.stuck_counter,
            "last_location": self.last_location,
            "needs_look": self.needs_look,
            "consecutive_same_dir": self.consecutive_same_dir,
            "last_direction": self.last_direction,
        }

    def restore_from_checkpoint(self, data: dict) -> None:
        """Restore agent state from checkpoint dictionary.

        Args:
            data: Dictionary containing serialized agent state.
        """
        # Restore goal
        goal_name = data.get("current_goal", "EXPLORE_OVERWORLD")
        self.current_goal = AgentGoal[goal_name]

        # Restore exploration state
        visited = data.get("visited_coordinates", [])
        self.visited_coordinates = {tuple(coord) for coord in visited}
        self.current_coords = tuple(data.get("current_coords", (0, 0)))
        self.direction_history = list(data.get("direction_history", []))
        self.talked_this_location = set(data.get("talked_this_location", []))
        self.sub_location_moves = data.get("sub_location_moves", 0)

        # Restore additional state
        self.exploration_depth = data.get("exploration_depth", 0)
        self.failed_enter_attempts = data.get("failed_enter_attempts", 0)
        self.last_command = data.get("last_command", "")
        self.stuck_counter = data.get("stuck_counter", 0)
        self.last_location = data.get("last_location", "")
        self.needs_look = data.get("needs_look", True)
        self.consecutive_same_dir = data.get("consecutive_same_dir", 0)
        self.last_direction = data.get("last_direction", "")


@dataclass
class GameSession:
    """Manages subprocess for CLI-RPG game session.

    Uses unbuffered I/O and a threaded reader to handle real-time
    interaction with the game subprocess.
    """

    seed: int
    max_commands: float = 1000  # float to support infinity
    timeout: float = 300.0  # seconds
    verbose: bool = False
    show_game_output: bool = False  # -vv mode: show full game output
    action_delay: float = 0.0  # delay between actions in seconds
    enable_checkpoints: bool = True  # Whether to create checkpoints
    session_manager: Optional["SessionManager"] = None  # Checkpoint manager
    session_id: Optional[str] = None  # Current session ID
    personality: Optional[str] = None  # Personality type name (for HumanLikeAgent)
    character_class: Optional[str] = None  # Character class name (for HumanLikeAgent)

    process: Optional[subprocess.Popen] = field(default=None, init=False)
    state: AgentState = field(default_factory=AgentState, init=False)
    stats: SessionStats = field(default_factory=SessionStats, init=False)
    agent: Agent = field(default=None, init=False)
    _initial_gold: int = field(default=0, init=False)
    _output_queue: queue.Queue = field(default_factory=queue.Queue, init=False)
    _reader_thread: Optional[threading.Thread] = field(default=None, init=False)
    _stop_reader: bool = field(default=False, init=False)
    _prev_state: Optional[AgentState] = field(default=None, init=False)  # For trigger detection

    def __post_init__(self):
        # Create agent - use HumanLikeAgent if personality or class specified
        if self.personality or self.character_class:
            from scripts.human_like_agent import HumanLikeAgent
            from scripts.agent import PersonalityType, CharacterClassName

            # Parse personality type
            personality = PersonalityType.CAUTIOUS_EXPLORER
            if self.personality:
                personality = PersonalityType[self.personality.upper()]

            # Parse character class
            char_class = CharacterClassName.WARRIOR
            if self.character_class:
                char_class = CharacterClassName[self.character_class.upper()]

            self.agent = HumanLikeAgent(
                personality=personality,
                character_class=char_class,
                verbose=self.verbose,
            )
        else:
            self.agent = Agent(verbose=self.verbose)

        # Import here to avoid circular imports
        if self.enable_checkpoints and self.session_manager is None:
            from scripts.agent_persistence import SessionManager
            self.session_manager = SessionManager()

    def _reader_worker(self) -> None:
        """Background thread that reads stdout lines into a queue."""
        import select

        try:
            buffer = ""
            while not self._stop_reader:
                # Use select with timeout to check for data
                rlist, _, _ = select.select([self._stdout_fd], [], [], 0.1)
                if self._stdout_fd in rlist:
                    try:
                        data = os.read(self._stdout_fd, 4096)
                        if not data:  # EOF
                            break
                        buffer += data.decode("utf-8", errors="replace")
                        # Split into lines
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            self._output_queue.put(line + "\n")
                    except (OSError, ValueError):
                        break
        except Exception:
            pass  # Process closed

    def start(self) -> None:
        """Start the game subprocess and reader thread."""
        import pty

        # Force unbuffered I/O in child process
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        cmd = [
            sys.executable, "-u",  # -u for unbuffered stdout
            "-m", "cli_rpg.main",
            "--json",
            "--skip-character-creation",
            f"--seed={self.seed}"
        ]

        # Use PTY to force line buffering (works better on Unix)
        master_fd, slave_fd = pty.openpty()

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=slave_fd,
            stderr=subprocess.PIPE,
            text=True,  # Text mode for stdin
            bufsize=1,  # Line buffered
            env=env,
        )

        # Close slave fd in parent
        os.close(slave_fd)

        # Store master fd for reading
        self._stdout_fd = master_fd

        # Start reader thread
        self._stop_reader = False
        self._reader_thread = threading.Thread(target=self._reader_worker, daemon=True)
        self._reader_thread.start()

    def stop(self) -> None:
        """Stop the game subprocess and reader thread."""
        self._stop_reader = True
        if self.process:
            try:
                self.process.stdin.write("quit\n")
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1)

    def _read_output(self, wait_time: float = 0.1, min_lines: int = 0) -> list[str]:
        """Read available output lines from the queue.

        Args:
            wait_time: Time to wait for output
            min_lines: Minimum lines to wait for (will retry until timeout)

        Returns:
            List of output lines
        """
        deadline = time.time() + wait_time
        lines = []

        while time.time() < deadline:
            try:
                line = self._output_queue.get(timeout=0.05)
                lines.append(line)
            except queue.Empty:
                if len(lines) >= min_lines:
                    break
                continue

        # Drain any remaining lines
        while True:
            try:
                line = self._output_queue.get_nowait()
                lines.append(line)
            except queue.Empty:
                break

        return lines

    def _send_command(self, command: str) -> None:
        """Send a command to the game.

        Args:
            command: Command string to send
        """
        if self.process and self.process.stdin:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            self.stats.commands_issued += 1

            # Track specific command types
            if command == "flee":
                self.stats.fled_count += 1
            elif command == "rest":
                self.stats.rested_count += 1
            elif command.startswith("use "):
                self.stats.potions_used += 1

    def _display_game_output(self, msg: dict) -> None:
        """Display game output in human-readable format for -vv mode.

        Args:
            msg: Parsed JSON message from game
        """
        msg_type = msg.get("type")

        if msg_type == "narrative":
            text = msg.get("text", "")
            if text:
                print(f"\n{text}")

        elif msg_type == "state":
            location = msg.get("location", "")
            health = msg.get("health", 0)
            max_health = msg.get("max_health", 0)
            gold = msg.get("gold", 0)
            print(f"\n[{location}] HP: {health}/{max_health} Gold: {gold}")

        elif msg_type == "actions":
            exits = msg.get("exits", [])
            npcs = msg.get("npcs", [])
            if exits:
                print(f"Exits: {', '.join(exits)}")
            if npcs:
                print(f"NPCs: {', '.join(npcs)}")

        elif msg_type == "combat":
            enemy = msg.get("enemy", "")
            enemy_hp = msg.get("enemy_health", 0)
            player_hp = msg.get("player_health", 0)
            print(f"\n=== COMBAT: {enemy} (HP: {enemy_hp}) | You (HP: {player_hp}) ===")

        elif msg_type == "error":
            error_msg = msg.get("message", "")
            print(f"\n[ERROR] {error_msg}")

    def _process_messages(self, lines: list[str]) -> None:
        """Process output lines and update state/stats.

        Args:
            lines: Output lines from game
        """
        for line in lines:
            msg = parse_line(line)
            if msg is None:
                continue

            # Display game output if in -vv mode
            if self.show_game_output:
                self._display_game_output(msg)

            # Track state before update for comparison
            was_in_sub = self.state.in_sub_location
            prev_quests = set(self.state.quests)

            update_state(self.state, msg)

            msg_type = msg.get("type")

            # Track location visits
            if msg_type == "state" and self.state.location:
                self.stats.locations_visited.add(self.state.location)

            # Track errors
            if msg_type == "error":
                self.stats.errors_encountered += 1
                # Track failed enter attempts
                error_msg = msg.get("message", "").lower()
                if "enter" in error_msg or "can't enter" in error_msg:
                    self.agent.failed_enter_attempts += 1

            # Track narrative events
            if msg_type == "narrative":
                text = msg.get("text", "").lower()

                # Track enemy defeats
                if "defeated" in text or "slain" in text or "killed" in text:
                    self.stats.enemies_defeated += 1
                    # Check for boss defeat
                    if "boss" in text or any(word in text for word in ["mighty", "fearsome", "ancient"]):
                        self.stats.bosses_defeated += 1

                # Track deaths
                if "you died" in text or "you have died" in text:
                    self.stats.deaths += 1

                # Track entering sub-locations
                if "you enter" in text and not was_in_sub and self.state.in_sub_location:
                    self.stats.sub_locations_entered += 1

                # Track quest acceptance
                if "quest accepted" in text or "accepted the quest" in text:
                    self.stats.quests_accepted += 1

                # Track quest completion
                if "quest complete" in text or "completed the quest" in text:
                    self.stats.quests_completed += 1

            # Track NPC talks from state changes
            # Note: This is approximate - we track via the agent's talked_this_location set
            if msg_type == "actions":
                # If we have NPCs, update the talked tracking
                for npc in self.state.npcs:
                    if npc in self.agent.talked_this_location:
                        self.stats.npcs_talked_to.add(npc)

            # Track quest changes from dump_state
            if msg_type == "dump_state":
                current_quests = set(self.state.quests)
                # New quests accepted
                new_quests = current_quests - prev_quests
                if new_quests:
                    self.stats.quests_accepted += len(new_quests)

    def _check_triggers(self, prev_state: AgentState) -> Optional["CheckpointTrigger"]:
        """Check if a checkpoint trigger occurred.

        Args:
            prev_state: State before the last command.

        Returns:
            CheckpointTrigger if triggered, None otherwise.
        """
        if not self.enable_checkpoints:
            return None

        from scripts.checkpoint_triggers import detect_trigger
        return detect_trigger(prev_state, self.state, self.stats.commands_issued)

    def _create_checkpoint(self, trigger: "CheckpointTrigger") -> None:
        """Create a checkpoint for the current state.

        Args:
            trigger: The trigger type that caused this checkpoint.
        """
        if not self.enable_checkpoints or self.session_manager is None:
            return

        from datetime import datetime
        from scripts.agent_checkpoint import AgentCheckpoint

        # Get agent state
        agent_data = self.agent.to_checkpoint_dict()

        # Create checkpoint
        checkpoint = AgentCheckpoint(
            current_goal=agent_data["current_goal"],
            visited_coordinates=agent_data["visited_coordinates"],
            current_coords=agent_data["current_coords"],
            direction_history=agent_data["direction_history"],
            talked_this_location=agent_data["talked_this_location"],
            sub_location_moves=agent_data["sub_location_moves"],
            stats=self.stats.to_dict(),
            checkpoint_type=trigger.name.lower(),
            game_save_path="",  # Game save path would be set if using game saves
            seed=self.seed,
            timestamp=datetime.now().isoformat(),
            command_index=self.stats.commands_issued,
        )

        # Save checkpoint
        if self.session_id:
            checkpoint_id = self.session_manager.save_checkpoint(
                checkpoint, trigger, self.session_id
            )
            if self.verbose:
                print(f"[SESSION] Checkpoint created: {checkpoint_id} ({trigger.name})")

    def _update_crash_recovery(self) -> None:
        """Update crash recovery checkpoint."""
        if not self.enable_checkpoints or self.session_manager is None:
            return
        if not self.session_id:
            return

        from datetime import datetime
        from scripts.agent_checkpoint import AgentCheckpoint
        from scripts.checkpoint_triggers import CheckpointTrigger

        agent_data = self.agent.to_checkpoint_dict()

        checkpoint = AgentCheckpoint(
            current_goal=agent_data["current_goal"],
            visited_coordinates=agent_data["visited_coordinates"],
            current_coords=agent_data["current_coords"],
            direction_history=agent_data["direction_history"],
            talked_this_location=agent_data["talked_this_location"],
            sub_location_moves=agent_data["sub_location_moves"],
            stats=self.stats.to_dict(),
            checkpoint_type="crash_recovery",
            game_save_path="",
            seed=self.seed,
            timestamp=datetime.now().isoformat(),
            command_index=self.stats.commands_issued,
        )

        self.session_manager.update_crash_recovery(checkpoint, self.session_id)

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_id: str,
        session_manager: Optional["SessionManager"] = None,
        **kwargs,
    ) -> "GameSession":
        """Create a GameSession from a checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore from.
            session_manager: SessionManager to use.
            **kwargs: Additional GameSession arguments.

        Returns:
            Restored GameSession.
        """
        if session_manager is None:
            from scripts.agent_persistence import SessionManager
            session_manager = SessionManager()

        # Load checkpoint
        checkpoint = session_manager.load_checkpoint(checkpoint_id)

        # Create session with checkpoint's seed
        session = cls(
            seed=checkpoint.seed,
            session_manager=session_manager,
            **kwargs,
        )

        # Restore agent state
        session.agent.restore_from_checkpoint({
            "current_goal": checkpoint.current_goal,
            "visited_coordinates": checkpoint.visited_coordinates,
            "current_coords": checkpoint.current_coords,
            "direction_history": checkpoint.direction_history,
            "talked_this_location": checkpoint.talked_this_location,
            "sub_location_moves": checkpoint.sub_location_moves,
        })

        # Restore stats (partial - some are derived)
        if "commands_issued" in checkpoint.stats:
            session.stats.commands_issued = checkpoint.stats["commands_issued"]
        if "locations_visited" in checkpoint.stats:
            session.stats.locations_visited = set(checkpoint.stats["locations_visited"])

        return session

    def _load_game_save(self, save_path: str) -> None:
        """Load a game save file (placeholder for future implementation).

        Args:
            save_path: Path to game save file.
        """
        # This would be implemented to load game state from a save file
        # For now, it's a placeholder
        pass

    def run(self) -> SessionStats:
        """Run the game session until max commands or timeout.

        Returns:
            Session statistics
        """
        # Create session for checkpointing if enabled
        if self.enable_checkpoints and self.session_manager and not self.session_id:
            self.session_id = self.session_manager.create_session(self.seed)
            if self.verbose:
                print(f"[SESSION] Created checkpoint session: {self.session_id}")

        self.start()
        start_time = time.time()

        try:
            # Wait for game to initialize and capture initial output
            # The game takes time to start - especially for world generation
            time.sleep(3.0)  # Longer wait for initial world generation
            initial_output = self._read_output(wait_time=3.0, min_lines=1)

            # If no output yet, keep waiting (world generation can take time)
            retry_count = 0
            while len(initial_output) == 0 and retry_count < 5:
                retry_count += 1
                if self.verbose:
                    print(f"[SESSION] Waiting for game output (retry {retry_count})...")
                time.sleep(1.0)
                initial_output = self._read_output(wait_time=1.0, min_lines=1)

            if self.verbose:
                print(f"[SESSION] Initial output: {len(initial_output)} lines")
                for line in initial_output[:5]:
                    print(f"[SESSION]   {line[:100].strip()}...")
            self._process_messages(initial_output)

            # Send look command to refresh state
            self._send_command("look")
            look_lines = self._read_output(wait_time=0.5, min_lines=2)
            self._process_messages(look_lines)
            self._initial_gold = self.state.gold

            # Get full state with dump-state
            self._send_command("dump-state")
            state_lines = self._read_output(wait_time=0.5, min_lines=1)
            self._process_messages(state_lines)

            # If still no exits, try one more look
            if not self.state.exits:
                if self.verbose:
                    print("[SESSION] No exits detected, retrying look")
                self._send_command("look")
                extra_lines = self._read_output(wait_time=0.5, min_lines=2)
                self._process_messages(extra_lines)

            # Debug: show what we captured
            if self.verbose and not self.state.exits:
                print(f"[SESSION] WARNING: Still no exits. State: location={self.state.location}, npcs={self.state.npcs}")
            elif self.verbose:
                print(f"[SESSION] Ready: location={self.state.location}, exits={self.state.exits}")

            # Initialize previous state for trigger detection
            import copy
            self._prev_state = copy.deepcopy(self.state)

            # Main loop
            while self.stats.commands_issued < self.max_commands:
                # Check timeout (skip if infinite)
                if self.timeout != float('inf') and time.time() - start_time > self.timeout:
                    if self.verbose:
                        print("[SESSION] Timeout reached")
                    break

                # Check if process is still running
                if self.process.poll() is not None:
                    if self.verbose:
                        print("[SESSION] Game process ended")
                    break

                # Apply action delay if configured
                if self.action_delay > 0:
                    time.sleep(self.action_delay)

                # Get agent decision
                command = self.agent.decide(self.state)

                # Show command in -vv mode
                if self.show_game_output:
                    print(f"\n>>> {command}")

                self._send_command(command)

                # Wait for and process response
                # Use longer wait for movement commands to allow world generation
                wait = 0.5 if command.startswith("go ") else 0.2
                response_lines = self._read_output(wait_time=wait, min_lines=1)
                self._process_messages(response_lines)

                # Check for checkpoint triggers
                if self.enable_checkpoints and self._prev_state:
                    trigger = self._check_triggers(self._prev_state)
                    if trigger:
                        self._create_checkpoint(trigger)
                    # Update previous state
                    self._prev_state = copy.deepcopy(self.state)

                # Periodically update crash recovery
                if self.enable_checkpoints and self.stats.commands_issued % 10 == 0:
                    self._update_crash_recovery()

                # Periodically refresh full state
                if self.stats.commands_issued % 20 == 0:
                    self._send_command("dump-state")
                    state_lines = self._read_output(wait_time=0.1)
                    self._process_messages(state_lines)

        finally:
            self.stop()
            # Calculate gold earned
            self.stats.gold_earned = self.state.gold - self._initial_gold

        return self.stats
