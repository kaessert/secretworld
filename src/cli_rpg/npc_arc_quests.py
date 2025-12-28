"""Helper functions for NPC arc-based quest prerequisites."""

from typing import Optional, Tuple

from cli_rpg.models.npc_arc import NPCArc

# Stage order from lowest to highest trust level
# Index position indicates trust level (higher = more trust)
ARC_STAGE_ORDER = [
    "enemy",      # 0: Worst relationship
    "hostile",    # 1: Very negative
    "wary",       # 2: Somewhat negative
    "stranger",   # 3: Default/neutral
    "acquaintance",  # 4: Positive
    "trusted",    # 5: High trust
    "devoted",    # 6: Highest trust
]


def get_arc_stage_index(stage_name: str) -> int:
    """Get the numerical index for an arc stage name.

    Args:
        stage_name: The stage name (case-insensitive)

    Returns:
        Index in ARC_STAGE_ORDER, or 3 (stranger) if not found
    """
    stage_lower = stage_name.lower()
    try:
        return ARC_STAGE_ORDER.index(stage_lower)
    except ValueError:
        # Unknown stage defaults to stranger level
        return 3  # stranger index


def check_arc_stage_requirement(
    arc: Optional[NPCArc], required: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """Check if an NPC's arc meets a quest's arc stage requirement.

    Args:
        arc: The NPC's current arc (None treated as STRANGER)
        required: The required arc stage name (None means no requirement)

    Returns:
        Tuple of (allowed, rejection_reason)
        - (True, None) if requirement met or no requirement
        - (False, reason) if requirement not met
    """
    # No requirement = always allowed
    if required is None:
        return (True, None)

    # Get required stage index
    required_index = get_arc_stage_index(required)

    # Get current stage - treat None arc as STRANGER
    if arc is None:
        current_stage = "stranger"
    else:
        current_stage = arc.get_stage().value

    current_index = get_arc_stage_index(current_stage)

    # Check if current >= required
    if current_index >= required_index:
        return (True, None)
    else:
        return (
            False,
            f"Requires {required.lower()} relationship (current: {current_stage})",
        )
