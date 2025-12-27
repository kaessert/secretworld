"""AI Agent for autonomous CLI-RPG gameplay.

Uses heuristic-based decision making to play the game via JSON mode.
Supports sophisticated exploration including dungeons, sub-locations,
and quest-driven behavior.
"""
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

    def decide(self, state: AgentState) -> str:
        """Determine next command based on current state.

        Args:
            state: Current game state

        Returns:
            Command string to send to game
        """
        # Detect stuck state (same location, no progress)
        if state.location == self.last_location:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
            self.last_location = state.location
            # Reset talked set when location changes
            self.talked_this_location.clear()

        if state.in_combat:
            return self._combat_decision(state)

        # Update goal based on state
        self._update_goal(state)

        return self._explore_decision(state)

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

        # Flee at critical health
        if hp_pct < 0.20:
            if self.verbose:
                print(f"[AGENT] Fleeing - HP critical ({hp_pct:.0%})")
            return "flee"

        # Use healing if hurt and have potion
        if hp_pct < 0.40 and state.has_healing_item():
            potion_name = state.get_healing_item_name()
            if potion_name:
                if self.verbose:
                    print(f"[AGENT] Using {potion_name} - HP low ({hp_pct:.0%})")
                return f"use {potion_name}"

        # Check if this enemy matches a kill quest target
        quest_target = state.get_kill_quest_target()
        if quest_target and quest_target.lower() in state.enemy.lower():
            if self.verbose:
                print(f"[AGENT] Attacking quest target: {state.enemy}")

        # Default: attack
        if self.verbose:
            print(f"[AGENT] Attacking {state.enemy} - HP ok ({hp_pct:.0%})")
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

    def _overworld_exploration_decision(self, state: AgentState) -> str:
        """Default exploration decision for overworld.

        Args:
            state: Current game state

        Returns:
            Exploration command
        """
        hp_pct = state.health_percent

        # Say bye if in conversation (has "bye" available but no other conversation indicators)
        if "bye" in state.commands:
            if self.verbose:
                print("[AGENT] Saying bye")
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
                return "accept"
        else:
            # Reset accept attempts when we move to a new context
            self._accept_attempts = 0

        # Explore: move to random exit (PRIORITIZE MOVEMENT)
        if state.exits:
            direction = random.choice(state.exits)
            if self.verbose:
                print(f"[AGENT] Moving {direction}")
            return f"go {direction}"

        # Talk to NPCs to get quests (if not already talked)
        for npc in state.npcs:
            if npc not in self.talked_this_location:
                self.talked_this_location.add(npc)
                if self.verbose:
                    print(f"[AGENT] Talking to {npc}")
                return f"talk {npc}"

        # Buy potions at shop if needed
        if "shop" in state.commands and state.gold > 50:
            if not state.has_healing_item():
                if self.verbose:
                    print("[AGENT] Buying potion at shop")
                return "buy health potion"

        # Enter sub-locations (dungeons, caves) when healthy
        if state.enterables and hp_pct > 0.70 and self.failed_enter_attempts < 3:
            enterable = state.enterables[0]
            if self.verbose:
                print(f"[AGENT] Entering sub-location: {enterable}")
            self.failed_enter_attempts = 0
            return f"enter {enterable}"

        # Reset failed attempts if we've moved on
        if state.exits:
            self.failed_enter_attempts = 0

        # Try generic enter if available
        if "enter" in state.commands and self.failed_enter_attempts < 2:
            self.failed_enter_attempts += 1
            if self.verbose:
                print("[AGENT] Entering location")
            return "enter"

        # Stuck detection: if we've been stuck, try different commands
        if self.stuck_counter > 3:
            self.stuck_counter = 0
            if state.npcs and "talk" in state.commands:
                npc = random.choice(state.npcs)
                if self.verbose:
                    print(f"[AGENT] Stuck - trying to talk to {npc}")
                return f"talk {npc}"
            # Try a random direction even if not in exits
            random_dirs = ["north", "south", "east", "west"]
            direction = random.choice(random_dirs)
            if self.verbose:
                print(f"[AGENT] Stuck - trying random direction: {direction}")
            return f"go {direction}"

        # Fallback: look around to refresh state
        if self.verbose:
            print("[AGENT] Looking around (fallback)")
        return "look"


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

    process: Optional[subprocess.Popen] = field(default=None, init=False)
    state: AgentState = field(default_factory=AgentState, init=False)
    stats: SessionStats = field(default_factory=SessionStats, init=False)
    agent: Agent = field(default=None, init=False)
    _initial_gold: int = field(default=0, init=False)
    _output_queue: queue.Queue = field(default_factory=queue.Queue, init=False)
    _reader_thread: Optional[threading.Thread] = field(default=None, init=False)
    _stop_reader: bool = field(default=False, init=False)

    def __post_init__(self):
        self.agent = Agent(verbose=self.verbose)

    def _reader_worker(self) -> None:
        """Background thread that reads stdout lines into a queue."""
        try:
            while not self._stop_reader:
                line = self.process.stdout.readline()
                if not line:  # EOF
                    break
                self._output_queue.put(line)
        except (ValueError, OSError):
            pass  # Process closed

    def start(self) -> None:
        """Start the game subprocess and reader thread."""
        import os

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
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,  # Unbuffered
            env=env,
        )

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

    def run(self) -> SessionStats:
        """Run the game session until max commands or timeout.

        Returns:
            Session statistics
        """
        self.start()
        start_time = time.time()

        try:
            # Wait for game to initialize and capture initial output
            # The game emits session_info, state, narrative, actions immediately
            time.sleep(0.3)
            initial_output = self._read_output(wait_time=1.0, min_lines=3)
            if self.verbose:
                print(f"[SESSION] Initial output: {len(initial_output)} lines")
                for line in initial_output[:5]:
                    print(f"[SESSION]   {line[:100]}...")
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
                response_lines = self._read_output(wait_time=0.15)
                self._process_messages(response_lines)

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
