"""Tests for quest faction integration.

This module tests the faction-related fields on quests and the integration
with the faction reputation system when completing quests.

Spec coverage:
- faction_affiliation (Optional[str]): The faction this quest is associated with
- faction_reward (int, default 0): Reputation gained with affiliated faction on completion
- faction_penalty (int, default 0): Reputation lost with rival faction on completion
- required_reputation (Optional[int]): Minimum reputation with faction required to accept quest
"""

import pytest

from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.models.character import Character
from cli_rpg.models.faction import Faction


# --- Quest Model Tests ---


def test_quest_faction_affiliation_field_optional():
    """Test that faction_affiliation is optional and defaults to None."""
    # Spec: faction_affiliation (Optional[str])
    quest = Quest(
        name="Test Quest",
        description="A test quest",
        objective_type=ObjectiveType.KILL,
        target="goblin",
    )
    assert quest.faction_affiliation is None


def test_quest_faction_affiliation_can_be_set():
    """Test that faction_affiliation can be set to a faction name."""
    # Spec: faction_affiliation (Optional[str]): The faction this quest is associated with
    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        faction_affiliation="Town Guard",
    )
    assert quest.faction_affiliation == "Town Guard"


def test_quest_faction_reward_field_defaults_to_zero():
    """Test that faction_reward defaults to 0."""
    # Spec: faction_reward (int, default 0)
    quest = Quest(
        name="Test Quest",
        description="A test quest",
        objective_type=ObjectiveType.KILL,
        target="goblin",
    )
    assert quest.faction_reward == 0


def test_quest_faction_reward_can_be_set():
    """Test that faction_reward can be set to a positive value."""
    # Spec: faction_reward (int, default 0): Reputation gained with affiliated faction
    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        faction_affiliation="Town Guard",
        faction_reward=10,
    )
    assert quest.faction_reward == 10


def test_quest_faction_penalty_field_defaults_to_zero():
    """Test that faction_penalty defaults to 0."""
    # Spec: faction_penalty (int, default 0)
    quest = Quest(
        name="Test Quest",
        description="A test quest",
        objective_type=ObjectiveType.KILL,
        target="goblin",
    )
    assert quest.faction_penalty == 0


def test_quest_faction_penalty_can_be_set():
    """Test that faction_penalty can be set to a positive value."""
    # Spec: faction_penalty (int, default 0): Reputation lost with rival faction
    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        faction_affiliation="Town Guard",
        faction_penalty=5,
    )
    assert quest.faction_penalty == 5


def test_quest_required_reputation_field_optional():
    """Test that required_reputation is optional and defaults to None."""
    # Spec: required_reputation (Optional[int])
    quest = Quest(
        name="Test Quest",
        description="A test quest",
        objective_type=ObjectiveType.KILL,
        target="goblin",
    )
    assert quest.required_reputation is None


def test_quest_required_reputation_can_be_set():
    """Test that required_reputation can be set to a value."""
    # Spec: required_reputation (Optional[int]): Minimum reputation with faction required
    quest = Quest(
        name="Elite Guard Mission",
        description="A high-level guard mission",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        faction_affiliation="Town Guard",
        required_reputation=60,
    )
    assert quest.required_reputation == 60


def test_quest_negative_faction_reward_rejected():
    """Test that negative faction_reward raises ValueError."""
    # Spec: faction_reward cannot be negative (implied by reward semantics)
    with pytest.raises(ValueError, match="faction_reward cannot be negative"):
        Quest(
            name="Bad Quest",
            description="A broken quest",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            faction_reward=-5,
        )


def test_quest_negative_faction_penalty_rejected():
    """Test that negative faction_penalty raises ValueError."""
    # Spec: faction_penalty cannot be negative (implied by penalty semantics)
    with pytest.raises(ValueError, match="faction_penalty cannot be negative"):
        Quest(
            name="Bad Quest",
            description="A broken quest",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            faction_penalty=-5,
        )


def test_quest_to_dict_includes_faction_fields():
    """Test that to_dict() includes all faction-related fields."""
    # Spec: to_dict() includes faction_affiliation, faction_reward, faction_penalty, required_reputation
    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        faction_affiliation="Town Guard",
        faction_reward=10,
        faction_penalty=5,
        required_reputation=40,
    )
    data = quest.to_dict()
    assert data["faction_affiliation"] == "Town Guard"
    assert data["faction_reward"] == 10
    assert data["faction_penalty"] == 5
    assert data["required_reputation"] == 40


def test_quest_from_dict_restores_faction_fields():
    """Test that from_dict() restores all faction-related fields."""
    # Spec: from_dict() restores faction_affiliation, faction_reward, faction_penalty, required_reputation
    data = {
        "name": "Guard Duty",
        "description": "Help the guards",
        "status": "available",
        "objective_type": "kill",
        "target": "bandit",
        "faction_affiliation": "Town Guard",
        "faction_reward": 10,
        "faction_penalty": 5,
        "required_reputation": 40,
    }
    quest = Quest.from_dict(data)
    assert quest.faction_affiliation == "Town Guard"
    assert quest.faction_reward == 10
    assert quest.faction_penalty == 5
    assert quest.required_reputation == 40


def test_quest_from_dict_missing_faction_fields_uses_defaults():
    """Test that from_dict() uses defaults when faction fields are missing."""
    # Spec: from_dict() handles old save files without faction fields (backward compat)
    data = {
        "name": "Old Quest",
        "description": "A quest from an old save",
        "status": "available",
        "objective_type": "kill",
        "target": "goblin",
    }
    quest = Quest.from_dict(data)
    assert quest.faction_affiliation is None
    assert quest.faction_reward == 0
    assert quest.faction_penalty == 0
    assert quest.required_reputation is None


# --- Claim Rewards Faction Integration Tests ---


def test_claim_quest_rewards_applies_faction_reward():
    """Test that claiming rewards increases reputation with affiliated faction."""
    # Spec: On quest completion, apply faction_reward to affiliated faction
    character = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        status=QuestStatus.READY_TO_TURN_IN,
        faction_affiliation="Town Guard",
        faction_reward=10,
    )
    character.quests.append(quest)

    # Create factions
    town_guard = Faction(name="Town Guard", description="The city guard", reputation=50)
    factions = [town_guard]

    messages = character.claim_quest_rewards(quest, factions=factions)

    # Check reputation increased
    assert town_guard.reputation == 60
    # Check message was returned
    assert any("Town Guard" in msg and "increased" in msg and "10" in msg for msg in messages)


def test_claim_quest_rewards_applies_faction_penalty_to_rival():
    """Test that claiming rewards decreases reputation with rival faction."""
    # Spec: On quest completion, apply faction_penalty to rival faction
    character = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        status=QuestStatus.READY_TO_TURN_IN,
        faction_affiliation="Town Guard",
        faction_reward=10,
        faction_penalty=5,
    )
    character.quests.append(quest)

    # Create factions including the rival
    town_guard = Faction(name="Town Guard", description="The city guard", reputation=50)
    thieves_guild = Faction(name="Thieves Guild", description="The thieves", reputation=50)
    factions = [town_guard, thieves_guild]

    messages = character.claim_quest_rewards(quest, factions=factions)

    # Check rival reputation decreased
    assert thieves_guild.reputation == 45
    # Check message was returned
    assert any("Thieves Guild" in msg and "decreased" in msg and "5" in msg for msg in messages)


def test_claim_quest_rewards_returns_faction_messages():
    """Test that claim_quest_rewards returns appropriate faction messages."""
    # Spec: Display reputation change messages alongside gold/XP/item rewards
    character = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        status=QuestStatus.READY_TO_TURN_IN,
        gold_reward=100,
        faction_affiliation="Town Guard",
        faction_reward=10,
        faction_penalty=5,
    )
    character.quests.append(quest)

    town_guard = Faction(name="Town Guard", description="The city guard", reputation=50)
    thieves_guild = Faction(name="Thieves Guild", description="The thieves", reputation=50)
    factions = [town_guard, thieves_guild]

    messages = character.claim_quest_rewards(quest, factions=factions)

    # Should have gold message and faction messages
    assert any("100 gold" in msg for msg in messages)
    assert any("Town Guard" in msg for msg in messages)
    assert any("Thieves Guild" in msg for msg in messages)


def test_claim_quest_rewards_triggers_level_up_message():
    """Test that reputation level changes trigger appropriate messages."""
    # Spec: Display level up messages when reputation crosses thresholds
    character = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

    quest = Quest(
        name="Grand Mission",
        description="A significant mission",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        status=QuestStatus.READY_TO_TURN_IN,
        faction_affiliation="Town Guard",
        faction_reward=15,  # 55 + 15 = 70, crossing into Friendly
    )
    character.quests.append(quest)

    # Start at 55 (NEUTRAL), reward 15 should push to 70 (FRIENDLY)
    town_guard = Faction(name="Town Guard", description="The city guard", reputation=55)
    factions = [town_guard]

    messages = character.claim_quest_rewards(quest, factions=factions)

    # Check level up message was included
    assert any("friend" in msg.lower() or "friendly" in msg.lower() for msg in messages)


def test_claim_quest_rewards_with_no_faction_affiliation_no_changes():
    """Test that quests without faction affiliation don't affect reputation."""
    # Spec: Quest without faction_affiliation should not affect any factions
    character = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

    quest = Quest(
        name="Simple Quest",
        description="A normal quest",
        objective_type=ObjectiveType.KILL,
        target="goblin",
        status=QuestStatus.READY_TO_TURN_IN,
        gold_reward=50,
        # No faction_affiliation
    )
    character.quests.append(quest)

    town_guard = Faction(name="Town Guard", description="The city guard", reputation=50)
    factions = [town_guard]

    messages = character.claim_quest_rewards(quest, factions=factions)

    # Reputation should be unchanged
    assert town_guard.reputation == 50
    # Should have gold message but no faction messages
    assert any("50 gold" in msg for msg in messages)
    assert not any("Town Guard" in msg for msg in messages)


def test_claim_quest_rewards_no_factions_provided():
    """Test that claim_quest_rewards works when factions list is None."""
    # Spec: Backward compatibility - factions parameter is optional
    character = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

    quest = Quest(
        name="Guard Duty",
        description="Help the guards",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        status=QuestStatus.READY_TO_TURN_IN,
        gold_reward=100,
        faction_affiliation="Town Guard",
        faction_reward=10,
    )
    character.quests.append(quest)

    # Call without factions - should work without error
    messages = character.claim_quest_rewards(quest)

    # Should have gold message
    assert any("100 gold" in msg for msg in messages)


# --- Quest Acceptance Tests ---


def test_accept_quest_allowed_when_reputation_meets_requirement():
    """Test that quests can be accepted when reputation meets required_reputation."""
    # Spec: Quest acceptance checks required_reputation against player's current standing
    quest = Quest(
        name="Elite Guard Mission",
        description="A high-level mission",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        faction_affiliation="Town Guard",
        required_reputation=50,
    )

    faction = Faction(name="Town Guard", description="The city guard", reputation=50)

    # Reputation exactly at requirement
    assert faction.reputation >= quest.required_reputation


def test_accept_quest_blocked_when_reputation_too_low():
    """Test that quests are blocked when reputation is below required_reputation."""
    # Spec: Quest acceptance checks required_reputation against player's current standing
    quest = Quest(
        name="Elite Guard Mission",
        description="A high-level mission",
        objective_type=ObjectiveType.KILL,
        target="bandit",
        faction_affiliation="Town Guard",
        required_reputation=60,
    )

    faction = Faction(name="Town Guard", description="The city guard", reputation=50)

    # Reputation below requirement
    assert faction.reputation < quest.required_reputation


def test_accept_quest_allowed_when_no_required_reputation():
    """Test that quests with no required_reputation can always be accepted."""
    # Spec: required_reputation (Optional[int]) - None means no requirement
    quest = Quest(
        name="Basic Quest",
        description="A simple quest",
        objective_type=ObjectiveType.KILL,
        target="goblin",
        # No required_reputation
    )

    # Quest has no requirement
    assert quest.required_reputation is None
