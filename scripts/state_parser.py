"""State parser for JSON Lines output from CLI-RPG.

Parses JSON messages emitted by --json mode and updates agent state.
"""
import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class QuestInfo:
    """Detailed quest information for agent decision-making.

    Attributes:
        name: Quest name
        objective_type: Type of objective (kill, collect, explore, talk, drop, use)
        target: Target name (enemy type, item, location, or NPC)
        target_count: How many to complete
        current_count: Current progress
        quest_giver: NPC who gave the quest
        status: Quest status (active, ready_to_turn_in, etc.)
    """
    name: str = ""
    objective_type: str = ""
    target: str = ""
    target_count: int = 1
    current_count: int = 0
    quest_giver: Optional[str] = None
    status: str = "active"

    @property
    def is_complete(self) -> bool:
        """Check if objective has been met."""
        return self.current_count >= self.target_count

    @property
    def is_ready_to_turn_in(self) -> bool:
        """Check if quest can be turned in."""
        return self.status == "ready_to_turn_in" or self.is_complete


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
        quest_details: Detailed quest info for tracking objectives
        in_sub_location: Whether currently in a sub-location (dungeon, cave, etc.)
        enterables: List of sub-locations that can be entered
        location_category: Category of current location (town, dungeon, cave, etc.)
        is_exit_point: Whether current location allows exiting to overworld
        has_boss: Whether current location has a boss
        boss_defeated: Whether boss has been defeated
        visited_locations: Set of all locations visited this session
        talked_to_npcs: Set of NPCs talked to in current location
        available_quests: NPCs with available quests to accept
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
    quest_details: list[QuestInfo] = field(default_factory=list)
    in_sub_location: bool = False
    enterables: list[str] = field(default_factory=list)
    location_category: str = ""
    is_exit_point: bool = False
    has_boss: bool = False
    boss_defeated: bool = False
    visited_locations: set[str] = field(default_factory=set)
    talked_to_npcs: set[str] = field(default_factory=set)
    available_quests: list[str] = field(default_factory=list)
    # Track last narrative for context
    last_narrative: str = ""

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

    def get_kill_quest_target(self) -> Optional[str]:
        """Get the target name from an active KILL quest."""
        for quest in self.quest_details:
            if quest.objective_type == "kill" and not quest.is_complete:
                return quest.target
        return None

    def get_explore_quest_target(self) -> Optional[str]:
        """Get the target location from an active EXPLORE quest."""
        for quest in self.quest_details:
            if quest.objective_type == "explore" and not quest.is_complete:
                return quest.target
        return None

    def get_talk_quest_target(self) -> Optional[str]:
        """Get the target NPC from an active TALK quest."""
        for quest in self.quest_details:
            if quest.objective_type == "talk" and not quest.is_complete:
                return quest.target
        return None

    def has_quest_ready_to_turn_in(self) -> bool:
        """Check if any quest is ready to turn in."""
        return any(q.is_ready_to_turn_in for q in self.quest_details)

    def get_quest_giver_for_turnin(self) -> Optional[str]:
        """Get the quest giver NPC for a quest ready to turn in."""
        for quest in self.quest_details:
            if quest.is_ready_to_turn_in and quest.quest_giver:
                return quest.quest_giver
        return None

    def can_enter_location(self) -> bool:
        """Check if there are sub-locations to enter."""
        return len(self.enterables) > 0 and "enter" in self.commands

    def should_exit_sublocation(self) -> bool:
        """Check if agent should exit current sub-location."""
        return self.in_sub_location and self.is_exit_point

    def has_unexplored_exits(self) -> bool:
        """Check if there are exits leading to unvisited locations."""
        # This is a heuristic - we don't know for sure without checking
        return len(self.exits) > 0


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
        # Track visited locations
        if state.location:
            state.visited_locations.add(state.location)

    elif msg_type == "combat":
        state.in_combat = True
        state.enemy = message.get("enemy", "")
        state.enemy_health = message.get("enemy_health", 0)
        # Combat messages also include player health
        if "player_health" in message:
            state.health = message["player_health"]

    elif msg_type == "actions":
        # Merge exits from actions with any parsed from narrative
        # (narrative often has more complete exits)
        json_exits = message.get("exits", [])
        if state.exits:
            # Merge: keep unique, preferring narrative exits first
            seen = set()
            merged = []
            for exit_dir in state.exits + json_exits:
                if exit_dir not in seen:
                    merged.append(exit_dir)
                    seen.add(exit_dir)
            state.exits = merged
        else:
            state.exits = json_exits

        state.npcs = message.get("npcs", [])
        state.commands = message.get("commands", [])
        # Actions are emitted when NOT in combat
        # (combat emits "combat" type messages instead)
        state.in_combat = False
        # Reset talked_to_npcs when NPCs change (new location)
        # We'll track talks via the agent

    elif msg_type == "narrative":
        text = message.get("text", "")
        state.last_narrative = text
        # Parse exits from narrative (often more complete than JSON)
        _parse_exits_from_narrative(state, text)
        # Parse "Enter: ..." from narrative for sub-location detection
        _parse_enterables_from_narrative(state, text)
        # Parse quest availability hints
        _parse_quest_hints_from_narrative(state, text)

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

            # Extract quests with full details
            if "quests" in char:
                state.quests = []
                state.quest_details = []
                for q in char["quests"]:
                    status = q.get("status", "")
                    if status in ("active", "ready_to_turn_in"):
                        state.quests.append(q.get("name", ""))
                        quest_info = QuestInfo(
                            name=q.get("name", ""),
                            objective_type=q.get("objective_type", ""),
                            target=q.get("target", ""),
                            target_count=q.get("target_count", 1),
                            current_count=q.get("current_count", 0),
                            quest_giver=q.get("quest_giver"),
                            status=status,
                        )
                        state.quest_details.append(quest_info)

        if "current_location" in message:
            state.location = message["current_location"]
            state.visited_locations.add(state.location)

        # Extract sub-location state
        state.in_sub_location = message.get("in_sub_location", False)

        # Extract current location details from world
        if "world" in message and state.location:
            loc_data = message["world"].get(state.location, {})
            state.location_category = loc_data.get("category", "")
            state.is_exit_point = loc_data.get("is_exit_point", False)
            state.has_boss = loc_data.get("boss_enemy") is not None
            state.boss_defeated = loc_data.get("boss_defeated", False)

            # Extract enterables from sub_grid or sub_locations
            state.enterables = []
            if "sub_grid" in loc_data and loc_data["sub_grid"]:
                sub_grid = loc_data["sub_grid"]
                if "locations" in sub_grid:
                    locations = sub_grid["locations"]
                    # Handle both dict (keyed by coord) and list formats
                    if isinstance(locations, dict):
                        location_items = locations.values()
                    else:
                        location_items = locations
                    for sub_loc in location_items:
                        if isinstance(sub_loc, dict) and sub_loc.get("is_exit_point", False):
                            state.enterables.append(sub_loc.get("name", ""))
            if "sub_locations" in loc_data:
                state.enterables.extend(loc_data["sub_locations"])


def _parse_enterables_from_narrative(state: AgentState, text: str) -> None:
    """Extract enterable locations from narrative text.

    Looks for patterns like "Enter: Location Name" in the narrative.

    Args:
        state: AgentState to update
        text: Narrative text to parse
    """
    # Look for "Enter:" lines in narrative
    enter_match = re.search(r"Enter:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if enter_match:
        enterables_text = enter_match.group(1).strip()
        # Split by comma for multiple enterables
        enterables = [e.strip() for e in enterables_text.split(",") if e.strip()]
        if enterables:
            state.enterables = enterables


def _parse_exits_from_narrative(state: AgentState, text: str) -> None:
    """Extract exit directions from narrative text.

    The narrative often includes more exits than the JSON (which only shows
    directions with existing locations). Merge narrative exits with JSON exits.

    Args:
        state: AgentState to update
        text: Narrative text to parse
    """
    # Look for "Exits:" lines in narrative
    exits_match = re.search(r"Exits?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if exits_match:
        exits_text = exits_match.group(1).strip()
        # Parse comma-separated or space-separated directions
        valid_dirs = {"north", "south", "east", "west", "up", "down"}
        narrative_exits = []
        for word in re.split(r"[,\s]+", exits_text.lower()):
            word = word.strip()
            if word in valid_dirs:
                narrative_exits.append(word)

        # Merge with existing exits (prefer narrative for completeness)
        if narrative_exits:
            # Keep unique, preserving order
            combined = []
            seen = set()
            for exit_dir in narrative_exits + state.exits:
                if exit_dir not in seen:
                    combined.append(exit_dir)
                    seen.add(exit_dir)
            state.exits = combined


def _parse_quest_hints_from_narrative(state: AgentState, text: str) -> None:
    """Extract quest-related hints from narrative text.

    Args:
        state: AgentState to update
        text: Narrative text to parse
    """
    text_lower = text.lower()
    # Detect quest availability hints
    if "quest" in text_lower and ("available" in text_lower or "offer" in text_lower):
        # NPC might have a quest
        pass  # Agent will try talking to NPCs


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
