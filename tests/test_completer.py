"""Tests for completer module - Tab auto-completion for game commands.

Spec requirements (from ISSUES.md lines 63-86):
1. Complete command names: `ta<tab>` -> `talk`
2. Complete arguments contextually:
   - `talk <tab>` -> shows NPCs at current location
   - `go <tab>` -> shows available directions
   - `equip <tab>` -> shows equippable items (WEAPON/ARMOR) in inventory
   - `use <tab>` -> shows usable items (CONSUMABLE) in inventory
   - `buy <tab>` -> shows shop items (when in shop)
3. Cycle through multiple matches with repeated tab
4. Show all options on double-tab when ambiguous
"""
import pytest
from unittest.mock import MagicMock, patch


class TestCommandCompletion:
    """Tests for command name completion - Spec requirement 1."""

    def test_complete_command_prefix(self):
        """Spec req 1: 'lo' completes to 'look'."""
        from cli_rpg.completer import CommandCompleter

        completer = CommandCompleter()
        # State 0 = first match
        result = completer.complete("lo", 0)
        assert result == "look "

    def test_complete_command_multiple_matches(self):
        """Spec req 3: Multiple matches cycle with state."""
        from cli_rpg.completer import CommandCompleter

        completer = CommandCompleter()
        # 's' matches: save, sell, shop, status
        matches = []
        state = 0
        while True:
            result = completer.complete("s", state)
            if result is None:
                break
            matches.append(result.strip())
            state += 1

        assert "save" in matches
        assert "sell" in matches
        assert "shop" in matches
        assert "status" in matches

    def test_complete_command_exact_match(self):
        """Exact match returns command with trailing space."""
        from cli_rpg.completer import CommandCompleter

        completer = CommandCompleter()
        result = completer.complete("look", 0)
        assert result == "look "

    def test_complete_unknown_prefix(self):
        """Unknown prefix returns None."""
        from cli_rpg.completer import CommandCompleter

        completer = CommandCompleter()
        result = completer.complete("xyz", 0)
        assert result is None


class TestGoCompletion:
    """Tests for 'go' command argument completion - Spec requirement 2."""

    def test_complete_go_directions(self):
        """Spec req 2: 'go n' completes to 'go north'."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        completer = CommandCompleter()

        # Create game state with location that has north exit
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        location = Location(
            name="Test",
            description="A test location.",
            connections={"north": "Other", "south": "Another"},
        )
        world = {"Test": location}
        game_state = GameState(char, world, "Test")
        completer.set_game_state(game_state)

        # Mock readline buffer
        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "go n"
            mock_readline.get_begidx.return_value = 3
            mock_readline.get_endidx.return_value = 4

            result = completer.complete("n", 0)
            assert result == "north"

    def test_complete_go_all_directions(self):
        """'go <tab>' shows all available directions."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        completer = CommandCompleter()

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        location = Location(
            name="Test",
            description="A test location.",
            connections={"north": "Other", "east": "East Place"},
        )
        world = {"Test": location}
        game_state = GameState(char, world, "Test")
        completer.set_game_state(game_state)

        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "go "
            mock_readline.get_begidx.return_value = 3
            mock_readline.get_endidx.return_value = 3

            matches = []
            state = 0
            while True:
                result = completer.complete("", state)
                if result is None:
                    break
                matches.append(result)
                state += 1

            assert "north" in matches
            assert "east" in matches


class TestTalkCompletion:
    """Tests for 'talk' command argument completion - Spec requirement 2."""

    def test_complete_talk_npc_names(self):
        """Spec req 2: 'talk T' completes to NPC names."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.models.npc import NPC

        completer = CommandCompleter()

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        npc = NPC(name="Town Merchant", description="A friendly merchant", dialogue=["Hello!"])
        location = Location(
            name="Test", description="A test location.", npcs=[npc]
        )
        world = {"Test": location}
        game_state = GameState(char, world, "Test")
        completer.set_game_state(game_state)

        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "talk T"
            mock_readline.get_begidx.return_value = 5
            mock_readline.get_endidx.return_value = 6

            result = completer.complete("T", 0)
            assert result == "Town Merchant"

    def test_complete_empty_location_npcs(self):
        """'talk ' with no NPCs returns no completions."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        completer = CommandCompleter()

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        location = Location(name="Test", description="A test location.", npcs=[])
        world = {"Test": location}
        game_state = GameState(char, world, "Test")
        completer.set_game_state(game_state)

        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "talk "
            mock_readline.get_begidx.return_value = 5
            mock_readline.get_endidx.return_value = 5

            result = completer.complete("", 0)
            assert result is None


class TestEquipCompletion:
    """Tests for 'equip' command argument completion - Spec requirement 2."""

    def test_complete_equip_weapon_armor(self):
        """Spec req 2: 'equip' shows only WEAPON/ARMOR items."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.models.item import Item, ItemType

        completer = CommandCompleter()

        sword = Item("Sword", "A sharp sword", ItemType.WEAPON, damage_bonus=5)
        shield = Item("Shield", "A sturdy shield", ItemType.ARMOR, defense_bonus=3)
        potion = Item("Potion", "Heals you", ItemType.CONSUMABLE, heal_amount=20)

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.inventory.add_item(sword)
        char.inventory.add_item(shield)
        char.inventory.add_item(potion)
        location = Location(name="Test", description="A test location.")
        world = {"Test": location}
        game_state = GameState(char, world, "Test")
        completer.set_game_state(game_state)

        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "equip "
            mock_readline.get_begidx.return_value = 6
            mock_readline.get_endidx.return_value = 6

            matches = []
            state = 0
            while True:
                result = completer.complete("", state)
                if result is None:
                    break
                matches.append(result)
                state += 1

            assert "Sword" in matches
            assert "Shield" in matches
            assert "Potion" not in matches  # Consumables not equippable


class TestUseCompletion:
    """Tests for 'use' command argument completion - Spec requirement 2."""

    def test_complete_use_consumables(self):
        """Spec req 2: 'use' shows only CONSUMABLE items."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.models.item import Item, ItemType

        completer = CommandCompleter()

        sword = Item("Sword", "A sharp sword", ItemType.WEAPON, damage_bonus=5)
        potion = Item("Potion", "Heals you", ItemType.CONSUMABLE, heal_amount=20)

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        char.inventory.add_item(sword)
        char.inventory.add_item(potion)
        location = Location(name="Test", description="A test location.")
        world = {"Test": location}
        game_state = GameState(char, world, "Test")
        completer.set_game_state(game_state)

        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "use "
            mock_readline.get_begidx.return_value = 4
            mock_readline.get_endidx.return_value = 4

            matches = []
            state = 0
            while True:
                result = completer.complete("", state)
                if result is None:
                    break
                matches.append(result)
                state += 1

            assert "Potion" in matches
            assert "Sword" not in matches  # Weapons not usable


class TestBuyCompletion:
    """Tests for 'buy' command argument completion - Spec requirement 2."""

    def test_complete_buy_shop_items(self):
        """Spec req 2: 'buy' shows shop inventory items."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.models.shop import Shop, ShopItem

        completer = CommandCompleter()

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        location = Location(name="Test", description="A test location.")
        world = {"Test": location}
        game_state = GameState(char, world, "Test")

        # Set up a shop
        sword = Item("Iron Sword", "A sturdy sword", ItemType.WEAPON, damage_bonus=3)
        potion = Item("Health Potion", "Restores health", ItemType.CONSUMABLE, heal_amount=25)
        shop = Shop(
            name="Town Shop",
            inventory=[ShopItem(sword, 50), ShopItem(potion, 25)],
        )
        game_state.current_shop = shop

        completer.set_game_state(game_state)

        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "buy "
            mock_readline.get_begidx.return_value = 4
            mock_readline.get_endidx.return_value = 4

            matches = []
            state = 0
            while True:
                result = completer.complete("", state)
                if result is None:
                    break
                matches.append(result)
                state += 1

            assert "Iron Sword" in matches
            assert "Health Potion" in matches

    def test_complete_not_in_shop(self):
        """'buy ' when not in shop returns no completions."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        completer = CommandCompleter()

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        location = Location(name="Test", description="A test location.")
        world = {"Test": location}
        game_state = GameState(char, world, "Test")
        # No shop set
        completer.set_game_state(game_state)

        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "buy "
            mock_readline.get_begidx.return_value = 4
            mock_readline.get_endidx.return_value = 4

            result = completer.complete("", 0)
            assert result is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_complete_without_game_state(self):
        """Without game state, only command names are completed."""
        from cli_rpg.completer import CommandCompleter

        completer = CommandCompleter()
        # No game state set

        # Command completion should work
        result = completer.complete("lo", 0)
        assert result == "look "

        # Argument completion should return None (no context)
        with patch("cli_rpg.completer.readline") as mock_readline:
            mock_readline.get_line_buffer.return_value = "go "
            mock_readline.get_begidx.return_value = 3
            mock_readline.get_endidx.return_value = 3

            result = completer.complete("", 0)
            assert result is None

    def test_set_game_state(self):
        """Verify set_game_state method works."""
        from cli_rpg.completer import CommandCompleter
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        completer = CommandCompleter()
        assert completer._game_state is None

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        location = Location(name="Test", description="A test location.")
        world = {"Test": location}
        game_state = GameState(char, world, "Test")

        completer.set_game_state(game_state)
        assert completer._game_state is game_state

        completer.set_game_state(None)
        assert completer._game_state is None

    def test_module_level_completer_instance(self):
        """Verify module exposes a singleton completer instance."""
        from cli_rpg.completer import completer, CommandCompleter

        assert isinstance(completer, CommandCompleter)


class TestInputHandlerIntegration:
    """Tests for input_handler.py integration with completer."""

    def test_set_completer_context_function_exists(self):
        """Verify set_completer_context function is exported."""
        from cli_rpg.input_handler import set_completer_context

        assert callable(set_completer_context)

    def test_set_completer_context_updates_completer(self):
        """Verify set_completer_context updates the completer's game state."""
        from cli_rpg.input_handler import set_completer_context
        from cli_rpg.completer import completer
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        location = Location(name="Test", description="A test location.")
        world = {"Test": location}
        game_state = GameState(char, world, "Test")

        set_completer_context(game_state)
        assert completer._game_state is game_state

        set_completer_context(None)
        assert completer._game_state is None

    def test_init_readline_sets_up_completer(self):
        """Verify init_readline configures tab completion."""
        mock_readline = MagicMock()

        with patch.dict("sys.modules", {"readline": mock_readline}):
            with patch("cli_rpg.input_handler.get_history_path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = False
                mock_path.return_value = mock_path_obj

                import cli_rpg.input_handler as ih
                ih._readline_available = False
                ih.init_readline()

                # Verify completer was set
                mock_readline.set_completer.assert_called_once()
                # Verify tab binding was configured
                mock_readline.parse_and_bind.assert_called()
