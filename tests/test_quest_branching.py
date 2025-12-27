"""Tests for branching quest objectives (TDD)."""
import pytest
from cli_rpg.models.quest import (
    Quest,
    QuestBranch,
    QuestStatus,
    ObjectiveType,
)
from cli_rpg.models.character import Character


class TestQuestBranchBasics:
    """Test QuestBranch dataclass basics."""

    def test_quest_branch_creation(self):
        """Test creating a basic QuestBranch."""
        # Tests: QuestBranch can be created with required fields
        branch = QuestBranch(
            id="kill",
            name="Eliminate the Threat",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
        )
        assert branch.id == "kill"
        assert branch.name == "Eliminate the Threat"
        assert branch.objective_type == ObjectiveType.KILL
        assert branch.target == "Bandit Leader"
        assert branch.target_count == 1
        assert branch.current_count == 0
        assert branch.faction_effects == {}
        assert branch.gold_modifier == 1.0
        assert branch.xp_modifier == 1.0

    def test_quest_branch_with_all_fields(self):
        """Test creating a QuestBranch with all optional fields."""
        # Tests: QuestBranch supports faction effects, modifiers, and description
        branch = QuestBranch(
            id="persuade",
            name="Peaceful Resolution",
            objective_type=ObjectiveType.TALK,
            target="Bandit Leader",
            target_count=1,
            description="Convince him to leave peacefully.",
            faction_effects={"Militia": 5, "Outlaws": 10},
            gold_modifier=0.5,
            xp_modifier=1.5,
        )
        assert branch.description == "Convince him to leave peacefully."
        assert branch.faction_effects == {"Militia": 5, "Outlaws": 10}
        assert branch.gold_modifier == 0.5
        assert branch.xp_modifier == 1.5


class TestQuestBranchSerialization:
    """Test QuestBranch serialization round-trip."""

    def test_quest_branch_serialization_round_trip(self):
        """Test QuestBranch to_dict and from_dict preserve all data."""
        # Tests: QuestBranch can be serialized and deserialized
        original = QuestBranch(
            id="betray",
            name="Join the Raiders",
            objective_type=ObjectiveType.KILL,
            target="Village Elder",
            target_count=1,
            current_count=0,
            description="Help raid the village for a cut.",
            faction_effects={"Militia": -20, "Outlaws": 25},
            gold_modifier=2.0,
            xp_modifier=0.5,
        )

        data = original.to_dict()
        restored = QuestBranch.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.objective_type == original.objective_type
        assert restored.target == original.target
        assert restored.target_count == original.target_count
        assert restored.current_count == original.current_count
        assert restored.description == original.description
        assert restored.faction_effects == original.faction_effects
        assert restored.gold_modifier == original.gold_modifier
        assert restored.xp_modifier == original.xp_modifier


class TestQuestWithBranches:
    """Test Quest with alternative branches."""

    def test_quest_with_no_branches_works_normally(self):
        """Backward compatibility - quests without branches work as before."""
        # Tests: Existing quest behavior unchanged when no branches
        quest = Quest(
            name="Simple Quest",
            description="A quest without branches.",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
        )
        assert quest.alternative_branches == []
        assert quest.completed_branch_id is None

        # Progress works normally
        quest.progress()
        assert quest.current_count == 1
        quest.progress()
        quest.progress()
        assert quest.is_complete

    def test_quest_with_branches_serialization(self):
        """Test Quest with branches serializes and deserializes correctly."""
        # Tests: Quest branches persist through save/load
        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
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
                    faction_effects={"Militia": 5, "Outlaws": 10},
                    gold_modifier=0.5,
                    xp_modifier=1.5,
                ),
            ],
        )

        data = quest.to_dict()
        restored = Quest.from_dict(data)

        assert len(restored.alternative_branches) == 2
        assert restored.alternative_branches[0].id == "kill"
        assert restored.alternative_branches[1].id == "persuade"
        assert restored.alternative_branches[1].gold_modifier == 0.5
        assert restored.alternative_branches[1].faction_effects == {"Militia": 5, "Outlaws": 10}

    def test_quest_branch_progress_independent(self):
        """Each branch tracks progress separately."""
        # Tests: Branch progress is tracked per-branch, not shared
        quest = Quest(
            name="The Bandit Problem",
            description="Deal with the bandit leader.",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            alternative_branches=[
                QuestBranch(
                    id="kill",
                    name="Eliminate the Threat",
                    objective_type=ObjectiveType.KILL,
                    target="Bandit Leader",
                    target_count=2,
                ),
                QuestBranch(
                    id="persuade",
                    name="Peaceful Resolution",
                    objective_type=ObjectiveType.TALK,
                    target="Bandit Leader",
                    target_count=1,
                ),
            ],
        )

        # Progress kill branch partially
        quest.alternative_branches[0].current_count = 1

        # Talk branch should be unaffected
        assert quest.alternative_branches[1].current_count == 0

        # Complete talk branch
        quest.alternative_branches[1].current_count = 1

        # Kill branch should still be at 1
        assert quest.alternative_branches[0].current_count == 1


class TestBranchCompletion:
    """Test branch completion mechanics."""

    def test_quest_ready_when_any_branch_complete(self):
        """First branch to complete marks quest ready to turn in."""
        # Tests: Any completed branch triggers quest completion
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

        # Talk to bandit leader (completes persuade branch)
        messages = character.record_talk("Bandit Leader")

        # Quest should be ready to turn in via the persuade branch
        assert quest.status == QuestStatus.READY_TO_TURN_IN
        assert quest.completed_branch_id == "persuade"
        assert len(messages) > 0

    def test_completed_branch_id_set_on_completion(self):
        """The completed_branch_id is set when a branch completes."""
        # Tests: Track which path player chose
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
        character.record_kill("Bandit Leader")

        assert quest.completed_branch_id == "kill"


class TestBranchRewards:
    """Test branch-specific rewards."""

    def test_branch_reward_modifiers_applied(self):
        """Branch modifiers scale gold and XP rewards."""
        # Tests: Gold/XP rewards adjusted by branch modifiers
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        initial_gold = character.gold
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
                    gold_modifier=0.5,  # Half gold
                    xp_modifier=1.5,    # 50% more XP
                ),
            ],
            completed_branch_id="persuade",  # Player chose persuade
        )
        character.quests.append(quest)

        messages = character.claim_quest_rewards(quest)

        # Gold should be 50 (100 * 0.5)
        assert character.gold == initial_gold + 50
        # XP should be 75 (50 * 1.5)
        assert character.xp == initial_xp + 75

    def test_branch_faction_effects_applied(self):
        """Branch-specific faction effects are applied on completion."""
        # Tests: Different branches affect factions differently
        from cli_rpg.models.faction import Faction

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
            completed_branch_id="persuade",  # Player chose persuade
        )
        character.quests.append(quest)

        initial_militia = militia.reputation
        initial_outlaws = outlaws.reputation

        messages = character.claim_quest_rewards(quest, factions=factions)

        # Persuade branch: +5 Militia, +10 Outlaws
        assert militia.reputation == initial_militia + 5
        assert outlaws.reputation == initial_outlaws + 10


class TestQuestDisplay:
    """Test quest display with branches."""

    def test_quest_display_shows_all_branches(self):
        """Quest str/repr includes branch information."""
        # Tests: UI shows all completion paths
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

        # The quest should have a method to get branch display info
        branches_info = quest.get_branches_display()

        assert len(branches_info) == 2
        assert branches_info[0]["name"] == "Eliminate the Threat"
        assert branches_info[0]["objective"] == "Kill Bandit Leader"
        assert branches_info[0]["progress"] == "[0/1]"
        assert branches_info[1]["name"] == "Peaceful Resolution"
        assert branches_info[1]["objective"] == "Talk to Bandit Leader"
