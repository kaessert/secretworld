"""Tests for the pre-generated test world fixture and loading utilities.

These tests verify that:
1. The test world fixture loads correctly (test_load_test_world_returns_valid_dict)
2. GameState.from_dict() succeeds on fixture data (test_create_demo_game_state_returns_game_state)
3. Character exists with expected stats (test_demo_game_state_has_character)
4. World has expected named locations (test_demo_game_state_has_locations)
5. NPCs exist with shops/quests (test_demo_game_state_has_npcs)
6. Navigation works between locations (test_demo_game_state_navigation_works)
7. look() returns valid output (test_demo_game_state_look_works)
8. SubGrid entry/exit works (test_demo_game_state_subgrid_entry)
"""

import pytest
from cli_rpg.test_world import load_test_world, create_demo_game_state
from cli_rpg.game_state import GameState
from cli_rpg.models.character import CharacterClass


class TestLoadTestWorld:
    """Tests for load_test_world() - Spec: Fixture loads as valid JSON."""

    def test_load_test_world_returns_valid_dict(self):
        """Fixture loads as valid JSON and returns a dictionary."""
        data = load_test_world()

        assert isinstance(data, dict)
        assert "character" in data
        assert "world" in data
        assert "current_location" in data
        assert "theme" in data

    def test_load_test_world_has_required_fields(self):
        """Fixture contains all required fields for GameState."""
        data = load_test_world()

        # Character fields
        assert "name" in data["character"]
        assert "strength" in data["character"]
        assert "level" in data["character"]
        assert "inventory" in data["character"]

        # World fields
        assert len(data["world"]) >= 5

        # Other required fields
        assert "factions" in data
        assert "game_time" in data
        assert "weather" in data


class TestCreateDemoGameState:
    """Tests for create_demo_game_state() - Spec: GameState.from_dict() succeeds."""

    def test_create_demo_game_state_returns_game_state(self):
        """GameState.from_dict() succeeds on fixture data."""
        game_state = create_demo_game_state()

        assert isinstance(game_state, GameState)
        assert game_state.current_character is not None
        assert game_state.world is not None
        assert game_state.current_location is not None


class TestDemoGameStateCharacter:
    """Tests for character in demo game state - Spec: Character exists with expected stats."""

    def test_demo_game_state_has_character(self):
        """Character exists with expected stats."""
        game_state = create_demo_game_state()
        char = game_state.current_character

        assert char.name == "Demo Hero"
        assert char.character_class == CharacterClass.WARRIOR
        assert char.level == 3

    def test_demo_character_has_equipment(self):
        """Character has equipped weapon and armor."""
        game_state = create_demo_game_state()
        char = game_state.current_character

        assert char.inventory.equipped_weapon is not None
        assert char.inventory.equipped_weapon.name == "Iron Sword"
        assert char.inventory.equipped_armor is not None
        assert char.inventory.equipped_armor.name == "Leather Armor"

    def test_demo_character_has_inventory_items(self):
        """Character has items in inventory."""
        game_state = create_demo_game_state()
        char = game_state.current_character

        # Should have health potions and torch
        item_names = [item.name for item in char.inventory.items]
        assert "Health Potion" in item_names
        assert "Torch" in item_names

    def test_demo_character_has_gold(self):
        """Character has starting gold."""
        game_state = create_demo_game_state()
        char = game_state.current_character

        assert char.gold >= 100

    def test_demo_character_has_active_quest(self):
        """Character has an active quest."""
        game_state = create_demo_game_state()
        char = game_state.current_character

        assert len(char.quests) >= 1
        # Find the active quest
        active_quests = [q for q in char.quests if q.status.value == "active"]
        assert len(active_quests) >= 1


class TestDemoGameStateLocations:
    """Tests for locations in demo game state - Spec: World has expected named locations."""

    def test_demo_game_state_has_locations(self):
        """World has expected named locations."""
        game_state = create_demo_game_state()

        # Should have 5 locations
        assert len(game_state.world) >= 5

        # Check for expected locations
        location_names = list(game_state.world.keys())
        assert "Peaceful Village" in location_names
        assert "Whispering Forest" in location_names
        assert "Dark Cave" in location_names
        assert "Abandoned Ruins" in location_names
        assert "Southern Crossroads" in location_names

    def test_demo_locations_have_coordinates(self):
        """All locations have valid coordinates."""
        game_state = create_demo_game_state()

        for name, location in game_state.world.items():
            assert location.coordinates is not None, f"{name} has no coordinates"

    def test_demo_starting_location_is_village(self):
        """Starting location is the village."""
        game_state = create_demo_game_state()

        assert game_state.current_location == "Peaceful Village"

    def test_demo_village_is_safe_zone(self):
        """Village is marked as a safe zone."""
        game_state = create_demo_game_state()
        village = game_state.world["Peaceful Village"]

        assert village.is_safe_zone is True


class TestDemoGameStateNPCs:
    """Tests for NPCs in demo game state - Spec: NPCs exist with shops/quests."""

    def test_demo_game_state_has_npcs(self):
        """NPCs exist with shops/quests."""
        game_state = create_demo_game_state()
        village = game_state.world["Peaceful Village"]

        assert len(village.npcs) >= 2

        # Find merchant
        merchant = None
        for npc in village.npcs:
            if npc.is_merchant:
                merchant = npc
                break
        assert merchant is not None, "Should have a merchant NPC"
        assert merchant.shop is not None

    def test_demo_merchant_has_shop_inventory(self):
        """Merchant shop has items for sale."""
        game_state = create_demo_game_state()
        village = game_state.world["Peaceful Village"]

        merchant = next(npc for npc in village.npcs if npc.is_merchant)
        assert len(merchant.shop.inventory) >= 3

    def test_demo_quest_giver_has_quests(self):
        """Quest giver NPC has available quests."""
        game_state = create_demo_game_state()
        village = game_state.world["Peaceful Village"]

        quest_giver = None
        for npc in village.npcs:
            if npc.is_quest_giver and npc.offered_quests:
                quest_giver = npc
                break
        assert quest_giver is not None, "Should have a quest-giving NPC"


class TestDemoGameStateNavigation:
    """Tests for navigation - Spec: Can move between locations."""

    def test_demo_game_state_navigation_works(self):
        """Can move between locations."""
        game_state = create_demo_game_state()

        # Start at village (0,0), move north to forest (0,1)
        success, message = game_state.move("north")

        assert success is True
        assert game_state.current_location == "Whispering Forest"

    def test_demo_navigation_returns_to_village(self):
        """Can move back to starting location."""
        game_state = create_demo_game_state()

        # Move north then south
        game_state.move("north")
        success, message = game_state.move("south")

        assert success is True
        assert game_state.current_location == "Peaceful Village"

    def test_demo_navigation_to_cave(self):
        """Can navigate to cave location."""
        game_state = create_demo_game_state()

        # Move east to cave
        success, message = game_state.move("east")

        assert success is True
        assert game_state.current_location == "Dark Cave"


class TestDemoGameStateLook:
    """Tests for look command - Spec: look() returns valid output."""

    def test_demo_game_state_look_works(self):
        """look() returns valid output."""
        game_state = create_demo_game_state()

        result = game_state.look()

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain location description
        assert "village" in result.lower() or "peaceful" in result.lower()

    def test_demo_look_at_different_locations(self):
        """look() works at different locations."""
        game_state = create_demo_game_state()

        # Look at village
        village_look = game_state.look()
        assert len(village_look) > 0

        # Move to forest and look
        game_state.move("north")
        forest_look = game_state.look()
        assert len(forest_look) > 0
        assert "forest" in forest_look.lower() or "tree" in forest_look.lower()


class TestDemoGameStateSubGrid:
    """Tests for SubGrid entry/exit - Spec: Can enter/exit dungeon SubGrid."""

    def test_demo_game_state_subgrid_entry(self):
        """Can enter/exit dungeon SubGrid."""
        game_state = create_demo_game_state()

        # Move to cave
        game_state.move("east")
        assert game_state.current_location == "Dark Cave"

        # Enter the cave
        success, message = game_state.enter()

        assert success is True
        assert game_state.in_sub_location is True
        assert game_state.current_sub_grid is not None
        assert game_state.current_location == "Cave Entrance"

    def test_demo_subgrid_exit(self):
        """Can exit SubGrid back to overworld."""
        game_state = create_demo_game_state()

        # Move to cave and enter
        game_state.move("east")
        game_state.enter()

        # Exit back to overworld
        success, message = game_state.exit_location()

        assert success is True
        assert game_state.in_sub_location is False
        assert game_state.current_sub_grid is None
        assert game_state.current_location == "Dark Cave"

    def test_demo_subgrid_navigation(self):
        """Can navigate within SubGrid."""
        game_state = create_demo_game_state()

        # Move to cave and enter
        game_state.move("east")
        game_state.enter()

        # Navigate north to dark passage
        success, message = game_state.move("north")

        assert success is True
        assert game_state.current_location == "Dark Passage"
        assert game_state.in_sub_location is True


class TestDemoGameStateFactions:
    """Tests for factions in demo game state."""

    def test_demo_has_default_factions(self):
        """Demo game has default factions."""
        game_state = create_demo_game_state()

        assert len(game_state.factions) >= 3

        faction_names = [f.name for f in game_state.factions]
        assert "Town Guard" in faction_names
        assert "Merchant Guild" in faction_names
        assert "Thieves Guild" in faction_names

    def test_demo_factions_have_neutral_reputation(self):
        """Default factions have neutral (50) reputation."""
        game_state = create_demo_game_state()

        for faction in game_state.factions:
            # Should be neutral (50)
            assert faction.reputation == 50
