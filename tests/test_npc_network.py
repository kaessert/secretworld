"""Tests for NPCNetworkManager class."""
import pytest

from cli_rpg.models.npc import NPC
from cli_rpg.models.npc_relationship import RelationshipType
from cli_rpg.models.npc_network import FamilyRole, NPCNetworkManager


# ==== FamilyRole Enum Tests ====


def test_family_role_spouse_exists():
    """FamilyRole.SPOUSE exists with value 'spouse'."""
    assert FamilyRole.SPOUSE.value == "spouse"


def test_family_role_parent_exists():
    """FamilyRole.PARENT exists with value 'parent'."""
    assert FamilyRole.PARENT.value == "parent"


def test_family_role_child_exists():
    """FamilyRole.CHILD exists with value 'child'."""
    assert FamilyRole.CHILD.value == "child"


def test_family_role_sibling_exists():
    """FamilyRole.SIBLING exists with value 'sibling'."""
    assert FamilyRole.SIBLING.value == "sibling"


# ==== NPCNetworkManager Initialization Tests ====


def test_network_manager_init_empty():
    """Manager initializes with empty NPC dict."""
    manager = NPCNetworkManager()
    assert manager.get_all_npcs() == []


def test_network_manager_add_npc():
    """add_npc(npc) registers NPC by name."""
    manager = NPCNetworkManager()
    npc = NPC(name="Alice", description="A friendly traveler", dialogue="Hello!")
    manager.add_npc(npc)
    assert manager.get_npc("Alice") is npc


def test_network_manager_get_npc():
    """get_npc(name) returns NPC or None."""
    manager = NPCNetworkManager()
    npc = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    manager.add_npc(npc)

    # Should find existing NPC
    assert manager.get_npc("Bob") is npc
    # Should return None for non-existent NPC
    assert manager.get_npc("Charlie") is None


def test_network_manager_get_npc_case_insensitive():
    """get_npc(name) is case-insensitive."""
    manager = NPCNetworkManager()
    npc = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    manager.add_npc(npc)

    assert manager.get_npc("alice") is npc
    assert manager.get_npc("ALICE") is npc
    assert manager.get_npc("AlIcE") is npc


def test_network_manager_get_all_npcs():
    """get_all_npcs() returns list of all NPCs."""
    manager = NPCNetworkManager()
    npc1 = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    npc2 = NPC(name="Bob", description="A merchant", dialogue="Welcome!")

    manager.add_npc(npc1)
    manager.add_npc(npc2)

    all_npcs = manager.get_all_npcs()
    assert len(all_npcs) == 2
    assert npc1 in all_npcs
    assert npc2 in all_npcs


# ==== Bidirectional Relationships Tests ====


def test_add_relationship_bidirectional():
    """add_relationship(npc_a, npc_b, type, bidirectional=True) adds to both."""
    manager = NPCNetworkManager()
    npc_a = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    npc_b = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    manager.add_npc(npc_a)
    manager.add_npc(npc_b)

    manager.add_relationship("Alice", "Bob", RelationshipType.FRIEND, bidirectional=True)

    # Alice should have relationship to Bob
    alice_rel = npc_a.get_relationship("Bob")
    assert alice_rel is not None
    assert alice_rel.relationship_type == RelationshipType.FRIEND

    # Bob should have relationship to Alice
    bob_rel = npc_b.get_relationship("Alice")
    assert bob_rel is not None
    assert bob_rel.relationship_type == RelationshipType.FRIEND


def test_add_relationship_unidirectional():
    """add_relationship(npc_a, npc_b, type, bidirectional=False) adds to A only."""
    manager = NPCNetworkManager()
    npc_a = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    npc_b = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    manager.add_npc(npc_a)
    manager.add_npc(npc_b)

    manager.add_relationship("Alice", "Bob", RelationshipType.MENTOR, bidirectional=False)

    # Alice should have relationship to Bob
    alice_rel = npc_a.get_relationship("Bob")
    assert alice_rel is not None
    assert alice_rel.relationship_type == RelationshipType.MENTOR

    # Bob should NOT have relationship to Alice
    bob_rel = npc_b.get_relationship("Alice")
    assert bob_rel is None


def test_add_relationship_with_trust():
    """Trust level is set correctly on both sides."""
    manager = NPCNetworkManager()
    npc_a = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    npc_b = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    manager.add_npc(npc_a)
    manager.add_npc(npc_b)

    manager.add_relationship("Alice", "Bob", RelationshipType.FAMILY, trust=80, bidirectional=True)

    alice_rel = npc_a.get_relationship("Bob")
    assert alice_rel.trust_level == 80

    bob_rel = npc_b.get_relationship("Alice")
    assert bob_rel.trust_level == 80


# ==== Family Generation Tests ====


def test_generate_spouse():
    """generate_spouse(npc, name) creates spouse NPC with FAMILY relationship."""
    manager = NPCNetworkManager()
    npc = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    manager.add_npc(npc)

    spouse = manager.generate_spouse("Alice", "Bob")

    # Spouse should be registered
    assert manager.get_npc("Bob") is spouse

    # Both should have FAMILY relationship with "spouse" description
    alice_rel = npc.get_relationship("Bob")
    assert alice_rel is not None
    assert alice_rel.relationship_type == RelationshipType.FAMILY
    assert alice_rel.description == "spouse"

    bob_rel = spouse.get_relationship("Alice")
    assert bob_rel is not None
    assert bob_rel.relationship_type == RelationshipType.FAMILY
    assert bob_rel.description == "spouse"


def test_generate_child():
    """generate_child(parents, name) creates child linked to both parents."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    bob = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    manager.add_npc(alice)
    manager.add_npc(bob)

    child = manager.generate_child(["Alice", "Bob"], "Charlie")

    # Child should be registered
    assert manager.get_npc("Charlie") is child

    # Child should have FAMILY relationship to each parent with "parent" description
    child_rel_alice = child.get_relationship("Alice")
    assert child_rel_alice is not None
    assert child_rel_alice.relationship_type == RelationshipType.FAMILY
    assert child_rel_alice.description == "parent"

    child_rel_bob = child.get_relationship("Bob")
    assert child_rel_bob is not None
    assert child_rel_bob.relationship_type == RelationshipType.FAMILY
    assert child_rel_bob.description == "parent"

    # Each parent should have FAMILY relationship to child with "child" description
    alice_rel = alice.get_relationship("Charlie")
    assert alice_rel is not None
    assert alice_rel.relationship_type == RelationshipType.FAMILY
    assert alice_rel.description == "child"

    bob_rel = bob.get_relationship("Charlie")
    assert bob_rel is not None
    assert bob_rel.relationship_type == RelationshipType.FAMILY
    assert bob_rel.description == "child"


def test_generate_sibling():
    """generate_sibling(npc, name) creates sibling with reciprocal relationships."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    manager.add_npc(alice)

    sibling = manager.generate_sibling("Alice", "Bob")

    # Sibling should be registered
    assert manager.get_npc("Bob") is sibling

    # Both should have FAMILY relationship with "sibling" description
    alice_rel = alice.get_relationship("Bob")
    assert alice_rel is not None
    assert alice_rel.relationship_type == RelationshipType.FAMILY
    assert alice_rel.description == "sibling"

    bob_rel = sibling.get_relationship("Alice")
    assert bob_rel is not None
    assert bob_rel.relationship_type == RelationshipType.FAMILY
    assert bob_rel.description == "sibling"


def test_generate_family_unit():
    """generate_family_unit(head_name, size) creates connected family."""
    manager = NPCNetworkManager()

    # Generate a family with head, spouse, and 2 children
    family = manager.generate_family_unit("Alice", spouse_name="Bob", child_names=["Charlie", "Diana"])

    # All family members should be registered
    assert manager.get_npc("Alice") is not None
    assert manager.get_npc("Bob") is not None
    assert manager.get_npc("Charlie") is not None
    assert manager.get_npc("Diana") is not None

    # Alice and Bob should be spouses
    alice = manager.get_npc("Alice")
    bob = manager.get_npc("Bob")
    alice_rel = alice.get_relationship("Bob")
    assert alice_rel is not None
    assert alice_rel.description == "spouse"

    # Both children should be linked to both parents
    charlie = manager.get_npc("Charlie")
    diana = manager.get_npc("Diana")

    # Charlie -> parents
    assert charlie.get_relationship("Alice").description == "parent"
    assert charlie.get_relationship("Bob").description == "parent"

    # Diana -> parents
    assert diana.get_relationship("Alice").description == "parent"
    assert diana.get_relationship("Bob").description == "parent"

    # Parents -> children
    assert alice.get_relationship("Charlie").description == "child"
    assert alice.get_relationship("Diana").description == "child"
    assert bob.get_relationship("Charlie").description == "child"
    assert bob.get_relationship("Diana").description == "child"

    # Siblings should know each other
    assert charlie.get_relationship("Diana").description == "sibling"
    assert diana.get_relationship("Charlie").description == "sibling"


# ==== Network Queries Tests ====


def test_get_npcs_by_relationship():
    """get_npcs_with_relationship(npc, type) returns list of connected NPCs."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    bob = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    charlie = NPC(name="Charlie", description="A guard", dialogue="Halt!")

    manager.add_npc(alice)
    manager.add_npc(bob)
    manager.add_npc(charlie)

    manager.add_relationship("Alice", "Bob", RelationshipType.FRIEND, bidirectional=False)
    manager.add_relationship("Alice", "Charlie", RelationshipType.FAMILY, bidirectional=False)

    friends = manager.get_npcs_with_relationship("Alice", RelationshipType.FRIEND)
    assert "Bob" in friends
    assert "Charlie" not in friends

    family = manager.get_npcs_with_relationship("Alice", RelationshipType.FAMILY)
    assert "Charlie" in family
    assert "Bob" not in family


def test_get_family_members():
    """get_family_members(npc) returns all FAMILY relationships."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    bob = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    charlie = NPC(name="Charlie", description="A guard", dialogue="Halt!")
    diana = NPC(name="Diana", description="A blacksmith", dialogue="Need repairs?")

    manager.add_npc(alice)
    manager.add_npc(bob)
    manager.add_npc(charlie)
    manager.add_npc(diana)

    # Bob and Charlie are family, Diana is a friend
    manager.add_relationship("Alice", "Bob", RelationshipType.FAMILY, bidirectional=True)
    manager.add_relationship("Alice", "Charlie", RelationshipType.FAMILY, bidirectional=True)
    manager.add_relationship("Alice", "Diana", RelationshipType.FRIEND, bidirectional=True)

    family = manager.get_family_members("Alice")
    assert len(family) == 2
    assert "Bob" in family
    assert "Charlie" in family
    assert "Diana" not in family


def test_get_connections_within_degrees():
    """get_connections(npc, max_degrees=2) returns NPCs within N hops."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    bob = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    charlie = NPC(name="Charlie", description="A guard", dialogue="Halt!")
    diana = NPC(name="Diana", description="A blacksmith", dialogue="Need repairs?")

    manager.add_npc(alice)
    manager.add_npc(bob)
    manager.add_npc(charlie)
    manager.add_npc(diana)

    # Alice -> Bob (1 hop), Bob -> Charlie (1 hop), Charlie -> Diana (1 hop)
    manager.add_relationship("Alice", "Bob", RelationshipType.FRIEND, bidirectional=True)
    manager.add_relationship("Bob", "Charlie", RelationshipType.FRIEND, bidirectional=True)
    manager.add_relationship("Charlie", "Diana", RelationshipType.FRIEND, bidirectional=True)

    # 1 hop from Alice: only Bob
    one_hop = manager.get_connections("Alice", max_degrees=1)
    assert "Bob" in one_hop
    assert "Charlie" not in one_hop
    assert "Diana" not in one_hop

    # 2 hops from Alice: Bob and Charlie
    two_hops = manager.get_connections("Alice", max_degrees=2)
    assert "Bob" in two_hops
    assert "Charlie" in two_hops
    assert "Diana" not in two_hops

    # 3 hops from Alice: Bob, Charlie, and Diana
    three_hops = manager.get_connections("Alice", max_degrees=3)
    assert "Bob" in three_hops
    assert "Charlie" in three_hops
    assert "Diana" in three_hops


def test_find_path_between_npcs():
    """find_path(npc_a, npc_b) returns relationship chain or None."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    bob = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    charlie = NPC(name="Charlie", description="A guard", dialogue="Halt!")

    manager.add_npc(alice)
    manager.add_npc(bob)
    manager.add_npc(charlie)

    # Alice -> Bob -> Charlie
    manager.add_relationship("Alice", "Bob", RelationshipType.FRIEND, bidirectional=True)
    manager.add_relationship("Bob", "Charlie", RelationshipType.FAMILY, bidirectional=True)

    path = manager.find_path("Alice", "Charlie")
    assert path is not None
    # Path should be: Alice -(FRIEND)-> Bob -(FAMILY)-> Charlie
    assert len(path) == 2
    assert path[0] == ("Bob", RelationshipType.FRIEND)
    assert path[1] == ("Charlie", RelationshipType.FAMILY)

    # No path should return None
    diana = NPC(name="Diana", description="A blacksmith", dialogue="Need repairs?")
    manager.add_npc(diana)  # Diana is not connected

    no_path = manager.find_path("Alice", "Diana")
    assert no_path is None


# ==== Serialization Tests ====


def test_to_dict():
    """Manager serializes to dict with all NPCs."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    bob = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    manager.add_npc(alice)
    manager.add_npc(bob)

    manager.add_relationship("Alice", "Bob", RelationshipType.FRIEND, bidirectional=True)

    data = manager.to_dict()

    assert "npcs" in data
    assert len(data["npcs"]) == 2


def test_from_dict():
    """Manager deserializes from dict."""
    data = {
        "npcs": [
            {
                "name": "Alice",
                "description": "A traveler",
                "dialogue": "Hi!",
                "is_merchant": False,
                "shop": None,
                "is_quest_giver": False,
                "offered_quests": [],
                "greetings": [],
                "conversation_history": [],
                "available_at_night": True,
                "is_recruitable": False,
                "willpower": 5,
                "bribeable": True,
                "persuaded": False,
                "haggleable": True,
                "haggle_cooldown": 0,
                "faction": None,
                "required_reputation": None,
                "relationships": [
                    {
                        "target_npc": "Bob",
                        "relationship_type": "friend",
                        "trust_level": 50,
                        "description": None,
                    }
                ],
            },
            {
                "name": "Bob",
                "description": "A merchant",
                "dialogue": "Welcome!",
                "is_merchant": False,
                "shop": None,
                "is_quest_giver": False,
                "offered_quests": [],
                "greetings": [],
                "conversation_history": [],
                "available_at_night": True,
                "is_recruitable": False,
                "willpower": 5,
                "bribeable": True,
                "persuaded": False,
                "haggleable": True,
                "haggle_cooldown": 0,
                "faction": None,
                "required_reputation": None,
                "relationships": [
                    {
                        "target_npc": "Alice",
                        "relationship_type": "friend",
                        "trust_level": 50,
                        "description": None,
                    }
                ],
            },
        ]
    }

    manager = NPCNetworkManager.from_dict(data)

    assert manager.get_npc("Alice") is not None
    assert manager.get_npc("Bob") is not None

    alice = manager.get_npc("Alice")
    assert alice.get_relationship("Bob") is not None


def test_roundtrip():
    """Roundtrip preserves all NPCs and relationships."""
    manager = NPCNetworkManager()
    alice = NPC(name="Alice", description="A traveler", dialogue="Hi!")
    bob = NPC(name="Bob", description="A merchant", dialogue="Welcome!")
    charlie = NPC(name="Charlie", description="A guard", dialogue="Halt!")

    manager.add_npc(alice)
    manager.add_npc(bob)
    manager.add_npc(charlie)

    manager.add_relationship("Alice", "Bob", RelationshipType.FAMILY, trust=80, bidirectional=True)
    manager.add_relationship("Bob", "Charlie", RelationshipType.FRIEND, trust=60, bidirectional=True)

    # Serialize and deserialize
    data = manager.to_dict()
    restored = NPCNetworkManager.from_dict(data)

    # Verify all NPCs exist
    assert restored.get_npc("Alice") is not None
    assert restored.get_npc("Bob") is not None
    assert restored.get_npc("Charlie") is not None

    # Verify relationships preserved
    alice_restored = restored.get_npc("Alice")
    alice_bob_rel = alice_restored.get_relationship("Bob")
    assert alice_bob_rel is not None
    assert alice_bob_rel.relationship_type == RelationshipType.FAMILY
    assert alice_bob_rel.trust_level == 80

    bob_restored = restored.get_npc("Bob")
    bob_charlie_rel = bob_restored.get_relationship("Charlie")
    assert bob_charlie_rel is not None
    assert bob_charlie_rel.relationship_type == RelationshipType.FRIEND
    assert bob_charlie_rel.trust_level == 60
