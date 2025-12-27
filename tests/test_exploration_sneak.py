"""Tests for Rogue exploration sneak command.

Spec: Rogue's sneak command enables sneaking mode during exploration:
- Command: sneak - Rogue-only exploration action
- Effect: Sets is_sneaking=True on GameState for next move
- Benefit: Reduces random encounter chance (success based on DEX, armor, light)
- Cost: 10 stamina
- Formula: 50% + (DEX * 2%) - (armor defense * 5%) - (15% if lit), capped 10-90%
"""
import pytest
from unittest.mock import patch
import random

from cli_rpg.game_state import GameState, calculate_sneak_success_chance
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.models.inventory import Inventory
from cli_rpg.models.item import Item, ItemType


def create_test_character(
    character_class: CharacterClass = CharacterClass.ROGUE,
    dexterity: int = 10,
    stamina: int = 100,
    light_remaining: int = 0,
    armor_defense: int = 0,
) -> Character:
    """Create a test character with specified attributes."""
    char = Character(
        name="TestHero",
        character_class=character_class,
        strength=10,
        intelligence=10,
        dexterity=dexterity,
        charisma=10,
        perception=10,
    )
    char.stamina = stamina
    char.light_remaining = light_remaining

    # Equip armor if defense bonus specified
    if armor_defense > 0:
        armor = Item(
            name="Test Armor",
            description="Test armor",
            item_type=ItemType.ARMOR,
            defense_bonus=armor_defense,
        )
        char.inventory.items.append(armor)
        char.inventory.equip(armor)

    return char


def create_test_world() -> dict[str, Location]:
    """Create a minimal test world with coordinates."""
    town = Location(
        name="Town Square",
        description="A peaceful town square",
        category="town",
        coordinates=(0, 0),
        is_safe_zone=True,
    )
    forest = Location(
        name="Dark Forest",
        description="A dark and dangerous forest",
        category="forest",
        coordinates=(0, 1),
    )
    woods = Location(
        name="Deep Woods",
        description="Deep in the forest",
        category="forest",
        coordinates=(0, 2),
    )
    return {"Town Square": town, "Dark Forest": forest, "Deep Woods": woods}


def create_test_game_state(
    character: Character = None,
    starting_location: str = "Dark Forest",
) -> GameState:
    """Create a test game state."""
    if character is None:
        character = create_test_character()
    world = create_test_world()
    return GameState(character, world, starting_location)


class TestSneakExplorationRogueOnly:
    """Test that sneak command is Rogue-only during exploration."""

    def test_sneak_exploration_rogue_success(self):
        """Spec: Rogue can use sneak, sets is_sneaking=True."""
        from cli_rpg.main import handle_exploration_command

        char = create_test_character(character_class=CharacterClass.ROGUE)
        game_state = create_test_game_state(character=char)

        # Verify initial state
        assert not game_state.is_sneaking

        # Execute sneak command
        continue_game, message = handle_exploration_command(game_state, "sneak", [])

        # Verify sneaking mode activated
        assert game_state.is_sneaking is True
        assert "shadow" in message.lower() or "sneak" in message.lower()
        assert "%" in message  # Should show success chance

    def test_sneak_exploration_non_rogue_fails(self):
        """Spec: Non-Rogues (Warrior, Mage, etc.) get error message."""
        from cli_rpg.main import handle_exploration_command

        for char_class in [CharacterClass.WARRIOR, CharacterClass.MAGE, CharacterClass.RANGER, CharacterClass.CLERIC]:
            char = create_test_character(character_class=char_class)
            game_state = create_test_game_state(character=char)

            continue_game, message = handle_exploration_command(game_state, "sneak", [])

            # Should fail and not set sneaking
            assert game_state.is_sneaking is False
            assert "only rogues" in message.lower() or "rogue" in message.lower()


class TestSneakExplorationStaminaCost:
    """Test stamina cost for exploration sneak."""

    def test_sneak_costs_10_stamina(self):
        """Spec: Sneak costs 10 stamina."""
        from cli_rpg.main import handle_exploration_command

        char = create_test_character(stamina=50)
        game_state = create_test_game_state(character=char)

        handle_exploration_command(game_state, "sneak", [])

        # Stamina should be reduced by 10
        assert char.stamina == 40

    def test_sneak_fails_without_stamina(self):
        """Spec: Error when stamina < 10."""
        from cli_rpg.main import handle_exploration_command

        char = create_test_character(stamina=5)
        game_state = create_test_game_state(character=char)

        continue_game, message = handle_exploration_command(game_state, "sneak", [])

        # Should fail due to insufficient stamina
        assert game_state.is_sneaking is False
        assert "stamina" in message.lower()
        # Stamina should not be consumed on failure
        assert char.stamina == 5


class TestSneakClearedAfterMove:
    """Test that sneaking mode is cleared after movement."""

    def test_sneak_cleared_after_successful_move(self):
        """Spec: is_sneaking reset to False after successful move."""
        from cli_rpg.main import handle_exploration_command

        char = create_test_character()
        game_state = create_test_game_state(character=char, starting_location="Dark Forest")

        # Activate sneak
        handle_exploration_command(game_state, "sneak", [])
        assert game_state.is_sneaking is True

        # Move (mock random to avoid combat encounters)
        with patch('cli_rpg.random_encounters.random.random', return_value=1.0):
            with patch('cli_rpg.game_state.random.random', return_value=1.0):
                game_state.move("north")

        # Sneaking should be cleared after move
        assert game_state.is_sneaking is False

    def test_sneak_cleared_after_blocked_move(self):
        """Spec: is_sneaking reset even on failed move."""
        from cli_rpg.main import handle_exploration_command
        from unittest.mock import MagicMock

        char = create_test_character()
        world = create_test_world()
        game_state = GameState(char, world, "Dark Forest")

        # Create a mock chunk_manager that returns impassable terrain (water) east
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.get_tile_at.return_value = "water"
        game_state.chunk_manager = mock_chunk_manager

        # Activate sneak
        handle_exploration_command(game_state, "sneak", [])
        assert game_state.is_sneaking is True

        # Try to move in blocked direction (east goes to water which is impassable)
        success, _ = game_state.move("east")

        # Move should fail but sneaking should be cleared
        assert success is False
        assert game_state.is_sneaking is False


class TestSneakEncounterAvoidance:
    """Test sneak effect on random encounter avoidance."""

    def test_sneak_high_dex_avoids_encounter(self):
        """Spec: High DEX Rogue avoids encounter when sneaking."""
        from cli_rpg.random_encounters import check_for_random_encounter

        # High DEX character - Rogue gets +3 DEX from class, so DEX 17 becomes 20 (90% capped)
        char = create_test_character(dexterity=17)
        game_state = create_test_game_state(character=char, starting_location="Dark Forest")
        game_state.is_sneaking = True

        # Mock random to trigger encounter check, but sneak should succeed
        with patch('cli_rpg.random_encounters.random.random') as mock_random:
            # First call: sneak success check (0.5 * 100 = 50 < 90% = success)
            mock_random.return_value = 0.5

            result = check_for_random_encounter(game_state)

        # Should have avoided encounter due to successful sneak
        # (is_sneaking is cleared by check_for_random_encounter)
        assert game_state.is_sneaking is False
        assert result is None  # No encounter

    def test_sneak_low_dex_may_encounter(self):
        """Spec: Low DEX Rogue can still trigger encounter."""
        from cli_rpg.random_encounters import check_for_random_encounter

        # Low DEX character (5 + 3 class bonus = 8) gives 66% success
        # Formula: 50 + (8 * 2) = 66%
        char = create_test_character(dexterity=5)
        game_state = create_test_game_state(character=char, starting_location="Dark Forest")
        game_state.is_sneaking = True

        # Mock random to fail sneak check then trigger encounter
        with patch('cli_rpg.random_encounters.random.random') as mock_random:
            # Call order:
            # 1. Sneak check: 0.7 * 100 = 70 >= 66% = fail
            # 2. Encounter roll: 0.0 <= 0.15 = would trigger
            # 3. _select_encounter_type: 0.0 = hostile (< 0.60)
            mock_random.side_effect = [0.7, 0.0, 0.0]

            result = check_for_random_encounter(game_state)

        # Sneak failed, encounter should trigger
        assert game_state.is_sneaking is False
        assert result is not None  # Encounter happened

    def test_sneak_heavy_armor_penalty(self):
        """Spec: Armor reduces sneak success."""
        # Character with high armor (defense 8 = -40% penalty)
        # Rogue gets +3 DEX, so base 10 becomes 13
        char = create_test_character(dexterity=10, armor_defense=8)

        success = calculate_sneak_success_chance(char)

        # Base 50% + (13 DEX * 2% = 26%) - (8 defense * 5% = 40%) = 36%
        assert success == 36

    def test_sneak_light_source_penalty(self):
        """Spec: Light reduces sneak success."""
        # Rogue gets +3 DEX, so base 10 becomes 13
        char = create_test_character(dexterity=10, light_remaining=5)

        success = calculate_sneak_success_chance(char)

        # Base 50% + (13 DEX * 2% = 26%) - 15% light penalty = 61%
        assert success == 61


class TestSneakSuccessFormula:
    """Test the sneak success formula capping."""

    def test_sneak_success_capped_at_90(self):
        """Spec: Even max DEX caps at 90%."""
        # Max DEX is 20, Rogue gets +3 = 23 effective DEX
        char = create_test_character(dexterity=20, armor_defense=0, light_remaining=0)

        success = calculate_sneak_success_chance(char)

        # Base 50% + (23 * 2% = 46%) = 96%, capped to 90%
        assert success == 90

    def test_sneak_success_minimum_10(self):
        """Spec: Even worst case has 10% floor."""
        # Low DEX (1 + 3 class = 4) with heavy armor and light
        char = create_test_character(dexterity=1, armor_defense=10, light_remaining=5)

        success = calculate_sneak_success_chance(char)

        # Base 50% + (4 * 2% = 8%) - (10 * 5% = 50%) - 15% = -7%, floored to 10%
        assert success == 10


class TestSneakNotInCombat:
    """Test that exploration sneak is separate from combat sneak."""

    def test_sneak_exploration_separate_from_combat(self):
        """Spec: Combat sneak unaffected by exploration sneak."""
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy

        char = create_test_character()
        game_state = create_test_game_state(character=char)

        # Create a mock combat
        enemy = Enemy(
            name="Test Goblin",
            health=20,
            max_health=20,
            attack_power=5,
            defense=1,
            xp_reward=10,
        )
        combat = CombatEncounter(char, enemies=[enemy])
        game_state.current_combat = combat

        # Combat sneak should work independently
        victory, message = combat.player_sneak()

        # Combat sneak should not set is_sneaking (that's exploration-only)
        # Combat sneak operates on combat.player.is_hidden
        assert game_state.is_sneaking is False
        # Combat sneak for Rogue should succeed
        assert "sneak" in message.lower() or "shadow" in message.lower()
