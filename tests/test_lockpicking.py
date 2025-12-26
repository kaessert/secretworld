"""Tests for lockpicking and treasure chest mechanics.

Spec:
- Rogue-only `pick` command to attempt unlocking locked chests
- DEX-based success: `20% base + (DEX * 2%)`, capped at 80%
- Difficulty levels 1-5 modify chance by +20%/+10%/0%/-10%/-20%
- Lockpick consumable items (consumed on attempt, success or fail)
- `open` command for unlocked chests (anyone can use)
- Chests contain items, can only be opened once
"""

import pytest
from unittest.mock import patch

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType
from cli_rpg.game_state import GameState
from cli_rpg.world import create_default_world
from cli_rpg.main import handle_exploration_command


def create_test_game_state(character_class: CharacterClass, dexterity: int = 10) -> GameState:
    """Create a game state for testing with the specified class and dexterity."""
    character = Character(
        name="Test",
        strength=10,
        dexterity=dexterity,
        intelligence=10,
        character_class=character_class
    )
    world, starting_location = create_default_world()
    return GameState(character, world, starting_location)


def add_treasure_to_location(location: Location, treasure: dict) -> None:
    """Helper to add a treasure chest to a location."""
    if not hasattr(location, 'treasures'):
        location.treasures = []
    location.treasures.append(treasure)


def create_lockpick() -> Item:
    """Create a lockpick consumable item."""
    return Item(
        name="Lockpick",
        description="A thin metal tool for bypassing locks",
        item_type=ItemType.CONSUMABLE,
        heal_amount=0
    )


class TestRogueCanPickLockedChest:
    """Test 1: Rogue with lockpick succeeds (mock random)."""

    def test_rogue_can_pick_locked_chest_success(self):
        """Rogue with lockpick can successfully pick a locked chest."""
        game_state = create_test_game_state(CharacterClass.ROGUE)

        # Add lockpick to inventory
        lockpick = create_lockpick()
        game_state.current_character.inventory.add_item(lockpick)

        # Add a locked chest to current location
        location = game_state.get_current_location()
        treasure = {
            "name": "Old Chest",
            "description": "A dusty wooden chest",
            "locked": True,
            "difficulty": 3,  # Medium difficulty
            "opened": False,
            "items": [{"name": "Gold Coin", "description": "A shiny gold coin", "item_type": "misc"}],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        # Mock random to ensure success
        with patch('random.random', return_value=0.1):  # Low roll = success
            continue_game, message = handle_exploration_command(game_state, "pick", ["old", "chest"])

        assert continue_game is True
        assert "unlocked" in message.lower() or "success" in message.lower()
        # Chest should now be unlocked
        assert treasure["locked"] is False


class TestNonRogueCannotPick:
    """Test 2: Warrior/Mage get rejection message."""

    def test_warrior_cannot_pick_locked_chest(self):
        """Warrior cannot use pick command."""
        game_state = create_test_game_state(CharacterClass.WARRIOR)

        # Add lockpick to inventory
        lockpick = create_lockpick()
        game_state.current_character.inventory.add_item(lockpick)

        # Add a locked chest
        location = game_state.get_current_location()
        treasure = {
            "name": "Old Chest",
            "description": "A dusty wooden chest",
            "locked": True,
            "difficulty": 1,
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        continue_game, message = handle_exploration_command(game_state, "pick", ["old", "chest"])

        assert continue_game is True
        assert "rogue" in message.lower() or "only rogues" in message.lower()
        # Chest should still be locked
        assert treasure["locked"] is True

    def test_mage_cannot_pick_locked_chest(self):
        """Mage cannot use pick command."""
        game_state = create_test_game_state(CharacterClass.MAGE)

        # Add lockpick to inventory
        lockpick = create_lockpick()
        game_state.current_character.inventory.add_item(lockpick)

        # Add a locked chest
        location = game_state.get_current_location()
        treasure = {
            "name": "Old Chest",
            "description": "A dusty wooden chest",
            "locked": True,
            "difficulty": 1,
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        continue_game, message = handle_exploration_command(game_state, "pick", ["old", "chest"])

        assert continue_game is True
        assert "rogue" in message.lower() or "only rogues" in message.lower()


class TestLockpickConsumed:
    """Test 3: Lockpick removed from inventory on attempt."""

    def test_lockpick_consumed_on_success(self):
        """Lockpick is consumed even when pick succeeds."""
        game_state = create_test_game_state(CharacterClass.ROGUE)

        lockpick = create_lockpick()
        game_state.current_character.inventory.add_item(lockpick)

        # Verify lockpick is in inventory
        assert game_state.current_character.inventory.find_item_by_name("Lockpick") is not None

        location = game_state.get_current_location()
        treasure = {
            "name": "Old Chest",
            "description": "A dusty wooden chest",
            "locked": True,
            "difficulty": 1,  # Easy
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        with patch('random.random', return_value=0.1):  # Success
            handle_exploration_command(game_state, "pick", ["old", "chest"])

        # Lockpick should be consumed
        assert game_state.current_character.inventory.find_item_by_name("Lockpick") is None

    def test_lockpick_consumed_on_failure(self):
        """Lockpick is consumed even when pick fails."""
        game_state = create_test_game_state(CharacterClass.ROGUE, dexterity=5)  # Low DEX

        lockpick = create_lockpick()
        game_state.current_character.inventory.add_item(lockpick)

        location = game_state.get_current_location()
        treasure = {
            "name": "Old Chest",
            "description": "A dusty wooden chest",
            "locked": True,
            "difficulty": 5,  # Very hard
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        with patch('random.random', return_value=0.99):  # Fail
            handle_exploration_command(game_state, "pick", ["old", "chest"])

        # Lockpick should be consumed even on failure
        assert game_state.current_character.inventory.find_item_by_name("Lockpick") is None


class TestNoLockpickFails:
    """Test 4: Error if no lockpick in inventory."""

    def test_pick_fails_without_lockpick(self):
        """Rogue cannot pick without a lockpick."""
        game_state = create_test_game_state(CharacterClass.ROGUE)

        # No lockpick in inventory

        location = game_state.get_current_location()
        treasure = {
            "name": "Old Chest",
            "description": "A dusty wooden chest",
            "locked": True,
            "difficulty": 1,
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        continue_game, message = handle_exploration_command(game_state, "pick", ["old", "chest"])

        assert continue_game is True
        assert "lockpick" in message.lower()
        # Chest should still be locked
        assert treasure["locked"] is True


class TestDexAffectsSuccessChance:
    """Test 5: Higher DEX = higher success rate."""

    def test_high_dex_succeeds_at_higher_roll(self):
        """Character with high DEX succeeds where low DEX would fail."""
        # High DEX character (20 = 20% base + 40% DEX = 60% chance for difficulty 3)
        game_state_high = create_test_game_state(CharacterClass.ROGUE, dexterity=20)
        lockpick = create_lockpick()
        game_state_high.current_character.inventory.add_item(lockpick)

        location = game_state_high.get_current_location()
        treasure = {
            "name": "Old Chest",
            "description": "A dusty wooden chest",
            "locked": True,
            "difficulty": 3,
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        # Roll that succeeds for high DEX (60%) but fails for low DEX
        with patch('random.random', return_value=0.5):  # 50% roll
            handle_exploration_command(game_state_high, "pick", ["old", "chest"])

        # High DEX should succeed
        assert treasure["locked"] is False


class TestDifficultyModifiesChance:
    """Test 6: Difficulty 1-5 adjustments (+20%/+10%/0%/-10%/-20%)."""

    def test_difficulty_1_is_easiest(self):
        """Difficulty 1 gives +20% bonus (easiest)."""
        game_state = create_test_game_state(CharacterClass.ROGUE, dexterity=10)
        # Base DEX 10 + class bonus 3 = 13 DEX
        # Base 20% + 26% DEX + 20% difficulty 1 bonus = 66%

        lockpick = create_lockpick()
        game_state.current_character.inventory.add_item(lockpick)

        location = game_state.get_current_location()
        treasure = {
            "name": "Easy Chest",
            "description": "A simple chest",
            "locked": True,
            "difficulty": 1,
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        # Roll that succeeds with +20% bonus
        with patch('random.random', return_value=0.6):
            handle_exploration_command(game_state, "pick", ["easy", "chest"])

        assert treasure["locked"] is False

    def test_difficulty_5_is_hardest(self):
        """Difficulty 5 gives -20% penalty (hardest)."""
        game_state = create_test_game_state(CharacterClass.ROGUE, dexterity=10)
        # Base DEX 10 + class bonus 3 = 13 DEX
        # Base 20% + 26% DEX - 20% difficulty 5 penalty = 26%

        lockpick = create_lockpick()
        game_state.current_character.inventory.add_item(lockpick)

        location = game_state.get_current_location()
        treasure = {
            "name": "Hard Chest",
            "description": "A reinforced chest",
            "locked": True,
            "difficulty": 5,
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        # Roll that would succeed at difficulty 1 (66%) but fails at difficulty 5 (26%)
        with patch('random.random', return_value=0.4):
            handle_exploration_command(game_state, "pick", ["hard", "chest"])

        # Should fail at difficulty 5
        assert treasure["locked"] is True


class TestOpenUnlockedChest:
    """Test 7: Anyone can open unlocked chest."""

    def test_warrior_can_open_unlocked_chest(self):
        """Warrior can open an already-unlocked chest."""
        game_state = create_test_game_state(CharacterClass.WARRIOR)

        location = game_state.get_current_location()
        treasure = {
            "name": "Open Chest",
            "description": "An unlocked chest",
            "locked": False,  # Already unlocked
            "difficulty": 1,
            "opened": False,
            "items": [{"name": "Gold Coin", "description": "Shiny", "item_type": "misc"}],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        continue_game, message = handle_exploration_command(game_state, "open", ["open", "chest"])

        assert continue_game is True
        assert treasure["opened"] is True

    def test_mage_can_open_unlocked_chest(self):
        """Mage can open an already-unlocked chest."""
        game_state = create_test_game_state(CharacterClass.MAGE)

        location = game_state.get_current_location()
        treasure = {
            "name": "Open Chest",
            "description": "An unlocked chest",
            "locked": False,
            "difficulty": 1,
            "opened": False,
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        continue_game, message = handle_exploration_command(game_state, "open", ["open", "chest"])

        assert continue_game is True
        assert treasure["opened"] is True


class TestChestItemsAddedToInventory:
    """Test 8: Items transfer on open."""

    def test_items_added_to_inventory_on_open(self):
        """Opening chest adds items to player inventory."""
        game_state = create_test_game_state(CharacterClass.WARRIOR)

        location = game_state.get_current_location()
        treasure = {
            "name": "Loot Chest",
            "description": "A chest full of treasure",
            "locked": False,
            "difficulty": 1,
            "opened": False,
            "items": [
                {"name": "Ruby", "description": "A precious gem", "item_type": "misc"},
                {"name": "Dagger", "description": "A sharp blade", "item_type": "weapon", "damage_bonus": 3}
            ],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        # Verify items not in inventory
        assert game_state.current_character.inventory.find_item_by_name("Ruby") is None
        assert game_state.current_character.inventory.find_item_by_name("Dagger") is None

        handle_exploration_command(game_state, "open", ["loot", "chest"])

        # Items should now be in inventory
        assert game_state.current_character.inventory.find_item_by_name("Ruby") is not None
        assert game_state.current_character.inventory.find_item_by_name("Dagger") is not None


class TestChestCannotReopen:
    """Test 9: Already-opened chest returns message."""

    def test_cannot_reopen_chest(self):
        """Opening an already-opened chest gives appropriate message."""
        game_state = create_test_game_state(CharacterClass.WARRIOR)

        location = game_state.get_current_location()
        treasure = {
            "name": "Empty Chest",
            "description": "An opened chest",
            "locked": False,
            "difficulty": 1,
            "opened": True,  # Already opened
            "items": [],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        continue_game, message = handle_exploration_command(game_state, "open", ["empty", "chest"])

        assert continue_game is True
        assert "already" in message.lower() or "empty" in message.lower()


class TestChestPersistence:
    """Test 10: Opened state survives save/load."""

    def test_chest_state_persists_in_location(self):
        """Treasure chest opened state is saved in location data."""
        game_state = create_test_game_state(CharacterClass.WARRIOR)

        location = game_state.get_current_location()
        treasure = {
            "name": "Test Chest",
            "description": "A test chest",
            "locked": False,
            "difficulty": 1,
            "opened": False,
            "items": [{"name": "Gold", "description": "Gold", "item_type": "misc"}],
            "requires_key": None
        }
        add_treasure_to_location(location, treasure)

        # Open the chest
        handle_exploration_command(game_state, "open", ["test", "chest"])

        # Serialize and deserialize game state
        state_dict = game_state.to_dict()
        restored_game_state = GameState.from_dict(state_dict)

        # Get restored location and check treasure state
        restored_location = restored_game_state.get_current_location()
        assert hasattr(restored_location, 'treasures')
        assert len(restored_location.treasures) == 1
        assert restored_location.treasures[0]["opened"] is True
