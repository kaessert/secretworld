"""Tests for game state persistence."""

import json
import os
import pytest
import tempfile

from cli_rpg.persistence import save_game_state, load_game_state
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


class TestSaveGameState:
    """Tests for save_game_state() function."""
    
    def test_save_game_state_creates_file(self, tmp_path):
        """Test that save_game_state creates a file.
        
        Spec: File should be created
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        assert os.path.exists(filepath)
    
    def test_save_game_state_returns_filepath(self, tmp_path):
        """Test that save_game_state returns a string path.
        
        Spec: Should return string path
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        assert isinstance(filepath, str)
        assert len(filepath) > 0
    
    def test_save_game_state_creates_directory(self):
        """Test that save_game_state creates save_dir if missing.
        
        Spec: Should create save_dir if it doesn't exist
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_dir = os.path.join(tmp_dir, "new_saves")
            
            character = Character("Hero", strength=10, dexterity=10, intelligence=10)
            world = {
                "Start": Location("Start", "Start location")
            }
            game_state = GameState(character, world, "Start")
            
            filepath = save_game_state(game_state, save_dir)
            
            assert os.path.exists(save_dir)
            assert os.path.exists(filepath)
    
    def test_save_game_state_valid_json(self, tmp_path):
        """Test that saved file contains valid JSON.
        
        Spec: File should contain valid JSON
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
    
    def test_save_game_state_contains_complete_data(self, tmp_path):
        """Test that saved file contains character, location, and world.
        
        Spec: Should contain character, current_location, world
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        assert "character" in data
        assert "current_location" in data
        assert "world" in data
        assert data["character"]["name"] == "Hero"
        assert data["current_location"] == "Start"
        assert "Start" in data["world"]
        assert "End" in data["world"]
    
    def test_save_game_state_custom_directory(self):
        """Test that save_game_state respects save_dir parameter.
        
        Spec: Should save to custom directory
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            custom_dir = os.path.join(tmp_dir, "custom_saves")
            
            character = Character("Hero", strength=10, dexterity=10, intelligence=10)
            world = {
                "Start": Location("Start", "Start location")
            }
            game_state = GameState(character, world, "Start")
            
            filepath = save_game_state(game_state, custom_dir)
            
            assert custom_dir in filepath
            assert os.path.exists(filepath)


class TestLoadGameState:
    """Tests for load_game_state() function."""
    
    def test_load_game_state_success(self, tmp_path):
        """Test that load_game_state loads a valid file.
        
        Spec: Should load valid file successfully
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert loaded_state is not None
    
    def test_load_game_state_returns_game_state(self, tmp_path):
        """Test that load_game_state returns GameState instance.
        
        Spec: Should return GameState instance
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert isinstance(loaded_state, GameState)
    
    def test_load_game_state_restores_character(self, tmp_path):
        """Test that load_game_state restores character correctly.
        
        Spec: Character should match original
        """
        character = Character("TestHero", strength=12, dexterity=15, intelligence=8)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert loaded_state.current_character.name == "TestHero"
        assert loaded_state.current_character.strength == 12
        assert loaded_state.current_character.dexterity == 15
        assert loaded_state.current_character.intelligence == 8
    
    def test_load_game_state_restores_location(self, tmp_path):
        """Test that load_game_state restores location correctly.
        
        Spec: Location should match original
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }
        game_state = GameState(character, world, "Start")
        game_state.move("north")  # Move to End
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert loaded_state.current_location == "End"
    
    def test_load_game_state_restores_world(self, tmp_path):
        """Test that load_game_state restores world correctly.
        
        Spec: World should match original
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location", {"south": "Start"})
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert "Start" in loaded_state.world
        assert "End" in loaded_state.world
        assert loaded_state.world["Start"].get_connection("north") == "End"
        assert loaded_state.world["End"].get_connection("south") == "Start"
    
    def test_load_game_state_file_not_found(self):
        """Test that load_game_state raises FileNotFoundError for missing file.
        
        Spec: Should raise FileNotFoundError
        """
        with pytest.raises(FileNotFoundError):
            load_game_state("nonexistent_file.json")
    
    def test_load_game_state_invalid_json(self, tmp_path):
        """Test that load_game_state raises ValueError for invalid JSON.
        
        Spec: Should raise ValueError
        """
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json{")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_game_state(str(invalid_file))
    
    def test_load_game_state_missing_fields(self, tmp_path):
        """Test that load_game_state raises ValueError for missing required fields.
        
        Spec: Should raise ValueError for missing fields
        """
        incomplete_file = tmp_path / "incomplete.json"
        incomplete_file.write_text(json.dumps({"character": {}}))
        
        with pytest.raises((ValueError, KeyError)):
            load_game_state(str(incomplete_file))
    
    def test_load_game_state_roundtrip(self, tmp_path):
        """Test that save -> load preserves complete state.
        
        Spec: Save and load should preserve complete state
        """
        character = Character("Hero", strength=12, dexterity=15, intelligence=8)
        character.take_damage(20)  # Test that modified health is preserved
        
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location", {"south": "Start"})
        }
        game_state = GameState(character, world, "Start")
        game_state.move("north")  # Move to End
        
        # Save
        filepath = save_game_state(game_state, str(tmp_path))
        
        # Load
        loaded_state = load_game_state(filepath)
        
        # Verify everything is preserved
        assert loaded_state.current_character.name == "Hero"
        assert loaded_state.current_character.strength == 12
        assert loaded_state.current_character.health == character.health
        assert loaded_state.current_location == "End"
        assert "Start" in loaded_state.world
        assert "End" in loaded_state.world
        
        # Verify we can continue playing
        success, _ = loaded_state.move("south")
        assert success is True
        assert loaded_state.current_location == "Start"

    def test_load_game_state_preserves_coordinates(self, tmp_path):
        """Test that save -> load preserves location coordinates.

        Spec: Location coordinates should be preserved through persistence.
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        # Create locations with coordinates
        world = {
            "Town Square": Location("Town Square", "A town square.", {"north": "Forest"}, coordinates=(0, 0)),
            "Forest": Location("Forest", "A dark forest.", {"south": "Town Square"}, coordinates=(0, 1))
        }
        game_state = GameState(character, world, "Town Square")

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Load
        loaded_state = load_game_state(filepath)

        # Verify coordinates are preserved
        assert loaded_state.world["Town Square"].coordinates == (0, 0)
        assert loaded_state.world["Forest"].coordinates == (0, 1)

    def test_load_game_state_backward_compat_no_coordinates(self, tmp_path):
        """Test that loading saves without coordinates works (backward compat).

        Spec: Saves without coordinates should load with coordinates=None.
        """
        # Create a save file without coordinates (legacy format)
        save_data = {
            "character": {
                "name": "Hero",
                "strength": 10,
                "dexterity": 10,
                "intelligence": 10,
                "level": 1,
                "health": 150,
                "max_health": 150
            },
            "current_location": "Start",
            "world": {
                "Start": {
                    "name": "Start",
                    "description": "Start location",
                    "connections": {},
                    "npcs": []
                    # No coordinates field
                }
            }
        }

        filepath = tmp_path / "legacy_save.json"
        with open(filepath, "w") as f:
            json.dump(save_data, f)

        # Load
        loaded_state = load_game_state(str(filepath))

        # Verify it loads without error
        assert loaded_state.current_location == "Start"
        assert "Start" in loaded_state.world
        # Legacy location should have no coordinates
        assert loaded_state.world["Start"].coordinates is None

    def test_load_game_state_preserves_npcs(self, tmp_path):
        """Test that save -> load preserves NPCs at locations.

        Spec: NPCs should persist through save/load cycle with all their fields.
        """
        from cli_rpg.models.npc import NPC

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create an NPC with various attributes
        merchant = NPC(
            name="Town Merchant",
            description="A friendly shopkeeper",
            dialogue="Welcome to my shop!",
            is_merchant=True,
            greetings=["Hello there!", "Welcome back!"],
            conversation_history=[
                {"role": "player", "content": "What do you sell?"},
                {"role": "npc", "content": "I have potions and weapons."}
            ]
        )

        # Create location with the NPC
        world = {
            "Market": Location(
                "Market", "A busy marketplace", {"north": "Town"},
                coordinates=(0, 0), npcs=[merchant]
            ),
            "Town": Location("Town", "A quiet town", {"south": "Market"}, coordinates=(0, 1))
        }
        game_state = GameState(character, world, "Market")

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Load
        loaded_state = load_game_state(filepath)

        # Verify NPCs are preserved
        loaded_location = loaded_state.world["Market"]
        assert len(loaded_location.npcs) == 1

        loaded_npc = loaded_location.npcs[0]
        assert loaded_npc.name == "Town Merchant"
        assert loaded_npc.description == "A friendly shopkeeper"
        assert loaded_npc.dialogue == "Welcome to my shop!"
        assert loaded_npc.is_merchant is True
        assert loaded_npc.greetings == ["Hello there!", "Welcome back!"]
        assert len(loaded_npc.conversation_history) == 2
        assert loaded_npc.conversation_history[0] == {
            "role": "player", "content": "What do you sell?"
        }
        assert loaded_npc.conversation_history[1] == {
            "role": "npc", "content": "I have potions and weapons."
        }


class TestSubGridPersistence:
    """Tests for SubGrid serialization through persistence.

    Spec: When a game state is saved while player is inside a SubGrid:
    1. in_sub_location: true is persisted
    2. current_location contains the name of the location within the SubGrid
    3. Parent location's sub_grid data is persisted with all interior locations
    4. On load, in_sub_location, current_sub_grid, and current_location are restored
    5. Player can continue navigating within the SubGrid after load
    """

    def test_save_game_state_with_subgrid(self, tmp_path):
        """Test that SubGrid data is included in save file.

        Spec: Parent location's sub_grid data is persisted with all interior locations.
        """
        from cli_rpg.world_grid import SubGrid

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create a sub-grid for a castle interior
        castle_interior = SubGrid(parent_name="Castle Entrance")
        entry = Location("Castle Entrance Hall", "The grand entrance hall")
        throne = Location("Throne Room", "The king's throne room")
        castle_interior.add_location(entry, 0, 0)
        castle_interior.add_location(throne, 0, 1)

        # Create world with parent location containing the sub-grid
        castle = Location(
            "Castle Entrance", "A towering castle", coordinates=(0, 0), sub_grid=castle_interior
        )
        world = {"Castle Entrance": castle}
        game_state = GameState(character, world, "Castle Entrance")

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Verify the save file contains sub_grid data
        with open(filepath, "r") as f:
            data = json.load(f)

        assert "sub_grid" in data["world"]["Castle Entrance"]
        sub_grid_data = data["world"]["Castle Entrance"]["sub_grid"]
        assert "locations" in sub_grid_data
        assert len(sub_grid_data["locations"]) == 2
        assert sub_grid_data["parent_name"] == "Castle Entrance"

        # Verify location names are present
        location_names = [loc["name"] for loc in sub_grid_data["locations"]]
        assert "Castle Entrance Hall" in location_names
        assert "Throne Room" in location_names

    def test_load_game_state_restores_subgrid(self, tmp_path):
        """Test that SubGrid is restored with locations.

        Spec: On load, parent location's sub_grid is restored with all interior locations.
        """
        from cli_rpg.world_grid import SubGrid

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create a sub-grid with multiple locations
        dungeon_interior = SubGrid(parent_name="Dungeon Gate")
        entry = Location("Dungeon Entry", "Dark entrance")
        hallway = Location("Dungeon Hallway", "A long corridor")
        dungeon_interior.add_location(entry, 0, 0)
        dungeon_interior.add_location(hallway, 1, 0)  # East of entry

        dungeon = Location(
            "Dungeon Gate", "An ominous gate", coordinates=(0, 0), sub_grid=dungeon_interior
        )
        world = {"Dungeon Gate": dungeon}
        game_state = GameState(character, world, "Dungeon Gate")

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Load
        loaded_state = load_game_state(filepath)

        # Verify SubGrid is restored
        loaded_dungeon = loaded_state.world["Dungeon Gate"]
        assert loaded_dungeon.sub_grid is not None
        assert loaded_dungeon.sub_grid.parent_name == "Dungeon Gate"

        # Verify locations within SubGrid are restored
        entry_loc = loaded_dungeon.sub_grid.get_by_name("Dungeon Entry")
        hallway_loc = loaded_dungeon.sub_grid.get_by_name("Dungeon Hallway")
        assert entry_loc is not None
        assert hallway_loc is not None
        assert entry_loc.description == "Dark entrance"
        assert hallway_loc.description == "A long corridor"

    def test_save_load_while_inside_subgrid(self, tmp_path):
        """Test that player position inside SubGrid persists.

        Spec: in_sub_location: true is persisted; current_location contains SubGrid location.
        """
        from cli_rpg.world_grid import SubGrid

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create sub-grid
        tower_interior = SubGrid(parent_name="Tower Base")
        base = Location("Tower Ground Floor", "Ground floor of the tower")
        upper = Location("Tower Upper Floor", "Upper floor with a view")
        tower_interior.add_location(base, 0, 0)
        tower_interior.add_location(upper, 0, 1)

        tower = Location(
            "Tower Base", "A tall tower", coordinates=(0, 0), sub_grid=tower_interior
        )
        world = {"Tower Base": tower}
        game_state = GameState(character, world, "Tower Base")

        # Simulate entering the sub-grid and moving within it
        game_state.in_sub_location = True
        game_state.current_sub_grid = tower_interior
        game_state.current_location = "Tower Upper Floor"

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Verify save file
        with open(filepath, "r") as f:
            data = json.load(f)

        assert data["in_sub_location"] is True
        assert data["current_location"] == "Tower Upper Floor"

        # Load
        loaded_state = load_game_state(filepath)

        # Verify player is still inside sub-grid at correct location
        assert loaded_state.in_sub_location is True
        assert loaded_state.current_location == "Tower Upper Floor"
        assert loaded_state.current_sub_grid is not None
        assert loaded_state.current_sub_grid.get_by_name("Tower Upper Floor") is not None

    def test_subgrid_roundtrip_preserves_connections(self, tmp_path):
        """Test that bidirectional connections within SubGrid survive save/load.

        Spec: Location connections within SubGrid are preserved through persistence.
        """
        from cli_rpg.world_grid import SubGrid

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create sub-grid with connected locations
        house_interior = SubGrid(parent_name="House")
        living = Location("Living Room", "A cozy living room")
        kitchen = Location("Kitchen", "A small kitchen")
        bedroom = Location("Bedroom", "A bedroom upstairs")
        house_interior.add_location(living, 0, 0)
        house_interior.add_location(kitchen, 1, 0)  # East of living room
        house_interior.add_location(bedroom, 0, 1)  # North of living room

        house = Location("House", "A small house", coordinates=(0, 0), sub_grid=house_interior)
        world = {"House": house}
        game_state = GameState(character, world, "House")

        # Verify connections before save
        assert living.get_connection("east") == "Kitchen"
        assert living.get_connection("north") == "Bedroom"
        assert kitchen.get_connection("west") == "Living Room"
        assert bedroom.get_connection("south") == "Living Room"

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Load
        loaded_state = load_game_state(filepath)

        # Verify connections after load
        loaded_sub_grid = loaded_state.world["House"].sub_grid
        loaded_living = loaded_sub_grid.get_by_name("Living Room")
        loaded_kitchen = loaded_sub_grid.get_by_name("Kitchen")
        loaded_bedroom = loaded_sub_grid.get_by_name("Bedroom")

        assert loaded_living.get_connection("east") == "Kitchen"
        assert loaded_living.get_connection("north") == "Bedroom"
        assert loaded_kitchen.get_connection("west") == "Living Room"
        assert loaded_bedroom.get_connection("south") == "Living Room"

    def test_subgrid_roundtrip_preserves_exit_points(self, tmp_path):
        """Test that is_exit_point markers survive save/load.

        Spec: Exit point markers are preserved through persistence.
        """
        from cli_rpg.world_grid import SubGrid

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create sub-grid with an exit point
        cave_interior = SubGrid(parent_name="Cave Mouth")
        entrance = Location("Cave Entrance", "The entrance to the cave", is_exit_point=True)
        deep = Location("Deep Cave", "The deepest part of the cave")
        cave_interior.add_location(entrance, 0, 0)
        cave_interior.add_location(deep, 0, -1)  # South of entrance

        cave = Location("Cave Mouth", "A dark cave", coordinates=(0, 0), sub_grid=cave_interior)
        world = {"Cave Mouth": cave}
        game_state = GameState(character, world, "Cave Mouth")

        # Verify exit point before save
        assert entrance.is_exit_point is True
        assert deep.is_exit_point is False

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Load
        loaded_state = load_game_state(filepath)

        # Verify exit point after load
        loaded_sub_grid = loaded_state.world["Cave Mouth"].sub_grid
        loaded_entrance = loaded_sub_grid.get_by_name("Cave Entrance")
        loaded_deep = loaded_sub_grid.get_by_name("Deep Cave")

        assert loaded_entrance.is_exit_point is True
        assert loaded_deep.is_exit_point is False

    def test_backward_compat_no_subgrid(self, tmp_path):
        """Test that old saves without SubGrid still load.

        Spec: Backward compatibility - saves without sub_grid load correctly.
        """
        # Create a save file without sub_grid (legacy format)
        save_data = {
            "character": {
                "name": "Hero",
                "strength": 10,
                "dexterity": 10,
                "intelligence": 10,
                "level": 1,
                "health": 150,
                "max_health": 150
            },
            "current_location": "Town",
            "world": {
                "Town": {
                    "name": "Town",
                    "description": "A peaceful town",
                    "connections": {"north": "Forest"},
                    "npcs": []
                    # No sub_grid field
                },
                "Forest": {
                    "name": "Forest",
                    "description": "A dark forest",
                    "connections": {"south": "Town"},
                    "npcs": []
                }
            }
            # No in_sub_location field
        }

        filepath = tmp_path / "legacy_no_subgrid.json"
        with open(filepath, "w") as f:
            json.dump(save_data, f)

        # Load
        loaded_state = load_game_state(str(filepath))

        # Verify it loads without error
        assert loaded_state.current_location == "Town"
        assert "Town" in loaded_state.world
        assert "Forest" in loaded_state.world
        # Verify sub_grid is None (not present in legacy saves)
        assert loaded_state.world["Town"].sub_grid is None
        assert loaded_state.world["Forest"].sub_grid is None
        # Verify in_sub_location defaults to False
        assert loaded_state.in_sub_location is False
