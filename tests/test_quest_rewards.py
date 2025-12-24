"""Tests for quest reward system.

Spec: When a quest's objectives are met, the system should:
1. Automatically mark the quest as COMPLETED (already implemented)
2. Grant defined rewards to the player: gold, XP, and optionally items
3. Display reward notification messages to the player
"""

import pytest

from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.models.character import Character
from cli_rpg.models.item import Item, ItemType


@pytest.fixture
def character():
    """Create a basic character for testing."""
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


class TestQuestRewardFields:
    """Tests for Quest reward fields (gold_reward, xp_reward, item_rewards)."""

    # Spec: Quests can have optional gold, XP, and item rewards
    def test_quest_with_gold_reward(self):
        """Test creating a quest with gold reward."""
        quest = Quest(
            name="Slay the Dragon",
            description="Defeat the dragon",
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            gold_reward=100,
        )
        assert quest.gold_reward == 100

    def test_quest_with_xp_reward(self):
        """Test creating a quest with XP reward."""
        quest = Quest(
            name="Slay the Dragon",
            description="Defeat the dragon",
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            xp_reward=50,
        )
        assert quest.xp_reward == 50

    def test_quest_with_item_rewards(self):
        """Test creating a quest with item rewards."""
        quest = Quest(
            name="Slay the Dragon",
            description="Defeat the dragon",
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            item_rewards=["Dragon Scale", "Dragon Tooth"],
        )
        assert quest.item_rewards == ["Dragon Scale", "Dragon Tooth"]

    def test_quest_with_all_rewards(self):
        """Test creating a quest with all types of rewards."""
        quest = Quest(
            name="Slay the Dragon",
            description="Defeat the dragon",
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            gold_reward=100,
            xp_reward=50,
            item_rewards=["Dragon Scale"],
        )
        assert quest.gold_reward == 100
        assert quest.xp_reward == 50
        assert quest.item_rewards == ["Dragon Scale"]

    # Spec: Reward fields default to 0/empty list
    def test_quest_reward_defaults(self):
        """Test that reward fields default to zero/empty."""
        quest = Quest(
            name="Simple Quest",
            description="A simple quest",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.gold_reward == 0
        assert quest.xp_reward == 0
        assert quest.item_rewards == []


class TestQuestRewardValidation:
    """Tests for quest reward validation."""

    # Spec: Negative rewards should be rejected
    def test_negative_gold_reward_rejected(self):
        """Test that negative gold reward raises ValueError."""
        with pytest.raises(ValueError, match="gold_reward cannot be negative"):
            Quest(
                name="Bad Quest",
                description="A quest with negative rewards",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                gold_reward=-10,
            )

    def test_negative_xp_reward_rejected(self):
        """Test that negative XP reward raises ValueError."""
        with pytest.raises(ValueError, match="xp_reward cannot be negative"):
            Quest(
                name="Bad Quest",
                description="A quest with negative rewards",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                xp_reward=-10,
            )

    def test_zero_rewards_accepted(self):
        """Test that zero rewards are valid."""
        quest = Quest(
            name="Zero Reward Quest",
            description="A quest with no rewards",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            gold_reward=0,
            xp_reward=0,
            item_rewards=[],
        )
        assert quest.gold_reward == 0
        assert quest.xp_reward == 0
        assert quest.item_rewards == []


class TestQuestRewardSerialization:
    """Tests for quest reward serialization (to_dict/from_dict)."""

    # Spec: Reward fields should be included in serialization
    def test_to_dict_includes_rewards(self):
        """Test that to_dict includes reward fields."""
        quest = Quest(
            name="Slay the Dragon",
            description="Defeat the dragon",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            target_count=1,
            current_count=0,
            gold_reward=100,
            xp_reward=50,
            item_rewards=["Dragon Scale", "Dragon Tooth"],
        )
        data = quest.to_dict()
        assert data["gold_reward"] == 100
        assert data["xp_reward"] == 50
        assert data["item_rewards"] == ["Dragon Scale", "Dragon Tooth"]

    def test_from_dict_restores_rewards(self):
        """Test that from_dict restores reward fields."""
        data = {
            "name": "Slay the Dragon",
            "description": "Defeat the dragon",
            "status": "active",
            "objective_type": "kill",
            "target": "Dragon",
            "target_count": 1,
            "current_count": 0,
            "gold_reward": 100,
            "xp_reward": 50,
            "item_rewards": ["Dragon Scale", "Dragon Tooth"],
        }
        quest = Quest.from_dict(data)
        assert quest.gold_reward == 100
        assert quest.xp_reward == 50
        assert quest.item_rewards == ["Dragon Scale", "Dragon Tooth"]

    def test_from_dict_with_missing_rewards_uses_defaults(self):
        """Test that from_dict uses defaults when reward fields are missing."""
        data = {
            "name": "Old Quest",
            "description": "A quest from before rewards were added",
            "status": "active",
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "current_count": 0,
        }
        quest = Quest.from_dict(data)
        assert quest.gold_reward == 0
        assert quest.xp_reward == 0
        assert quest.item_rewards == []

    def test_serialization_roundtrip_with_rewards(self):
        """Test that to_dict -> from_dict roundtrip preserves rewards."""
        original = Quest(
            name="Collect Herbs",
            description="Gather healing herbs",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.COLLECT,
            target="Healing Herb",
            target_count=5,
            current_count=2,
            gold_reward=25,
            xp_reward=10,
            item_rewards=["Herb Pouch"],
        )
        data = original.to_dict()
        restored = Quest.from_dict(data)

        assert restored.gold_reward == original.gold_reward
        assert restored.xp_reward == original.xp_reward
        assert restored.item_rewards == original.item_rewards


class TestClaimQuestRewards:
    """Tests for Character.claim_quest_rewards() method."""

    # Spec: claim_quest_rewards grants gold to the player
    def test_claim_quest_rewards_grants_gold(self, character):
        """Test that claiming rewards grants gold to character."""
        quest = Quest(
            name="Gold Quest",
            description="Get some gold",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            gold_reward=100,
        )

        initial_gold = character.gold
        character.claim_quest_rewards(quest)

        assert character.gold == initial_gold + 100

    # Spec: claim_quest_rewards grants XP to the player
    def test_claim_quest_rewards_grants_xp(self, character):
        """Test that claiming rewards grants XP to character."""
        quest = Quest(
            name="XP Quest",
            description="Get some XP",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            xp_reward=50,
        )

        initial_xp = character.xp
        character.claim_quest_rewards(quest)

        assert character.xp == initial_xp + 50

    # Spec: claim_quest_rewards grants items to the player
    def test_claim_quest_rewards_grants_items(self, character):
        """Test that claiming rewards grants items to character."""
        quest = Quest(
            name="Item Quest",
            description="Get some items",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            item_rewards=["Health Potion"],
        )

        character.claim_quest_rewards(quest)

        # Character should have the item in inventory
        item_names = [item.name for item in character.inventory.items]
        assert "Health Potion" in item_names

    # Spec: claim_quest_rewards returns reward messages
    def test_claim_quest_rewards_returns_gold_message(self, character):
        """Test that claiming rewards returns gold message."""
        quest = Quest(
            name="Gold Quest",
            description="Get some gold",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            gold_reward=100,
        )

        messages = character.claim_quest_rewards(quest)

        assert any("100 gold" in msg for msg in messages)

    def test_claim_quest_rewards_returns_xp_message(self, character):
        """Test that claiming rewards returns XP message."""
        quest = Quest(
            name="XP Quest",
            description="Get some XP",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            xp_reward=50,
        )

        messages = character.claim_quest_rewards(quest)

        # XP message comes from gain_xp
        assert any("50 XP" in msg or "Gained 50" in msg for msg in messages)

    def test_claim_quest_rewards_returns_item_message(self, character):
        """Test that claiming rewards returns item message."""
        quest = Quest(
            name="Item Quest",
            description="Get some items",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            item_rewards=["Health Potion"],
        )

        messages = character.claim_quest_rewards(quest)

        assert any("Health Potion" in msg for msg in messages)

    # Spec: claim_quest_rewards requires COMPLETED status
    def test_claim_quest_rewards_requires_completed_status(self, character):
        """Test that claiming rewards requires quest to be COMPLETED."""
        for status in [QuestStatus.ACTIVE, QuestStatus.AVAILABLE, QuestStatus.FAILED]:
            quest = Quest(
                name=f"Quest {status.value}",
                description="A quest",
                status=status,
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                gold_reward=100,
            )

            with pytest.raises(ValueError, match="Quest must be completed"):
                character.claim_quest_rewards(quest)

    def test_claim_quest_rewards_with_no_rewards(self, character):
        """Test that claiming rewards with no rewards defined returns empty list."""
        quest = Quest(
            name="No Reward Quest",
            description="A quest with no rewards",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )

        initial_gold = character.gold
        initial_xp = character.xp
        messages = character.claim_quest_rewards(quest)

        assert character.gold == initial_gold
        assert character.xp == initial_xp
        assert messages == []

    def test_claim_quest_rewards_with_all_reward_types(self, character):
        """Test claiming rewards with gold, XP, and items together."""
        quest = Quest(
            name="Full Reward Quest",
            description="Get all the rewards",
            status=QuestStatus.COMPLETED,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            gold_reward=100,
            xp_reward=50,
            item_rewards=["Health Potion"],
        )

        initial_gold = character.gold
        initial_xp = character.xp
        messages = character.claim_quest_rewards(quest)

        assert character.gold == initial_gold + 100
        assert character.xp >= initial_xp + 50  # >= because of potential level up
        item_names = [item.name for item in character.inventory.items]
        assert "Health Potion" in item_names
        assert len(messages) >= 3  # At least gold, XP, and item messages


class TestRecordKillWithRewards:
    """Tests for reward granting when quests complete via record_kill."""

    # Spec: When quest completes via record_kill, rewards are granted
    def test_record_kill_grants_rewards_on_completion(self, character):
        """Test that completing a quest via record_kill grants rewards."""
        quest = Quest(
            name="Goblin Slayer",
            description="Kill 1 goblin",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=1,
            current_count=0,
            gold_reward=50,
            xp_reward=25,
        )
        character.quests.append(quest)

        initial_gold = character.gold
        initial_xp = character.xp
        messages = character.record_kill("Goblin")

        # Quest should be completed
        assert quest.status == QuestStatus.COMPLETED
        # Rewards should be granted
        assert character.gold == initial_gold + 50
        assert character.xp >= initial_xp + 25

    def test_record_kill_includes_reward_messages(self, character):
        """Test that record_kill returns reward messages on completion."""
        quest = Quest(
            name="Goblin Slayer",
            description="Kill 1 goblin",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=1,
            current_count=0,
            gold_reward=50,
            xp_reward=25,
        )
        character.quests.append(quest)

        messages = character.record_kill("Goblin")

        # Should have completion message + reward messages
        assert any("Quest Complete" in msg for msg in messages)
        assert any("50 gold" in msg for msg in messages)
        assert any("25 XP" in msg or "Gained 25" in msg for msg in messages)

    def test_record_kill_does_not_grant_rewards_on_progress(self, character):
        """Test that progress (not completion) doesn't grant rewards."""
        quest = Quest(
            name="Goblin Hunter",
            description="Kill 3 goblins",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
            current_count=0,
            gold_reward=50,
            xp_reward=25,
        )
        character.quests.append(quest)

        initial_gold = character.gold
        initial_xp = character.xp
        messages = character.record_kill("Goblin")

        # Quest should NOT be completed yet
        assert quest.status == QuestStatus.ACTIVE
        # Rewards should NOT be granted
        assert character.gold == initial_gold
        assert character.xp == initial_xp
        # Should only have progress message
        assert len(messages) == 1
        assert "progress" in messages[0].lower()

    def test_record_kill_grants_item_rewards_on_completion(self, character):
        """Test that item rewards are granted when quest completes via record_kill."""
        quest = Quest(
            name="Goblin Slayer",
            description="Kill 1 goblin",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=1,
            current_count=0,
            item_rewards=["Goblin Ear"],
        )
        character.quests.append(quest)

        character.record_kill("Goblin")

        # Item should be in inventory
        item_names = [item.name for item in character.inventory.items]
        assert "Goblin Ear" in item_names
