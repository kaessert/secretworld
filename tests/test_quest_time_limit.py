"""Tests for time-sensitive quests feature.

This module tests the time limit functionality for quests:
- time_limit_hours field (Optional[int])
- accepted_at field (Optional[int])
- is_expired() method
- get_time_remaining() method
- Integration with quest acceptance and journal display

Spec: Add optional time limits to quests, creating urgency and gameplay tension.
When a time-limited quest expires, it automatically fails.
"""

import pytest

from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType


class TestQuestTimeLimitModelDefaults:
    """Test default values for time limit fields."""

    def test_quest_time_limit_defaults_to_none(self):
        """Spec: new quests have no time limit by default."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        assert quest.time_limit_hours is None

    def test_quest_accepted_at_defaults_to_none(self):
        """Spec: new quests have no accepted_at by default."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        assert quest.accepted_at is None


class TestQuestIsExpired:
    """Test is_expired() method."""

    def test_is_expired_returns_false_when_no_time_limit(self):
        """Spec: no limit = never expires."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=None,
            accepted_at=100,
        )
        # Should never expire, no matter how much time passes
        assert quest.is_expired(current_game_hour=1000000) is False

    def test_is_expired_returns_false_when_no_accepted_at(self):
        """Spec: if accepted_at is None, quest is not expired."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=None,
        )
        assert quest.is_expired(current_game_hour=1000) is False

    def test_is_expired_returns_false_when_time_remaining(self):
        """Spec: still has time left = not expired."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=100,
        )
        # Only 10 hours have passed, 14 remaining
        assert quest.is_expired(current_game_hour=110) is False

    def test_is_expired_returns_true_when_time_exceeded(self):
        """Spec: past deadline = expired."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=100,
        )
        # 25 hours have passed, deadline was 24 hours
        assert quest.is_expired(current_game_hour=125) is True

    def test_is_expired_returns_true_when_exactly_at_limit(self):
        """Spec: edge case - exactly at limit = expired."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=100,
        )
        # Exactly 24 hours have passed
        assert quest.is_expired(current_game_hour=124) is True


class TestQuestGetTimeRemaining:
    """Test get_time_remaining() method."""

    def test_get_time_remaining_returns_none_when_no_limit(self):
        """Spec: no limit = None."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=None,
            accepted_at=100,
        )
        assert quest.get_time_remaining(current_game_hour=500) is None

    def test_get_time_remaining_returns_none_when_no_accepted_at(self):
        """Spec: if accepted_at is None, return None."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=None,
        )
        assert quest.get_time_remaining(current_game_hour=500) is None

    def test_get_time_remaining_returns_hours_left(self):
        """Spec: calculates remaining hours correctly."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=100,
        )
        # 10 hours have passed, 14 remaining
        assert quest.get_time_remaining(current_game_hour=110) == 14

    def test_get_time_remaining_returns_zero_when_expired(self):
        """Spec: floor at 0 (never negative)."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=100,
        )
        # 30 hours have passed, way past deadline
        assert quest.get_time_remaining(current_game_hour=130) == 0


class TestQuestTimeLimitValidation:
    """Test validation of time_limit_hours field."""

    def test_time_limit_validation_rejects_zero(self):
        """Spec: time_limit_hours must be >= 1."""
        with pytest.raises(ValueError, match="time_limit_hours must be at least 1"):
            Quest(
                name="Test Quest",
                description="A test quest",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                time_limit_hours=0,
            )

    def test_time_limit_validation_rejects_negative(self):
        """Spec: time_limit_hours must be >= 1."""
        with pytest.raises(ValueError, match="time_limit_hours must be at least 1"):
            Quest(
                name="Test Quest",
                description="A test quest",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                time_limit_hours=-5,
            )

    def test_time_limit_accepts_valid_positive_value(self):
        """Valid positive time limit should be accepted."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=1,
        )
        assert quest.time_limit_hours == 1


class TestQuestSerialization:
    """Test serialization of time limit fields."""

    def test_to_dict_includes_time_limit_fields(self):
        """Spec: to_dict serializes new fields."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            time_limit_hours=24,
            accepted_at=100,
        )
        data = quest.to_dict()
        assert data["time_limit_hours"] == 24
        assert data["accepted_at"] == 100

    def test_to_dict_includes_none_time_limit_fields(self):
        """Spec: to_dict serializes None values for time fields."""
        quest = Quest(
            name="Test Quest",
            description="A test quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        data = quest.to_dict()
        assert data["time_limit_hours"] is None
        assert data["accepted_at"] is None

    def test_from_dict_restores_time_limit_fields(self):
        """Spec: from_dict deserializes correctly."""
        data = {
            "name": "Test Quest",
            "description": "A test quest",
            "status": "active",
            "objective_type": "kill",
            "target": "Goblin",
            "time_limit_hours": 48,
            "accepted_at": 200,
        }
        quest = Quest.from_dict(data)
        assert quest.time_limit_hours == 48
        assert quest.accepted_at == 200

    def test_from_dict_handles_missing_time_fields(self):
        """Spec: backward compat - missing fields default to None."""
        data = {
            "name": "Test Quest",
            "description": "A test quest",
            "status": "active",
            "objective_type": "kill",
            "target": "Goblin",
            # No time_limit_hours or accepted_at fields
        }
        quest = Quest.from_dict(data)
        assert quest.time_limit_hours is None
        assert quest.accepted_at is None


class TestQuestAcceptanceIntegration:
    """Test integration of time limit fields with quest acceptance."""

    def test_accept_quest_sets_accepted_at(self):
        """Spec: main.py sets accepted_at on accept when quest has time_limit."""
        # This tests the Quest creation logic when accepting from NPC
        # We simulate what main.py should do when accepting a time-limited quest
        from cli_rpg.models.quest import Quest, QuestStatus

        # Simulated matching_quest from NPC (has time limit)
        matching_quest = Quest(
            name="Urgent Delivery",
            description="Deliver this package before nightfall",
            objective_type=ObjectiveType.TALK,
            target="Village Elder",
            time_limit_hours=24,
        )

        # Simulated current game hour
        current_game_hour = 150

        # This is the creation logic that should be in main.py
        new_quest = Quest(
            name=matching_quest.name,
            description=matching_quest.description,
            objective_type=matching_quest.objective_type,
            target=matching_quest.target,
            target_count=matching_quest.target_count,
            status=QuestStatus.ACTIVE,
            current_count=0,
            time_limit_hours=matching_quest.time_limit_hours,
            accepted_at=current_game_hour if matching_quest.time_limit_hours else None,
        )

        assert new_quest.time_limit_hours == 24
        assert new_quest.accepted_at == 150

    def test_accept_quest_no_accepted_at_when_no_time_limit(self):
        """Spec: accepted_at is None when quest has no time_limit."""
        from cli_rpg.models.quest import Quest, QuestStatus

        # Simulated matching_quest from NPC (no time limit)
        matching_quest = Quest(
            name="Casual Task",
            description="Do this whenever",
            objective_type=ObjectiveType.TALK,
            target="Farmer",
            time_limit_hours=None,
        )

        current_game_hour = 150

        new_quest = Quest(
            name=matching_quest.name,
            description=matching_quest.description,
            objective_type=matching_quest.objective_type,
            target=matching_quest.target,
            target_count=matching_quest.target_count,
            status=QuestStatus.ACTIVE,
            current_count=0,
            time_limit_hours=matching_quest.time_limit_hours,
            accepted_at=current_game_hour if matching_quest.time_limit_hours else None,
        )

        assert new_quest.time_limit_hours is None
        assert new_quest.accepted_at is None

    def test_companion_quest_sets_accepted_at(self):
        """Spec: companion_quests.py sets accepted_at on accept."""
        from cli_rpg.models.companion import Companion
        from cli_rpg.companion_quests import accept_companion_quest

        # Create companion with time-limited personal quest
        companion = Companion(
            name="Test Companion",
            description="A helpful companion",
            recruited_at="Test Town",
            bond_points=50,  # TRUSTED level
            personal_quest=Quest(
                name="Companion's Errand",
                description="Help me with something urgent",
                objective_type=ObjectiveType.COLLECT,
                target="Lost Heirloom",
                time_limit_hours=48,
            ),
        )

        current_game_hour = 300
        new_quest = accept_companion_quest(companion, current_hour=current_game_hour)

        assert new_quest is not None
        assert new_quest.time_limit_hours == 48
        assert new_quest.accepted_at == 300


class TestCheckExpiredQuests:
    """Test check_expired_quests method in GameState."""

    def test_expired_quest_auto_fails(self):
        """Spec: check_expired_quests fails expired quests."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        # Create minimal game state
        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add time-limited quest that is expired
        expired_quest = Quest(
            name="Expired Quest",
            description="This quest has expired",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            status=QuestStatus.ACTIVE,
            time_limit_hours=24,
            accepted_at=100,
        )
        game_state.current_character.quests.append(expired_quest)

        # Set game time past the deadline
        game_state.game_time.advance(200)  # Way past 124 (100 + 24)

        # Check for expired quests
        messages = game_state.check_expired_quests()

        # Quest should be failed
        assert expired_quest.status == QuestStatus.FAILED
        assert len(messages) == 1
        assert "Expired Quest" in messages[0]
        assert "expired" in messages[0].lower()

    def test_check_expired_quests_ignores_non_active(self):
        """Spec: only ACTIVE quests are checked for expiration."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add completed quest that would be "expired" if it were active
        completed_quest = Quest(
            name="Completed Quest",
            description="This quest is done",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            status=QuestStatus.COMPLETED,
            time_limit_hours=24,
            accepted_at=100,
        )
        game_state.current_character.quests.append(completed_quest)

        game_state.game_time.advance(200)
        messages = game_state.check_expired_quests()

        # Should not change status of completed quest
        assert completed_quest.status == QuestStatus.COMPLETED
        assert len(messages) == 0

    def test_check_expired_quests_ignores_no_time_limit(self):
        """Spec: quests without time limits are never expired."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add quest with no time limit
        normal_quest = Quest(
            name="Normal Quest",
            description="Take your time",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            status=QuestStatus.ACTIVE,
            time_limit_hours=None,
        )
        game_state.current_character.quests.append(normal_quest)

        game_state.game_time.advance(99999)
        messages = game_state.check_expired_quests()

        # Should not expire
        assert normal_quest.status == QuestStatus.ACTIVE
        assert len(messages) == 0


class TestJournalDisplay:
    """Test journal display of time remaining."""

    def test_journal_shows_time_remaining(self):
        """Spec: quests command shows '(Xh left)' for time-limited quests."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add time-limited quest with time remaining
        timed_quest = Quest(
            name="Urgent Delivery",
            description="Deliver before time runs out",
            objective_type=ObjectiveType.TALK,
            target="Elder",
            status=QuestStatus.ACTIVE,
            time_limit_hours=24,
            accepted_at=100,
        )
        game_state.current_character.quests.append(timed_quest)

        # Set game time so 10 hours have passed (14 remaining)
        game_state.game_time.advance(110)

        # Run quests command
        success, output = handle_exploration_command(game_state, "quests", [])

        assert success
        assert "(14h left)" in output

    def test_journal_shows_expired(self):
        """Spec: quests command shows '(EXPIRED!)' for expired quests."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add expired quest
        expired_quest = Quest(
            name="Too Late",
            description="You missed the deadline",
            objective_type=ObjectiveType.TALK,
            target="Elder",
            status=QuestStatus.ACTIVE,
            time_limit_hours=24,
            accepted_at=100,
        )
        game_state.current_character.quests.append(expired_quest)

        # Set game time past deadline
        game_state.game_time.advance(130)

        # Run quests command
        success, output = handle_exploration_command(game_state, "quests", [])

        assert success
        assert "(EXPIRED!)" in output

    def test_quest_details_shows_time_remaining(self):
        """Spec: quest command shows deadline in details."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add time-limited quest
        timed_quest = Quest(
            name="Urgent Delivery",
            description="Deliver before time runs out",
            objective_type=ObjectiveType.TALK,
            target="Elder",
            status=QuestStatus.ACTIVE,
            time_limit_hours=48,
            accepted_at=100,
        )
        game_state.current_character.quests.append(timed_quest)

        # Set game time so 20 hours have passed (28 remaining)
        game_state.game_time.advance(120)

        # Run quest command for details
        success, output = handle_exploration_command(game_state, "quest", ["urgent"])

        assert success
        assert "Time Remaining: 28 hours" in output

    def test_quest_details_shows_expired(self):
        """Spec: quest command shows 'EXPIRED!' when time limit exceeded."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add expired quest
        expired_quest = Quest(
            name="Urgent Delivery",
            description="Deliver before time runs out",
            objective_type=ObjectiveType.TALK,
            target="Elder",
            status=QuestStatus.ACTIVE,
            time_limit_hours=24,
            accepted_at=100,
        )
        game_state.current_character.quests.append(expired_quest)

        # Set game time past deadline
        game_state.game_time.advance(130)

        # Run quest command for details
        success, output = handle_exploration_command(game_state, "quest", ["urgent"])

        assert success
        assert "Time Remaining: EXPIRED!" in output

    def test_journal_no_time_info_for_unlimited_quests(self):
        """Quests without time limits should not show time info."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        character = Character(
            name="Test Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        location = Location(
            name="Test Town",
            description="A test town",
            coordinates=(0, 0),
        )
        game_state = GameState(
            character=character,
            world={"Test Town": location},
            starting_location="Test Town",
        )

        # Add quest without time limit
        normal_quest = Quest(
            name="Casual Task",
            description="No rush",
            objective_type=ObjectiveType.TALK,
            target="Farmer",
            status=QuestStatus.ACTIVE,
        )
        game_state.current_character.quests.append(normal_quest)

        # Run quests command
        success, output = handle_exploration_command(game_state, "quests", [])

        assert success
        assert "h left)" not in output
        assert "EXPIRED" not in output
