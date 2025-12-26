"""State parser for JSON Lines output from CLI-RPG.

Parses JSON messages emitted by --json mode and updates agent state.
"""
import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentState:
    """Tracks parsed game state for the AI agent.

    Attributes:
        location: Current location name
        health: Current health points
        max_health: Maximum health points
        gold: Current gold amount
        level: Character level
        in_combat: Whether player is in combat
        enemy: Current enemy name (if in combat)
        enemy_health: Current enemy health (if in combat)
        exits: Available exit directions
        npcs: NPCs present at location
        commands: Valid commands at current state
        inventory: List of item names in inventory
        dread: Current dread level (0-100)
        quests: List of active quest names
    """
    location: str = ""
    health: int = 100
    max_health: int = 100
    gold: int = 0
    level: int = 1
    in_combat: bool = False
    enemy: str = ""
    enemy_health: int = 0
    exits: list[str] = field(default_factory=list)
    npcs: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)
    dread: int = 0
    quests: list[str] = field(default_factory=list)

    @property
    def health_percent(self) -> float:
        """Get health as a percentage of max health."""
        if self.max_health <= 0:
            return 0.0
        return self.health / self.max_health

    def has_healing_item(self) -> bool:
        """Check if agent has a healing potion or similar item."""
        healing_keywords = ["potion", "elixir", "heal", "salve", "bandage"]
        for item in self.inventory:
            item_lower = item.lower()
            for keyword in healing_keywords:
                if keyword in item_lower:
                    return True
        return False

    def get_healing_item_name(self) -> Optional[str]:
        """Get the name of a healing item in inventory."""
        healing_keywords = ["potion", "elixir", "heal", "salve", "bandage"]
        for item in self.inventory:
            item_lower = item.lower()
            for keyword in healing_keywords:
                if keyword in item_lower:
                    return item
        return None


def parse_line(line: str) -> Optional[dict[str, Any]]:
    """Parse a single JSON line from game output.

    Args:
        line: A line of text from game stdout

    Returns:
        Parsed JSON dict, or None if line is empty/invalid
    """
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def update_state(state: AgentState, message: dict[str, Any]) -> None:
    """Update agent state from a parsed JSON message.

    Args:
        state: AgentState to update
        message: Parsed JSON message dict
    """
    msg_type = message.get("type")

    if msg_type == "state":
        state.location = message.get("location", state.location)
        state.health = message.get("health", state.health)
        state.max_health = message.get("max_health", state.max_health)
        state.gold = message.get("gold", state.gold)
        state.level = message.get("level", state.level)

    elif msg_type == "combat":
        state.in_combat = True
        state.enemy = message.get("enemy", "")
        state.enemy_health = message.get("enemy_health", 0)
        # Combat messages also include player health
        if "player_health" in message:
            state.health = message["player_health"]

    elif msg_type == "actions":
        state.exits = message.get("exits", [])
        state.npcs = message.get("npcs", [])
        state.commands = message.get("commands", [])
        # Actions are emitted when NOT in combat
        # (combat emits "combat" type messages instead)
        state.in_combat = False

    elif msg_type == "dump_state":
        # Full state snapshot - extract what we need
        if "character" in message:
            char = message["character"]
            state.health = char.get("health", state.health)
            state.max_health = char.get("max_health", state.max_health)
            state.gold = char.get("gold", state.gold)
            state.level = char.get("level", state.level)

            # Extract inventory item names
            if "inventory" in char:
                inv = char["inventory"]
                items = inv.get("items", [])
                state.inventory = [item.get("name", "") for item in items]

            # Extract dread
            if "dread_meter" in char:
                state.dread = char["dread_meter"].get("dread", 0)

            # Extract quests
            if "quests" in char:
                state.quests = [
                    q.get("name", "") for q in char["quests"]
                    if q.get("status") == "active"
                ]

        if "current_location" in message:
            state.location = message["current_location"]


def parse_output_lines(lines: list[str], state: AgentState) -> list[dict[str, Any]]:
    """Parse multiple output lines and update state.

    Args:
        lines: List of output lines from game
        state: AgentState to update

    Returns:
        List of parsed message dicts (excluding None for invalid lines)
    """
    messages = []
    for line in lines:
        msg = parse_line(line)
        if msg is not None:
            update_state(state, msg)
            messages.append(msg)
    return messages
