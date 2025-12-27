"""Tests for rival adventurers feature (Issue 25).

Rival adventurer parties race the player to boss rooms and treasure chests
within SubGrid interiors.
"""

import pytest
from unittest.mock import MagicMock, patch
import random

from cli_rpg.interior_events import (
    InteriorEvent,
    RIVAL_SPAWN_CHANCE,
    RIVAL_PARTY_SIZE_RANGE,
    RIVAL_CATEGORIES,
    RIVAL_PARTY_NAMES,
    RIVAL_ADVENTURER_TEMPLATES,
    check_for_rival_spawn,
    progress_rival_party,
    get_active_rival_event,
    get_rival_encounter_at_location,
)
from cli_rpg.world_grid import SubGrid
from cli_rpg.models.location import Location


class TestRivalAdventurerEvent:
    """Tests for InteriorEvent model with rival adventurer fields."""

    def test_event_creation_with_rival_fields(self):
        """Test creating InteriorEvent with rival adventurer fields."""
        # Spec: RivalEvent with event_id, party, target_room, progress, arrival_turns
        rival_party = [
            {"name": "Rival Warrior", "hp": 30, "attack": 8, "defense": 4}
        ]
        event = InteriorEvent(
            event_id="rival_001",
            event_type="rival_adventurers",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=rival_party,
            target_room="Boss Chamber",
            rival_progress=0,
            arrival_turns=5,
        )

        assert event.event_id == "rival_001"
        assert event.event_type == "rival_adventurers"
        assert event.rival_party == rival_party
        assert event.target_room == "Boss Chamber"
        assert event.rival_progress == 0
        assert event.arrival_turns == 5
        assert event.is_active is True

    def test_event_serialization_with_rival_fields(self):
        """Test to_dict/from_dict including NPC party serialization."""
        # Spec: Serialization includes rival party data
        rival_party = [
            {"name": "Rival Mage", "hp": 20, "attack": 10, "defense": 2},
            {"name": "Rival Rogue", "hp": 25, "attack": 9, "defense": 3},
        ]
        event = InteriorEvent(
            event_id="rival_002",
            event_type="rival_adventurers",
            location_coords=(1, 2, -1),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            rival_party=rival_party,
            target_room="Treasure Vault",
            rival_progress=3,
            arrival_turns=8,
        )

        data = event.to_dict()
        restored = InteriorEvent.from_dict(data)

        assert restored.event_id == event.event_id
        assert restored.event_type == "rival_adventurers"
        assert restored.rival_party == rival_party
        assert restored.target_room == "Treasure Vault"
        assert restored.rival_progress == 3
        assert restored.arrival_turns == 8
        assert restored.location_coords == (1, 2, -1)

    def test_arrival_check_returns_true_when_arrived(self):
        """Test is_rival_arrived() returns True when progress >= arrival_turns."""
        event = InteriorEvent(
            event_id="rival_003",
            event_type="rival_adventurers",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=[{"name": "Rival Warrior", "hp": 30, "attack": 8, "defense": 4}],
            target_room="Boss Room",
            rival_progress=5,
            arrival_turns=5,
        )

        assert event.is_rival_arrived() is True

        # Not arrived yet
        event.rival_progress = 4
        assert event.is_rival_arrived() is False

        # Exceeded arrival time
        event.rival_progress = 10
        assert event.is_rival_arrived() is True


class TestRivalSpawning:
    """Tests for rival adventurer spawn mechanics."""

    def test_spawn_chance_15_percent(self):
        """Test that rivals only spawn when random < 0.15."""
        # Spec: RIVAL_SPAWN_CHANCE = 0.15
        assert RIVAL_SPAWN_CHANCE == 0.15

    def test_spawn_only_in_valid_categories(self):
        """Test spawn only in dungeon/cave/ruins/temple."""
        # Spec: Spawn in dungeon, cave, ruins, temple only
        assert "dungeon" in RIVAL_CATEGORIES
        assert "cave" in RIVAL_CATEGORIES
        assert "ruins" in RIVAL_CATEGORIES
        assert "temple" in RIVAL_CATEGORIES
        assert "town" not in RIVAL_CATEGORIES
        assert "forest" not in RIVAL_CATEGORIES

    def test_spawn_creates_party_with_correct_size(self):
        """Test spawn creates 1-3 rival NPCs."""
        # Spec: RIVAL_PARTY_SIZE_RANGE = (1, 3)
        assert RIVAL_PARTY_SIZE_RANGE == (1, 3)

    def test_rival_templates_have_combat_stats(self):
        """Test rival templates have required combat stats."""
        for template in RIVAL_ADVENTURER_TEMPLATES:
            assert "name" in template
            assert "hp" in template
            assert "attack" in template
            assert "defense" in template

    def test_check_for_rival_spawn_creates_event(self):
        """Test check_for_rival_spawn creates event with correct properties."""
        # Setup mock game_state and sub_grid
        game_state = MagicMock()
        game_state.game_time.total_hours = 100

        # Create sub_grid with boss room
        sub_grid = SubGrid()
        sub_grid.parent_name = "Dark Dungeon"
        sub_grid.bounds = (-3, 3, -3, 3, 0, 0)

        entry_room = Location(name="Entrance", description="Entry point")
        entry_room.is_exit_point = True
        sub_grid.add_location(entry_room, 0, 0, 0)

        boss_room = Location(name="Boss Chamber", description="A dark chamber")
        boss_room.boss_enemy = "stone_golem"
        sub_grid.add_location(boss_room, 0, 2, 0)

        # Mock parent location with valid category
        parent = Location(name="Dark Dungeon", description="A dark dungeon")
        parent.category = "dungeon"
        game_state.world = {"Dark Dungeon": parent}

        # Force spawn (set random to 0)
        with patch('cli_rpg.interior_events.random.random', return_value=0.1):
            with patch('cli_rpg.interior_events.random.randint', return_value=2):
                with patch('cli_rpg.interior_events.random.choice', side_effect=lambda x: x[0]):
                    message = check_for_rival_spawn(game_state, sub_grid)

        assert message is not None
        assert len(sub_grid.interior_events) > 0

        # Find the rival event
        rival_event = get_active_rival_event(sub_grid)
        assert rival_event is not None
        assert rival_event.event_type == "rival_adventurers"
        assert rival_event.target_room == "Boss Chamber"
        assert rival_event.rival_party is not None
        assert len(rival_event.rival_party) >= 1

    def test_no_spawn_if_no_targets(self):
        """Test no rivals spawn if no boss/treasure rooms exist."""
        game_state = MagicMock()
        game_state.game_time.total_hours = 100

        # Create sub_grid with no boss or treasure rooms
        sub_grid = SubGrid()
        sub_grid.parent_name = "Empty Cave"
        sub_grid.bounds = (-1, 1, -1, 1, 0, 0)

        entry_room = Location(name="Entrance", description="Entry point")
        entry_room.is_exit_point = True
        sub_grid.add_location(entry_room, 0, 0, 0)

        plain_room = Location(name="Plain Room", description="Nothing special")
        sub_grid.add_location(plain_room, 0, 1, 0)

        # Mock parent location with valid category
        parent = Location(name="Empty Cave", description="An empty cave")
        parent.category = "cave"
        game_state.world = {"Empty Cave": parent}

        with patch('cli_rpg.interior_events.random.random', return_value=0.1):
            message = check_for_rival_spawn(game_state, sub_grid)

        # Should not spawn because no valid targets
        assert message is None

    def test_spawn_selects_boss_over_treasure(self):
        """Test target is boss_room preferred over treasure room."""
        game_state = MagicMock()
        game_state.game_time.total_hours = 100

        sub_grid = SubGrid()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.bounds = (-3, 3, -3, 3, 0, 0)

        entry = Location(name="Entry", description="Entry")
        entry.is_exit_point = True
        sub_grid.add_location(entry, 0, 0, 0)

        # Add treasure room first
        treasure_room = Location(name="Treasure Room", description="Has treasure")
        treasure_room.treasures = [{"item": "gold", "amount": 100}]
        sub_grid.add_location(treasure_room, 1, 0, 0)

        # Add boss room
        boss_room = Location(name="Boss Room", description="Has boss")
        boss_room.boss_enemy = "dragon"
        sub_grid.add_location(boss_room, 0, 1, 0)

        parent = Location(name="Test Dungeon", description="Test")
        parent.category = "dungeon"
        game_state.world = {"Test Dungeon": parent}

        with patch('cli_rpg.interior_events.random.random', return_value=0.1):
            with patch('cli_rpg.interior_events.random.randint', return_value=1):
                with patch('cli_rpg.interior_events.random.choice', side_effect=lambda x: x[0]):
                    message = check_for_rival_spawn(game_state, sub_grid)

        rival_event = get_active_rival_event(sub_grid)
        # Should prefer boss room
        assert rival_event.target_room == "Boss Room"


class TestRivalProgress:
    """Tests for rival party progress mechanics."""

    def test_progress_on_player_move(self):
        """Test progress_rival_party() increments progress."""
        game_state = MagicMock()

        sub_grid = SubGrid()
        rival_event = InteriorEvent(
            event_id="rival_progress_test",
            event_type="rival_adventurers",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=[{"name": "Rival", "hp": 30, "attack": 8, "defense": 4}],
            target_room="Boss Chamber",
            rival_progress=0,
            arrival_turns=5,
        )
        sub_grid.interior_events.append(rival_event)

        # Progress should increase by 1
        message = progress_rival_party(game_state, sub_grid)
        assert rival_event.rival_progress == 1

    def test_warning_messages_by_progress(self):
        """Test different messages at 25%, 50%, 75% progress."""
        game_state = MagicMock()

        sub_grid = SubGrid()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.bounds = (-3, 3, -3, 3, 0, 0)

        # Create boss room
        boss_room = Location(name="Boss Chamber", description="Boss room")
        boss_room.boss_enemy = "dragon"
        sub_grid.add_location(boss_room, 0, 2, 0)

        rival_event = InteriorEvent(
            event_id="rival_warnings",
            event_type="rival_adventurers",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=[{"name": "Rival", "hp": 30, "attack": 8, "defense": 4}],
            target_room="Boss Chamber",
            rival_progress=0,
            arrival_turns=8,
        )
        sub_grid.interior_events.append(rival_event)

        # Progress to 25% (2/8)
        rival_event.rival_progress = 1
        message = progress_rival_party(game_state, sub_grid)
        assert message is not None
        assert "voices" in message.lower() or "ahead" in message.lower() or "hear" in message.lower()

        # Progress to 50% (4/8)
        rival_event.rival_progress = 3
        message = progress_rival_party(game_state, sub_grid)
        assert message is not None

        # Progress to 75% (6/8)
        rival_event.rival_progress = 5
        message = progress_rival_party(game_state, sub_grid)
        assert message is not None

    def test_rivals_arrive_at_boss(self):
        """Test when arrived, boss_defeated=True, rivals present at location."""
        game_state = MagicMock()

        sub_grid = SubGrid()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.bounds = (-3, 3, -3, 3, 0, 0)

        # Create entry and boss room
        entry = Location(name="Entry", description="Entry")
        entry.is_exit_point = True
        sub_grid.add_location(entry, 0, 0, 0)

        boss_room = Location(name="Boss Chamber", description="Boss room")
        boss_room.boss_enemy = "dragon"
        boss_room.boss_defeated = False
        sub_grid.add_location(boss_room, 0, 2, 0)

        rival_party = [
            {"name": "Rival Warrior", "hp": 30, "attack": 8, "defense": 4}
        ]
        rival_event = InteriorEvent(
            event_id="rival_arrive_boss",
            event_type="rival_adventurers",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=rival_party,
            target_room="Boss Chamber",
            rival_progress=4,  # One away from arrival
            arrival_turns=5,
        )
        sub_grid.interior_events.append(rival_event)

        # Progress to arrival
        message = progress_rival_party(game_state, sub_grid)

        assert rival_event.rival_progress >= rival_event.arrival_turns
        assert boss_room.boss_defeated is True
        assert "rival" in message.lower() or "defeated" in message.lower()

    def test_rivals_arrive_at_treasure(self):
        """Test when arrived at treasure, chest opened=True, rivals present."""
        game_state = MagicMock()

        sub_grid = SubGrid()
        sub_grid.parent_name = "Test Cave"
        sub_grid.bounds = (-3, 3, -3, 3, 0, 0)

        # Create entry and treasure room
        entry = Location(name="Entry", description="Entry")
        entry.is_exit_point = True
        sub_grid.add_location(entry, 0, 0, 0)

        treasure_room = Location(name="Treasure Room", description="Gold!")
        treasure_room.treasures = [{"item": "gold", "amount": 100, "opened": False}]
        sub_grid.add_location(treasure_room, 0, 2, 0)

        rival_party = [
            {"name": "Rival Rogue", "hp": 25, "attack": 9, "defense": 3}
        ]
        rival_event = InteriorEvent(
            event_id="rival_arrive_treasure",
            event_type="rival_adventurers",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=rival_party,
            target_room="Treasure Room",
            rival_progress=4,
            arrival_turns=5,
        )
        sub_grid.interior_events.append(rival_event)

        message = progress_rival_party(game_state, sub_grid)

        # Treasure should be marked as opened
        assert treasure_room.treasures[0].get("opened") is True
        assert "rival" in message.lower() or "treasure" in message.lower()


class TestRivalCombat:
    """Tests for rival encounter combat mechanics."""

    def test_encounter_rivals_in_room(self):
        """Test entering room with rivals returns encounter info."""
        sub_grid = SubGrid()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.bounds = (-3, 3, -3, 3, 0, 0)

        boss_room = Location(name="Boss Chamber", description="Boss room")
        boss_room.boss_enemy = "dragon"
        boss_room.boss_defeated = True  # Rivals defeated it
        sub_grid.add_location(boss_room, 0, 2, 0)

        rival_party = [
            {"name": "Rival Warrior", "hp": 30, "attack": 8, "defense": 4}
        ]
        rival_event = InteriorEvent(
            event_id="rival_encounter",
            event_type="rival_adventurers",
            location_coords=(0, 2, 0),  # At boss room
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=rival_party,
            target_room="Boss Chamber",
            rival_progress=5,
            arrival_turns=5,
            rival_at_target=True,  # Rivals have arrived
        )
        sub_grid.interior_events.append(rival_event)

        # Check for encounter at boss room
        encounter = get_rival_encounter_at_location(sub_grid, boss_room)
        assert encounter is not None
        assert encounter.rival_party == rival_party

    def test_defeating_rivals_stops_race(self):
        """Test on combat victory, rival event marked inactive."""
        sub_grid = SubGrid()

        rival_event = InteriorEvent(
            event_id="rival_defeat",
            event_type="rival_adventurers",
            location_coords=(0, 2, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=0,
            rival_party=[{"name": "Rival", "hp": 30, "attack": 8, "defense": 4}],
            target_room="Boss Chamber",
            rival_progress=5,
            arrival_turns=5,
            rival_at_target=True,
        )
        sub_grid.interior_events.append(rival_event)

        # Simulate defeating rivals
        rival_event.is_active = False

        # Should no longer be an active rival event
        active_rival = get_active_rival_event(sub_grid)
        assert active_rival is None


class TestRivalIntegration:
    """Integration tests for rival adventurer system."""

    def test_subgrid_serialization_with_rivals(self):
        """Test SubGrid saves/loads rival events correctly."""
        sub_grid = SubGrid()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.bounds = (-3, 3, -3, 3, 0, 0)

        entry = Location(name="Entry", description="Entry")
        sub_grid.add_location(entry, 0, 0, 0)

        rival_event = InteriorEvent(
            event_id="rival_serialize",
            event_type="rival_adventurers",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            rival_party=[{"name": "Rival", "hp": 30, "attack": 8, "defense": 4}],
            target_room="Boss Chamber",
            rival_progress=3,
            arrival_turns=7,
        )
        sub_grid.interior_events.append(rival_event)

        # Serialize and restore
        data = sub_grid.to_dict()
        restored = SubGrid.from_dict(data)

        assert len(restored.interior_events) == 1
        restored_event = restored.interior_events[0]
        assert restored_event.event_type == "rival_adventurers"
        assert restored_event.rival_party == [{"name": "Rival", "hp": 30, "attack": 8, "defense": 4}]
        assert restored_event.target_room == "Boss Chamber"
        assert restored_event.rival_progress == 3
        assert restored_event.arrival_turns == 7

    def test_backward_compatible_load(self):
        """Test old SubGrid without rivals loads with empty list."""
        # Simulate old save data without rival fields
        data = {
            "locations": [],
            "bounds": [-2, 2, -2, 2, 0, 0],
            "parent_name": "Old Location",
            "secret_passages": [],
            "districts": [],
            "visited_rooms": [],
            "exploration_bonus_awarded": False,
            "interior_events": [
                {
                    "event_id": "cave_in_old",
                    "event_type": "cave_in",
                    "location_coords": [0, 0, 0],
                    "blocked_direction": "north",
                    "start_hour": 50,
                    "duration_hours": 8,
                    "is_active": True,
                    # No rival_party, target_room, etc.
                }
            ],
        }

        restored = SubGrid.from_dict(data)

        # Should load successfully with defaults
        assert len(restored.interior_events) == 1
        event = restored.interior_events[0]
        assert event.event_type == "cave_in"
        # Rival fields should be defaults
        assert event.rival_party is None
        assert event.target_room is None
        assert event.rival_progress == 0
        assert event.arrival_turns == 0


class TestRivalPartyNames:
    """Test rival party naming constants."""

    def test_party_names_exist(self):
        """Test that rival party names are defined."""
        assert len(RIVAL_PARTY_NAMES) >= 3

    def test_party_names_are_strings(self):
        """Test all party names are non-empty strings."""
        for name in RIVAL_PARTY_NAMES:
            assert isinstance(name, str)
            assert len(name) > 0
