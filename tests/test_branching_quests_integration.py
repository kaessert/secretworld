"""Integration tests for branching quest features.

Tests the complete flow of branching quests:
1. Quest accept clones branches correctly
2. Quest details displays branch options
3. Procedural quest generation creates branches
4. Branch completion works via record_kill/record_talk
5. Branch rewards are applied correctly
"""

import pytest

from cli_rpg.models.quest import (
    Quest,
    QuestBranch,
    QuestStatus,
    ObjectiveType,
    WorldEffect,
)
from cli_rpg.models.character import Character
from cli_rpg.models.faction import Faction


class TestQuestAcceptClonesBranches:
    """Test that quest accept properly clones branches and world_effects."""

    def test_accept_quest_clones_alternative_branches(self):
        """Test: accepting a quest clones its alternative_branches."""
        # Create a quest with alternative branches
        original_quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            gold_reward=100,
            xp_reward=50,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                    faction_effects={"Militia": 15},
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                    faction_effects={"Outlaws": 10},
                    gold_modifier=0.5,
                    xp_modifier=1.5,
                ),
            ],
        )

        # Simulate cloning as done in quest accept (main.py)
        cloned_quest = Quest(
            name=original_quest.name,
            description=original_quest.description,
            objective_type=original_quest.objective_type,
            target=original_quest.target,
            target_count=original_quest.target_count,
            status=QuestStatus.ACTIVE,
            current_count=0,
            gold_reward=original_quest.gold_reward,
            xp_reward=original_quest.xp_reward,
            alternative_branches=[
                QuestBranch(
                    id=b.id,
                    name=b.name,
                    objective_type=b.objective_type,
                    target=b.target,
                    target_count=b.target_count,
                    current_count=0,
                    description=b.description,
                    faction_effects=b.faction_effects.copy(),
                    gold_modifier=b.gold_modifier,
                    xp_modifier=b.xp_modifier,
                )
                for b in original_quest.alternative_branches
            ],
            world_effects=[
                WorldEffect(
                    effect_type=e.effect_type,
                    target=e.target,
                    description=e.description,
                    metadata=e.metadata.copy(),
                )
                for e in original_quest.world_effects
            ],
        )

        # Verify cloned branches
        assert len(cloned_quest.alternative_branches) == 2
        assert cloned_quest.alternative_branches[0].id == "kill"
        assert cloned_quest.alternative_branches[1].id == "persuade"
        assert cloned_quest.alternative_branches[1].gold_modifier == 0.5
        assert cloned_quest.alternative_branches[1].xp_modifier == 1.5
        assert cloned_quest.alternative_branches[0].faction_effects == {"Militia": 15}
        assert cloned_quest.alternative_branches[1].faction_effects == {"Outlaws": 10}

        # Verify branches are independent copies (not references)
        original_quest.alternative_branches[0].current_count = 1
        assert cloned_quest.alternative_branches[0].current_count == 0

    def test_accept_quest_clones_world_effects(self):
        """Test: accepting a quest clones its world_effects."""
        # Create a quest with world effects
        original_quest = Quest(
            name="Clear the Cave",
            description="Clear the cave of monsters.",
            objective_type=ObjectiveType.KILL,
            target="Cave Beast",
            gold_reward=150,
            xp_reward=75,
            world_effects=[
                WorldEffect(
                    effect_type="area_cleared",
                    target="Dark Cave",
                    description="The cave is now safe for travelers.",
                    metadata={"spawn_rate": 0},
                ),
            ],
        )

        # Simulate cloning as done in quest accept
        cloned_quest = Quest(
            name=original_quest.name,
            description=original_quest.description,
            objective_type=original_quest.objective_type,
            target=original_quest.target,
            gold_reward=original_quest.gold_reward,
            xp_reward=original_quest.xp_reward,
            world_effects=[
                WorldEffect(
                    effect_type=e.effect_type,
                    target=e.target,
                    description=e.description,
                    metadata=e.metadata.copy(),
                )
                for e in original_quest.world_effects
            ],
        )

        # Verify cloned world effects
        assert len(cloned_quest.world_effects) == 1
        assert cloned_quest.world_effects[0].effect_type == "area_cleared"
        assert cloned_quest.world_effects[0].target == "Dark Cave"
        assert cloned_quest.world_effects[0].metadata == {"spawn_rate": 0}

        # Verify effects are independent copies
        original_quest.world_effects[0].metadata["spawn_rate"] = 1
        assert cloned_quest.world_effects[0].metadata["spawn_rate"] == 0


class TestQuestDetailsShowsBranches:
    """Test that quest details command shows branch options."""

    def test_get_branches_display_shows_all_branches(self):
        """Test: get_branches_display returns info for all branches."""
        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            status=QuestStatus.ACTIVE,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                    current_count=0,
                    target_count=1,
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                    current_count=0,
                    target_count=1,
                ),
            ],
        )

        branches_info = quest.get_branches_display()

        assert len(branches_info) == 2
        assert branches_info[0]["name"] == "Eliminate the Threat"
        assert branches_info[0]["objective"] == "Kill Bandit Leader"
        assert branches_info[0]["progress"] == "[0/1]"
        assert branches_info[0]["is_complete"] is False
        assert branches_info[1]["name"] == "Peaceful Resolution"
        assert branches_info[1]["objective"] == "Talk to Bandit Leader"
        assert branches_info[1]["progress"] == "[0/1]"
        assert branches_info[1]["is_complete"] is False

    def test_get_branches_display_shows_completed_branch(self):
        """Test: get_branches_display shows which branch is completed."""
        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            status=QuestStatus.ACTIVE,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                    current_count=1,  # Completed!
                    target_count=1,
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                    current_count=0,
                    target_count=1,
                ),
            ],
        )

        branches_info = quest.get_branches_display()

        assert branches_info[0]["is_complete"] is True
        assert branches_info[0]["progress"] == "[1/1]"
        assert branches_info[1]["is_complete"] is False


class TestProceduralQuestBranches:
    """Test procedural quest generation creates branches."""

    def test_branching_quest_templates_exist(self):
        """Test: BRANCHING_QUEST_TEMPLATES is defined with proper structure."""
        from cli_rpg.procedural_quests import BRANCHING_QUEST_TEMPLATES, QuestTemplateType

        # Should have entries for quest types that can branch
        assert QuestTemplateType.KILL_BOSS in BRANCHING_QUEST_TEMPLATES

        # Each entry should be a list of branch template sets
        boss_branches = BRANCHING_QUEST_TEMPLATES[QuestTemplateType.KILL_BOSS]
        assert isinstance(boss_branches, list)
        assert len(boss_branches) > 0

        # Each set should contain multiple branch templates
        first_set = boss_branches[0]
        assert isinstance(first_set, list)
        assert len(first_set) >= 2  # At least two branches per set

    def test_branch_template_dataclass_exists(self):
        """Test: BranchTemplate dataclass is defined with proper fields."""
        from cli_rpg.procedural_quests import BranchTemplate, ObjectiveType

        branch = BranchTemplate(
            id="kill",
            objective_type=ObjectiveType.KILL,
            gold_modifier=1.0,
            xp_modifier=1.0,
        )

        assert branch.id == "kill"
        assert branch.objective_type == ObjectiveType.KILL
        assert branch.gold_modifier == 1.0
        assert branch.xp_modifier == 1.0
        assert branch.faction_effects == {}

    def test_generate_branches_for_template_creates_branches(self):
        """Test: generate_branches_for_template creates QuestBranch list."""
        from cli_rpg.procedural_quests import (
            generate_branches_for_template,
            QuestTemplateType,
        )
        from cli_rpg.models.quest import QuestBranch

        branches = generate_branches_for_template(
            template_type=QuestTemplateType.KILL_BOSS,
            target="Dark Lord",
            category="dungeon",
            seed=12345,
        )

        # Should return a list of QuestBranch objects
        assert isinstance(branches, list)
        assert len(branches) >= 2

        # Each should be a proper QuestBranch
        for branch in branches:
            assert isinstance(branch, QuestBranch)
            assert branch.id  # Has an ID
            assert branch.name  # Has a name
            assert branch.target  # Has a target


class TestBranchContentFallback:
    """Test fallback content for branches."""

    def test_branch_name_templates_exist(self):
        """Test: BRANCH_NAME_TEMPLATES is defined in fallback_content."""
        from cli_rpg.fallback_content import BRANCH_NAME_TEMPLATES

        assert "kill_boss" in BRANCH_NAME_TEMPLATES
        assert "kill" in BRANCH_NAME_TEMPLATES["kill_boss"]
        assert "persuade" in BRANCH_NAME_TEMPLATES["kill_boss"]

    def test_branch_description_templates_exist(self):
        """Test: BRANCH_DESCRIPTION_TEMPLATES is defined in fallback_content."""
        from cli_rpg.fallback_content import BRANCH_DESCRIPTION_TEMPLATES

        assert "kill_boss" in BRANCH_DESCRIPTION_TEMPLATES
        assert "kill" in BRANCH_DESCRIPTION_TEMPLATES["kill_boss"]
        assert "persuade" in BRANCH_DESCRIPTION_TEMPLATES["kill_boss"]

    def test_fallback_provider_get_branch_content(self):
        """Test: FallbackContentProvider.get_branch_content works."""
        from cli_rpg.fallback_content import FallbackContentProvider

        provider = FallbackContentProvider(seed=12345)

        content = provider.get_branch_content(
            template_type="kill_boss",
            branch_id="kill",
            target="Dark Lord",
            category="dungeon",
        )

        assert "name" in content
        assert "description" in content
        assert "Dark Lord" in content["name"] or "Dark Lord" in content["description"]


class TestBranchCompletionIntegration:
    """Test branch completion via record_kill/record_talk."""

    def test_record_kill_completes_kill_branch(self):
        """Test: record_kill progresses and completes kill branch."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )

        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            status=QuestStatus.ACTIVE,
            gold_reward=100,
            xp_reward=50,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                ),
            ],
        )
        character.quests.append(quest)

        # Kill the bandit leader
        messages = character.record_kill("Bandit Leader")

        # Quest should be ready to turn in via the kill branch
        assert quest.status == QuestStatus.READY_TO_TURN_IN
        assert quest.completed_branch_id == "kill"
        assert quest.alternative_branches[0].is_complete
        assert not quest.alternative_branches[1].is_complete

    def test_record_talk_completes_talk_branch(self):
        """Test: record_talk progresses and completes talk branch."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )

        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            status=QuestStatus.ACTIVE,
            gold_reward=100,
            xp_reward=50,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                ),
            ],
        )
        character.quests.append(quest)

        # Talk to the bandit leader
        messages = character.record_talk("Bandit Leader")

        # Quest should be ready to turn in via the persuade branch
        assert quest.status == QuestStatus.READY_TO_TURN_IN
        assert quest.completed_branch_id == "persuade"
        assert not quest.alternative_branches[0].is_complete
        assert quest.alternative_branches[1].is_complete


class TestBranchRewardsIntegration:
    """Test branch-specific rewards are applied correctly."""

    def test_branch_gold_modifier_applied(self):
        """Test: gold_modifier from completed branch affects gold reward."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        initial_gold = character.gold

        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            status=QuestStatus.READY_TO_TURN_IN,
            gold_reward=100,
            xp_reward=50,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                    gold_modifier=1.0,
                    xp_modifier=1.0,
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                    gold_modifier=0.5,  # Half gold
                    xp_modifier=1.5,  # 50% more XP
                ),
            ],
            completed_branch_id="persuade",
        )
        character.quests.append(quest)

        messages = character.claim_quest_rewards(quest)

        # Gold should be 50 (100 * 0.5)
        assert character.gold == initial_gold + 50

    def test_branch_xp_modifier_applied(self):
        """Test: xp_modifier from completed branch affects XP reward."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        initial_xp = character.xp

        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            status=QuestStatus.READY_TO_TURN_IN,
            gold_reward=100,
            xp_reward=50,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                    gold_modifier=1.0,
                    xp_modifier=1.0,
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                    gold_modifier=0.5,
                    xp_modifier=1.5,  # 50% more XP
                ),
            ],
            completed_branch_id="persuade",
        )
        character.quests.append(quest)

        messages = character.claim_quest_rewards(quest)

        # XP should be 75 (50 * 1.5)
        assert character.xp == initial_xp + 75

    def test_branch_faction_effects_applied(self):
        """Test: faction_effects from completed branch are applied."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )

        militia = Faction(name="Militia", description="Town guards")
        outlaws = Faction(name="Outlaws", description="Bandits")
        factions = [militia, outlaws]

        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            status=QuestStatus.READY_TO_TURN_IN,
            gold_reward=100,
            xp_reward=50,
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                    faction_effects={"Militia": 15, "Outlaws": -10},
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                    faction_effects={"Militia": 5, "Outlaws": 10},
                ),
            ],
            completed_branch_id="persuade",
        )
        character.quests.append(quest)

        initial_militia = militia.reputation
        initial_outlaws = outlaws.reputation

        messages = character.claim_quest_rewards(quest, factions=factions)

        # Persuade branch: +5 Militia, +10 Outlaws
        assert militia.reputation == initial_militia + 5
        assert outlaws.reputation == initial_outlaws + 10
