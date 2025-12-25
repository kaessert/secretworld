"""Companion quest management.

Handles personal quests for companions that unlock at higher bond levels.
Each companion can have a personal quest that becomes available when their bond
reaches TRUSTED (50+ points). Completing the quest provides bond points and
unique rewards.
"""

from typing import Optional

from cli_rpg.models.companion import Companion, BondLevel
from cli_rpg.models.quest import Quest, QuestStatus
from cli_rpg import colors


# Bond points awarded when completing a companion's personal quest
QUEST_COMPLETION_BOND_BONUS = 15

# Minimum bond level required to unlock personal quests
QUEST_UNLOCK_LEVEL = BondLevel.TRUSTED


def is_quest_available(companion: Companion) -> bool:
    """Check if companion's personal quest is available.

    A quest is available when:
    - The companion has a personal_quest defined
    - The bond level is TRUSTED or DEVOTED (50+ points)

    Args:
        companion: The companion to check

    Returns:
        True if quest is available, False otherwise
    """
    if companion.personal_quest is None:
        return False
    bond_level = companion.get_bond_level()
    return bond_level in (BondLevel.TRUSTED, BondLevel.DEVOTED)


def accept_companion_quest(companion: Companion) -> Optional[Quest]:
    """Accept a companion's personal quest, returning an ACTIVE copy for the player.

    Creates a copy of the quest with:
    - Status set to ACTIVE
    - quest_giver set to the companion's name

    Args:
        companion: The companion whose quest to accept

    Returns:
        A new Quest instance ready for the player's quest log, or None if
        the quest is not available
    """
    if not is_quest_available(companion):
        return None

    quest = companion.personal_quest
    if quest is None:
        return None

    return Quest(
        name=quest.name,
        description=quest.description,
        objective_type=quest.objective_type,
        target=quest.target,
        target_count=quest.target_count,
        status=QuestStatus.ACTIVE,
        gold_reward=quest.gold_reward,
        xp_reward=quest.xp_reward,
        item_rewards=quest.item_rewards.copy() if quest.item_rewards else [],
        quest_giver=companion.name,
        drop_item=quest.drop_item,
    )


def check_companion_quest_completion(
    companion: Companion,
    completed_quest_name: str
) -> list[str]:
    """Check if completed quest matches companion's personal quest and award bonus.

    When a player completes a quest that matches a companion's personal quest,
    the companion receives a significant bond bonus and flavor messages are returned.

    Args:
        companion: The companion to check
        completed_quest_name: Name of the quest that was just completed

    Returns:
        List of messages to display (empty if quest doesn't match)
    """
    messages: list[str] = []

    if companion.personal_quest is None:
        return messages

    if companion.personal_quest.name != completed_quest_name:
        return messages

    # Award bond bonus
    level_msg = companion.add_bond(QUEST_COMPLETION_BOND_BONUS)

    # Add flavor message about strengthened bond
    messages.append(colors.companion(
        f"{companion.name}'s trust in you deepens. \"I won't forget what you've done for me.\""
    ))

    # Include level-up message if applicable
    if level_msg:
        messages.append(level_msg)

    return messages
