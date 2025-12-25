"""JSON output module for non-interactive structured output.

This module provides functions to emit structured JSON Lines output
for machine consumption. Each function prints a single JSON object
per line with a 'type' field indicating the message category.

Message types:
- state: Current game state (location, health, gold, level)
- narrative: Human-readable text (descriptions, action results)
- actions: Available actions (exits, NPCs, valid commands)
- error: Error with machine-readable code and human message
- combat: Combat-specific state when in battle
"""
import json
from typing import List, Optional


# Error codes for machine-readable errors
ERROR_CODES = {
    "invalid_direction": "INVALID_DIRECTION",
    "not_in_shop": "NOT_IN_SHOP",
    "item_not_found": "ITEM_NOT_FOUND",
    "unknown_command": "UNKNOWN_COMMAND",
    "not_in_combat": "NOT_IN_COMBAT",
    "in_conversation": "IN_CONVERSATION",
    "no_npc": "NO_NPC",
    "inventory_full": "INVENTORY_FULL",
    "insufficient_gold": "INSUFFICIENT_GOLD",
}


def emit_state(location: str, health: int, max_health: int, gold: int, level: int) -> None:
    """Emit a state message with current game state.

    Args:
        location: Current location name
        health: Current health points
        max_health: Maximum health points
        gold: Current gold amount
        level: Character level
    """
    print(json.dumps({
        "type": "state",
        "location": location,
        "health": health,
        "max_health": max_health,
        "gold": gold,
        "level": level
    }))


def emit_narrative(text: str) -> None:
    """Emit a narrative message with human-readable text.

    Args:
        text: The narrative text (description, action result, etc.)
    """
    print(json.dumps({"type": "narrative", "text": text}))


def emit_actions(exits: List[str], npcs: List[str], commands: List[str]) -> None:
    """Emit an actions message with available options.

    Args:
        exits: List of available exit directions
        npcs: List of NPC names present
        commands: List of valid commands
    """
    print(json.dumps({
        "type": "actions",
        "exits": exits,
        "npcs": npcs,
        "commands": commands
    }))


def emit_error(code: str, message: str) -> None:
    """Emit an error message with machine-readable code.

    Args:
        code: Machine-readable error code (e.g., "INVALID_DIRECTION")
        message: Human-readable error message
    """
    print(json.dumps({"type": "error", "code": code, "message": message}))


def emit_combat(enemy: str, enemy_health: int, player_health: int) -> None:
    """Emit a combat state message.

    Args:
        enemy: Enemy name
        enemy_health: Current enemy health
        player_health: Current player health
    """
    print(json.dumps({
        "type": "combat",
        "enemy": enemy,
        "enemy_health": enemy_health,
        "player_health": player_health
    }))


def classify_output(message: str) -> tuple[str, Optional[str]]:
    """Classify command output as error or narrative.

    Analyzes the message content to determine if it's an error
    (and which type) or narrative text.

    Args:
        message: The output message to classify

    Returns:
        Tuple of (type, error_code) where:
        - type is 'error' or 'narrative'
        - error_code is the code if type is 'error', None otherwise
    """
    error_patterns = {
        "You can't go that way": "INVALID_DIRECTION",
        "Invalid direction": "INVALID_DIRECTION",
        "You're not at a shop": "NOT_IN_SHOP",
        "Talk to a merchant first": "NOT_IN_SHOP",
        "Unknown command": "UNKNOWN_COMMAND",
        "Not in combat": "NOT_IN_COMBAT",
        "You're in a conversation": "IN_CONVERSATION",
        "need to talk to an NPC": "NO_NPC",
        "There are no NPCs here": "NO_NPC",
        "inventory is full": "INVENTORY_FULL",
        "can't afford": "INSUFFICIENT_GOLD",
        "don't have": "ITEM_NOT_FOUND",
    }
    for pattern, code in error_patterns.items():
        if pattern.lower() in message.lower():
            return ("error", code)
    return ("narrative", None)
