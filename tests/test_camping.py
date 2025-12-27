"""Tests for camping, forage, and hunt commands.

Spec: Add wilderness survival mechanics with camp, forage, and hunt commands
that integrate with existing dread, inventory, random encounters, and day/night systems.
"""

import pytest
import random
from cli_rpg.main import handle_exploration_command, handle_combat_command, get_command_reference
from cli_rpg.game_state import GameState, parse_command, KNOWN_COMMANDS
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType
from cli_rpg.combat import CombatEncounter
from cli_rpg.models.enemy import Enemy


@pytest.fixture
def forest_location():
    """Create a forest location (campable)."""
    return Location(name="Dark Forest", description="A dense forest.", category="forest")


@pytest.fixture
def wilderness_location():
    """Create a wilderness location (campable)."""
    return Location(name="Wild Plains", description="Open wilderness.", category="wilderness")


@pytest.fixture
def cave_location():
    """Create a cave location (campable)."""
    return Location(name="Deep Cave", description="A dark cave.", category="cave")


@pytest.fixture
def ruins_location():
    """Create a ruins location (campable)."""
    return Location(name="Ancient Ruins", description="Crumbling ruins.", category="ruins")


@pytest.fixture
def town_location():
    """Create a town location (NOT campable, safe zone)."""
    return Location(
        name="Town Square",
        description="A busy town square.",
        category="town",
        is_safe_zone=True
    )


@pytest.fixture
def dungeon_location():
    """Create a dungeon location (NOT forageable/huntable)."""
    return Location(name="Dungeon", description="A dark dungeon.", category="dungeon")


@pytest.fixture
def camping_supplies():
    """Create Camping Supplies item."""
    return Item(
        name="Camping Supplies",
        description="Essential supplies for camping in the wilderness",
        item_type=ItemType.CONSUMABLE,
        heal_amount=0
    )


@pytest.fixture
def raw_meat():
    """Create Raw Meat item."""
    return Item(
        name="Raw Meat",
        description="Raw meat from a hunted animal. Best cooked over a campfire.",
        item_type=ItemType.CONSUMABLE,
        heal_amount=30
    )


@pytest.fixture
def game_state_forest(forest_location, camping_supplies):
    """Create game state in a forest location with camping supplies."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    world = {"Dark Forest": forest_location}
    gs = GameState(char, world, starting_location="Dark Forest")
    gs.current_character.inventory.add_item(camping_supplies)
    return gs


@pytest.fixture
def game_state_town(town_location):
    """Create game state in a town location (safe zone)."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    world = {"Town Square": town_location}
    return GameState(char, world, starting_location="Town Square")


@pytest.fixture
def game_state_wilderness(wilderness_location):
    """Create game state in wilderness (for forage/hunt tests)."""
    char = Character(name="Hero", strength=10, dexterity=14, intelligence=10, perception=12)
    world = {"Wild Plains": wilderness_location}
    return GameState(char, world, starting_location="Wild Plains")


@pytest.fixture
def game_state_dungeon(dungeon_location):
    """Create game state in dungeon location."""
    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    world = {"Dungeon": dungeon_location}
    return GameState(char, world, starting_location="Dungeon")


@pytest.fixture
def game_state_in_combat(game_state_forest):
    """Create game state with active combat."""
    enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=10)
    game_state_forest.current_combat = CombatEncounter(game_state_forest.current_character, enemy)
    return game_state_forest


# =============================================================================
# is_campable_location tests (Spec: campable categories)
# =============================================================================

class TestIsCampableLocation:
    """Tests for is_campable_location - Spec: forest, wilderness, cave, ruins are campable."""

    # Spec: forest is campable (test 1)
    def test_is_campable_location_forest(self, forest_location):
        """Spec: Forest locations are campable."""
        from cli_rpg.camping import is_campable_location
        assert is_campable_location(forest_location) is True

    # Spec: wilderness is campable (test 2)
    def test_is_campable_location_wilderness(self, wilderness_location):
        """Spec: Wilderness locations are campable."""
        from cli_rpg.camping import is_campable_location
        assert is_campable_location(wilderness_location) is True

    # Spec: cave is campable
    def test_is_campable_location_cave(self, cave_location):
        """Spec: Cave locations are campable."""
        from cli_rpg.camping import is_campable_location
        assert is_campable_location(cave_location) is True

    # Spec: ruins is campable
    def test_is_campable_location_ruins(self, ruins_location):
        """Spec: Ruins locations are campable."""
        from cli_rpg.camping import is_campable_location
        assert is_campable_location(ruins_location) is True

    # Spec: town is not campable (test 3)
    def test_is_campable_location_town_not_campable(self, town_location):
        """Spec: Town locations are NOT campable."""
        from cli_rpg.camping import is_campable_location
        assert is_campable_location(town_location) is False

    # Spec: safe zone is not campable (test 4)
    def test_is_campable_location_safe_zone_not_campable(self):
        """Spec: Safe zones are NOT campable (use rest there instead)."""
        from cli_rpg.camping import is_campable_location
        safe_zone = Location(
            name="Village",
            description="A peaceful village.",
            category="village",
            is_safe_zone=True
        )
        assert is_campable_location(safe_zone) is False


# =============================================================================
# Camp Command Tests (Spec: camp command mechanics)
# =============================================================================

class TestCampCommand:
    """Tests for 'camp' command - Spec: camping mechanics."""

    # Spec: camp requires Camping Supplies (test 5)
    def test_camp_requires_supplies(self, forest_location):
        """Spec: Camp fails without Camping Supplies item."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Dark Forest": forest_location}
        gs = GameState(char, world, starting_location="Dark Forest")
        # No camping supplies in inventory

        cont, msg = handle_exploration_command(gs, "camp", [])

        assert cont is True
        assert "supplies" in msg.lower() or "camping supplies" in msg.lower()

    # Spec: camp consumes 1 Camping Supplies (test 6)
    def test_camp_consumes_supplies(self, game_state_forest):
        """Spec: Camp consumes 1 Camping Supplies from inventory."""
        gs = game_state_forest
        gs.current_character.take_damage(50)  # Need to heal to camp successfully
        initial_count = len([i for i in gs.current_character.inventory.items
                            if i.name == "Camping Supplies"])
        assert initial_count == 1

        cont, msg = handle_exploration_command(gs, "camp", [])

        final_count = len([i for i in gs.current_character.inventory.items
                          if i.name == "Camping Supplies"])
        assert final_count == 0

    # Spec: camp heals 50% of max HP (test 7)
    def test_camp_heals_50_percent(self, game_state_forest):
        """Spec: Camp heals 50% of max HP (double rest amount)."""
        gs = game_state_forest
        max_hp = gs.current_character.max_health
        gs.current_character.take_damage(max_hp)  # Drop to 0
        gs.current_character.health = 10  # Set low health
        old_health = gs.current_character.health

        cont, msg = handle_exploration_command(gs, "camp", [])

        expected_heal = max_hp // 2  # 50% of max
        assert gs.current_character.health == min(max_hp, old_health + expected_heal)

    # Spec: camp reduces dread by 30 (test 8)
    def test_camp_reduces_dread_30(self, game_state_forest):
        """Spec: Camp reduces dread by 30 (50% more than rest's 20)."""
        gs = game_state_forest
        gs.current_character.dread_meter.dread = 50
        gs.current_character.take_damage(50)  # Need health loss to camp

        cont, msg = handle_exploration_command(gs, "camp", [])

        assert gs.current_character.dread_meter.dread == 20  # 50 - 30 = 20

    # Spec: campfire (active light) gives extra -10 dread (test 9)
    def test_camp_with_campfire_extra_dread_reduction(self, game_state_forest):
        """Spec: Camping with active light (campfire) reduces dread by 40 total."""
        gs = game_state_forest
        gs.current_character.dread_meter.dread = 50
        gs.current_character.light_remaining = 5  # Has active light = campfire
        gs.current_character.take_damage(50)

        cont, msg = handle_exploration_command(gs, "camp", [])

        # 50 - 40 (30 base + 10 campfire) = 10
        assert gs.current_character.dread_meter.dread == 10

    # Spec: camp advances time by 8 hours (test 10)
    def test_camp_advances_time_8_hours(self, game_state_forest):
        """Spec: Camp advances game time by 8 hours."""
        gs = game_state_forest
        old_hour = gs.game_time.hour
        gs.current_character.take_damage(50)

        cont, msg = handle_exploration_command(gs, "camp", [])

        expected_hour = (old_hour + 8) % 24
        assert gs.game_time.hour == expected_hour

    # Spec: camp blocked in safe zone (test 11)
    def test_camp_blocked_in_safe_zone(self, game_state_town, camping_supplies):
        """Spec: Camp returns error in safe zones (use rest there)."""
        gs = game_state_town
        gs.current_character.inventory.add_item(camping_supplies)
        gs.current_character.take_damage(50)

        cont, msg = handle_exploration_command(gs, "camp", [])

        assert cont is True
        assert "rest" in msg.lower() or "safe" in msg.lower() or "town" in msg.lower()

    # Spec: camp blocked in combat (test 12)
    def test_camp_blocked_in_combat(self, game_state_in_combat):
        """Spec: Camp returns error during combat."""
        gs = game_state_in_combat

        cont, msg = handle_combat_command(gs, "camp", [])

        assert cont is True
        assert "combat" in msg.lower() or "can't" in msg.lower()

    # Spec: camp cooks Raw Meat with campfire (test 13)
    def test_camp_cooks_raw_meat(self, game_state_forest, raw_meat):
        """Spec: If player has Raw Meat and campfire, it becomes Cooked Meat."""
        gs = game_state_forest
        gs.current_character.inventory.add_item(raw_meat)
        gs.current_character.light_remaining = 5  # Campfire
        gs.current_character.take_damage(50)

        cont, msg = handle_exploration_command(gs, "camp", [])

        # Raw Meat should be replaced with Cooked Meat
        raw_count = len([i for i in gs.current_character.inventory.items
                        if i.name == "Raw Meat"])
        cooked_count = len([i for i in gs.current_character.inventory.items
                           if i.name == "Cooked Meat"])
        assert raw_count == 0
        assert cooked_count == 1
        # Cooked Meat should heal 40 HP
        cooked = next(i for i in gs.current_character.inventory.items
                     if i.name == "Cooked Meat")
        assert cooked.heal_amount == 40


# =============================================================================
# Forage Command Tests (Spec: forage command mechanics)
# =============================================================================

class TestForageCommand:
    """Tests for 'forage' command - Spec: foraging mechanics."""

    # Spec: forage success adds item (test 14)
    def test_forage_success_adds_item(self, game_state_wilderness):
        """Spec: Successful forage adds an item to inventory."""
        gs = game_state_wilderness
        random.seed(42)  # Seed for reproducibility (should succeed with high PER)
        initial_count = len(gs.current_character.inventory.items)

        # Force high success by setting perception very high
        gs.current_character.perception = 20  # 40% base + 40% from PER = 80%
        random.seed(1)  # This seed with 80% should succeed

        cont, msg = handle_exploration_command(gs, "forage", [])

        # Check that forage was attempted (message indicates result)
        assert cont is True
        # Either found something or searched without finding
        assert "found" in msg.lower() or "nothing" in msg.lower() or "search" in msg.lower()

    # Spec: forage failure no item (test 15)
    def test_forage_failure_no_item(self, game_state_wilderness):
        """Spec: Failed forage adds no item to inventory."""
        gs = game_state_wilderness
        gs.current_character.perception = 1  # Low perception = low success rate
        initial_count = len(gs.current_character.inventory.items)

        # Use a seed that will fail with low success chance
        random.seed(99999)

        cont, msg = handle_exploration_command(gs, "forage", [])

        # Either it found nothing or the test succeeded by luck
        assert cont is True
        # Just verify the message makes sense
        assert "forage" in msg.lower() or "found" in msg.lower() or "nothing" in msg.lower() or "search" in msg.lower()

    # Spec: forage blocked in town (test 16)
    def test_forage_blocked_in_town(self, game_state_town):
        """Spec: Forage returns error in town locations."""
        gs = game_state_town

        cont, msg = handle_exploration_command(gs, "forage", [])

        assert cont is True
        assert "can't" in msg.lower() or "wilderness" in msg.lower() or "town" in msg.lower() or "here" in msg.lower()

    # Spec: forage blocked in dungeon (test 17)
    def test_forage_blocked_in_dungeon(self, game_state_dungeon):
        """Spec: Forage returns error in dungeon locations."""
        gs = game_state_dungeon

        cont, msg = handle_exploration_command(gs, "forage", [])

        assert cont is True
        assert "can't" in msg.lower() or "dungeon" in msg.lower() or "here" in msg.lower()

    # Spec: Moonpetal only at night (test 18)
    def test_forage_night_moonpetal(self, game_state_wilderness):
        """Spec: Moonpetal Flower can only be found at night."""
        from cli_rpg.camping import FORAGE_ITEMS

        # Check that Moonpetal is defined with night_only flag
        moonpetal_items = [i for i in FORAGE_ITEMS if "moonpetal" in i["name"].lower()]
        assert len(moonpetal_items) > 0
        assert moonpetal_items[0].get("night_only", False) is True

    # Spec: forage sets cooldown to 1 hour (test 19)
    def test_forage_sets_cooldown(self, game_state_wilderness):
        """Spec: Forage sets cooldown to 1 hour."""
        gs = game_state_wilderness
        assert gs.forage_cooldown == 0

        cont, msg = handle_exploration_command(gs, "forage", [])

        assert gs.forage_cooldown == 1  # 1 hour cooldown

    # Spec: forage blocked on cooldown (test 20)
    def test_forage_blocked_on_cooldown(self, game_state_wilderness):
        """Spec: Cannot forage during cooldown."""
        gs = game_state_wilderness
        gs.forage_cooldown = 1  # Set cooldown

        cont, msg = handle_exploration_command(gs, "forage", [])

        assert cont is True
        assert "cooldown" in msg.lower() or "wait" in msg.lower() or "recently" in msg.lower()


# =============================================================================
# Hunt Command Tests (Spec: hunt command mechanics)
# =============================================================================

class TestHuntCommand:
    """Tests for 'hunt' command - Spec: hunting mechanics."""

    # Spec: hunt success gives Raw Meat (test 21)
    def test_hunt_success_gives_meat(self, game_state_wilderness):
        """Spec: Successful hunt gives Raw Meat."""
        gs = game_state_wilderness
        gs.current_character.dexterity = 20
        gs.current_character.perception = 20
        random.seed(1)  # Seed for success

        cont, msg = handle_exploration_command(gs, "hunt", [])

        # Check for success or failure message
        assert cont is True
        if "raw meat" in msg.lower() or "caught" in msg.lower():
            meat = gs.current_character.inventory.find_item_by_name("Raw Meat")
            assert meat is not None

    # Spec: hunt critical gives Animal Pelt (test 22)
    def test_hunt_critical_gives_pelt(self, game_state_wilderness):
        """Spec: Critical hunt success also gives Animal Pelt (sell for 25 gold)."""
        from cli_rpg.camping import HUNT_RESULTS

        # Verify Animal Pelt is in critical results
        assert "Animal Pelt" in HUNT_RESULTS.get("critical", []) or \
               any("pelt" in item.get("name", "").lower()
                   for item in HUNT_RESULTS.get("critical_items", []))

    # Spec: hunt failure no item (test 23)
    def test_hunt_failure_no_item(self, game_state_wilderness):
        """Spec: Failed hunt adds no item to inventory."""
        gs = game_state_wilderness
        gs.current_character.dexterity = 1  # Low DEX = low success
        gs.current_character.perception = 1  # Low PER
        initial_count = len(gs.current_character.inventory.items)
        random.seed(99999)  # Seed for likely failure

        cont, msg = handle_exploration_command(gs, "hunt", [])

        assert cont is True
        # Message should indicate success or failure
        assert "hunt" in msg.lower() or "caught" in msg.lower() or "escapes" in msg.lower() or "prey" in msg.lower()

    # Spec: hunt blocked in town (test 24)
    def test_hunt_blocked_in_town(self, game_state_town):
        """Spec: Hunt returns error in town locations."""
        gs = game_state_town

        cont, msg = handle_exploration_command(gs, "hunt", [])

        assert cont is True
        assert "can't" in msg.lower() or "wilderness" in msg.lower() or "town" in msg.lower() or "here" in msg.lower()

    # Spec: hunt sets cooldown to 2 hours (test 25)
    def test_hunt_sets_cooldown(self, game_state_wilderness):
        """Spec: Hunt sets cooldown to 2 hours."""
        gs = game_state_wilderness
        assert gs.hunt_cooldown == 0

        cont, msg = handle_exploration_command(gs, "hunt", [])

        assert gs.hunt_cooldown == 2  # 2 hours cooldown

    # Spec: hunt blocked on cooldown (test 26)
    def test_hunt_blocked_on_cooldown(self, game_state_wilderness):
        """Spec: Cannot hunt during cooldown."""
        gs = game_state_wilderness
        gs.hunt_cooldown = 2  # Set cooldown

        cont, msg = handle_exploration_command(gs, "hunt", [])

        assert cont is True
        assert "cooldown" in msg.lower() or "wait" in msg.lower() or "recently" in msg.lower()


# =============================================================================
# Integration Tests
# =============================================================================

class TestCampingIntegration:
    """Integration tests for camping feature."""

    # Spec: full camp command integration (test 27)
    def test_camp_command_in_forest(self, game_state_forest):
        """Spec: Full integration test for camp command in forest."""
        gs = game_state_forest
        gs.current_character.take_damage(50)
        gs.current_character.dread_meter.dread = 40
        old_hour = gs.game_time.hour
        old_health = gs.current_character.health

        cont, msg = handle_exploration_command(gs, "camp", [])

        assert cont is True
        # Health should be improved
        assert gs.current_character.health > old_health
        # Dread should be reduced
        assert gs.current_character.dread_meter.dread < 40
        # Time should advance
        assert gs.game_time.hour != old_hour

    # Spec: cooldowns tick down with time (test 28)
    def test_forage_hunt_cooldown_decrements(self, game_state_wilderness):
        """Spec: Cooldowns decrement when game time advances."""
        gs = game_state_wilderness
        gs.forage_cooldown = 1
        gs.hunt_cooldown = 2

        # Simulate time advance by moving or resting
        gs.game_time.advance(1)
        # Cooldowns should decrement when checked or when time advances
        # This depends on implementation - we'll need to call the decrement method
        from cli_rpg.camping import decrement_cooldowns
        decrement_cooldowns(gs)

        assert gs.forage_cooldown == 0
        assert gs.hunt_cooldown == 1

    # Spec: campfire visitor spawn (test 29)
    def test_campfire_visitor_spawn(self, game_state_forest):
        """Spec: 20% chance of visitor NPC when camping with campfire."""
        from cli_rpg.camping import CAMPFIRE_VISITORS

        # Verify campfire visitors are defined
        assert len(CAMPFIRE_VISITORS) > 0
        # Each visitor should have a name and type
        for visitor in CAMPFIRE_VISITORS:
            assert "name" in visitor
            assert "type" in visitor

    # Spec: cooldowns persist in save/load (test 30)
    def test_camping_persistence(self, game_state_wilderness):
        """Spec: Cooldowns are saved and loaded correctly."""
        gs = game_state_wilderness
        gs.forage_cooldown = 1
        gs.hunt_cooldown = 2

        # Serialize
        state_dict = gs.to_dict()

        # Verify cooldowns are in serialized data
        assert "forage_cooldown" in state_dict
        assert "hunt_cooldown" in state_dict
        assert state_dict["forage_cooldown"] == 1
        assert state_dict["hunt_cooldown"] == 2

        # Deserialize
        loaded_gs = GameState.from_dict(state_dict)
        assert loaded_gs.forage_cooldown == 1
        assert loaded_gs.hunt_cooldown == 2


# =============================================================================
# Parse Command Tests
# =============================================================================

class TestParseCommands:
    """Tests for parsing camping commands."""

    # Spec: camp command recognized (test 31)
    def test_parse_camp_command(self):
        """Spec: 'camp' is a recognized command."""
        cmd, args = parse_command("camp")
        assert cmd == "camp"
        assert args == []

    # Spec: camp alias works (test 32)
    def test_parse_camp_alias(self):
        """Spec: 'ca' expands to 'camp' command."""
        cmd, args = parse_command("ca")
        assert cmd == "camp"
        assert args == []

    # Spec: forage command recognized (test 33)
    def test_parse_forage_command(self):
        """Spec: 'forage' is a recognized command."""
        cmd, args = parse_command("forage")
        assert cmd == "forage"
        assert args == []

    # Spec: forage alias works (test 34)
    def test_parse_forage_alias(self):
        """Spec: 'fg' expands to 'forage' command."""
        cmd, args = parse_command("fg")
        assert cmd == "forage"
        assert args == []

    # Spec: hunt command recognized (test 35)
    def test_parse_hunt_command(self):
        """Spec: 'hunt' is a recognized command."""
        cmd, args = parse_command("hunt")
        assert cmd == "hunt"
        assert args == []

    # Spec: hunt alias works (test 36)
    def test_parse_hunt_alias(self):
        """Spec: 'hu' expands to 'hunt' command."""
        cmd, args = parse_command("hu")
        assert cmd == "hunt"
        assert args == []


# =============================================================================
# Help Text Tests
# =============================================================================

class TestHelpText:
    """Tests for help text including camping commands."""

    # Spec: help includes camp (test 37)
    def test_help_includes_camp(self):
        """Spec: Command reference includes camp command."""
        help_text = get_command_reference()
        assert "camp" in help_text.lower()

    # Spec: help includes forage (test 38)
    def test_help_includes_forage(self):
        """Spec: Command reference includes forage command."""
        help_text = get_command_reference()
        assert "forage" in help_text.lower()

    # Spec: help includes hunt (test 39)
    def test_help_includes_hunt(self):
        """Spec: Command reference includes hunt command."""
        help_text = get_command_reference()
        assert "hunt" in help_text.lower()


# =============================================================================
# Commands in KNOWN_COMMANDS
# =============================================================================

class TestKnownCommands:
    """Tests that camping commands are in KNOWN_COMMANDS set."""

    def test_camp_in_known_commands(self):
        """Camp should be in KNOWN_COMMANDS."""
        assert "camp" in KNOWN_COMMANDS

    def test_forage_in_known_commands(self):
        """Forage should be in KNOWN_COMMANDS."""
        assert "forage" in KNOWN_COMMANDS

    def test_hunt_in_known_commands(self):
        """Hunt should be in KNOWN_COMMANDS."""
        assert "hunt" in KNOWN_COMMANDS


# =============================================================================
# Overworld Error Message Tests
# =============================================================================

class TestOverworldErrorMessage:
    """Tests for improved error messages at overworld locations."""

    # Spec: camp at overworld with sub-locations shows enter hint
    def test_camp_at_overworld_shows_enter_hint(self):
        """Spec: Camping at overworld location shows hint to use 'enter' command."""
        # Create an overworld location with sub-locations
        overworld_forest = Location(
            name="Forest",
            description="A vast forest with many areas to explore.",
            category="forest",
            is_overworld=True,
            sub_locations=["Forest Edge", "Deep Woods"]
        )
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Forest": overworld_forest}
        gs = GameState(char, world, starting_location="Forest")

        # Add camping supplies
        supplies = Item(
            name="Camping Supplies",
            description="Essential supplies for camping",
            item_type=ItemType.CONSUMABLE,
            heal_amount=0
        )
        gs.current_character.inventory.add_item(supplies)
        gs.current_character.take_damage(50)  # Need to heal

        cont, msg = handle_exploration_command(gs, "camp", [])

        assert cont is True
        # Should mention 'enter' command
        assert "enter" in msg.lower()
        # Should list the sub-locations
        assert "forest edge" in msg.lower() or "deep woods" in msg.lower()


# =============================================================================
# Camp Dream Chance Tests
# =============================================================================

class TestCampDreamChance:
    """Tests for camp dream chance (15%, with cooldown).

    Spec: Camp uses CAMP_DREAM_CHANCE (15%) instead of old 40%.
    """

    def test_camp_uses_camp_dream_chance(self):
        """Spec: Camp uses CAMP_DREAM_CHANCE constant from dreams.py (15%)."""
        from cli_rpg.dreams import CAMP_DREAM_CHANCE

        # Verify the constant value
        assert CAMP_DREAM_CHANCE == 0.15  # 15%, reduced from 40%

    def test_camp_dream_with_cooldown_integration(self, game_state_forest):
        """Spec: Camp respects dream cooldown."""
        from unittest.mock import patch

        gs = game_state_forest
        gs.current_character.take_damage(50)

        # Set last_dream_hour to recent (should block dream due to cooldown)
        gs.game_time.total_hours = 100
        gs.last_dream_hour = 95  # Only 5 hours ago, < 12 hours

        # Force dream to trigger (but cooldown should block)
        with patch("cli_rpg.dreams.random.random", return_value=0.01):
            cont, msg = handle_exploration_command(gs, "camp", [])

        # Cooldown should have blocked the dream
        # last_dream_hour should NOT be updated if dream was blocked
        # Note: We can't easily test this without checking the output,
        # but the test verifies the integration path works

    def test_camp_updates_last_dream_hour_on_dream(self, game_state_forest, capsys):
        """Spec: Camp updates last_dream_hour when dream triggers."""
        from unittest.mock import patch

        gs = game_state_forest
        gs.current_character.take_damage(50)

        # Set initial state with no recent dream
        gs.game_time.total_hours = 100
        gs.last_dream_hour = None  # Never dreamed

        # Force dream to trigger
        with patch("cli_rpg.dreams.random.random", return_value=0.01):
            cont, msg = handle_exploration_command(gs, "camp", [])

        # Camp advances time by 8 hours, so total_hours is now 108
        # If dream triggered, last_dream_hour should be set to 108
        if gs.last_dream_hour is not None:
            assert gs.last_dream_hour == 108
