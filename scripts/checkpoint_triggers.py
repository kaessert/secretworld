"""Checkpoint trigger detection for agent simulations.

Defines checkpoint trigger types and detection logic for identifying
when to create checkpoints during gameplay.
"""
from enum import Enum, auto
from typing import Optional

from scripts.state_parser import AgentState


class CheckpointTrigger(Enum):
    """Types of events that trigger checkpoint creation."""

    QUEST_ACCEPT = auto()
    QUEST_COMPLETE = auto()
    DUNGEON_ENTRY = auto()
    DUNGEON_EXIT = auto()
    BOSS_ENCOUNTER = auto()
    BOSS_DEFEAT = auto()
    DEATH = auto()
    LEVEL_UP = auto()
    INTERVAL = auto()  # Every 50 commands
    CRASH_RECOVERY = auto()


# Keywords that indicate boss enemies
BOSS_KEYWORDS = frozenset([
    "boss",
    "ancient",
    "fearsome",
    "mighty",
    "lord",
    "king",
    "queen",
    "dragon",
    "demon",
    "lich",
])


def _is_boss_encounter(curr_state: AgentState) -> bool:
    """Check if current combat is a boss encounter.

    Args:
        curr_state: Current game state.

    Returns:
        True if fighting a boss enemy.
    """
    if not curr_state.in_combat or not curr_state.enemy:
        return False

    # Check enemy name for boss keywords
    enemy_lower = curr_state.enemy.lower()
    if any(keyword in enemy_lower for keyword in BOSS_KEYWORDS):
        return True

    # Check narrative for boss indicators
    narrative_lower = curr_state.last_narrative.lower()
    if "boss" in narrative_lower or "fearsome" in narrative_lower:
        return True

    # Check if location has boss flag
    if curr_state.has_boss:
        return True

    return False


def detect_trigger(
    prev_state: AgentState,
    curr_state: AgentState,
    command_count: int,
) -> Optional[CheckpointTrigger]:
    """Detect if a checkpoint trigger has occurred.

    Compares previous and current state to identify significant events
    that warrant creating a checkpoint.

    Args:
        prev_state: State before the command.
        curr_state: State after the command.
        command_count: Total commands issued so far.

    Returns:
        CheckpointTrigger if an event was detected, None otherwise.
    """
    # Priority 1: Death (most critical)
    if _detect_death(prev_state, curr_state):
        return CheckpointTrigger.DEATH

    # Priority 2: Boss defeat
    if _detect_boss_defeat(prev_state, curr_state):
        return CheckpointTrigger.BOSS_DEFEAT

    # Priority 3: Boss encounter (save before fighting)
    if _detect_boss_encounter(prev_state, curr_state):
        return CheckpointTrigger.BOSS_ENCOUNTER

    # Priority 4: Level up
    if _detect_level_up(prev_state, curr_state):
        return CheckpointTrigger.LEVEL_UP

    # Priority 5: Quest completion
    if _detect_quest_complete(prev_state, curr_state):
        return CheckpointTrigger.QUEST_COMPLETE

    # Priority 6: Quest acceptance
    if _detect_quest_accept(prev_state, curr_state):
        return CheckpointTrigger.QUEST_ACCEPT

    # Priority 7: Dungeon entry
    if _detect_dungeon_entry(prev_state, curr_state):
        return CheckpointTrigger.DUNGEON_ENTRY

    # Priority 8: Dungeon exit
    if _detect_dungeon_exit(prev_state, curr_state):
        return CheckpointTrigger.DUNGEON_EXIT

    # Priority 9: Interval checkpoint (every 50 commands)
    if _detect_interval(command_count):
        return CheckpointTrigger.INTERVAL

    return None


def _detect_death(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect player death."""
    # Check for health dropping to 0
    if curr_state.health <= 0 and prev_state.health > 0:
        return True

    # Check narrative for death indicators
    narrative_lower = curr_state.last_narrative.lower()
    death_indicators = ["you died", "you have died", "you are dead", "death"]
    return any(indicator in narrative_lower for indicator in death_indicators)


def _detect_boss_defeat(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect boss defeat."""
    # Was in combat with boss, now boss is defeated
    if prev_state.in_combat and prev_state.has_boss and not prev_state.boss_defeated:
        if curr_state.boss_defeated:
            return True

    # Check narrative for boss defeat
    if prev_state.in_combat and _is_boss_encounter(prev_state):
        if not curr_state.in_combat:
            narrative_lower = curr_state.last_narrative.lower()
            defeat_indicators = ["defeated", "slain", "vanquished", "victory"]
            if any(indicator in narrative_lower for indicator in defeat_indicators):
                return True

    return False


def _detect_boss_encounter(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect entering combat with a boss."""
    # Transitioned into combat with a boss
    if not prev_state.in_combat and curr_state.in_combat:
        return _is_boss_encounter(curr_state)
    return False


def _detect_level_up(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect character level up."""
    return curr_state.level > prev_state.level


def _detect_quest_complete(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect quest completion."""
    # Check for ready_to_turn_in status change
    prev_ready = set()
    for quest in prev_state.quest_details:
        if quest.is_ready_to_turn_in:
            prev_ready.add(quest.name)

    curr_ready = set()
    for quest in curr_state.quest_details:
        if quest.is_ready_to_turn_in:
            curr_ready.add(quest.name)

    # New quest became ready to turn in
    new_ready = curr_ready - prev_ready
    if new_ready:
        return True

    # Quest was removed (turned in)
    prev_quests = set(prev_state.quests)
    curr_quests = set(curr_state.quests)
    completed = prev_quests - curr_quests
    if completed:
        narrative_lower = curr_state.last_narrative.lower()
        if "quest complete" in narrative_lower or "completed" in narrative_lower:
            return True

    return False


def _detect_quest_accept(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect quest acceptance."""
    prev_quests = set(prev_state.quests)
    curr_quests = set(curr_state.quests)

    # New quests added
    new_quests = curr_quests - prev_quests
    return len(new_quests) > 0


def _detect_dungeon_entry(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect entering a sub-location (dungeon, cave, etc.)."""
    return not prev_state.in_sub_location and curr_state.in_sub_location


def _detect_dungeon_exit(prev_state: AgentState, curr_state: AgentState) -> bool:
    """Detect exiting a sub-location."""
    return prev_state.in_sub_location and not curr_state.in_sub_location


def _detect_interval(command_count: int) -> bool:
    """Detect interval checkpoint (every 50 commands)."""
    return command_count > 0 and command_count % 50 == 0
