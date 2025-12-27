"""Regression tests for NPC persistence when navigating away and returning.

Bug report: NPCs show as "???" when revisiting locations in WFC mode.
These tests verify that NPCs remain properly visible after navigation.
"""

import pytest

from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC


class TestNPCPersistenceNavigation:
    """Tests that NPCs persist correctly when navigating away and back."""

    # Regression test: NPCs should persist when leaving and returning to a location
    def test_npcs_persist_after_leaving_and_returning(self):
        """NPCs should be present when revisiting a location."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

        # Create two connected locations
        loc_a = Location(
            name="Location A",
            description="Test location A",
            coordinates=(0, 0)
        )
        loc_a.npcs = [NPC(name="TestNPC", description="A test NPC", dialogue="Hello")]

        loc_b = Location(
            name="Location B",
            description="Test location B",
            coordinates=(1, 0)
        )

        world = {"Location A": loc_a, "Location B": loc_b}
        game_state = GameState(char, world, starting_location="Location A")

        # Verify NPC is present initially
        look_result = game_state.look()
        assert "TestNPC" in look_result
        assert "???" not in look_result

        # Move east
        success, _ = game_state.move("east")
        assert success

        # Move back west
        success, _ = game_state.move("west")
        assert success

        # Verify NPC is still present
        look_result = game_state.look()
        assert "TestNPC" in look_result
        assert "???" not in look_result

    # Regression test: NPCs should persist through multiple navigation cycles
    def test_npcs_persist_after_multiple_navigation_cycles(self):
        """NPCs should persist after navigating away and back multiple times."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

        loc_a = Location(
            name="Location A",
            description="Test location A",
            coordinates=(0, 0)
        )
        loc_a.npcs = [
            NPC(name="Merchant Alice", description="A friendly merchant", dialogue="Welcome!"),
            NPC(name="Guard Bob", description="A vigilant guard", dialogue="Halt!"),
        ]

        loc_b = Location(
            name="Location B",
            description="Test location B",
            coordinates=(1, 0)
        )

        loc_c = Location(
            name="Location C",
            description="Test location C",
            coordinates=(0, 1)
        )

        world = {"Location A": loc_a, "Location B": loc_b, "Location C": loc_c}
        game_state = GameState(char, world, starting_location="Location A")

        # Navigate away and back multiple times
        for _ in range(3):
            # Go east and back
            game_state.move("east")
            game_state.move("west")

            # Go north and back
            game_state.move("north")
            game_state.move("south")

        # Verify both NPCs are still present with proper names
        look_result = game_state.look()
        assert "Merchant Alice" in look_result
        assert "Guard Bob" in look_result
        assert "???" not in look_result

    # Regression test: NPCs persist with WFC fallback location generation
    def test_npcs_persist_wfc_fallback_generation(self):
        """NPCs persist when navigating through WFC-generated fallback locations."""
        from cli_rpg.wfc_chunks import ChunkManager
        from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

        # Create starting location with NPC
        start = Location(
            name="Start",
            description="Starting location",
            coordinates=(0, 0)
        )
        start.npcs = [NPC(name="HomeNPC", description="An NPC at home", dialogue="Welcome!")]

        world = {"Start": start}
        chunk_manager = ChunkManager(tile_registry=DEFAULT_TILE_REGISTRY, world_seed=42)
        chunk_manager.sync_with_locations(world)

        game_state = GameState(
            char, world, starting_location="Start", chunk_manager=chunk_manager
        )

        # Verify NPC is present
        assert "HomeNPC" in game_state.look()

        # Move east (generates new fallback location)
        success, _ = game_state.move("east")
        assert success

        # Move back west
        success, _ = game_state.move("west")
        assert success

        # Verify original NPC is still present
        look_result = game_state.look()
        assert "HomeNPC" in look_result
        assert "???" not in look_result

    # Regression test: NPCs with special characters in names persist correctly
    def test_npcs_with_special_names_persist(self):
        """NPCs with apostrophes or special characters persist correctly."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

        loc_a = Location(
            name="Location A",
            description="Test location A",
            coordinates=(0, 0)
        )
        loc_a.npcs = [
            NPC(name="O'Brien the Smith", description="An Irish blacksmith", dialogue="Hello!"),
            NPC(name="Jean-Pierre", description="A French merchant", dialogue="Bonjour!"),
        ]

        loc_b = Location(
            name="Location B",
            description="Test location B",
            coordinates=(1, 0)
        )

        world = {"Location A": loc_a, "Location B": loc_b}
        game_state = GameState(char, world, starting_location="Location A")

        # Navigate away and back
        game_state.move("east")
        game_state.move("west")

        # Verify NPCs with special names are still present
        look_result = game_state.look()
        assert "O'Brien" in look_result
        assert "Jean-Pierre" in look_result
        assert "???" not in look_result

    # Regression test: Multiple NPCs all persist correctly
    def test_multiple_npcs_all_persist(self):
        """All NPCs in a location persist when navigating away and back."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

        loc_a = Location(
            name="Town Square",
            description="A bustling town square",
            coordinates=(0, 0)
        )
        # Add multiple NPCs
        npc_names = ["Baker Tom", "Guard Sarah", "Merchant Elena", "Beggar Joe"]
        loc_a.npcs = [
            NPC(name=name, description=f"A {name.split()[0].lower()}", dialogue="Hello!")
            for name in npc_names
        ]

        loc_b = Location(
            name="Market",
            description="A busy market",
            coordinates=(1, 0)
        )

        world = {"Town Square": loc_a, "Market": loc_b}
        game_state = GameState(char, world, starting_location="Town Square")

        # Navigate away and back
        game_state.move("east")
        game_state.move("west")

        # Verify ALL NPCs are still present
        look_result = game_state.look()
        for name in npc_names:
            assert name in look_result, f"NPC '{name}' should be present"
        assert "???" not in look_result

    # Regression test: NPCs should never display as "???"
    def test_npc_names_never_show_question_marks(self):
        """NPC names should never be displayed as '???'."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

        # Create a more complex navigation scenario
        locations = {}
        for i, name in enumerate(["Center", "North", "South", "East", "West"]):
            coords = {
                "Center": (0, 0),
                "North": (0, 1),
                "South": (0, -1),
                "East": (1, 0),
                "West": (-1, 0),
            }[name]

            loc = Location(name=name, description=f"The {name}", coordinates=coords)
            loc.npcs = [NPC(name=f"NPC_{name}", description=f"An NPC in {name}", dialogue="Hi")]
            locations[name] = loc

        # Set up connections
        locations["Center"].connections = {
            "north": "North",
            "south": "South",
            "east": "East",
            "west": "West",
        }
        locations["North"].connections = {"south": "Center"}
        locations["South"].connections = {"north": "Center"}
        locations["East"].connections = {"west": "Center"}
        locations["West"].connections = {"east": "Center"}

        game_state = GameState(char, locations, starting_location="Center")

        # Visit all locations and return to center
        for direction in ["north", "south", "east", "west"]:
            game_state.move(direction)
            look = game_state.look()
            assert "???" not in look, f"'???' found after moving {direction}"

            # Return to center
            opposite = {
                "north": "south",
                "south": "north",
                "east": "west",
                "west": "east",
            }[direction]
            game_state.move(opposite)

            # Check center NPCs are still visible
            look = game_state.look()
            assert "NPC_Center" in look
            assert "???" not in look
