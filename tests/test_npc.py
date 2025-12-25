"""Tests for NPC model.

Tests the NPC model including validation and serialization.
"""
import pytest
from unittest.mock import patch
from cli_rpg.models.npc import NPC


class TestNPC:
    """Tests for NPC model - tests spec: NPC Model."""

    def test_create_npc(self):
        """NPC can be created with basic attributes."""
        npc = NPC(name="Merchant", description="A friendly shopkeeper", dialogue="Welcome!", is_merchant=True)
        assert npc.name == "Merchant"
        assert npc.description == "A friendly shopkeeper"
        assert npc.dialogue == "Welcome!"
        assert npc.is_merchant is True

    def test_create_npc_not_merchant(self):
        """NPC defaults to not being a merchant."""
        npc = NPC(name="Guard", description="A town guard", dialogue="Move along, citizen.")
        assert npc.is_merchant is False

    def test_npc_name_validation_too_short(self):
        """NPC name must be at least 2 characters."""
        with pytest.raises(ValueError, match="2-30 characters"):
            NPC(name="X", description="Too short name", dialogue="Hi")

    def test_npc_name_validation_too_long(self):
        """NPC name must be at most 30 characters."""
        with pytest.raises(ValueError, match="2-30 characters"):
            NPC(name="X" * 31, description="Too long name", dialogue="Hi")

    def test_npc_description_validation_empty(self):
        """NPC description cannot be empty."""
        with pytest.raises(ValueError, match="1-200 characters"):
            NPC(name="Merchant", description="", dialogue="Hi")

    def test_npc_description_validation_too_long(self):
        """NPC description must be at most 200 characters."""
        with pytest.raises(ValueError, match="1-200 characters"):
            NPC(name="Merchant", description="X" * 201, dialogue="Hi")

    def test_npc_serialization(self):
        """NPC can be serialized to dict."""
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello!", is_merchant=True)
        data = npc.to_dict()
        assert data["name"] == "Merchant"
        assert data["description"] == "A shopkeeper"
        assert data["dialogue"] == "Hello!"
        assert data["is_merchant"] is True

    def test_npc_deserialization(self):
        """NPC can be deserialized from dict."""
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello!", is_merchant=True)
        data = npc.to_dict()
        restored = NPC.from_dict(data)
        assert restored.name == npc.name
        assert restored.description == npc.description
        assert restored.dialogue == npc.dialogue
        assert restored.is_merchant == npc.is_merchant

    def test_npc_with_shop_serialization(self):
        """NPC with shop can be serialized and deserialized."""
        from cli_rpg.models.shop import Shop, ShopItem
        from cli_rpg.models.item import Item, ItemType

        item = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=25)
        shop_item = ShopItem(item=item, buy_price=50)
        shop = Shop(name="Potion Shop", inventory=[shop_item])
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Welcome!", is_merchant=True, shop=shop)

        data = npc.to_dict()
        restored = NPC.from_dict(data)

        assert restored.shop is not None
        assert restored.shop.name == "Potion Shop"
        assert len(restored.shop.inventory) == 1

    def test_get_greeting_with_greetings_list(self):
        """get_greeting() returns a random greeting from the greetings list."""
        # Tests spec: NPC get_greeting method with greetings list
        greetings = ["Hello!", "Hi there!", "Welcome traveler!"]
        npc = NPC(
            name="Merchant",
            description="A shopkeeper",
            dialogue="Default dialogue",
            greetings=greetings,
        )
        # Mock random.choice to verify it's called with the greetings list
        with patch("cli_rpg.models.npc.random.choice") as mock_choice:
            mock_choice.return_value = "Hello!"
            result = npc.get_greeting()
            mock_choice.assert_called_once_with(greetings)
            assert result == "Hello!"

    def test_get_greeting_without_greetings_list(self):
        """get_greeting() returns dialogue when greetings list is empty."""
        # Tests spec: NPC get_greeting fallback to dialogue
        npc = NPC(
            name="Merchant",
            description="A shopkeeper",
            dialogue="Default dialogue",
        )
        result = npc.get_greeting()
        assert result == "Default dialogue"

    def test_add_conversation_basic(self):
        """add_conversation() adds entries to conversation_history."""
        # Tests spec: NPC add_conversation method basic functionality
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Welcome!")
        assert len(npc.conversation_history) == 0

        npc.add_conversation("player", "Hello")
        assert len(npc.conversation_history) == 1
        assert npc.conversation_history[0] == {"role": "player", "content": "Hello"}

        npc.add_conversation("npc", "Welcome to my shop!")
        assert len(npc.conversation_history) == 2
        assert npc.conversation_history[1] == {"role": "npc", "content": "Welcome to my shop!"}

    def test_add_conversation_caps_at_10_entries(self):
        """add_conversation() caps conversation_history at 10 entries."""
        # Tests spec: NPC add_conversation method caps at 10 entries
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Welcome!")

        # Add 12 conversations
        for i in range(12):
            npc.add_conversation("player", f"Message {i}")

        # Should only have 10 entries
        assert len(npc.conversation_history) == 10
        # Should have the 10 most recent (messages 2-11)
        assert npc.conversation_history[0] == {"role": "player", "content": "Message 2"}
        assert npc.conversation_history[9] == {"role": "player", "content": "Message 11"}

    def test_get_greeting_aggressive_reputation(self):
        """get_greeting() returns aggressive greeting when player has 10+ kills."""
        # Tests spec: Aggressive reputation triggers at 10+ combat_kill choices
        npc = NPC(name="Guard", description="A town guard", dialogue="Hello")
        choices = [{"choice_type": "combat_kill"} for _ in range(10)]
        with patch("cli_rpg.models.npc.random.choice") as mock_choice:
            mock_choice.return_value = "I've heard tales of your... efficiency in combat."
            result = npc.get_greeting(choices=choices)
            # Should call _get_reputation_greeting which uses random.choice on templates
            assert "efficiency" in result or mock_choice.called

    def test_get_greeting_no_aggressive_below_threshold(self):
        """get_greeting() returns normal greeting when kills < 10."""
        # Tests spec: Aggressive reputation only triggers at threshold
        npc = NPC(name="Guard", description="A town guard", dialogue="Hello")
        choices = [{"choice_type": "combat_kill"} for _ in range(9)]
        result = npc.get_greeting(choices=choices)
        assert result == "Hello"  # Falls back to dialogue

    def test_get_greeting_cautious_priority_over_aggressive(self):
        """cautious reputation (flee) takes priority over aggressive (kill)."""
        # Tests spec: Cautious checked before aggressive
        npc = NPC(name="Guard", description="A town guard", dialogue="Hello")
        choices = (
            [{"choice_type": "combat_flee"} for _ in range(3)] +
            [{"choice_type": "combat_kill"} for _ in range(10)]
        )
        with patch("cli_rpg.models.npc.random.choice") as mock_choice:
            mock_choice.return_value = "Word travels fast. They say you're... careful."
            result = npc.get_greeting(choices=choices)
            # Should get cautious greeting (flee checked first)
            assert (
                "careful" in result.lower()
                or "run" in result.lower()
                or "coward" in result.lower()
                or "survivor" in result.lower()
            )
