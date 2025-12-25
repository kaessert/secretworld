"""Tests for NPC greetings feature.

Tests the NPC greetings field and get_greeting() method that allows
NPCs to have varied greeting text for more immersive interactions.
"""
import pytest
from cli_rpg.models.npc import NPC


class TestNPCGreetings:
    """Tests for NPC greetings list and get_greeting() method."""

    def test_npc_greetings_default_empty(self):
        """NPC greetings defaults to empty list."""
        # Spec: NPCs gain an optional greetings: List[str] field (default: empty list)
        npc = NPC(name="Guard", description="A guard", dialogue="Halt!")
        assert npc.greetings == []

    def test_npc_with_greetings(self):
        """NPC can be created with greetings list."""
        # Spec: NPCs gain an optional greetings: List[str] field
        greetings = ["Hello!", "Welcome!", "Good day!"]
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hi", greetings=greetings)
        assert npc.greetings == greetings

    def test_npc_get_greeting_returns_from_list(self):
        """get_greeting returns a greeting from the list when available."""
        # Spec: If greetings is non-empty, display a random greeting from the list
        greetings = ["Hello!", "Welcome!"]
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hi", greetings=greetings)
        assert npc.get_greeting() in greetings

    def test_npc_get_greeting_falls_back_to_dialogue(self):
        """get_greeting returns dialogue when greetings is empty."""
        # Spec: Otherwise, fall back to existing dialogue field (backward compatible)
        npc = NPC(name="Guard", description="A guard", dialogue="Move along.")
        assert npc.get_greeting() == "Move along."

    def test_npc_greetings_serialization(self):
        """Greetings are serialized to dict."""
        # Spec: Greetings should persist (serialization)
        greetings = ["Hello!", "Welcome!"]
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hi", greetings=greetings)
        data = npc.to_dict()
        assert data["greetings"] == greetings

    def test_npc_greetings_deserialization(self):
        """Greetings are deserialized from dict."""
        # Spec: Greetings should persist (deserialization)
        data = {
            "name": "Merchant",
            "description": "A shopkeeper",
            "dialogue": "Hi",
            "greetings": ["Hello!", "Welcome!"],
            "is_merchant": False,
            "shop": None,
            "is_quest_giver": False,
            "offered_quests": []
        }
        npc = NPC.from_dict(data)
        assert npc.greetings == ["Hello!", "Welcome!"]

    def test_npc_greetings_deserialization_missing(self):
        """Missing greetings in dict defaults to empty list."""
        # Spec: Backward compatibility - old save files without greetings should work
        data = {
            "name": "Guard",
            "description": "A guard",
            "dialogue": "Halt!",
            "is_merchant": False,
            "shop": None
        }
        npc = NPC.from_dict(data)
        assert npc.greetings == []
