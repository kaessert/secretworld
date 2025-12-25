"""Tests for NPC consequence system - NPCs react to player choices.

Spec: NPC Echo Consequences MVP - NPCs reference tracked player choices when greeting the player.
"""
import pytest
from unittest.mock import patch
from cli_rpg.models.npc import NPC


class TestNPCReputationGreetings:
    """Tests for NPC greetings based on player reputation/choices."""

    def test_get_greeting_acknowledges_flee_reputation(self):
        """Spec: NPC acknowledges player's 'cautious' reputation when 3+ combat_flee choices."""
        npc = NPC(
            name="Merchant",
            description="A shopkeeper",
            dialogue="Welcome!",
            greetings=["Hello there!"],
        )

        # Create choices with 3+ combat_flee entries
        choices = [
            {"choice_type": "combat_flee", "choice_id": "flee_1", "target": "Goblin"},
            {"choice_type": "combat_flee", "choice_id": "flee_2", "target": "Orc"},
            {"choice_type": "combat_flee", "choice_id": "flee_3", "target": "Troll"},
        ]

        greeting = npc.get_greeting(choices=choices)

        # Should contain reputation reference (cautious/run/survivor/coward)
        reputation_words = ["cautious", "careful", "run", "survivor", "coward"]
        assert any(word in greeting.lower() for word in reputation_words), (
            f"Expected reputation greeting, got: {greeting}"
        )

    def test_get_greeting_normal_when_few_flees(self):
        """Spec: Normal greeting when less than 3 combat_flee choices."""
        npc = NPC(
            name="Merchant",
            description="A shopkeeper",
            dialogue="Welcome!",
            greetings=["Hello there!", "Greetings!"],
        )

        # Only 2 flee choices - not enough for reputation
        choices = [
            {"choice_type": "combat_flee", "choice_id": "flee_1", "target": "Goblin"},
            {"choice_type": "combat_flee", "choice_id": "flee_2", "target": "Orc"},
        ]

        # Mock random.choice to verify normal greeting path is used
        with patch("cli_rpg.models.npc.random.choice") as mock_choice:
            mock_choice.return_value = "Hello there!"
            greeting = npc.get_greeting(choices=choices)
            # Should use normal greeting path (random.choice from greetings)
            mock_choice.assert_called_once_with(npc.greetings)
            assert greeting == "Hello there!"

    def test_get_greeting_normal_when_no_choices(self):
        """Spec: Normal greeting when no choices passed (backward compatibility)."""
        npc = NPC(
            name="Merchant",
            description="A shopkeeper",
            dialogue="Welcome!",
            greetings=["Hello there!"],
        )

        # No choices - default behavior
        with patch("cli_rpg.models.npc.random.choice") as mock_choice:
            mock_choice.return_value = "Hello there!"
            greeting = npc.get_greeting()  # No choices argument
            mock_choice.assert_called_once_with(npc.greetings)
            assert greeting == "Hello there!"

    def test_get_greeting_normal_when_empty_choices(self):
        """Spec: Normal greeting when empty choices list passed."""
        npc = NPC(
            name="Merchant",
            description="A shopkeeper",
            dialogue="Welcome!",
            greetings=["Hello there!"],
        )

        # Empty list - should use normal greeting
        with patch("cli_rpg.models.npc.random.choice") as mock_choice:
            mock_choice.return_value = "Hello there!"
            greeting = npc.get_greeting(choices=[])
            mock_choice.assert_called_once_with(npc.greetings)
            assert greeting == "Hello there!"

    def test_reputation_greeting_serializes_correctly(self):
        """Spec: NPC serialization still works (no regression from changes)."""
        npc = NPC(
            name="Merchant",
            description="A shopkeeper",
            dialogue="Welcome!",
            greetings=["Hello there!", "Greetings!"],
        )

        # Serialize and deserialize
        data = npc.to_dict()
        restored = NPC.from_dict(data)

        # Should work correctly
        assert restored.name == npc.name
        assert restored.greetings == npc.greetings

        # get_greeting should still work on restored NPC
        choices = [
            {"choice_type": "combat_flee", "choice_id": "flee_1", "target": "Goblin"},
            {"choice_type": "combat_flee", "choice_id": "flee_2", "target": "Orc"},
            {"choice_type": "combat_flee", "choice_id": "flee_3", "target": "Troll"},
        ]
        greeting = restored.get_greeting(choices=choices)
        reputation_words = ["cautious", "careful", "run", "survivor", "coward"]
        assert any(word in greeting.lower() for word in reputation_words)

    def test_get_greeting_with_dialogue_fallback_and_reputation(self):
        """Spec: Reputation greeting works even when NPC has no greetings list."""
        npc = NPC(
            name="Guard",
            description="A town guard",
            dialogue="Move along, citizen.",
            # No greetings list
        )

        choices = [
            {"choice_type": "combat_flee", "choice_id": "flee_1", "target": "Goblin"},
            {"choice_type": "combat_flee", "choice_id": "flee_2", "target": "Orc"},
            {"choice_type": "combat_flee", "choice_id": "flee_3", "target": "Troll"},
        ]

        greeting = npc.get_greeting(choices=choices)
        # Should still get reputation greeting
        reputation_words = ["cautious", "careful", "run", "survivor", "coward"]
        assert any(word in greeting.lower() for word in reputation_words)
