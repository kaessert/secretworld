"""Tests for quest outcome tracking and NPC reactions.

These tests verify the QuestOutcome model, GameState integration,
and NPC greeting reactions to completed quests.
"""

import pytest

from cli_rpg.models.quest_outcome import QuestOutcome
from cli_rpg.models.npc import NPC
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState


# =============================================================================
# QuestOutcome Model Tests
# =============================================================================


class TestQuestOutcomeModel:
    """Tests for the QuestOutcome dataclass."""

    def test_create_basic_outcome(self):
        """Test creating a basic QuestOutcome with required fields."""
        # Tests: QuestOutcome model creation
        outcome = QuestOutcome(
            quest_name="Slay the Dragon",
            quest_giver="Elder Marcus",
            completion_method="main",
        )
        assert outcome.quest_name == "Slay the Dragon"
        assert outcome.quest_giver == "Elder Marcus"
        assert outcome.completion_method == "main"
        assert outcome.completed_branch_name is None
        assert outcome.timestamp == 0
        assert outcome.affected_npcs == []
        assert outcome.faction_changes == {}

    def test_create_branch_outcome(self):
        """Test creating a QuestOutcome completed via alternative branch."""
        # Tests: QuestOutcome with branch completion
        outcome = QuestOutcome(
            quest_name="The Bandit Problem",
            quest_giver="Sheriff Blake",
            completion_method="branch_peaceful",
            completed_branch_name="Negotiate Peace",
            timestamp=48,
            affected_npcs=["Bandit Leader", "Village Elder"],
            faction_changes={"Bandits": 10, "Town Watch": -5},
        )
        assert outcome.completion_method == "branch_peaceful"
        assert outcome.completed_branch_name == "Negotiate Peace"
        assert outcome.is_branch_completion is True
        assert outcome.is_success is True
        assert len(outcome.affected_npcs) == 2
        assert outcome.faction_changes["Bandits"] == 10

    def test_expired_outcome(self):
        """Test QuestOutcome for an expired quest."""
        # Tests: QuestOutcome with expired method
        outcome = QuestOutcome(
            quest_name="Urgent Delivery",
            quest_giver="Courier Master",
            completion_method="expired",
        )
        assert outcome.is_success is False
        assert outcome.is_branch_completion is False

    def test_abandoned_outcome(self):
        """Test QuestOutcome for an abandoned quest."""
        # Tests: QuestOutcome with abandoned method
        outcome = QuestOutcome(
            quest_name="Lost Artifact",
            quest_giver="Archaeologist",
            completion_method="abandoned",
        )
        assert outcome.is_success is False
        assert outcome.is_branch_completion is False

    def test_validation_empty_quest_name(self):
        """Test that empty quest_name raises ValueError."""
        # Tests: QuestOutcome validation - quest_name
        with pytest.raises(ValueError, match="Quest name cannot be empty"):
            QuestOutcome(
                quest_name="",
                quest_giver="Someone",
                completion_method="main",
            )

    def test_validation_empty_quest_giver(self):
        """Test that empty quest_giver raises ValueError."""
        # Tests: QuestOutcome validation - quest_giver
        with pytest.raises(ValueError, match="Quest giver cannot be empty"):
            QuestOutcome(
                quest_name="Some Quest",
                quest_giver="",
                completion_method="main",
            )

    def test_validation_invalid_completion_method(self):
        """Test that invalid completion_method raises ValueError."""
        # Tests: QuestOutcome validation - completion_method
        with pytest.raises(ValueError, match="Invalid completion method"):
            QuestOutcome(
                quest_name="Some Quest",
                quest_giver="Someone",
                completion_method="invalid_method",
            )

    def test_serialization_to_dict(self):
        """Test QuestOutcome.to_dict() serialization."""
        # Tests: QuestOutcome serialization
        outcome = QuestOutcome(
            quest_name="Goblin Hunt",
            quest_giver="Hunter",
            completion_method="main",
            timestamp=100,
            affected_npcs=["Farmer"],
            faction_changes={"Hunters Guild": 5},
        )
        data = outcome.to_dict()
        assert data["quest_name"] == "Goblin Hunt"
        assert data["quest_giver"] == "Hunter"
        assert data["completion_method"] == "main"
        assert data["timestamp"] == 100
        assert data["affected_npcs"] == ["Farmer"]
        assert data["faction_changes"] == {"Hunters Guild": 5}

    def test_deserialization_from_dict(self):
        """Test QuestOutcome.from_dict() deserialization."""
        # Tests: QuestOutcome deserialization
        data = {
            "quest_name": "Dark Cave",
            "quest_giver": "Explorer",
            "completion_method": "branch_stealth",
            "completed_branch_name": "Sneak Through",
            "timestamp": 50,
            "affected_npcs": ["Cave Dweller"],
            "faction_changes": {"Thieves Guild": 10},
        }
        outcome = QuestOutcome.from_dict(data)
        assert outcome.quest_name == "Dark Cave"
        assert outcome.quest_giver == "Explorer"
        assert outcome.completion_method == "branch_stealth"
        assert outcome.completed_branch_name == "Sneak Through"
        assert outcome.timestamp == 50
        assert outcome.affected_npcs == ["Cave Dweller"]
        assert outcome.faction_changes == {"Thieves Guild": 10}

    def test_deserialization_with_defaults(self):
        """Test QuestOutcome.from_dict() with minimal data uses defaults."""
        # Tests: QuestOutcome deserialization with backward compat
        data = {
            "quest_name": "Simple Quest",
            "quest_giver": "NPC",
            "completion_method": "main",
        }
        outcome = QuestOutcome.from_dict(data)
        assert outcome.completed_branch_name is None
        assert outcome.timestamp == 0
        assert outcome.affected_npcs == []
        assert outcome.faction_changes == {}


# =============================================================================
# GameState Quest Outcome Integration Tests
# =============================================================================


class TestGameStateQuestOutcomes:
    """Tests for GameState quest outcome tracking."""

    @pytest.fixture
    def game_state(self):
        """Create a minimal GameState for testing."""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Town Square",
            description="A bustling town square.",
            coordinates=(0, 0),
        )
        return GameState(
            character=character,
            world={"Town Square": location},
            starting_location="Town Square",
        )

    def test_record_quest_outcome_main(self, game_state):
        """Test recording a main quest completion outcome."""
        # Tests: GameState.record_quest_outcome() for main completion
        quest = Quest(
            name="Save the Village",
            description="Defend the village from raiders.",
            objective_type=ObjectiveType.KILL,
            target="Raider",
            quest_giver="Village Chief",
        )
        game_state.record_quest_outcome(quest, method="main")

        assert len(game_state.quest_outcomes) == 1
        outcome = game_state.quest_outcomes[0]
        assert outcome.quest_name == "Save the Village"
        assert outcome.quest_giver == "Village Chief"
        assert outcome.completion_method == "main"

    def test_record_quest_outcome_branch(self, game_state):
        """Test recording a branch quest completion outcome."""
        # Tests: GameState.record_quest_outcome() for branch completion
        quest = Quest(
            name="The Merchant's Request",
            description="Help the merchant.",
            objective_type=ObjectiveType.COLLECT,
            target="Goods",
            quest_giver="Merchant",
        )
        game_state.record_quest_outcome(
            quest,
            method="branch_bribe",
            branch_name="Bribe the Guards",
            affected_npcs=["Guard Captain"],
            faction_changes={"Town Guard": -10},
        )

        assert len(game_state.quest_outcomes) == 1
        outcome = game_state.quest_outcomes[0]
        assert outcome.completion_method == "branch_bribe"
        assert outcome.completed_branch_name == "Bribe the Guards"
        assert "Guard Captain" in outcome.affected_npcs
        assert outcome.faction_changes["Town Guard"] == -10

    def test_record_quest_outcome_unknown_giver(self, game_state):
        """Test recording outcome when quest has no quest_giver."""
        # Tests: GameState.record_quest_outcome() handles missing quest_giver
        quest = Quest(
            name="Found Quest",
            description="A quest found in the wild.",
            objective_type=ObjectiveType.EXPLORE,
            target="Cave",
            # quest_giver not set (defaults to None)
        )
        game_state.record_quest_outcome(quest, method="main")

        assert len(game_state.quest_outcomes) == 1
        outcome = game_state.quest_outcomes[0]
        assert outcome.quest_giver == "Unknown"

    def test_get_quest_outcomes_for_npc_as_giver(self, game_state):
        """Test filtering outcomes where NPC was the quest giver."""
        # Tests: GameState.get_quest_outcomes_for_npc() for quest givers
        quest1 = Quest(
            name="Quest One",
            description="First quest.",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            quest_giver="Elder Sarah",
        )
        quest2 = Quest(
            name="Quest Two",
            description="Second quest.",
            objective_type=ObjectiveType.TALK,
            target="Person",
            quest_giver="Elder Sarah",
        )
        quest3 = Quest(
            name="Quest Three",
            description="Third quest.",
            objective_type=ObjectiveType.COLLECT,
            target="Item",
            quest_giver="Merchant Bob",
        )

        game_state.record_quest_outcome(quest1, method="main")
        game_state.record_quest_outcome(quest2, method="main")
        game_state.record_quest_outcome(quest3, method="main")

        sarah_outcomes = game_state.get_quest_outcomes_for_npc("Elder Sarah")
        assert len(sarah_outcomes) == 2
        assert all(o.quest_giver == "Elder Sarah" for o in sarah_outcomes)

        bob_outcomes = game_state.get_quest_outcomes_for_npc("Merchant Bob")
        assert len(bob_outcomes) == 1
        assert bob_outcomes[0].quest_name == "Quest Three"

    def test_get_quest_outcomes_for_npc_as_affected(self, game_state):
        """Test filtering outcomes where NPC was affected."""
        # Tests: GameState.get_quest_outcomes_for_npc() for affected NPCs
        quest = Quest(
            name="The Rescue",
            description="Rescue the prisoners.",
            objective_type=ObjectiveType.EXPLORE,
            target="Prison",
            quest_giver="Guard Captain",
        )
        game_state.record_quest_outcome(
            quest,
            method="main",
            affected_npcs=["Prisoner Alice", "Prisoner Bob"],
        )

        alice_outcomes = game_state.get_quest_outcomes_for_npc("Prisoner Alice")
        assert len(alice_outcomes) == 1
        assert alice_outcomes[0].quest_name == "The Rescue"

        # Case-insensitive matching
        bob_outcomes = game_state.get_quest_outcomes_for_npc("prisoner bob")
        assert len(bob_outcomes) == 1

    def test_get_quest_outcomes_for_npc_none_found(self, game_state):
        """Test filtering returns empty list when no matches."""
        # Tests: GameState.get_quest_outcomes_for_npc() with no matches
        quest = Quest(
            name="Solo Quest",
            description="A quest.",
            objective_type=ObjectiveType.KILL,
            target="Monster",
            quest_giver="Hermit",
        )
        game_state.record_quest_outcome(quest, method="main")

        outcomes = game_state.get_quest_outcomes_for_npc("Random NPC")
        assert len(outcomes) == 0

    def test_serialization_with_quest_outcomes(self, game_state):
        """Test GameState serialization includes quest_outcomes."""
        # Tests: GameState.to_dict() includes quest_outcomes
        quest = Quest(
            name="Test Quest",
            description="A test.",
            objective_type=ObjectiveType.KILL,
            target="Target",
            quest_giver="NPC",
        )
        game_state.record_quest_outcome(quest, method="main")

        data = game_state.to_dict()
        assert "quest_outcomes" in data
        assert len(data["quest_outcomes"]) == 1
        assert data["quest_outcomes"][0]["quest_name"] == "Test Quest"

    def test_deserialization_with_quest_outcomes(self, game_state):
        """Test GameState deserialization restores quest_outcomes."""
        # Tests: GameState.from_dict() restores quest_outcomes
        quest = Quest(
            name="Serialized Quest",
            description="Testing serialization.",
            objective_type=ObjectiveType.EXPLORE,
            target="Location",
            quest_giver="Serializer",
        )
        game_state.record_quest_outcome(quest, method="branch_test", branch_name="Test Branch")

        data = game_state.to_dict()
        restored = GameState.from_dict(data)

        assert len(restored.quest_outcomes) == 1
        outcome = restored.quest_outcomes[0]
        assert outcome.quest_name == "Serialized Quest"
        assert outcome.completion_method == "branch_test"
        assert outcome.completed_branch_name == "Test Branch"

    def test_backward_compatibility_no_quest_outcomes(self, game_state):
        """Test GameState deserializes old saves without quest_outcomes."""
        # Tests: GameState.from_dict() backward compat
        data = game_state.to_dict()
        # Simulate old save format without quest_outcomes
        del data["quest_outcomes"]

        restored = GameState.from_dict(data)
        assert restored.quest_outcomes == []


# =============================================================================
# NPC Greeting Quest Reaction Tests
# =============================================================================


class TestNPCQuestReactionGreetings:
    """Tests for NPC.get_greeting() with quest outcomes."""

    def test_greeting_quest_giver_success(self):
        """Test NPC greeting when player completed their quest successfully."""
        # Tests: NPC.get_greeting() reacts to successful quest completion
        npc = NPC(
            name="Elder Marcus",
            description="A wise village elder.",
            dialogue="Welcome, traveler.",
        )
        outcome = QuestOutcome(
            quest_name="Slay the Dragon",
            quest_giver="Elder Marcus",
            completion_method="main",
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome])

        # Should be one of the success templates
        assert "Slay the Dragon" in greeting
        assert any(phrase in greeting for phrase in ["Well done", "proven yourself", "hero who completed"])

    def test_greeting_quest_giver_branch(self):
        """Test NPC greeting when player completed their quest via branch."""
        # Tests: NPC.get_greeting() reacts to branch completion
        npc = NPC(
            name="Sheriff Blake",
            description="The town sheriff.",
            dialogue="Move along.",
        )
        outcome = QuestOutcome(
            quest_name="Bandit Problem",
            quest_giver="Sheriff Blake",
            completion_method="branch_peaceful",
            completed_branch_name="Negotiate",
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome])

        # Should be one of the branch templates
        assert "Bandit Problem" in greeting
        assert any(phrase in greeting for phrase in ["how you handled", "unconventional", "your own way"])

    def test_greeting_quest_giver_failed(self):
        """Test NPC greeting when player's quest expired."""
        # Tests: NPC.get_greeting() reacts to expired quest
        npc = NPC(
            name="Courier Master",
            description="The courier guild leader.",
            dialogue="What do you want?",
        )
        outcome = QuestOutcome(
            quest_name="Urgent Delivery",
            quest_giver="Courier Master",
            completion_method="expired",
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome])

        # Should be one of the failure templates
        assert "Urgent Delivery" in greeting
        assert any(phrase in greeting for phrase in ["failed me", "Time ran out", "let me down"])

    def test_greeting_quest_giver_abandoned(self):
        """Test NPC greeting when player abandoned their quest."""
        # Tests: NPC.get_greeting() reacts to abandoned quest
        npc = NPC(
            name="Archaeologist",
            description="A dusty researcher.",
            dialogue="The artifacts call...",
        )
        outcome = QuestOutcome(
            quest_name="Lost Artifact",
            quest_giver="Archaeologist",
            completion_method="abandoned",
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome])

        # Should be one of the abandoned templates
        assert "Lost Artifact" in greeting
        assert any(phrase in greeting for phrase in ["abandoned", "Walking away", "couldn't handle"])

    def test_greeting_affected_positive(self):
        """Test NPC greeting when they were positively affected by quest."""
        # Tests: NPC.get_greeting() reacts positively when affected by success
        npc = NPC(
            name="Rescued Farmer",
            description="A grateful farmer.",
            dialogue="Thank you for saving my farm!",
        )
        outcome = QuestOutcome(
            quest_name="Clear the Fields",
            quest_giver="Village Chief",
            completion_method="main",
            affected_npcs=["Rescued Farmer"],
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome])

        # Should be one of the positive affected templates
        assert any(phrase in greeting for phrase in ["gratitude", "Thank you", "won't forget"])

    def test_greeting_affected_negative(self):
        """Test NPC greeting when they were negatively affected by quest failure."""
        # Tests: NPC.get_greeting() reacts negatively when affected by failure
        npc = NPC(
            name="Disappointed Villager",
            description="A villager who needed help.",
            dialogue="I thought you would help...",
        )
        outcome = QuestOutcome(
            quest_name="Defend the Village",
            quest_giver="Village Chief",
            completion_method="expired",
            affected_npcs=["Disappointed Villager"],
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome])

        # Should be one of the negative affected templates
        assert any(phrase in greeting for phrase in ["Don't expect", "nothing to discuss", "not gone unnoticed"])

    def test_greeting_most_recent_outcome_priority(self):
        """Test that most recent quest outcome takes priority."""
        # Tests: NPC.get_greeting() uses most recent outcome
        npc = NPC(
            name="Elder Marcus",
            description="A wise elder.",
            dialogue="Hello.",
        )
        outcome1 = QuestOutcome(
            quest_name="First Quest",
            quest_giver="Elder Marcus",
            completion_method="expired",
            timestamp=10,
        )
        outcome2 = QuestOutcome(
            quest_name="Second Quest",
            quest_giver="Elder Marcus",
            completion_method="main",
            timestamp=50,
        )
        # Pass outcomes in order (oldest first)
        greeting = npc.get_greeting(quest_outcomes=[outcome1, outcome2])

        # Should reference the second (most recent) quest
        assert "Second Quest" in greeting

    def test_greeting_quest_giver_priority_over_affected(self):
        """Test that quest giver role takes priority over affected role."""
        # Tests: NPC.get_greeting() prioritizes quest giver over affected
        npc = NPC(
            name="Multi-Role NPC",
            description="An NPC with multiple roles.",
            dialogue="Default.",
        )
        outcome1 = QuestOutcome(
            quest_name="Quest I Gave",
            quest_giver="Multi-Role NPC",
            completion_method="main",
        )
        outcome2 = QuestOutcome(
            quest_name="Quest That Affected Me",
            quest_giver="Someone Else",
            completion_method="main",
            affected_npcs=["Multi-Role NPC"],
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome1, outcome2])

        # Should reference the quest they gave (priority)
        assert "Quest I Gave" in greeting

    def test_greeting_fallback_to_choices(self):
        """Test that greeting falls back to choices when no quest outcomes."""
        # Tests: NPC.get_greeting() falls back to choices-based greetings
        npc = NPC(
            name="Bystander",
            description="Just watching.",
            dialogue="Hello there.",
        )
        choices = [{"choice_type": "combat_flee"} for _ in range(5)]
        greeting = npc.get_greeting(choices=choices, quest_outcomes=[])

        # Should use cautious reputation greeting (5+ flees)
        assert any(phrase in greeting for phrase in ["knows when to run", "careful", "survivor"])

    def test_greeting_fallback_to_dialogue(self):
        """Test that greeting falls back to dialogue when no context."""
        # Tests: NPC.get_greeting() falls back to dialogue
        npc = NPC(
            name="Simple NPC",
            description="A simple villager.",
            dialogue="Good day to you!",
        )
        greeting = npc.get_greeting(choices=[], quest_outcomes=[])

        assert greeting == "Good day to you!"

    def test_greeting_case_insensitive_npc_matching(self):
        """Test that NPC matching for outcomes is case-insensitive."""
        # Tests: NPC.get_greeting() case-insensitive matching
        npc = NPC(
            name="elder marcus",  # lowercase
            description="An elder.",
            dialogue="Hello.",
        )
        outcome = QuestOutcome(
            quest_name="Test Quest",
            quest_giver="Elder Marcus",  # Mixed case
            completion_method="main",
        )
        greeting = npc.get_greeting(quest_outcomes=[outcome])

        # Should still match despite case difference
        assert "Test Quest" in greeting
