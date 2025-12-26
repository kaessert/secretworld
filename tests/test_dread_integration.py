"""Integration tests for the Dread system.

Tests cover:
- Dread increases when moving to dungeon/cave/ruins
- Dread decreases when entering towns
- Night movement adds extra dread
- Combat increases dread
- Rest decreases dread
- Talk to NPC decreases dread
- Status command shows dread meter
- High dread triggers paranoid whispers
- Critical dread events (100%)
"""

import pytest
from unittest.mock import patch, MagicMock

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.game_state import GameState, DREAD_BY_CATEGORY, DREAD_NIGHT_BONUS, DREAD_TOWN_REDUCTION
from cli_rpg.main import handle_exploration_command
from cli_rpg.whisper import WhisperService, DREAD_WHISPERS


def create_test_character():
    """Create a test character."""
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


def create_test_world():
    """Create a simple test world with various location types."""
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        connections={"north": "Dark Cave", "east": "Forest Path"},
        coordinates=(0, 0),
        category="town"
    )
    cave = Location(
        name="Dark Cave",
        description="A dark and ominous cave.",
        connections={"south": "Town Square"},
        coordinates=(0, 1),
        category="cave"
    )
    forest = Location(
        name="Forest Path",
        description="A peaceful forest path.",
        connections={"west": "Town Square"},
        coordinates=(1, 0),
        category="forest"
    )
    return {"Town Square": town, "Dark Cave": cave, "Forest Path": forest}


class TestDreadMoveIntegration:
    """Test dread changes when moving to different locations."""

    def test_move_to_dungeon_increases_dread(self):
        """Moving to a dungeon should increase dread by ~15."""
        char = create_test_character()
        # Create a simple world with just town and dungeon
        town = Location(
            name="Town Square",
            description="A town square.",
            connections={"north": "Dungeon Entrance"},
            coordinates=(0, 0),
            category="town"
        )
        dungeon = Location(
            name="Dungeon Entrance",
            description="A forbidding dungeon entrance.",
            connections={"south": "Town Square"},
            coordinates=(0, 1),
            category="dungeon"
        )
        world = {"Town Square": town, "Dungeon Entrance": dungeon}

        game_state = GameState(char, world, "Town Square")
        initial_dread = char.dread_meter.dread

        # Move to dungeon - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):  # No encounter (>0.3)
            success, _ = game_state.move("north")

        assert success
        assert char.dread_meter.dread > initial_dread
        expected_increase = DREAD_BY_CATEGORY["dungeon"]
        assert char.dread_meter.dread == initial_dread + expected_increase

    def test_move_to_cave_increases_dread(self):
        """Moving to a cave should increase dread by ~12."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        initial_dread = char.dread_meter.dread

        # Move to cave - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):  # No encounter (>0.3)
            success, _ = game_state.move("north")

        assert success
        assert char.dread_meter.dread > initial_dread
        expected_increase = DREAD_BY_CATEGORY["cave"]
        assert char.dread_meter.dread == initial_dread + expected_increase

    def test_move_to_town_decreases_dread(self):
        """Moving to a town should decrease dread by 15."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Dark Cave")

        # Set some initial dread
        char.dread_meter.dread = 50
        initial_dread = char.dread_meter.dread

        # Move to town - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):  # No encounter (>0.3)
            success, _ = game_state.move("south")

        assert success
        assert char.dread_meter.dread < initial_dread
        assert char.dread_meter.dread == initial_dread - DREAD_TOWN_REDUCTION

    def test_move_at_night_adds_extra_dread(self):
        """Moving at night should add extra dread."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Set it to night (hour 22)
        game_state.game_time.hour = 22
        initial_dread = char.dread_meter.dread

        # Move to cave at night - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):  # No encounter (>0.3)
            success, _ = game_state.move("north")

        assert success
        expected_increase = DREAD_BY_CATEGORY["cave"] + DREAD_NIGHT_BONUS
        assert char.dread_meter.dread == initial_dread + expected_increase


class TestDreadCombatIntegration:
    """Test dread changes during combat."""

    def test_combat_increases_dread(self):
        """Starting combat should increase dread by 10."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")
        initial_dread = char.dread_meter.dread

        # Force a combat encounter by patching random
        with patch("cli_rpg.game_state.random.random", return_value=0.1):  # Trigger encounter
            message = game_state.trigger_encounter("Town Square")

        assert message is not None  # Combat triggered
        assert char.dread_meter.dread == initial_dread + 10


class TestDreadRestIntegration:
    """Test dread reduction when resting."""

    def test_rest_decreases_dread(self):
        """Resting should decrease dread by 20."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Set some initial dread and damage
        char.dread_meter.dread = 50
        char.take_damage(10)

        success, message = handle_exploration_command(game_state, "rest", [])

        assert success
        assert "eases your mind" in message
        assert char.dread_meter.dread == 30  # 50 - 20

    def test_rest_with_no_dread_only_heals(self):
        """Resting with 0 dread should only mention healing."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # No dread but damaged
        char.take_damage(10)
        char.dread_meter.dread = 0

        success, message = handle_exploration_command(game_state, "rest", [])

        assert success
        assert "recover" in message
        assert "eases your mind" not in message

    def test_rest_at_full_health_and_no_dread(self):
        """Resting at full health and 0 dread should give special message."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Full health and no dread
        char.dread_meter.dread = 0

        success, message = handle_exploration_command(game_state, "rest", [])

        assert success
        assert "already at full health" in message
        assert "feeling calm" in message


class TestDreadTalkIntegration:
    """Test dread reduction when talking to NPCs."""

    def test_talk_decreases_dread(self):
        """Talking to an NPC should decrease dread by 5."""
        char = create_test_character()
        world = create_test_world()

        # Add an NPC to the town
        npc = NPC(
            name="Innkeeper",
            description="A friendly innkeeper.",
            dialogue="Welcome to my inn!",
            greetings=["Welcome, traveler!"]
        )
        world["Town Square"].npcs.append(npc)

        game_state = GameState(char, world, "Town Square")

        # Set some initial dread
        char.dread_meter.dread = 30

        success, _ = handle_exploration_command(game_state, "talk", ["Innkeeper"])

        assert success
        assert char.dread_meter.dread == 25  # 30 - 5

    def test_talk_with_no_dread_stays_zero(self):
        """Talking to an NPC with 0 dread should stay at 0."""
        char = create_test_character()
        world = create_test_world()

        # Add an NPC to the town
        npc = NPC(
            name="Innkeeper",
            description="A friendly innkeeper.",
            dialogue="Welcome to my inn!",
            greetings=["Welcome, traveler!"]
        )
        world["Town Square"].npcs.append(npc)

        game_state = GameState(char, world, "Town Square")
        char.dread_meter.dread = 0

        success, _ = handle_exploration_command(game_state, "talk", ["Innkeeper"])

        assert success
        assert char.dread_meter.dread == 0


class TestDreadStatusIntegration:
    """Test that status command shows dread meter."""

    def test_status_shows_dread_meter(self):
        """Status command should include dread meter display."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Set some dread
        char.dread_meter.dread = 42

        success, output = handle_exploration_command(game_state, "status", [])

        assert success
        assert "DREAD" in output
        assert "42%" in output


class TestDreadWhisperIntegration:
    """Test that high dread triggers paranoid whispers."""

    def test_high_dread_whispers_appear(self):
        """Whispers at 50%+ dread should use dread-specific pool."""
        service = WhisperService()

        # Set a fixed seed and force whisper trigger + dread whisper selection
        with patch("cli_rpg.whisper.random.random", side_effect=[0.1, 0.1]):  # Trigger whisper, select dread whisper
            whisper = service.get_whisper(
                location_category="dungeon",
                dread=60  # High dread
            )

        # Should be from dread whisper pool
        assert whisper is not None
        assert whisper in DREAD_WHISPERS

    def test_low_dread_uses_normal_whispers(self):
        """Whispers at <50% dread should use normal pool."""
        service = WhisperService()

        # Force whisper trigger
        with patch("cli_rpg.whisper.random.random", return_value=0.1):
            whisper = service.get_whisper(
                location_category="dungeon",
                dread=30  # Low dread
            )

        # Should not be from dread whisper pool
        if whisper:
            assert whisper not in DREAD_WHISPERS


class TestDreadMilestoneIntegration:
    """Test milestone messages when crossing thresholds."""

    def test_crossing_threshold_shows_message(self):
        """Crossing a dread threshold should show a milestone message."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Set dread just below 25 threshold
        char.dread_meter.dread = 20

        # Move to a dungeon (adds 15 dread, crosses 25)
        dungeon = Location(
            name="Dungeon",
            description="A dungeon.",
            connections={"south": "Town Square"},
            coordinates=(0, 1),
            category="dungeon"
        )
        world["Dungeon"] = dungeon
        world["Town Square"].add_connection("north", "Dungeon")
        # Fix coordinates conflict
        world["Dark Cave"].coordinates = (-1, 0)
        world["Town Square"].connections["west"] = "Dark Cave"
        del world["Town Square"].connections["north"]
        world["Town Square"].add_connection("north", "Dungeon")

        success, message = game_state.move("north")

        assert success
        # Check that milestone message is in the output
        assert "unease" in message.lower() or "something" in message.lower()


class TestDreadCriticalIntegration:
    """Test critical dread (100%) effects."""

    def test_critical_dread_at_100(self):
        """At 100% dread, is_critical should be True."""
        char = create_test_character()
        char.dread_meter.dread = 100

        assert char.dread_meter.is_critical() is True

    def test_dread_attack_penalty_at_high_dread(self):
        """At 75%+ dread, attack power should be reduced by 10%."""
        char = create_test_character()
        base_attack = char.get_attack_power()

        char.dread_meter.dread = 80
        reduced_attack = char.get_attack_power()

        # Should be 90% of base attack
        expected = int(base_attack * 0.9)
        assert reduced_attack == expected


class TestDreadPersistence:
    """Test that dread is persisted correctly."""

    def test_game_state_saves_dread(self):
        """GameState should save and restore dread correctly."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Set dread
        char.dread_meter.dread = 67

        # Serialize
        data = game_state.to_dict()

        # Deserialize
        restored = GameState.from_dict(data)

        assert restored.current_character.dread_meter.dread == 67


class TestLightSourceDreadReduction:
    """Test that active light sources reduce dread buildup."""

    def test_light_halves_category_dread(self):
        """Active light halves dread from location category."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Activate light
        char.use_light_source(10)
        initial_dread = char.dread_meter.dread

        # Move to cave - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            success, _ = game_state.move("north")

        assert success
        # Cave normally gives 12 dread, but with light it should be 6 (12 // 2)
        expected_increase = DREAD_BY_CATEGORY["cave"] // 2
        assert char.dread_meter.dread == initial_dread + expected_increase

    def test_light_negates_night_bonus(self):
        """Active light removes DREAD_NIGHT_BONUS."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Activate light
        char.use_light_source(10)

        # Set it to night (hour 22)
        game_state.game_time.hour = 22
        initial_dread = char.dread_meter.dread

        # Move to cave at night - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            success, _ = game_state.move("north")

        assert success
        # Cave normally gives 12 + 5 (night) = 17, but with light it should be 6 (just halved category, no night bonus)
        expected_increase = DREAD_BY_CATEGORY["cave"] // 2
        assert char.dread_meter.dread == initial_dread + expected_increase

    def test_light_ticks_down_on_move(self):
        """Light decrements after each move."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Activate light
        char.use_light_source(5)
        assert char.light_remaining == 5

        # Move - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            game_state.move("north")

        # Should tick down by 1
        assert char.light_remaining == 4

    def test_light_expires_after_duration(self):
        """Light reaches 0 after correct number of moves."""
        char = create_test_character()
        # Create a multi-location world for multiple moves
        town = Location(
            name="Town Square",
            description="A town.",
            connections={"north": "Cave 1"},
            coordinates=(0, 0),
            category="town"
        )
        cave1 = Location(
            name="Cave 1",
            description="First cave.",
            connections={"south": "Town Square", "north": "Cave 2"},
            coordinates=(0, 1),
            category="cave"
        )
        cave2 = Location(
            name="Cave 2",
            description="Second cave.",
            connections={"south": "Cave 1", "north": "Cave 3"},
            coordinates=(0, 2),
            category="cave"
        )
        cave3 = Location(
            name="Cave 3",
            description="Third cave.",
            connections={"south": "Cave 2"},
            coordinates=(0, 3),
            category="cave"
        )
        world = {"Town Square": town, "Cave 1": cave1, "Cave 2": cave2, "Cave 3": cave3}
        game_state = GameState(char, world, "Town Square")

        # Activate light for 3 moves
        char.use_light_source(3)

        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            game_state.move("north")  # Cave 1, light_remaining = 2
            assert char.light_remaining == 2

            game_state.move("north")  # Cave 2, light_remaining = 1
            assert char.light_remaining == 1

            game_state.move("north")  # Cave 3, light_remaining = 0
            assert char.light_remaining == 0

    def test_light_expiration_message_in_move(self):
        """Move output includes 'light fades' message when light expires."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Town Square")

        # Activate light for 1 move
        char.use_light_source(1)

        # Move - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            success, message = game_state.move("north")

        assert success
        assert char.light_remaining == 0
        assert "fades" in message.lower() or "darkness" in message.lower()

    def test_dread_normal_after_light_expires(self):
        """Full dread returns when light is gone."""
        char = create_test_character()
        # Create a world with adjacent caves
        town = Location(
            name="Town Square",
            description="A town.",
            connections={"north": "Cave 1"},
            coordinates=(0, 0),
            category="town"
        )
        cave1 = Location(
            name="Cave 1",
            description="First cave.",
            connections={"south": "Town Square", "north": "Cave 2"},
            coordinates=(0, 1),
            category="cave"
        )
        cave2 = Location(
            name="Cave 2",
            description="Second cave.",
            connections={"south": "Cave 1"},
            coordinates=(0, 2),
            category="cave"
        )
        world = {"Town Square": town, "Cave 1": cave1, "Cave 2": cave2}
        game_state = GameState(char, world, "Town Square")

        # Activate light for 1 move only
        char.use_light_source(1)

        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            # First move with light - cave dread halved
            game_state.move("north")
            dread_after_first = char.dread_meter.dread
            assert char.light_remaining == 0  # Light expired

            # Second move without light - full cave dread
            game_state.move("north")
            dread_after_second = char.dread_meter.dread

        # First move added halved dread (cave=12//2=6)
        # Second move added full dread (cave=12)
        # So second increase should be larger
        first_increase = dread_after_first  # From 0
        second_increase = dread_after_second - dread_after_first
        assert second_increase == DREAD_BY_CATEGORY["cave"]
        assert first_increase == DREAD_BY_CATEGORY["cave"] // 2

    def test_light_does_not_affect_town_reduction(self):
        """Town dread reduction is unchanged by light."""
        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Dark Cave")

        # Set some initial dread
        char.dread_meter.dread = 50

        # Activate light
        char.use_light_source(10)

        # Move to town - patch random to prevent encounter
        with patch("cli_rpg.game_state.random.random", return_value=0.9):
            success, _ = game_state.move("south")

        assert success
        # Town should reduce dread by 15 regardless of light
        assert char.dread_meter.dread == 50 - DREAD_TOWN_REDUCTION
