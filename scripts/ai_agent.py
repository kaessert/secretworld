"""AI Agent for autonomous CLI-RPG gameplay.

Uses heuristic-based decision making to play the game via JSON mode.
"""
import queue
import random
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from scripts.state_parser import AgentState, parse_line, update_state


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
        }


class Agent:
    """Heuristic-based decision engine for CLI-RPG.

    Makes contextual decisions based on game state using priority rules.
    """

    def __init__(self, verbose: bool = False):
        """Initialize agent.

        Args:
            verbose: If True, print decision reasoning
        """
        self.verbose = verbose

    def decide(self, state: AgentState) -> str:
        """Determine next command based on current state.

        Args:
            state: Current game state

        Returns:
            Command string to send to game
        """
        if state.in_combat:
            return self._combat_decision(state)
        return self._explore_decision(state)

    def _combat_decision(self, state: AgentState) -> str:
        """Make combat decision.

        Priority:
        1. Flee if HP < 25%
        2. Use potion if HP < 50% and has healing item
        3. Attack otherwise

        Args:
            state: Current game state

        Returns:
            Combat command
        """
        hp_pct = state.health_percent

        # Flee at critical health
        if hp_pct < 0.25:
            if self.verbose:
                print(f"[AGENT] Fleeing - HP critical ({hp_pct:.0%})")
            return "flee"

        # Use healing if hurt and have potion
        if hp_pct < 0.50 and state.has_healing_item():
            potion_name = state.get_healing_item_name()
            if potion_name:
                if self.verbose:
                    print(f"[AGENT] Using {potion_name} - HP low ({hp_pct:.0%})")
                return f"use {potion_name}"

        # Default: attack
        if self.verbose:
            print(f"[AGENT] Attacking - HP ok ({hp_pct:.0%})")
        return "attack"

    def _explore_decision(self, state: AgentState) -> str:
        """Make exploration decision.

        Priority:
        1. Rest if HP < 50% or dread > 60%
        2. Use potion if HP < 30% and has healing item
        3. Buy potion if at shop, gold > 50, no potion
        4. Complete quest if ready (quest turn-in)
        5. Talk to NPC if present (may get quest or info)
        6. Explore - move to random exit

        Args:
            state: Current game state

        Returns:
            Exploration command
        """
        hp_pct = state.health_percent

        # Rest if hurt or high dread
        if hp_pct < 0.50 or state.dread > 60:
            if self.verbose:
                reason = "HP low" if hp_pct < 0.50 else "dread high"
                print(f"[AGENT] Resting - {reason}")
            return "rest"

        # Emergency healing
        if hp_pct < 0.30 and state.has_healing_item():
            potion_name = state.get_healing_item_name()
            if potion_name:
                if self.verbose:
                    print(f"[AGENT] Using {potion_name} - emergency heal")
                return f"use {potion_name}"

        # Buy potion if at shop with enough gold and no potions
        if "shop" in state.commands and state.gold > 50:
            if not state.has_healing_item():
                if self.verbose:
                    print("[AGENT] Buying potion at shop")
                # Try to buy a health potion
                return "buy health potion"

        # Complete quest if ready (only when NPC present AND have active quests)
        if state.npcs and state.quests and "complete" in state.commands:
            if self.verbose:
                print("[AGENT] Completing quest")
            return "complete"

        # Explore: move to random exit (primary gameplay loop - prioritize exploration)
        if state.exits:
            direction = random.choice(state.exits)
            if self.verbose:
                print(f"[AGENT] Moving {direction}")
            return f"go {direction}"

        # Talk to NPC if present and no exits (sub-locations, dead-ends)
        if state.npcs and "talk" in state.commands:
            npc = random.choice(state.npcs)
            if self.verbose:
                print(f"[AGENT] Talking to {npc}")
            return f"talk {npc}"

        # Enter sub-location if available
        if "enter" in state.commands:
            if self.verbose:
                print("[AGENT] Entering location")
            return "enter"

        # Fallback: look around
        if self.verbose:
            print("[AGENT] Looking around (no exits)")
        return "look"


@dataclass
class GameSession:
    """Manages subprocess for CLI-RPG game session.

    Uses unbuffered I/O and a threaded reader to handle real-time
    interaction with the game subprocess.
    """

    seed: int
    max_commands: int = 1000
    timeout: float = 300.0  # seconds
    verbose: bool = False

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
            for line in self.process.stdout:
                if self._stop_reader:
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

    def _read_output(self, wait_time: float = 0.1) -> list[str]:
        """Read available output lines from the queue.

        Args:
            wait_time: Time to wait for output

        Returns:
            List of output lines
        """
        time.sleep(wait_time)

        lines = []
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

    def _process_messages(self, lines: list[str]) -> None:
        """Process output lines and update state/stats.

        Args:
            lines: Output lines from game
        """
        for line in lines:
            msg = parse_line(line)
            if msg is None:
                continue

            update_state(self.state, msg)

            msg_type = msg.get("type")

            # Track location visits
            if msg_type == "state" and self.state.location:
                self.stats.locations_visited.add(self.state.location)

            # Track errors
            if msg_type == "error":
                self.stats.errors_encountered += 1

            # Track enemy defeats (look for narrative about defeating)
            if msg_type == "narrative":
                text = msg.get("text", "").lower()
                if "defeated" in text or "slain" in text or "killed" in text:
                    self.stats.enemies_defeated += 1
                if "you died" in text or "you have died" in text:
                    self.stats.deaths += 1

    def run(self) -> SessionStats:
        """Run the game session until max commands or timeout.

        Returns:
            Session statistics
        """
        self.start()
        start_time = time.time()

        try:
            # Send initial look command to get game state
            self._send_command("look")
            initial_lines = self._read_output(wait_time=0.3)
            self._process_messages(initial_lines)
            self._initial_gold = self.state.gold

            # Get full state with dump-state
            self._send_command("dump-state")
            state_lines = self._read_output(wait_time=0.2)
            self._process_messages(state_lines)

            # Main loop
            while self.stats.commands_issued < self.max_commands:
                # Check timeout
                if time.time() - start_time > self.timeout:
                    if self.verbose:
                        print("[SESSION] Timeout reached")
                    break

                # Check if process is still running
                if self.process.poll() is not None:
                    if self.verbose:
                        print("[SESSION] Game process ended")
                    break

                # Get agent decision
                command = self.agent.decide(self.state)
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
