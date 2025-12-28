"""Procedural quest generation with template-based structure.

This module provides quest templates that define procedural structure (objective type,
difficulty scaling, reward formulas) while ContentLayer fills in narrative content
(name, description, target names) via AI or fallback.

Architecture:
- QuestTemplateType: Enum of quest archetype types
- QuestTemplate: Blueprint for procedurally generated quests
- QUEST_TEMPLATES: Dict mapping location category -> list of templates
- QUEST_CHAINS: Dict mapping chain_id -> list of templates for multi-quest arcs
- select_quest_template(): Deterministic template selection
- scale_quest_difficulty(): Calculate scaled values based on player/danger level
- generate_quest_chain(): Create a linked chain of quests
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from cli_rpg.models.quest import ObjectiveType, Quest, QuestDifficulty, QuestStatus


class QuestTemplateType(Enum):
    """Quest template archetypes for procedural generation.

    Each type defines a general quest structure that can be populated
    with thematic content.
    """

    KILL_BOSS = "kill_boss"  # Kill a boss enemy
    KILL_MOBS = "kill_mobs"  # Kill X creatures
    COLLECT_ITEMS = "collect"  # Collect X items
    EXPLORE_AREA = "explore"  # Reach a specific location
    TALK_NPC = "talk"  # Talk to an NPC
    ESCORT = "escort"  # Escort NPC to destination
    FETCH = "fetch"  # Retrieve item from location


@dataclass
class QuestTemplate:
    """Blueprint for procedurally generated quests.

    Defines the structural parameters that determine quest behavior
    while leaving narrative content (name, description, targets) to
    be filled by ContentLayer.

    Attributes:
        template_type: The archetype of this quest template.
        objective_type: Maps to existing Quest.objective_type for mechanics.
        base_target_count: Base number of targets (e.g., 5 for "kill 5 wolves").
        difficulty_scaling: Multiplier applied based on player level.
        base_gold_reward: Base gold reward before scaling.
        base_xp_reward: Base XP reward before scaling.
        category_tags: Location categories where this template spawns.
        chain_position: 0 for standalone, 1+ for position in a chain.
    """

    template_type: QuestTemplateType
    objective_type: ObjectiveType
    base_target_count: int
    difficulty_scaling: float
    base_gold_reward: int
    base_xp_reward: int
    category_tags: list[str] = field(default_factory=list)
    chain_position: int = 0


# =============================================================================
# QUEST_TEMPLATES: Category -> List of QuestTemplate
# =============================================================================

QUEST_TEMPLATES: dict[str, list[QuestTemplate]] = {
    "dungeon": [
        QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=2.0,
            base_gold_reward=200,
            base_xp_reward=100,
            category_tags=["dungeon"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.2,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["dungeon"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.COLLECT_ITEMS,
            objective_type=ObjectiveType.COLLECT,
            base_target_count=3,
            difficulty_scaling=1.0,
            base_gold_reward=80,
            base_xp_reward=40,
            category_tags=["dungeon"],
        ),
    ],
    "cave": [
        QuestTemplate(
            template_type=QuestTemplateType.KILL_MOBS,
            objective_type=ObjectiveType.KILL,
            base_target_count=5,
            difficulty_scaling=1.3,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["cave"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.COLLECT_ITEMS,
            objective_type=ObjectiveType.COLLECT,
            base_target_count=4,
            difficulty_scaling=0.8,
            base_gold_reward=60,
            base_xp_reward=30,
            category_tags=["cave"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=0.6,
            base_gold_reward=50,
            base_xp_reward=25,
            category_tags=["cave"],
        ),
    ],
    "ruins": [
        QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.5,
            base_gold_reward=120,
            base_xp_reward=60,
            category_tags=["ruins"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.COLLECT_ITEMS,
            objective_type=ObjectiveType.COLLECT,
            base_target_count=2,
            difficulty_scaling=1.2,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["ruins"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=2.2,
            base_gold_reward=250,
            base_xp_reward=125,
            category_tags=["ruins"],
        ),
    ],
    "temple": [
        QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=0.5,
            base_gold_reward=40,
            base_xp_reward=20,
            category_tags=["temple"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.3,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["temple"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.ESCORT,
            objective_type=ObjectiveType.EXPLORE,  # Escort uses explore mechanics
            base_target_count=1,
            difficulty_scaling=1.5,
            base_gold_reward=150,
            base_xp_reward=75,
            category_tags=["temple"],
        ),
    ],
    "town": [
        QuestTemplate(
            template_type=QuestTemplateType.FETCH,
            objective_type=ObjectiveType.COLLECT,  # Fetch uses collect mechanics
            base_target_count=1,
            difficulty_scaling=0.8,
            base_gold_reward=60,
            base_xp_reward=30,
            category_tags=["town"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=0.4,
            base_gold_reward=30,
            base_xp_reward=15,
            category_tags=["town"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.ESCORT,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.0,
            base_gold_reward=80,
            base_xp_reward=40,
            category_tags=["town"],
        ),
    ],
    "village": [
        QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=0.3,
            base_gold_reward=25,
            base_xp_reward=10,
            category_tags=["village"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.FETCH,
            objective_type=ObjectiveType.COLLECT,
            base_target_count=1,
            difficulty_scaling=0.6,
            base_gold_reward=40,
            base_xp_reward=20,
            category_tags=["village"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.COLLECT_ITEMS,
            objective_type=ObjectiveType.COLLECT,
            base_target_count=3,
            difficulty_scaling=0.5,
            base_gold_reward=50,
            base_xp_reward=25,
            category_tags=["village"],
        ),
    ],
    "default": [
        QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.0,
            base_gold_reward=50,
            base_xp_reward=25,
            category_tags=["default"],
        ),
        QuestTemplate(
            template_type=QuestTemplateType.KILL_MOBS,
            objective_type=ObjectiveType.KILL,
            base_target_count=3,
            difficulty_scaling=1.0,
            base_gold_reward=75,
            base_xp_reward=35,
            category_tags=["default"],
        ),
    ],
}


# =============================================================================
# QUEST_CHAINS: chain_id -> List of QuestTemplate (with chain_position set)
# =============================================================================

QUEST_CHAINS: dict[str, list[QuestTemplate]] = {
    "lost_artifact": [
        QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=0.5,
            base_gold_reward=25,
            base_xp_reward=15,
            category_tags=["town", "village"],
            chain_position=1,
        ),
        QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.0,
            base_gold_reward=75,
            base_xp_reward=40,
            category_tags=["ruins", "dungeon"],
            chain_position=2,
        ),
        QuestTemplate(
            template_type=QuestTemplateType.COLLECT_ITEMS,
            objective_type=ObjectiveType.COLLECT,
            base_target_count=1,
            difficulty_scaling=1.5,
            base_gold_reward=150,
            base_xp_reward=75,
            category_tags=["ruins", "dungeon"],
            chain_position=3,
        ),
    ],
    "goblin_war": [
        QuestTemplate(
            template_type=QuestTemplateType.KILL_MOBS,
            objective_type=ObjectiveType.KILL,
            base_target_count=5,
            difficulty_scaling=0.8,
            base_gold_reward=50,
            base_xp_reward=30,
            category_tags=["cave", "dungeon"],
            chain_position=1,
        ),
        QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.2,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["cave", "dungeon"],
            chain_position=2,
        ),
        QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=2.5,
            base_gold_reward=300,
            base_xp_reward=150,
            category_tags=["cave", "dungeon"],
            chain_position=3,
        ),
    ],
    "temple_corruption": [
        QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=0.4,
            base_gold_reward=20,
            base_xp_reward=10,
            category_tags=["temple"],
            chain_position=1,
        ),
        QuestTemplate(
            template_type=QuestTemplateType.COLLECT_ITEMS,
            objective_type=ObjectiveType.COLLECT,
            base_target_count=3,
            difficulty_scaling=1.0,
            base_gold_reward=80,
            base_xp_reward=40,
            category_tags=["temple"],
            chain_position=2,
        ),
        QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=2.0,
            base_gold_reward=250,
            base_xp_reward=125,
            category_tags=["temple"],
            chain_position=3,
        ),
    ],
}


# =============================================================================
# Quest Name/Description Templates for Fallback
# =============================================================================

# Name templates by QuestTemplateType (filled by ContentLayer)
QUEST_NAME_TEMPLATES: dict[QuestTemplateType, list[str]] = {
    QuestTemplateType.KILL_BOSS: [
        "Slay the {target}",
        "Defeat the {target}",
        "End of the {target}",
        "The {target} Must Fall",
    ],
    QuestTemplateType.KILL_MOBS: [
        "Clear the {target}",
        "Hunt the {target}",
        "Exterminate {target}",
        "Cull the {target}",
    ],
    QuestTemplateType.COLLECT_ITEMS: [
        "Gather {target}",
        "Collect {target}",
        "Retrieve {target}",
        "Acquire {target}",
    ],
    QuestTemplateType.EXPLORE_AREA: [
        "Explore the {target}",
        "Chart the {target}",
        "Discover {target}",
        "Venture to {target}",
    ],
    QuestTemplateType.TALK_NPC: [
        "Seek the {target}",
        "Speak with {target}",
        "Consult the {target}",
        "Find {target}",
    ],
    QuestTemplateType.ESCORT: [
        "Escort {target}",
        "Protect {target}",
        "Guide {target}",
        "Safeguard {target}",
    ],
    QuestTemplateType.FETCH: [
        "Fetch the {target}",
        "Bring Back {target}",
        "Retrieve the {target}",
        "Obtain {target}",
    ],
}

# Description templates by QuestTemplateType
QUEST_DESCRIPTION_TEMPLATES: dict[QuestTemplateType, list[str]] = {
    QuestTemplateType.KILL_BOSS: [
        "A powerful {target} threatens the region. It must be stopped.",
        "The {target} has terrorized too many. End its reign.",
        "Defeat the fearsome {target} and claim your reward.",
    ],
    QuestTemplateType.KILL_MOBS: [
        "The area is overrun with {target}. Thin their numbers.",
        "Too many {target} threaten travelers. Deal with them.",
        "Clear the {target} infestation for the locals.",
    ],
    QuestTemplateType.COLLECT_ITEMS: [
        "Valuable {target} can be found in this area. Bring some back.",
        "Gather {target} for those who need them.",
        "Collect rare {target} from the surroundings.",
    ],
    QuestTemplateType.EXPLORE_AREA: [
        "The {target} holds secrets waiting to be discovered.",
        "Map the unknown reaches of {target}.",
        "Explore {target} and report what you find.",
    ],
    QuestTemplateType.TALK_NPC: [
        "Find and speak with {target} about important matters.",
        "Seek wisdom from {target}.",
        "Deliver a message to {target}.",
    ],
    QuestTemplateType.ESCORT: [
        "Safely escort {target} to their destination.",
        "Protect {target} from dangers along the way.",
        "Guide {target} through dangerous territory.",
    ],
    QuestTemplateType.FETCH: [
        "Retrieve the valuable {target} and bring it back.",
        "Obtain {target} from a distant location.",
        "Fetch the precious {target} for a reward.",
    ],
}


def select_quest_template(category: str, seed: int) -> QuestTemplate:
    """Select a quest template deterministically based on category and seed.

    Args:
        category: The location category (dungeon, cave, town, etc.)
        seed: Random seed for deterministic selection.

    Returns:
        A QuestTemplate from the category's template list.
    """
    rng = random.Random(seed)

    # Get templates for category, fall back to default
    templates = QUEST_TEMPLATES.get(category.lower(), QUEST_TEMPLATES["default"])

    return rng.choice(templates)


def scale_quest_difficulty(
    template: QuestTemplate,
    player_level: int,
    danger_level: int,
) -> dict:
    """Calculate scaled quest values based on player level and danger.

    Applies the difficulty scaling formula from the spec:
    - difficulty = based on player_level * region_danger_level * template_scaling
    - target_count = base_target_count + (player_level // 3)
    - gold_reward = base_gold_reward * (1 + player_level * 0.1) * difficulty_multiplier
    - xp_reward = base_xp_reward * (1 + player_level * 0.15) * difficulty_multiplier

    Args:
        template: The QuestTemplate to scale.
        player_level: The player's current level.
        danger_level: The region's danger level (1-3 typically).

    Returns:
        Dict with 'difficulty', 'target_count', 'gold_reward', 'xp_reward',
        'recommended_level'.
    """
    # Calculate composite difficulty score
    difficulty_score = player_level * danger_level * template.difficulty_scaling

    # Map score to QuestDifficulty
    if difficulty_score < 3:
        difficulty = QuestDifficulty.TRIVIAL
        diff_multiplier = 0.5
    elif difficulty_score < 6:
        difficulty = QuestDifficulty.EASY
        diff_multiplier = 0.75
    elif difficulty_score < 12:
        difficulty = QuestDifficulty.NORMAL
        diff_multiplier = 1.0
    elif difficulty_score < 20:
        difficulty = QuestDifficulty.HARD
        diff_multiplier = 1.5
    else:
        difficulty = QuestDifficulty.DEADLY
        diff_multiplier = 2.0

    # Scale target count
    target_count = template.base_target_count + (player_level // 3)

    # Scale rewards
    level_gold_mult = 1 + player_level * 0.1
    level_xp_mult = 1 + player_level * 0.15

    gold_reward = int(template.base_gold_reward * level_gold_mult * diff_multiplier)
    xp_reward = int(template.base_xp_reward * level_xp_mult * diff_multiplier)

    # Calculate recommended level
    recommended_level = max(1, int(difficulty_score / template.difficulty_scaling))

    return {
        "difficulty": difficulty,
        "target_count": target_count,
        "gold_reward": gold_reward,
        "xp_reward": xp_reward,
        "recommended_level": recommended_level,
    }


def generate_quest_chain(
    chain_id: str,
    player_level: int,
    seed: int,
    content_callback: Optional[callable] = None,
) -> list[Quest]:
    """Generate a linked chain of quests from a chain template.

    Creates Quest objects with proper prerequisite and unlocks links.

    Args:
        chain_id: The ID of the quest chain to generate.
        player_level: The player's level for difficulty scaling.
        seed: Random seed for deterministic content generation.
        content_callback: Optional callback for AI content generation.
            Should take (template_type, category, seed) and return
            dict with 'name', 'description', 'target'.

    Returns:
        List of Quest objects with proper chain links, or empty list
        if chain_id is not found.
    """
    if chain_id not in QUEST_CHAINS:
        return []

    chain_templates = QUEST_CHAINS[chain_id]
    rng = random.Random(seed)

    quests: list[Quest] = []

    for i, template in enumerate(chain_templates):
        # Scale difficulty for this step
        danger_level = 1 + (i * 0.5)  # Danger increases through chain
        scaled = scale_quest_difficulty(template, player_level, int(danger_level))

        # Generate content
        content_seed = rng.randint(0, 2**31)
        if content_callback:
            content = content_callback(
                template.template_type,
                template.category_tags[0] if template.category_tags else "default",
                content_seed,
            )
        else:
            # Fallback content generation
            content = _generate_fallback_quest_content(
                template.template_type,
                template.category_tags[0] if template.category_tags else "default",
                content_seed,
            )

        # Create quest
        quest = Quest(
            name=content["name"],
            description=content["description"],
            objective_type=template.objective_type,
            target=content["target"],
            target_count=scaled["target_count"],
            gold_reward=scaled["gold_reward"],
            xp_reward=scaled["xp_reward"],
            difficulty=scaled["difficulty"],
            recommended_level=scaled["recommended_level"],
            chain_id=chain_id,
            chain_position=template.chain_position,
            status=QuestStatus.AVAILABLE,
        )

        quests.append(quest)

    # Link prerequisites and unlocks
    for i in range(len(quests)):
        if i > 0:
            quests[i].prerequisite_quests = [quests[i - 1].name]
        if i < len(quests) - 1:
            quests[i].unlocks_quests = [quests[i + 1].name]

    return quests


def _generate_fallback_quest_content(
    template_type: QuestTemplateType,
    category: str,
    seed: int,
) -> dict:
    """Generate fallback quest content using templates.

    Args:
        template_type: The type of quest template.
        category: The location category.
        seed: Random seed for selection.

    Returns:
        Dict with 'name', 'description', 'target'.
    """
    rng = random.Random(seed)

    # Target name pools by template type and category
    target_pools: dict[QuestTemplateType, dict[str, list[str]]] = {
        QuestTemplateType.KILL_BOSS: {
            "dungeon": ["Dark Lord", "Dungeon Master", "Shadow King"],
            "cave": ["Cave Beast", "Giant Spider", "Stone Golem"],
            "ruins": ["Ancient Guardian", "Ruin Spirit", "Forgotten King"],
            "temple": ["Corrupted High Priest", "Temple Avatar", "Fallen Deity"],
            "default": ["Fearsome Monster", "Ancient Evil", "Dark Entity"],
        },
        QuestTemplateType.KILL_MOBS: {
            "dungeon": ["Skeletons", "Goblins", "Undead"],
            "cave": ["Cave Spiders", "Bats", "Cave Trolls"],
            "ruins": ["Stone Guardians", "Ghosts", "Haunted Spirits"],
            "temple": ["Corrupted Priests", "Temple Guards", "Zealots"],
            "default": ["Monsters", "Creatures", "Enemies"],
        },
        QuestTemplateType.COLLECT_ITEMS: {
            "dungeon": ["Ancient Coins", "Dungeon Keys", "Old Scrolls"],
            "cave": ["Rare Crystals", "Cave Mushrooms", "Glowing Gems"],
            "ruins": ["Artifacts", "Relic Shards", "Ancient Texts"],
            "temple": ["Sacred Relics", "Holy Symbols", "Prayer Beads"],
            "default": ["Valuable Items", "Rare Objects", "Collectibles"],
        },
        QuestTemplateType.EXPLORE_AREA: {
            "dungeon": ["Deep Chambers", "Hidden Vault", "Lower Depths"],
            "cave": ["Crystal Cavern", "Underground Lake", "Deep Tunnels"],
            "ruins": ["Lost Library", "Ancient Temple", "Forgotten Halls"],
            "temple": ["Inner Sanctum", "Sacred Grove", "Holy Shrine"],
            "default": ["Unknown Region", "Unexplored Area", "Hidden Place"],
        },
        QuestTemplateType.TALK_NPC: {
            "dungeon": ["Imprisoned Sage", "Lost Explorer", "Dungeon Hermit"],
            "cave": ["Lost Miner", "Cave Hermit", "Stranded Traveler"],
            "ruins": ["Ancient Ghost", "Ruin Scholar", "Old Guardian"],
            "temple": ["Temple Oracle", "High Priest", "Sacred Keeper"],
            "town": ["Town Elder", "Local Sage", "Guild Master"],
            "village": ["Village Elder", "Wise Woman", "Local Healer"],
            "default": ["Mysterious Figure", "Wise Elder", "Knowledgeable One"],
        },
        QuestTemplateType.ESCORT: {
            "temple": ["Pilgrim", "Acolyte", "Sacred Messenger"],
            "town": ["Merchant", "Noble", "Traveler"],
            "village": ["Farmer", "Child", "Elderly Villager"],
            "default": ["Refugee", "Survivor", "Wanderer"],
        },
        QuestTemplateType.FETCH: {
            "town": ["Medicine", "Important Letter", "Trade Goods"],
            "village": ["Herbal Remedy", "Lost Heirloom", "Farm Supplies"],
            "default": ["Valuable Package", "Important Item", "Requested Object"],
        },
    }

    # Get target pool
    type_pools = target_pools.get(template_type, target_pools[QuestTemplateType.EXPLORE_AREA])
    category_targets = type_pools.get(category.lower(), type_pools.get("default", ["Target"]))
    target = rng.choice(category_targets)

    # Get name template
    name_templates = QUEST_NAME_TEMPLATES.get(template_type, ["Task: {target}"])
    name_template = rng.choice(name_templates)
    name = name_template.format(target=target)

    # Ensure name fits Quest constraints (max 30 chars)
    if len(name) > 30:
        name = name[:27] + "..."

    # Get description template
    desc_templates = QUEST_DESCRIPTION_TEMPLATES.get(
        template_type, ["Complete the task involving {target}."]
    )
    desc_template = rng.choice(desc_templates)
    description = desc_template.format(target=target)

    # Ensure description fits Quest constraints (max 200 chars)
    if len(description) > 200:
        description = description[:197] + "..."

    return {"name": name, "description": description, "target": target}
