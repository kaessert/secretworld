"""Tests for QuestNetworkManager - interconnected quest network management."""

import pytest

from cli_rpg.models.quest import Quest, ObjectiveType, QuestStatus
from cli_rpg.models.quest_network import QuestNetworkManager


def make_quest(
    name: str,
    chain_id: str = None,
    chain_position: int = 0,
    prerequisite_quests: list = None,
    unlocks_quests: list = None,
) -> Quest:
    """Helper to create a quest with minimal required fields."""
    return Quest(
        name=name,
        description="Test quest description",
        objective_type=ObjectiveType.KILL,
        target="goblin",
        chain_id=chain_id,
        chain_position=chain_position,
        prerequisite_quests=prerequisite_quests or [],
        unlocks_quests=unlocks_quests or [],
    )


class TestQuestNetworkBasics:
    """Tests for basic quest registration and lookup."""

    # Spec: Quest added and retrievable
    def test_add_quest(self):
        manager = QuestNetworkManager()
        quest = make_quest("Goblin War")
        manager.add_quest(quest)

        result = manager.get_quest("Goblin War")
        assert result is quest

    # Spec: Case-insensitive lookup - "Goblin War" matches "goblin war"
    def test_get_quest_case_insensitive(self):
        manager = QuestNetworkManager()
        quest = make_quest("Goblin War")
        manager.add_quest(quest)

        assert manager.get_quest("goblin war") is quest
        assert manager.get_quest("GOBLIN WAR") is quest
        assert manager.get_quest("GoBLiN wAr") is quest

    # Spec: Returns None for missing quest
    def test_get_quest_not_found(self):
        manager = QuestNetworkManager()
        assert manager.get_quest("Nonexistent Quest") is None

    # Spec: Returns all registered quests
    def test_get_all_quests(self):
        manager = QuestNetworkManager()
        quest1 = make_quest("Quest One")
        quest2 = make_quest("Quest Two")
        quest3 = make_quest("Quest Three")

        manager.add_quest(quest1)
        manager.add_quest(quest2)
        manager.add_quest(quest3)

        all_quests = manager.get_all_quests()
        assert len(all_quests) == 3
        assert quest1 in all_quests
        assert quest2 in all_quests
        assert quest3 in all_quests


class TestChainManagement:
    """Tests for quest chain management."""

    # Spec: Returns quests sorted by chain_position
    def test_get_chain_quests_sorted(self):
        manager = QuestNetworkManager()
        # Add out of order
        quest3 = make_quest("Chain Quest 3", chain_id="main", chain_position=3)
        quest1 = make_quest("Chain Quest 1", chain_id="main", chain_position=1)
        quest2 = make_quest("Chain Quest 2", chain_id="main", chain_position=2)

        manager.add_quest(quest3)
        manager.add_quest(quest1)
        manager.add_quest(quest2)

        chain = manager.get_chain_quests("main")
        assert len(chain) == 3
        assert chain[0] is quest1
        assert chain[1] is quest2
        assert chain[2] is quest3

    # Spec: Returns [] for unknown chain_id
    def test_get_chain_quests_empty(self):
        manager = QuestNetworkManager()
        assert manager.get_chain_quests("nonexistent_chain") == []

    # Spec: Returns (completed_count, total_count)
    def test_get_chain_progression(self):
        manager = QuestNetworkManager()
        quest1 = make_quest("Chain Quest 1", chain_id="main", chain_position=1)
        quest2 = make_quest("Chain Quest 2", chain_id="main", chain_position=2)
        quest3 = make_quest("Chain Quest 3", chain_id="main", chain_position=3)

        manager.add_quest(quest1)
        manager.add_quest(quest2)
        manager.add_quest(quest3)

        # None completed
        assert manager.get_chain_progression("main", []) == (0, 3)

        # One completed
        assert manager.get_chain_progression("main", ["Chain Quest 1"]) == (1, 3)

        # Two completed (case-insensitive)
        assert manager.get_chain_progression(
            "main", ["chain quest 1", "CHAIN QUEST 2"]
        ) == (2, 3)

        # All completed
        assert manager.get_chain_progression(
            "main", ["Chain Quest 1", "Chain Quest 2", "Chain Quest 3"]
        ) == (3, 3)

    # Spec: Returns first incomplete quest in chain
    def test_get_next_in_chain(self):
        manager = QuestNetworkManager()
        quest1 = make_quest("Chain Quest 1", chain_id="main", chain_position=1)
        quest2 = make_quest("Chain Quest 2", chain_id="main", chain_position=2)
        quest3 = make_quest("Chain Quest 3", chain_id="main", chain_position=3)

        manager.add_quest(quest1)
        manager.add_quest(quest2)
        manager.add_quest(quest3)

        # None completed - first is next
        assert manager.get_next_in_chain("main", []) is quest1

        # First completed - second is next
        assert manager.get_next_in_chain("main", ["Chain Quest 1"]) is quest2

        # First two completed - third is next
        assert manager.get_next_in_chain(
            "main", ["Chain Quest 1", "Chain Quest 2"]
        ) is quest3

    # Spec: Returns None when chain finished
    def test_get_next_in_chain_all_complete(self):
        manager = QuestNetworkManager()
        quest1 = make_quest("Chain Quest 1", chain_id="main", chain_position=1)
        quest2 = make_quest("Chain Quest 2", chain_id="main", chain_position=2)

        manager.add_quest(quest1)
        manager.add_quest(quest2)

        result = manager.get_next_in_chain(
            "main", ["Chain Quest 1", "Chain Quest 2"]
        )
        assert result is None


class TestDependencyQueries:
    """Tests for prerequisite and unlock queries."""

    # Spec: Includes quests with empty prerequisite_quests
    def test_get_available_quests_no_prereqs(self):
        manager = QuestNetworkManager()
        quest_no_prereq = make_quest("No Prereq Quest")
        quest_with_prereq = make_quest(
            "Has Prereq", prerequisite_quests=["Some Other Quest"]
        )

        manager.add_quest(quest_no_prereq)
        manager.add_quest(quest_with_prereq)

        available = manager.get_available_quests([])
        assert quest_no_prereq in available
        assert quest_with_prereq not in available

    # Spec: Includes quests with satisfied prerequisites
    def test_get_available_quests_prereqs_met(self):
        manager = QuestNetworkManager()
        quest1 = make_quest("First Quest")
        quest2 = make_quest("Second Quest", prerequisite_quests=["First Quest"])

        manager.add_quest(quest1)
        manager.add_quest(quest2)

        available = manager.get_available_quests(["First Quest"])
        assert quest1 in available
        assert quest2 in available

    # Spec: Excludes quests with unmet prerequisites
    def test_get_available_quests_excludes_unmet(self):
        manager = QuestNetworkManager()
        quest1 = make_quest("First Quest")
        quest2 = make_quest(
            "Requires Both",
            prerequisite_quests=["First Quest", "Another Quest"]
        )

        manager.add_quest(quest1)
        manager.add_quest(quest2)

        # Only one prereq met, not both
        available = manager.get_available_quests(["First Quest"])
        assert quest1 in available
        assert quest2 not in available

    # Spec: Returns quests in unlocks_quests list
    def test_get_unlocked_quests(self):
        manager = QuestNetworkManager()
        quest1 = make_quest(
            "First Quest",
            unlocks_quests=["Second Quest", "Third Quest"]
        )
        quest2 = make_quest("Second Quest")
        quest3 = make_quest("Third Quest")

        manager.add_quest(quest1)
        manager.add_quest(quest2)
        manager.add_quest(quest3)

        unlocked = manager.get_unlocked_quests("First Quest")
        assert len(unlocked) == 2
        assert quest2 in unlocked
        assert quest3 in unlocked


class TestStorylineQueries:
    """Tests for storyline navigation."""

    # Spec: Returns Quest objects for prerequisite_quests
    def test_get_prerequisites_of(self):
        manager = QuestNetworkManager()
        prereq1 = make_quest("Prereq One")
        prereq2 = make_quest("Prereq Two")
        main_quest = make_quest(
            "Main Quest",
            prerequisite_quests=["Prereq One", "Prereq Two"]
        )

        manager.add_quest(prereq1)
        manager.add_quest(prereq2)
        manager.add_quest(main_quest)

        prereqs = manager.get_prerequisites_of("Main Quest")
        assert len(prereqs) == 2
        assert prereq1 in prereqs
        assert prereq2 in prereqs

    # Spec: Returns Quest objects for unlocks_quests
    def test_get_unlocks_of(self):
        manager = QuestNetworkManager()
        main_quest = make_quest(
            "Main Quest",
            unlocks_quests=["Follow Up One", "Follow Up Two"]
        )
        follow1 = make_quest("Follow Up One")
        follow2 = make_quest("Follow Up Two")

        manager.add_quest(main_quest)
        manager.add_quest(follow1)
        manager.add_quest(follow2)

        unlocks = manager.get_unlocks_of("Main Quest")
        assert len(unlocks) == 2
        assert follow1 in unlocks
        assert follow2 in unlocks

    # Spec: Finds path A→B when B in A.unlocks_quests
    def test_find_path_direct(self):
        manager = QuestNetworkManager()
        quest_a = make_quest("Quest A", unlocks_quests=["Quest B"])
        quest_b = make_quest("Quest B")

        manager.add_quest(quest_a)
        manager.add_quest(quest_b)

        path = manager.find_path("Quest A", "Quest B")
        assert path == ["Quest A", "Quest B"]

    # Spec: Finds A→B→C chain
    def test_find_path_multi_hop(self):
        manager = QuestNetworkManager()
        quest_a = make_quest("Quest A", unlocks_quests=["Quest B"])
        quest_b = make_quest("Quest B", unlocks_quests=["Quest C"])
        quest_c = make_quest("Quest C")

        manager.add_quest(quest_a)
        manager.add_quest(quest_b)
        manager.add_quest(quest_c)

        path = manager.find_path("Quest A", "Quest C")
        assert path == ["Quest A", "Quest B", "Quest C"]

    # Spec: Returns None for unconnected quests
    def test_find_path_no_connection(self):
        manager = QuestNetworkManager()
        quest_a = make_quest("Quest A")
        quest_b = make_quest("Quest B")

        manager.add_quest(quest_a)
        manager.add_quest(quest_b)

        path = manager.find_path("Quest A", "Quest B")
        assert path is None


class TestSerialization:
    """Tests for serialization/deserialization."""

    # Spec: Preserves all quests through serialization
    def test_to_dict_from_dict_roundtrip(self):
        manager = QuestNetworkManager()
        quest1 = make_quest(
            "First Quest",
            chain_id="main",
            chain_position=1,
            unlocks_quests=["Second Quest"]
        )
        quest2 = make_quest(
            "Second Quest",
            chain_id="main",
            chain_position=2,
            prerequisite_quests=["First Quest"]
        )

        manager.add_quest(quest1)
        manager.add_quest(quest2)

        # Serialize and deserialize
        data = manager.to_dict()
        restored = QuestNetworkManager.from_dict(data)

        # Check quests preserved
        assert len(restored.get_all_quests()) == 2

        restored_q1 = restored.get_quest("First Quest")
        assert restored_q1 is not None
        assert restored_q1.name == "First Quest"
        assert restored_q1.chain_id == "main"
        assert restored_q1.chain_position == 1
        assert restored_q1.unlocks_quests == ["Second Quest"]

        restored_q2 = restored.get_quest("Second Quest")
        assert restored_q2 is not None
        assert restored_q2.name == "Second Quest"
        assert restored_q2.chain_id == "main"
        assert restored_q2.chain_position == 2
        assert restored_q2.prerequisite_quests == ["First Quest"]
