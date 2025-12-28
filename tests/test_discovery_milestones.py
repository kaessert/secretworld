"""Tests for discovery milestones (Issue 24).

Milestones track:
1. First Secret Found - When player discovers their first secret in a SubGrid
2. All Treasures Opened - When player opens the last treasure chest in a SubGrid
3. Boss Defeated - When player defeats the boss in a SubGrid

Each milestone awards 25 XP and displays a celebration message.
"""
import pytest

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid
from cli_rpg.game_state import (
    GameState,
    MILESTONE_XP_FIRST_SECRET,
    MILESTONE_XP_ALL_TREASURES,
    MILESTONE_XP_BOSS_DEFEATED,
)


# ============================================================================
# Test SubGrid Milestone Tracking
# ============================================================================


class TestSubGridMilestoneTracking:
    """Tests for SubGrid milestone field defaults and serialization."""

    def test_subgrid_default_milestone_fields(self):
        """SubGrid has default milestone tracking fields set to False."""
        # Spec: SubGrid has first_secret_found, all_treasures_opened, boss_milestone_awarded
        sub_grid = SubGrid()

        assert sub_grid.first_secret_found is False
        assert sub_grid.all_treasures_opened is False
        assert sub_grid.boss_milestone_awarded is False

    def test_subgrid_milestone_fields_serialization(self):
        """Milestone fields are serialized and deserialized correctly."""
        # Spec: to_dict() and from_dict() include milestone fields
        sub_grid = SubGrid(parent_name="Test Dungeon")

        # Add a location for valid serialization
        loc = Location(name="Entry", description="An entrance.")
        sub_grid.add_location(loc, 0, 0, 0)

        # Set milestone flags
        sub_grid.first_secret_found = True
        sub_grid.all_treasures_opened = True
        sub_grid.boss_milestone_awarded = True

        # Serialize and deserialize
        data = sub_grid.to_dict()
        restored = SubGrid.from_dict(data)

        assert restored.first_secret_found is True
        assert restored.all_treasures_opened is True
        assert restored.boss_milestone_awarded is True

    def test_subgrid_backward_compatibility_defaults(self):
        """Old saves without milestone fields default to False."""
        # Spec: Backward compatible with existing saves
        data = {
            "locations": [],
            "bounds": [-2, 2, -2, 2, 0, 0],
            "parent_name": "Test",
            "secret_passages": [],
            # No milestone fields - simulating old save
        }

        restored = SubGrid.from_dict(data)

        assert restored.first_secret_found is False
        assert restored.all_treasures_opened is False
        assert restored.boss_milestone_awarded is False


# ============================================================================
# Test Treasure Stats Methods
# ============================================================================


class TestTreasureStats:
    """Tests for treasure tracking helper methods."""

    def test_get_treasure_stats_no_treasures(self):
        """Empty SubGrid returns (0, 0) for treasure stats."""
        # Spec: get_treasure_stats() returns (opened, total)
        sub_grid = SubGrid()
        loc = Location(name="Empty Room", description="A room with no treasures.")
        sub_grid.add_location(loc, 0, 0, 0)

        opened, total = sub_grid.get_treasure_stats()

        assert opened == 0
        assert total == 0

    def test_get_treasure_stats_with_treasures(self):
        """Treasure stats correctly count opened and total."""
        # Spec: get_treasure_stats() returns (opened_count, total_count)
        sub_grid = SubGrid()

        # Room with 2 treasures - one opened, one closed
        loc1 = Location(name="Treasure Room", description="A room with treasures.")
        loc1.treasures = [
            {"name": "Chest 1", "opened": True, "locked": False, "items": []},
            {"name": "Chest 2", "opened": False, "locked": False, "items": []},
        ]
        sub_grid.add_location(loc1, 0, 0, 0)

        # Room with 1 treasure - closed
        loc2 = Location(name="Another Room", description="Another room.")
        loc2.treasures = [
            {"name": "Chest 3", "opened": False, "locked": False, "items": []},
        ]
        sub_grid.add_location(loc2, 1, 0, 0)

        opened, total = sub_grid.get_treasure_stats()

        assert opened == 1
        assert total == 3

    def test_are_all_treasures_opened_true(self):
        """Returns True when all treasures are opened."""
        # Spec: are_all_treasures_opened() checks completion
        sub_grid = SubGrid()

        loc = Location(name="Treasure Room", description="A room with treasures.")
        loc.treasures = [
            {"name": "Chest 1", "opened": True, "locked": False, "items": []},
            {"name": "Chest 2", "opened": True, "locked": False, "items": []},
        ]
        sub_grid.add_location(loc, 0, 0, 0)

        assert sub_grid.are_all_treasures_opened() is True

    def test_are_all_treasures_opened_false(self):
        """Returns False when some treasures remain closed."""
        # Spec: are_all_treasures_opened() returns False for partial completion
        sub_grid = SubGrid()

        loc = Location(name="Treasure Room", description="A room with treasures.")
        loc.treasures = [
            {"name": "Chest 1", "opened": True, "locked": False, "items": []},
            {"name": "Chest 2", "opened": False, "locked": False, "items": []},
        ]
        sub_grid.add_location(loc, 0, 0, 0)

        assert sub_grid.are_all_treasures_opened() is False

    def test_are_all_treasures_opened_no_treasures(self):
        """Returns True when there are no treasures (vacuously true)."""
        # Spec: No treasures = all treasures opened (vacuously true)
        sub_grid = SubGrid()
        loc = Location(name="Empty Room", description="A room with no treasures.")
        sub_grid.add_location(loc, 0, 0, 0)

        assert sub_grid.are_all_treasures_opened() is True


# ============================================================================
# Test First Secret Milestone
# ============================================================================


class TestFirstSecretMilestone:
    """Tests for first secret discovered milestone."""

    @pytest.fixture
    def game_state_with_subgrid(self):
        """Create a game state inside a SubGrid with secrets."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10, perception=15)

        # Create overworld
        overworld_loc = Location(
            name="Town Square",
            description="The center of town.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        world = {"Town Square": overworld_loc}

        # Create game state
        gs = GameState(character=char, world=world, starting_location="Town Square")

        # Create SubGrid with secrets
        sub_grid = SubGrid(parent_name="Town Square")

        entry = Location(
            name="Dungeon Entry",
            description="The entrance to a dungeon.",
            is_exit_point=True,
        )
        entry.hidden_secrets = [
            {
                "type": "hidden_treasure",
                "description": "A hidden cache of gold.",
                "threshold": 10,
                "discovered": False,
            }
        ]
        sub_grid.add_location(entry, 0, 0, 0)

        # Set game state to be inside SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Dungeon Entry"

        return gs

    def test_first_secret_milestone_awards_xp(self, game_state_with_subgrid):
        """First secret found awards milestone XP."""
        # Spec: First secret discovered in SubGrid triggers milestone (+25 XP)
        gs = game_state_with_subgrid
        initial_xp = gs.current_character.xp

        # Simulate finding a secret
        result = gs.check_and_award_milestones("secret")

        assert result is not None  # Milestone message returned
        assert gs.current_character.xp == initial_xp + MILESTONE_XP_FIRST_SECRET
        assert gs.current_sub_grid.first_secret_found is True

    def test_first_secret_milestone_only_once(self, game_state_with_subgrid):
        """First secret milestone only awarded once per SubGrid."""
        # Spec: Each milestone only awarded once per SubGrid
        gs = game_state_with_subgrid

        # First discovery
        gs.check_and_award_milestones("secret")
        xp_after_first = gs.current_character.xp

        # Second discovery should not award again
        result = gs.check_and_award_milestones("secret")

        assert result is None  # No milestone message
        assert gs.current_character.xp == xp_after_first  # No additional XP

    def test_first_secret_milestone_message_format(self, game_state_with_subgrid):
        """First secret milestone returns celebration message with stars."""
        # Spec: Visual celebration message with star decoration
        gs = game_state_with_subgrid

        result = gs.check_and_award_milestones("secret")

        assert "★" in result  # Star decoration
        assert "SECRET" in result.upper() or "secret" in result.lower()


# ============================================================================
# Test All Treasures Milestone
# ============================================================================


class TestAllTreasuresMilestone:
    """Tests for all treasures opened milestone."""

    @pytest.fixture
    def game_state_with_treasures(self):
        """Create a game state inside a SubGrid with treasures."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

        # Create overworld
        overworld_loc = Location(
            name="Town Square",
            description="The center of town.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        world = {"Town Square": overworld_loc}

        # Create game state
        gs = GameState(character=char, world=world, starting_location="Town Square")

        # Create SubGrid with treasures
        sub_grid = SubGrid(parent_name="Town Square")

        entry = Location(
            name="Treasure Room",
            description="A room full of treasure chests.",
            is_exit_point=True,
        )
        entry.treasures = [
            {"name": "Chest 1", "opened": True, "locked": False, "items": []},
            {"name": "Chest 2", "opened": False, "locked": False, "items": []},  # Last one
        ]
        sub_grid.add_location(entry, 0, 0, 0)

        # Set game state to be inside SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Treasure Room"

        return gs

    def test_all_treasures_milestone_awards_xp(self, game_state_with_treasures):
        """All treasures opened awards milestone XP."""
        # Spec: Opening last treasure in SubGrid triggers milestone (+25 XP)
        gs = game_state_with_treasures
        initial_xp = gs.current_character.xp

        # Open the last chest first
        loc = gs.current_sub_grid.get_by_name("Treasure Room")
        loc.treasures[1]["opened"] = True

        # Check milestone
        result = gs.check_and_award_milestones("treasure")

        assert result is not None  # Milestone message returned
        assert gs.current_character.xp == initial_xp + MILESTONE_XP_ALL_TREASURES
        assert gs.current_sub_grid.all_treasures_opened is True

    def test_all_treasures_milestone_only_once(self, game_state_with_treasures):
        """All treasures milestone only awarded once per SubGrid."""
        # Spec: Each milestone only awarded once per SubGrid
        gs = game_state_with_treasures

        # Open last chest and award first time
        loc = gs.current_sub_grid.get_by_name("Treasure Room")
        loc.treasures[1]["opened"] = True
        gs.check_and_award_milestones("treasure")
        xp_after_first = gs.current_character.xp

        # Second check should not award again
        result = gs.check_and_award_milestones("treasure")

        assert result is None  # No milestone message
        assert gs.current_character.xp == xp_after_first  # No additional XP

    def test_partial_treasures_no_milestone(self, game_state_with_treasures):
        """Partial treasure opening does not trigger milestone."""
        # Spec: Only awarded when ALL treasures are opened
        gs = game_state_with_treasures
        initial_xp = gs.current_character.xp

        # Don't open the last chest (already opened: 1/2)
        result = gs.check_and_award_milestones("treasure")

        assert result is None  # No milestone yet
        assert gs.current_character.xp == initial_xp  # No XP change


# ============================================================================
# Test Boss Defeated Milestone
# ============================================================================


class TestBossDefeatedMilestone:
    """Tests for boss defeated milestone."""

    @pytest.fixture
    def game_state_with_boss(self):
        """Create a game state inside a SubGrid with a boss."""
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

        # Create overworld
        overworld_loc = Location(
            name="Town Square",
            description="The center of town.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        world = {"Town Square": overworld_loc}

        # Create game state
        gs = GameState(character=char, world=world, starting_location="Town Square")

        # Create SubGrid with boss room
        sub_grid = SubGrid(parent_name="Town Square")

        boss_room = Location(
            name="Boss Chamber",
            description="A chamber where a powerful creature dwells.",
            boss_enemy="dragon",
            is_exit_point=True,
        )
        sub_grid.add_location(boss_room, 0, 0, 0)

        # Set game state to be inside SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Boss Chamber"

        return gs

    def test_boss_milestone_awards_xp(self, game_state_with_boss):
        """Boss defeated awards milestone XP."""
        # Spec: Defeating boss in SubGrid triggers milestone (+25 XP)
        gs = game_state_with_boss
        initial_xp = gs.current_character.xp

        # Mark boss as defeated first
        loc = gs.get_current_location()
        loc.boss_defeated = True

        # Check milestone
        result = gs.check_and_award_milestones("boss")

        assert result is not None  # Milestone message returned
        assert gs.current_character.xp == initial_xp + MILESTONE_XP_BOSS_DEFEATED
        assert gs.current_sub_grid.boss_milestone_awarded is True

    def test_boss_milestone_only_once(self, game_state_with_boss):
        """Boss milestone only awarded once per SubGrid."""
        # Spec: Each milestone only awarded once per SubGrid
        gs = game_state_with_boss

        # Defeat boss and award first time
        loc = gs.get_current_location()
        loc.boss_defeated = True
        gs.check_and_award_milestones("boss")
        xp_after_first = gs.current_character.xp

        # Second check should not award again
        result = gs.check_and_award_milestones("boss")

        assert result is None  # No milestone message
        assert gs.current_character.xp == xp_after_first  # No additional XP

    def test_boss_milestone_requires_subgrid(self):
        """Boss milestone not awarded when not in SubGrid."""
        # Spec: Milestones are per-SubGrid, not overworld
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

        # Create overworld with boss location (not in SubGrid)
        boss_loc = Location(
            name="Dragon Lair",
            description="A lair with a dragon.",
            boss_enemy="dragon",
            boss_defeated=True,
            coordinates=(0, 0),
        )
        world = {"Dragon Lair": boss_loc}

        gs = GameState(character=char, world=world, starting_location="Dragon Lair")
        initial_xp = gs.current_character.xp

        # Not in SubGrid
        assert gs.in_sub_location is False

        # Check milestone - should return None (no SubGrid)
        result = gs.check_and_award_milestones("boss")

        assert result is None
        assert gs.current_character.xp == initial_xp


# ============================================================================
# Test Milestone Integration with Existing Mechanics
# ============================================================================


class TestMilestoneIntegration:
    """Tests for milestone integration with existing game mechanics."""

    def test_milestone_persists_in_save_load(self):
        """Milestone state persists through save/load cycle."""
        # Spec: Milestones persist in save/load
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

        overworld_loc = Location(
            name="Town Square",
            description="The center of town.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        overworld_loc.sub_grid = SubGrid(parent_name="Town Square")
        entry = Location(name="Dungeon Entry", description="Entry.", is_exit_point=True)
        overworld_loc.sub_grid.add_location(entry, 0, 0, 0)

        world = {"Town Square": overworld_loc}
        gs = GameState(character=char, world=world, starting_location="Town Square")

        # Enter SubGrid and set milestones
        gs.in_sub_location = True
        gs.current_sub_grid = overworld_loc.sub_grid
        gs.current_location = "Dungeon Entry"
        gs.current_sub_grid.first_secret_found = True
        gs.current_sub_grid.all_treasures_opened = True

        # Serialize and restore
        data = gs.to_dict()
        restored_gs = GameState.from_dict(data)

        # Check milestones persisted
        # Need to get the sub_grid from the restored world
        restored_sub_grid = restored_gs.world["Town Square"].sub_grid
        assert restored_sub_grid.first_secret_found is True
        assert restored_sub_grid.all_treasures_opened is True


# ============================================================================
# Test Game Loop Integration (Issue 24)
# ============================================================================


class TestGameLoopIntegration:
    """Tests for milestone triggers integrated into the game loop."""

    def test_search_command_triggers_secret_milestone(self):
        """Search command includes milestone message when finding first secret.

        Spec: search command calls check_and_award_milestones("secret") when
        a secret is successfully discovered, and the milestone message is
        included in the command output.
        """
        from cli_rpg.main import handle_exploration_command

        # Setup: character in SubGrid with discoverable secret
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)
        char.perception = 20  # High perception to guarantee finding secret

        # Create SubGrid with a secret
        overworld_loc = Location(
            name="Ancient Ruins",
            description="Crumbling ruins.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        sub_grid = SubGrid(parent_name="Ancient Ruins")
        # Use hidden_secrets (with threshold field) as expected by perform_active_search
        secret_room = Location(
            name="Secret Chamber",
            description="A hidden room.",
            is_exit_point=True,
            hidden_secrets=[{
                "name": "Hidden Cache",
                "description": "A concealed cache behind loose stones.",
                "discovered": False,
                "threshold": 10,  # Low threshold so it's easily found
            }],
        )
        sub_grid.add_location(secret_room, 0, 0, 0)
        overworld_loc.sub_grid = sub_grid

        world = {"Ancient Ruins": overworld_loc}
        gs = GameState(character=char, world=world, starting_location="Ancient Ruins")

        # Enter SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Secret Chamber"

        initial_xp = gs.current_character.xp

        # Execute search command
        success, message = handle_exploration_command(gs, "search", [])

        # Verify milestone was awarded and message included
        assert "FIRST SECRET DISCOVERED" in message
        assert "Ancient Ruins" in message
        assert gs.current_character.xp > initial_xp
        assert sub_grid.first_secret_found is True

    def test_search_command_no_milestone_when_no_secret_found(self):
        """Search command doesn't include milestone when no secret is found.

        Spec: Milestone only triggers when search actually finds something.
        """
        from cli_rpg.main import handle_exploration_command

        # Setup: character in SubGrid with no secrets
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)
        char.perception = 5

        overworld_loc = Location(
            name="Empty Cave",
            description="An empty cave.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        sub_grid = SubGrid(parent_name="Empty Cave")
        empty_room = Location(
            name="Empty Room",
            description="Nothing here.",
            is_exit_point=True,
            hidden_secrets=[],  # No secrets (use hidden_secrets not secrets)
        )
        sub_grid.add_location(empty_room, 0, 0, 0)
        overworld_loc.sub_grid = sub_grid

        world = {"Empty Cave": overworld_loc}
        gs = GameState(character=char, world=world, starting_location="Empty Cave")

        # Enter SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Empty Room"

        initial_xp = gs.current_character.xp

        # Execute search command
        success, message = handle_exploration_command(gs, "search", [])

        # Verify no milestone
        assert "FIRST SECRET DISCOVERED" not in message
        assert gs.current_character.xp == initial_xp
        assert sub_grid.first_secret_found is False

    def test_open_command_triggers_treasure_milestone(self):
        """Open command includes milestone message when opening final treasure.

        Spec: open command calls check_and_award_milestones("treasure") after
        opening a chest, and includes the milestone message when it's the last
        treasure in the SubGrid.
        """
        from cli_rpg.main import handle_exploration_command

        # Setup: character in SubGrid with one treasure
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

        overworld_loc = Location(
            name="Treasure Vault",
            description="A vault with treasure.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        sub_grid = SubGrid(parent_name="Treasure Vault")
        treasure_room = Location(
            name="Vault Room",
            description="A room with a chest.",
            is_exit_point=True,
            treasures=[
                {"name": "Gold Chest", "locked": False, "opened": False, "items": [
                    {"name": "Gold Coins", "item_type": "misc", "value": 100}
                ]}
            ],
        )
        sub_grid.add_location(treasure_room, 0, 0, 0)
        overworld_loc.sub_grid = sub_grid

        world = {"Treasure Vault": overworld_loc}
        gs = GameState(character=char, world=world, starting_location="Treasure Vault")

        # Enter SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Vault Room"

        initial_xp = gs.current_character.xp

        # Execute open command
        success, message = handle_exploration_command(gs, "open", ["gold", "chest"])

        # Verify milestone was awarded and message included
        assert "ALL TREASURES FOUND" in message
        assert "Treasure Vault" in message
        assert gs.current_character.xp > initial_xp
        assert sub_grid.all_treasures_opened is True

    def test_open_command_no_milestone_when_treasures_remain(self):
        """Open command doesn't include milestone when other treasures remain.

        Spec: Milestone only triggers when ALL treasures are opened.
        """
        from cli_rpg.main import handle_exploration_command

        # Setup: character in SubGrid with two treasures
        char = Character(name="Tester", strength=10, dexterity=10, intelligence=10)

        overworld_loc = Location(
            name="Dual Vault",
            description="A vault with treasures.",
            is_overworld=True,
            coordinates=(0, 0),
        )
        sub_grid = SubGrid(parent_name="Dual Vault")
        treasure_room = Location(
            name="Vault Room",
            description="A room with chests.",
            is_exit_point=True,
            treasures=[
                {"name": "Gold Chest", "locked": False, "opened": False, "items": []},
                {"name": "Silver Chest", "locked": False, "opened": False, "items": []},
            ],
        )
        sub_grid.add_location(treasure_room, 0, 0, 0)
        overworld_loc.sub_grid = sub_grid

        world = {"Dual Vault": overworld_loc}
        gs = GameState(character=char, world=world, starting_location="Dual Vault")

        # Enter SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Vault Room"

        initial_xp = gs.current_character.xp

        # Execute open command for first chest
        success, message = handle_exploration_command(gs, "open", ["gold", "chest"])

        # Verify no milestone (one chest still closed)
        assert "ALL TREASURES FOUND" not in message
        assert gs.current_character.xp == initial_xp
        assert sub_grid.all_treasures_opened is False

    def test_boss_defeat_triggers_boss_milestone(self):
        """Boss defeat includes milestone message after boss is vanquished.

        Spec: After mark_boss_defeated() is called and combat ends victoriously,
        check_and_award_milestones("boss") is called and the milestone message
        is included in the combat output.
        """
        from cli_rpg.main import handle_combat_command
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy

        # Setup: character in SubGrid in combat with boss
        char = Character(name="Tester", strength=20, dexterity=10, intelligence=10)
        char.max_hp = 100
        char.current_hp = 100

        overworld_loc = Location(
            name="Dragon Lair",
            description="A lair with a dragon.",
            is_overworld=True,
            coordinates=(0, 0),
            boss_enemy="dragon",
        )
        sub_grid = SubGrid(parent_name="Dragon Lair")
        boss_room = Location(
            name="Boss Chamber",
            description="The dragon's chamber.",
            is_exit_point=True,
            boss_enemy="dragon",
        )
        sub_grid.add_location(boss_room, 0, 0, 0)
        overworld_loc.sub_grid = sub_grid

        world = {"Dragon Lair": overworld_loc}
        gs = GameState(character=char, world=world, starting_location="Dragon Lair")

        # Enter SubGrid
        gs.in_sub_location = True
        gs.current_sub_grid = sub_grid
        gs.current_location = "Boss Chamber"

        # Start combat with a weak boss for testing
        boss = Enemy(name="Dragon", health=1, max_health=1, attack_power=1, defense=0, xp_reward=100, is_boss=True)
        gs.current_combat = CombatEncounter(player=char, enemies=[boss], companions=[])
        gs.current_combat.is_active = True  # Activate combat state

        initial_xp = gs.current_character.xp

        # Execute attack command to defeat the boss
        success, message = handle_combat_command(gs, "attack", ["dragon"])

        # Verify milestone was awarded and message included
        assert "BOSS VANQUISHED" in message
        assert "Dragon Lair" in message
        assert gs.current_character.xp > initial_xp
        assert sub_grid.boss_milestone_awarded is True
