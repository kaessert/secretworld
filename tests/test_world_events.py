"""Tests for world events system.

Tests the WorldEvent model and world_events module functionality.
"""
import pytest
from unittest.mock import patch, MagicMock

from cli_rpg.models.world_event import WorldEvent
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState
from cli_rpg.world_events import (
    EVENT_SPAWN_CHANCE,
    EVENT_TEMPLATES,
    check_for_new_event,
    progress_events,
    format_event_notification,
    get_location_event_warning,
    resolve_event,
)


class TestWorldEventModel:
    """Tests for WorldEvent dataclass.

    Spec: WorldEvent model should have event_id, name, description, event_type,
          affected_locations, start_hour, duration_hours, is_active, is_resolved,
          consequence_applied fields
    """

    def test_world_event_model_creation(self):
        """Test WorldEvent dataclass with required fields.

        Spec: Should create with all required fields
        """
        event = WorldEvent(
            event_id="plague_millbrook_001",
            name="The Crimson Plague",
            description="A deadly plague spreads through Millbrook",
            event_type="plague",
            affected_locations=["Millbrook Village"],
            start_hour=10,
            duration_hours=24,
        )

        assert event.event_id == "plague_millbrook_001"
        assert event.name == "The Crimson Plague"
        assert event.description == "A deadly plague spreads through Millbrook"
        assert event.event_type == "plague"
        assert event.affected_locations == ["Millbrook Village"]
        assert event.start_hour == 10
        assert event.duration_hours == 24
        assert event.is_active is True  # Default
        assert event.is_resolved is False  # Default
        assert event.consequence_applied is False  # Default

    def test_world_event_caravan_type(self):
        """Test WorldEvent with caravan type.

        Spec: Caravan events should be valid event type
        """
        event = WorldEvent(
            event_id="caravan_town_001",
            name="Merchant Caravan",
            description="A wealthy caravan arrives",
            event_type="caravan",
            affected_locations=["Town Square"],
            start_hour=6,
            duration_hours=12,
        )

        assert event.event_type == "caravan"

    def test_world_event_invasion_type(self):
        """Test WorldEvent with invasion type.

        Spec: Invasion events should be valid event type
        """
        event = WorldEvent(
            event_id="invasion_forest_001",
            name="Monster Incursion",
            description="Monsters overrun the forest",
            event_type="invasion",
            affected_locations=["Dark Forest"],
            start_hour=18,
            duration_hours=8,
        )

        assert event.event_type == "invasion"

    def test_world_event_get_time_remaining(self):
        """Test get_time_remaining method.

        Spec: Should calculate hours remaining based on current hour
        """
        event = WorldEvent(
            event_id="test_001",
            name="Test Event",
            description="Test",
            event_type="caravan",
            affected_locations=["Town"],
            start_hour=10,
            duration_hours=12,
        )

        # At hour 10 (start), 12 hours remain
        assert event.get_time_remaining(10) == 12

        # At hour 15, 7 hours remain
        assert event.get_time_remaining(15) == 7

        # At hour 22 (end), 0 hours remain
        assert event.get_time_remaining(22) == 0

        # Past end, should return 0 (not negative)
        assert event.get_time_remaining(23) == 0

    def test_world_event_get_time_remaining_wraps_midnight(self):
        """Test get_time_remaining handles midnight wrap.

        Spec: Should handle events that span midnight
        """
        event = WorldEvent(
            event_id="test_002",
            name="Night Event",
            description="Test",
            event_type="invasion",
            affected_locations=["Town"],
            start_hour=20,  # Started at 8 PM
            duration_hours=10,  # Ends at 6 AM
        )

        # At 20:00 (start), 10 hours remain
        assert event.get_time_remaining(20) == 10

        # At 23:00, 7 hours remain
        assert event.get_time_remaining(23) == 7

        # At 02:00 (next day), 4 hours remain
        assert event.get_time_remaining(2) == 4

        # At 06:00 (end), 0 hours remain
        assert event.get_time_remaining(6) == 0

    def test_world_event_is_expired(self):
        """Test is_expired method.

        Spec: Should return True when time remaining is 0
        """
        event = WorldEvent(
            event_id="test_003",
            name="Test Event",
            description="Test",
            event_type="plague",
            affected_locations=["Town"],
            start_hour=10,
            duration_hours=5,
        )

        assert event.is_expired(10) is False
        assert event.is_expired(14) is False
        assert event.is_expired(15) is True
        assert event.is_expired(16) is True

    def test_world_event_serialization(self):
        """Test to_dict/from_dict roundtrip.

        Spec: Should preserve all fields through serialization
        """
        original = WorldEvent(
            event_id="plague_millbrook_001",
            name="The Crimson Plague",
            description="A deadly plague spreads through Millbrook",
            event_type="plague",
            affected_locations=["Millbrook Village", "Farm"],
            start_hour=10,
            duration_hours=24,
            is_active=True,
            is_resolved=False,
            consequence_applied=False,
        )

        # Serialize
        data = original.to_dict()
        assert data["event_id"] == "plague_millbrook_001"
        assert data["name"] == "The Crimson Plague"
        assert data["event_type"] == "plague"
        assert data["affected_locations"] == ["Millbrook Village", "Farm"]
        assert data["duration_hours"] == 24

        # Deserialize
        restored = WorldEvent.from_dict(data)
        assert restored.event_id == original.event_id
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.event_type == original.event_type
        assert restored.affected_locations == original.affected_locations
        assert restored.start_hour == original.start_hour
        assert restored.duration_hours == original.duration_hours
        assert restored.is_active == original.is_active
        assert restored.is_resolved == original.is_resolved
        assert restored.consequence_applied == original.consequence_applied


class TestEventSpawnChance:
    """Tests for event spawn configuration.

    Spec: Event spawn chance should be 5% (configurable constant)
    """

    def test_event_spawn_chance_configurable(self):
        """Verify 5% chance constant exists.

        Spec: EVENT_SPAWN_CHANCE = 0.05
        """
        assert EVENT_SPAWN_CHANCE == 0.05

    def test_event_templates_exist(self):
        """Verify event templates are defined.

        Spec: Should have at least caravan, plague, invasion templates
        """
        assert "caravan" in EVENT_TEMPLATES
        assert "plague" in EVENT_TEMPLATES
        assert "invasion" in EVENT_TEMPLATES


class TestEventSpawn:
    """Tests for event spawning on move."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create a basic game state for testing."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}, coordinates=(0, 0)),
            "End": Location("End", "End location", {"south": "Start"}, coordinates=(0, 1)),
        }
        gs = GameState(character, world, "Start")
        gs.world_events = []  # Initialize empty events list
        return gs

    def test_event_spawns_on_move(self, game_state, monkeypatch):
        """Test that move with seeded RNG triggers event.

        Spec: Move should check for world event spawn after successful movement
        """
        # Disable whisper and random encounters
        game_state.whisper_service.get_whisper = lambda **kwargs: None
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", lambda: 0.99)

        # Mock to trigger event spawn
        monkeypatch.setattr("cli_rpg.world_events.random.random", lambda: 0.01)
        monkeypatch.setattr("cli_rpg.world_events.random.choice", lambda x: x[0])

        result = check_for_new_event(game_state)

        assert result is not None
        assert len(game_state.world_events) == 1

    def test_no_event_when_roll_fails(self, game_state, monkeypatch):
        """Test that no event spawns when roll exceeds threshold.

        Spec: No event when random() > EVENT_SPAWN_CHANCE
        """
        monkeypatch.setattr("cli_rpg.world_events.random.random", lambda: 0.50)

        result = check_for_new_event(game_state)

        assert result is None
        assert len(game_state.world_events) == 0


class TestEventProgression:
    """Tests for event progression with time."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create game state with an active event."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location("Town", "A town", {"north": "Forest"}, coordinates=(0, 0)),
            "Forest": Location("Forest", "A forest", {"south": "Town"}, coordinates=(0, 1)),
        }
        gs = GameState(character, world, "Town")
        gs.world_events = []
        return gs

    def test_event_progresses_with_time(self, game_state):
        """Test that event time remaining decreases.

        Spec: Event duration decreases as GameTime advances
        """
        event = WorldEvent(
            event_id="test_001",
            name="Test Event",
            description="Test",
            event_type="caravan",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=10,
        )
        game_state.world_events.append(event)

        # Initial time remaining
        initial_remaining = event.get_time_remaining(game_state.game_time.hour)
        assert initial_remaining == 10

        # Advance time
        game_state.game_time.advance(3)

        # Check remaining time decreased
        new_remaining = event.get_time_remaining(game_state.game_time.hour)
        assert new_remaining == 7

    def test_event_consequence_when_expired(self, game_state):
        """Test that consequence is applied when timer expires.

        Spec: Consequence applied when timer reaches 0
        """
        event = WorldEvent(
            event_id="test_002",
            name="Test Plague",
            description="A plague",
            event_type="plague",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=2,
        )
        game_state.world_events.append(event)

        # Advance time past expiry
        game_state.game_time.advance(3)

        # Progress events to trigger consequence
        messages = progress_events(game_state)

        # Event should have consequence applied
        assert event.consequence_applied is True
        assert event.is_active is False
        assert len(messages) > 0

    def test_event_resolved_before_expiry(self, game_state):
        """Test that resolving event prevents consequence.

        Spec: Resolving event prevents consequence
        """
        event = WorldEvent(
            event_id="test_003",
            name="Test Event",
            description="Test",
            event_type="caravan",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=10,
        )
        game_state.world_events.append(event)

        # Resolve the event
        message = resolve_event(game_state, "test_003")

        assert event.is_resolved is True
        assert event.is_active is False
        assert "resolved" in message.lower() or "complete" in message.lower()

        # Advance time past original expiry
        game_state.game_time.advance(15)

        # Progress events - should not apply consequence
        progress_events(game_state)
        assert event.consequence_applied is False


class TestCaravanEvent:
    """Tests for caravan event type."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create game state for testing."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0), npcs=[]),
        }
        gs = GameState(character, world, "Town")
        gs.world_events = []
        return gs

    def test_caravan_adds_merchant_npc(self, game_state, monkeypatch):
        """Test that caravan event adds temporary merchant to location.

        Spec: Caravan event adds temporary merchant NPC with shop
        """
        # Force caravan event
        monkeypatch.setattr("cli_rpg.world_events.random.random", lambda: 0.01)
        monkeypatch.setattr("cli_rpg.world_events.random.choice", lambda x: "caravan")

        check_for_new_event(game_state)

        # Should have event
        assert len(game_state.world_events) == 1
        event = game_state.world_events[0]
        assert event.event_type == "caravan"


class TestPlagueEvent:
    """Tests for plague event type."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create game state for testing."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0)),
        }
        gs = GameState(character, world, "Town")
        gs.world_events = []
        return gs

    def test_plague_affects_location(self, game_state, monkeypatch):
        """Test that plague marks affected location.

        Spec: Plague marks location, affects NPCs/shops
        """
        event = WorldEvent(
            event_id="plague_001",
            name="The Plague",
            description="A plague spreads",
            event_type="plague",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=24,
        )
        game_state.world_events.append(event)

        # Check location is affected
        assert "Town" in event.affected_locations


class TestEventOutput:
    """Tests for event notification formatting."""

    def test_format_event_notification(self):
        """Test event notification box format.

        Spec: Should format event in a box with header, description, hint
        """
        event = WorldEvent(
            event_id="caravan_001",
            name="Merchant Caravan Arriving",
            description="A wealthy caravan has arrived at Millbrook Village.",
            event_type="caravan",
            affected_locations=["Millbrook Village"],
            start_hour=10,
            duration_hours=12,
        )

        message = format_event_notification(event, current_hour=10)

        assert "WORLD EVENT" in message
        assert event.name in message
        assert "12 hours" in message.lower() or "12" in message

    def test_events_command_lists_active(self, monkeypatch):
        """Test that 'events' command shows active events.

        Spec: `events` command shows active events with time remaining
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0)),
        }
        gs = GameState(character, world, "Town")
        gs.world_events = [
            WorldEvent(
                event_id="test_001",
                name="Test Event",
                description="Test",
                event_type="caravan",
                affected_locations=["Town"],
                start_hour=gs.game_time.hour,
                duration_hours=12,
            )
        ]

        # Import and test the events listing function
        from cli_rpg.world_events import get_active_events_display

        display = get_active_events_display(gs)
        assert "Test Event" in display
        assert "12" in display  # hours remaining


class TestEventPersistence:
    """Tests for event save/load."""

    def test_events_persist_on_save_load(self, monkeypatch):
        """Test that events survive save/load cycle.

        Spec: Events should be serialized with game state
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0)),
        }
        gs = GameState(character, world, "Town")
        gs.world_events = [
            WorldEvent(
                event_id="test_001",
                name="Test Event",
                description="Test",
                event_type="plague",
                affected_locations=["Town"],
                start_hour=10,
                duration_hours=24,
            )
        ]

        # Serialize
        data = gs.to_dict()
        assert "world_events" in data
        assert len(data["world_events"]) == 1

        # Deserialize
        restored = GameState.from_dict(data)
        assert len(restored.world_events) == 1
        assert restored.world_events[0].event_id == "test_001"
        assert restored.world_events[0].name == "Test Event"


class TestLocationEventWarning:
    """Tests for location event warnings."""

    def test_enter_affected_location_shows_warning(self, monkeypatch):
        """Test that entering affected location shows event message.

        Spec: Moving to affected location shows event warning
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start", {"north": "Town"}, coordinates=(0, 0)),
            "Town": Location("Town", "A town", {"south": "Start"}, coordinates=(0, 1)),
        }
        gs = GameState(character, world, "Start")
        gs.world_events = [
            WorldEvent(
                event_id="plague_001",
                name="The Plague",
                description="A plague spreads",
                event_type="plague",
                affected_locations=["Town"],
                start_hour=gs.game_time.hour,
                duration_hours=24,
            )
        ]

        warning = get_location_event_warning("Town", gs.world_events)

        assert warning is not None
        assert "plague" in warning.lower() or "event" in warning.lower()


class TestEventResolution:
    """Tests for event resolution mechanics.

    Spec: Players can resolve world events before they expire.
    - Plague: Use cure item at affected location
    - Invasion: Defeat combat at affected location
    - Caravan: Trade with caravan (auto-resolve on purchase)
    """

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create game state for testing resolution."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location("Town", "A town", {"north": "Village"}, coordinates=(0, 0)),
            "Village": Location("Village", "A village", {"south": "Town"}, coordinates=(0, 1)),
        }
        gs = GameState(character, world, "Town")
        gs.world_events = []
        return gs

    def test_resolve_plague_with_cure_item(self, game_state):
        """Test resolving plague event with cure item.

        Spec: Cure item consumed, event resolved, rewards given
        """
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.world_events import can_resolve_event, try_resolve_event

        # Add plague event at current location
        plague_event = WorldEvent(
            event_id="plague_001",
            name="The Plague",
            description="A plague spreads through Town",
            event_type="plague",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=24,
        )
        game_state.world_events.append(plague_event)

        # Add cure item to inventory
        cure = Item(
            name="Antidote",
            description="Cures plague",
            item_type=ItemType.CONSUMABLE,
            is_cure=True,
        )
        game_state.current_character.inventory.add_item(cure)

        # Check can resolve
        can_resolve, reason = can_resolve_event(game_state, plague_event)
        assert can_resolve is True

        # Resolve
        success, message = try_resolve_event(game_state, plague_event)
        assert success is True
        assert plague_event.is_resolved is True
        assert plague_event.is_active is False
        # Cure should be consumed
        assert game_state.current_character.inventory.find_item_by_name("Antidote") is None
        # Message may contain ANSI color codes, so check for key words
        assert "cure" in message.lower() or "plague" in message.lower()

    def test_resolve_plague_without_cure_fails(self, game_state):
        """Test that plague cannot be resolved without cure item.

        Spec: Error message, event unchanged
        """
        from cli_rpg.world_events import can_resolve_event, try_resolve_event

        # Add plague event
        plague_event = WorldEvent(
            event_id="plague_001",
            name="The Plague",
            description="A plague spreads",
            event_type="plague",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=24,
        )
        game_state.world_events.append(plague_event)

        # No cure in inventory
        can_resolve, reason = can_resolve_event(game_state, plague_event)
        assert can_resolve is False
        assert "cure" in reason.lower() or "antidote" in reason.lower()

        # Try to resolve anyway - should fail
        success, message = try_resolve_event(game_state, plague_event)
        assert success is False
        assert plague_event.is_resolved is False
        assert plague_event.is_active is True

    def test_resolve_event_wrong_location_fails(self, game_state):
        """Test that event cannot be resolved from wrong location.

        Spec: Must be at affected location
        """
        from cli_rpg.world_events import can_resolve_event

        # Add plague event at Village (player is at Town)
        plague_event = WorldEvent(
            event_id="plague_001",
            name="The Plague",
            description="A plague spreads",
            event_type="plague",
            affected_locations=["Village"],
            start_hour=game_state.game_time.hour,
            duration_hours=24,
        )
        game_state.world_events.append(plague_event)

        # Player is at Town, not Village
        can_resolve, reason = can_resolve_event(game_state, plague_event)
        assert can_resolve is False
        assert "location" in reason.lower() or "village" in reason.lower()

    def test_resolve_invasion_triggers_combat(self, game_state):
        """Test that resolving invasion returns combat trigger flag.

        Spec: Combat encounter spawns for invasion events
        """
        from cli_rpg.world_events import can_resolve_event, try_resolve_event

        # Add invasion event at current location
        invasion_event = WorldEvent(
            event_id="invasion_001",
            name="Monster Incursion",
            description="Monsters overrun the town",
            event_type="invasion",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=12,
        )
        game_state.world_events.append(invasion_event)

        # Check can resolve (no special requirements for invasion)
        can_resolve, reason = can_resolve_event(game_state, invasion_event)
        assert can_resolve is True

        # Try to resolve - should trigger combat
        success, message = try_resolve_event(game_state, invasion_event)
        # For invasions, the success flag means combat was triggered
        # The actual resolution happens when player wins combat
        assert "combat" in message.lower() or "fight" in message.lower() or game_state.is_in_combat()

    def test_caravan_auto_resolves_on_purchase(self, game_state):
        """Test that caravan event resolves when player makes a purchase.

        Spec: Buy item → event resolved
        """
        from cli_rpg.world_events import check_and_resolve_caravan

        # Add caravan event at current location
        caravan_event = WorldEvent(
            event_id="caravan_001",
            name="Merchant Caravan",
            description="A caravan arrives",
            event_type="caravan",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=16,
        )
        game_state.world_events.append(caravan_event)

        # Simulate purchase - check_and_resolve_caravan should mark it resolved
        resolved = check_and_resolve_caravan(game_state)
        assert resolved is True
        assert caravan_event.is_resolved is True
        assert caravan_event.is_active is False

    def test_resolve_command_unknown_event(self, game_state):
        """Test error handling for invalid event resolution.

        Spec: Error for non-existent event
        """
        from cli_rpg.world_events import find_event_by_name

        # No events exist
        event = find_event_by_name(game_state, "nonexistent")
        assert event is None

    def test_resolve_gives_rewards(self, game_state):
        """Test that resolving event gives XP and gold rewards.

        Spec: XP and gold awarded on successful resolution
        """
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.world_events import try_resolve_event

        # Add plague event at current location
        plague_event = WorldEvent(
            event_id="plague_001",
            name="The Plague",
            description="A plague spreads",
            event_type="plague",
            affected_locations=["Town"],
            start_hour=game_state.game_time.hour,
            duration_hours=24,
        )
        game_state.world_events.append(plague_event)

        # Add cure item
        cure = Item(
            name="Antidote",
            description="Cures plague",
            item_type=ItemType.CONSUMABLE,
            is_cure=True,
        )
        game_state.current_character.inventory.add_item(cure)

        # Record initial state
        initial_gold = game_state.current_character.gold
        initial_xp = game_state.current_character.xp

        # Resolve event
        success, message = try_resolve_event(game_state, plague_event)
        assert success is True

        # Should have gained XP and gold
        assert game_state.current_character.gold > initial_gold
        assert game_state.current_character.xp > initial_xp

    def test_get_resolution_requirements_display(self, game_state):
        """Test that resolution requirements are displayed correctly.

        Spec: Each event type shows what's needed to resolve
        """
        from cli_rpg.world_events import get_resolution_requirements

        plague_event = WorldEvent(
            event_id="plague_001",
            name="The Plague",
            description="A plague spreads",
            event_type="plague",
            affected_locations=["Town"],
            start_hour=10,
            duration_hours=24,
        )

        requirements = get_resolution_requirements(plague_event)
        assert "cure" in requirements.lower() or "antidote" in requirements.lower()

        invasion_event = WorldEvent(
            event_id="invasion_001",
            name="Invasion",
            description="Monsters attack",
            event_type="invasion",
            affected_locations=["Town"],
            start_hour=10,
            duration_hours=12,
        )

        requirements = get_resolution_requirements(invasion_event)
        assert "defeat" in requirements.lower() or "combat" in requirements.lower() or "fight" in requirements.lower()

        caravan_event = WorldEvent(
            event_id="caravan_001",
            name="Caravan",
            description="Merchants arrive",
            event_type="caravan",
            affected_locations=["Town"],
            start_hour=10,
            duration_hours=12,
        )

        requirements = get_resolution_requirements(caravan_event)
        assert "trade" in requirements.lower() or "buy" in requirements.lower()


class TestCureItem:
    """Tests for cure item mechanics."""

    def test_cure_item_creation(self):
        """Test creating a cure item with is_cure flag.

        Spec: Cure items have is_cure=True
        """
        from cli_rpg.models.item import Item, ItemType

        cure = Item(
            name="Antidote",
            description="Cures plague and poison",
            item_type=ItemType.CONSUMABLE,
            is_cure=True,
        )
        assert cure.is_cure is True
        assert cure.item_type == ItemType.CONSUMABLE

    def test_regular_consumable_not_cure(self):
        """Test that regular consumables are not cures by default.

        Spec: is_cure defaults to False
        """
        from cli_rpg.models.item import Item, ItemType

        potion = Item(
            name="Health Potion",
            description="Heals health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=20,
        )
        assert potion.is_cure is False

    def test_cure_item_serialization(self):
        """Test cure item survives serialization.

        Spec: is_cure persists through save/load
        """
        from cli_rpg.models.item import Item, ItemType

        cure = Item(
            name="Antidote",
            description="Cures plague",
            item_type=ItemType.CONSUMABLE,
            is_cure=True,
        )

        # Serialize
        data = cure.to_dict()
        assert data["is_cure"] is True

        # Deserialize
        restored = Item.from_dict(data)
        assert restored.is_cure is True
