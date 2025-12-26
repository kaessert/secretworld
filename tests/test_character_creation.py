"""Tests for character creation functionality."""
from unittest.mock import patch
from cli_rpg.character_creation import (
    get_valid_name,
    get_allocation_method,
    get_manual_stats,
    generate_random_stats,
    display_character_summary,
    confirm_creation,
    create_character,
    get_theme_selection,
    get_class_selection,
)
from cli_rpg.models.character import Character, CharacterClass


class TestGetValidName:
    """Test name input validation."""
    
    @patch('builtins.input', return_value="Hero")
    def test_get_valid_name_accepts_valid_input(self, mock_input):
        """Test: Accept valid name (spec requirement)"""
        name = get_valid_name()
        assert name == "Hero"
    
    @patch('builtins.input', side_effect=["H", "Hero"])
    def test_name_retry_on_too_short(self, mock_input):
        """Test: Retry prompt on name too short (spec requirement)"""
        name = get_valid_name()
        assert name == "Hero"
        assert mock_input.call_count == 2
    
    @patch('builtins.input', side_effect=["A" * 31, "Hero"])
    def test_name_retry_on_too_long(self, mock_input):
        """Test: Retry prompt on name too long (spec requirement)"""
        name = get_valid_name()
        assert name == "Hero"
        assert mock_input.call_count == 2
    
    @patch('builtins.input', side_effect=["", "Hero"])
    def test_name_retry_on_empty(self, mock_input):
        """Test: Retry prompt on empty name (spec requirement)"""
        name = get_valid_name()
        assert name == "Hero"
        assert mock_input.call_count == 2
    
    @patch('builtins.input', return_value="cancel")
    def test_name_cancel(self, mock_input):
        """Test: Return None when user cancels (spec requirement)"""
        name = get_valid_name()
        assert name is None


class TestGetAllocationMethod:
    """Test stat allocation method selection."""
    
    @patch('builtins.input', return_value="1")
    def test_allocation_method_manual_number(self, mock_input):
        """Test: Accept '1' for manual (spec requirement)"""
        method = get_allocation_method()
        assert method == "manual"
    
    @patch('builtins.input', return_value="manual")
    def test_allocation_method_manual_word(self, mock_input):
        """Test: Accept 'manual' for manual (spec requirement)"""
        method = get_allocation_method()
        assert method == "manual"
    
    @patch('builtins.input', return_value="2")
    def test_allocation_method_random_number(self, mock_input):
        """Test: Accept '2' for random (spec requirement)"""
        method = get_allocation_method()
        assert method == "random"
    
    @patch('builtins.input', return_value="random")
    def test_allocation_method_random_word(self, mock_input):
        """Test: Accept 'random' for random (spec requirement)"""
        method = get_allocation_method()
        assert method == "random"
    
    @patch('builtins.input', side_effect=["3", "1"])
    def test_allocation_method_retry_on_invalid(self, mock_input):
        """Test: Retry on invalid allocation method (spec requirement)"""
        method = get_allocation_method()
        assert method == "manual"
        assert mock_input.call_count == 2
    
    @patch('builtins.input', return_value="cancel")
    def test_allocation_method_cancel(self, mock_input):
        """Test: Return None when user cancels (spec requirement)"""
        method = get_allocation_method()
        assert method is None


class TestGetManualStats:
    """Test manual stat entry."""
    
    @patch('builtins.input', side_effect=["10", "12", "8", "14"])
    def test_manual_stats_valid_input(self, mock_input):
        """Test: Accept valid manual stats (spec requirement)"""
        stats = get_manual_stats()
        assert stats == {
            "strength": 10,
            "dexterity": 12,
            "intelligence": 8,
            "charisma": 14,
        }
    
    @patch('builtins.input', side_effect=["0", "10", "12", "8", "10"])
    def test_manual_stats_retry_on_too_low(self, mock_input):
        """Test: Retry prompt on stat too low (spec requirement)"""
        stats = get_manual_stats()
        assert stats["strength"] == 10
        assert mock_input.call_count == 5
    
    @patch('builtins.input', side_effect=["21", "10", "12", "8", "10"])
    def test_manual_stats_retry_on_too_high(self, mock_input):
        """Test: Retry prompt on stat too high (spec requirement)"""
        stats = get_manual_stats()
        assert stats["strength"] == 10
        assert mock_input.call_count == 5
    
    @patch('builtins.input', side_effect=["abc", "10", "12", "8", "10"])
    def test_manual_stats_retry_on_non_numeric(self, mock_input):
        """Test: Retry prompt on non-numeric input (spec requirement)"""
        stats = get_manual_stats()
        assert stats["strength"] == 10
        assert mock_input.call_count == 5
    
    @patch('builtins.input', return_value="cancel")
    def test_manual_stats_cancel(self, mock_input):
        """Test: Return None when user cancels (spec requirement)"""
        stats = get_manual_stats()
        assert stats is None


class TestGenerateRandomStats:
    """Test random stat generation."""
    
    def test_random_stats_in_range(self):
        """Test: Verify random stats are 8-15 (spec requirement)"""
        for _ in range(20):  # Test multiple times for randomness
            stats = generate_random_stats()
            assert 8 <= stats["strength"] <= 15
            assert 8 <= stats["dexterity"] <= 15
            assert 8 <= stats["intelligence"] <= 15
            assert 8 <= stats["charisma"] <= 15

    def test_random_stats_has_all_stats(self):
        """Test: Verify all required stats are present"""
        stats = generate_random_stats()
        assert "strength" in stats
        assert "dexterity" in stats
        assert "intelligence" in stats
        assert "charisma" in stats


class TestDisplayCharacterSummary:
    """Test character summary display."""
    
    @patch('builtins.print')
    def test_display_character_summary(self, mock_print):
        """Test: Display summary is called (spec requirement)"""
        character = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        display_character_summary(character)
        # Verify print was called
        assert mock_print.call_count > 0
        # Verify character info was printed
        calls_str = ' '.join([str(call) for call in mock_print.call_args_list])
        assert "Hero" in calls_str


class TestConfirmCreation:
    """Test creation confirmation."""
    
    @patch('builtins.input', return_value="yes")
    def test_confirm_creation_yes(self, mock_input):
        """Test: Return True for 'yes' (spec requirement)"""
        result = confirm_creation()
        assert result is True
    
    @patch('builtins.input', return_value="y")
    def test_confirm_creation_y(self, mock_input):
        """Test: Return True for 'y' (spec requirement)"""
        result = confirm_creation()
        assert result is True
    
    @patch('builtins.input', return_value="no")
    def test_confirm_creation_no(self, mock_input):
        """Test: Return False for 'no' (spec requirement)"""
        result = confirm_creation()
        assert result is False
    
    @patch('builtins.input', return_value="n")
    def test_confirm_creation_n(self, mock_input):
        """Test: Return False for 'n' (spec requirement)"""
        result = confirm_creation()
        assert result is False
    
    @patch('builtins.input', side_effect=["maybe", "yes"])
    def test_confirm_creation_retry_on_invalid(self, mock_input):
        """Test: Retry on invalid input (spec requirement)"""
        result = confirm_creation()
        assert result is True
        assert mock_input.call_count == 2


class TestCreateCharacter:
    """Test full character creation flow (updated for class selection)."""

    @patch('builtins.input', side_effect=["Hero", "1", "1", "10", "12", "8", "10", "yes"])
    def test_create_character_manual_valid_input(self, mock_input):
        """Test: Complete manual creation with valid inputs (spec requirement)"""
        # Flow: name -> class -> method -> stats (str, dex, int, cha) -> confirm
        character = create_character()
        assert character is not None
        assert character.name == "Hero"
        assert character.character_class == CharacterClass.WARRIOR
        # Stats include Warrior bonuses: STR +3, DEX +1, INT 0, CHA 0
        assert character.strength == 13  # 10 + 3
        assert character.dexterity == 13  # 12 + 1
        assert character.intelligence == 8  # 8 + 0
        assert character.charisma == 10  # 10 + 0

    @patch('builtins.input', side_effect=["Hero", "2", "2", "yes"])
    def test_create_character_random_generation(self, mock_input):
        """Test: Complete random stat generation (spec requirement)"""
        # Flow: name -> class (Mage) -> method (random) -> confirm
        character = create_character()
        assert character is not None
        assert character.name == "Hero"
        assert character.character_class == CharacterClass.MAGE
        # Random stats are 8-15, Mage adds DEX +1, INT +3
        assert character.dexterity >= 9  # min 8 + 1
        assert character.intelligence >= 11  # min 8 + 3

    @patch('builtins.input', side_effect=["H", "Hero", "1", "1", "10", "12", "8", "10", "yes"])
    def test_create_character_name_retry_on_invalid(self, mock_input):
        """Test: Retry prompt on invalid name (spec requirement)"""
        character = create_character()
        assert character is not None
        assert character.name == "Hero"

    @patch('builtins.input', side_effect=["Hero", "1", "1", "0", "10", "12", "8", "10", "yes"])
    def test_create_character_stat_retry_on_invalid(self, mock_input):
        """Test: Retry prompt on invalid stat value (spec requirement)"""
        # Flow: name -> class -> method -> invalid str -> valid str -> dex -> int -> cha -> confirm
        character = create_character()
        assert character is not None
        # Warrior bonuses: STR +3
        assert character.strength == 13  # 10 + 3

    @patch('builtins.input', return_value="cancel")
    def test_create_character_cancelled_by_user_at_name(self, mock_input):
        """Test: Return None when user cancels at name (spec requirement)"""
        character = create_character()
        assert character is None

    @patch('builtins.input', side_effect=["Hero", "cancel"])
    def test_create_character_cancelled_by_user_at_class(self, mock_input):
        """Test: Return None when user cancels at class (spec requirement)"""
        character = create_character()
        assert character is None

    @patch('builtins.input', side_effect=["Hero", "1", "cancel"])
    def test_create_character_cancelled_by_user_at_method(self, mock_input):
        """Test: Return None when user cancels at method (spec requirement)"""
        character = create_character()
        assert character is None

    @patch('builtins.input', side_effect=["Hero", "1", "1", "cancel"])
    def test_create_character_cancelled_by_user_at_stats(self, mock_input):
        """Test: Return None when user cancels at stats (spec requirement)"""
        character = create_character()
        assert character is None

    @patch('builtins.input', side_effect=["Hero", "1", "1", "10", "12", "8", "10", "no"])
    def test_create_character_cancelled_by_user_at_confirm(self, mock_input):
        """Test: Return None when user cancels at confirm (spec requirement)"""
        character = create_character()
        assert character is None

    @patch('builtins.input', side_effect=["Hero", "1", "3", "2", "yes"])
    def test_create_character_invalid_allocation_method(self, mock_input):
        """Test: Retry on invalid allocation method (spec requirement)"""
        # Flow: name -> class -> invalid method -> valid method (random) -> confirm
        character = create_character()
        assert character is not None
        # Warrior with random stats (8-15 base + bonuses)
        assert character.strength >= 11  # min 8 + 3


class TestGetThemeSelection:
    """Test theme selection functionality for AI world generation."""
    
    @patch('builtins.input', return_value="1")
    def test_theme_selection_fantasy_by_number(self, mock_input):
        """Test: Accept '1' for fantasy theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "fantasy"
    
    @patch('builtins.input', return_value="2")
    def test_theme_selection_scifi_by_number(self, mock_input):
        """Test: Accept '2' for sci-fi theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "sci-fi"
    
    @patch('builtins.input', return_value="3")
    def test_theme_selection_cyberpunk_by_number(self, mock_input):
        """Test: Accept '3' for cyberpunk theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "cyberpunk"
    
    @patch('builtins.input', return_value="4")
    def test_theme_selection_horror_by_number(self, mock_input):
        """Test: Accept '4' for horror theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "horror"
    
    @patch('builtins.input', return_value="5")
    def test_theme_selection_steampunk_by_number(self, mock_input):
        """Test: Accept '5' for steampunk theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "steampunk"
    
    @patch('builtins.input', return_value="fantasy")
    def test_theme_selection_fantasy_by_word(self, mock_input):
        """Test: Accept 'fantasy' for fantasy theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "fantasy"
    
    @patch('builtins.input', return_value="sci-fi")
    def test_theme_selection_scifi_by_word(self, mock_input):
        """Test: Accept 'sci-fi' for sci-fi theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "sci-fi"
    
    @patch('builtins.input', return_value="scifi")
    def test_theme_selection_scifi_alternate_spelling(self, mock_input):
        """Test: Accept 'scifi' for sci-fi theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "sci-fi"
    
    @patch('builtins.input', return_value="")
    def test_theme_selection_default_on_empty(self, mock_input):
        """Test: Default to 'fantasy' when empty input (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "fantasy"
    
    @patch('builtins.input', return_value="invalid")
    def test_theme_selection_default_on_invalid(self, mock_input):
        """Test: Default to 'fantasy' on invalid input (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "fantasy"
    
    @patch('builtins.input', side_effect=["6", "post-apocalyptic"])
    def test_theme_selection_custom(self, mock_input):
        """Test: Accept custom theme input (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "post-apocalyptic"
    
    @patch('builtins.input', side_effect=["custom", "noir"])
    def test_theme_selection_custom_by_word(self, mock_input):
        """Test: Accept 'custom' keyword for custom theme (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "noir"
    
    @patch('builtins.input', side_effect=["6", ""])
    def test_theme_selection_custom_empty_defaults_to_fantasy(self, mock_input):
        """Test: Default to 'fantasy' when custom theme is empty (spec requirement)"""
        theme = get_theme_selection()
        assert theme == "fantasy"


class TestGetClassSelection:
    """Spec: get_class_selection() returns valid class from input (1-5 or name)."""

    @patch('builtins.input', return_value="1")
    def test_class_selection_warrior_by_number(self, mock_input):
        """Spec: Accept '1' for Warrior class."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.WARRIOR

    @patch('builtins.input', return_value="2")
    def test_class_selection_mage_by_number(self, mock_input):
        """Spec: Accept '2' for Mage class."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.MAGE

    @patch('builtins.input', return_value="3")
    def test_class_selection_rogue_by_number(self, mock_input):
        """Spec: Accept '3' for Rogue class."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.ROGUE

    @patch('builtins.input', return_value="4")
    def test_class_selection_ranger_by_number(self, mock_input):
        """Spec: Accept '4' for Ranger class."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.RANGER

    @patch('builtins.input', return_value="5")
    def test_class_selection_cleric_by_number(self, mock_input):
        """Spec: Accept '5' for Cleric class."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.CLERIC

    @patch('builtins.input', return_value="warrior")
    def test_class_selection_warrior_by_name(self, mock_input):
        """Spec: Accept 'warrior' for Warrior class (case-insensitive)."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.WARRIOR

    @patch('builtins.input', return_value="Mage")
    def test_class_selection_mage_by_name(self, mock_input):
        """Spec: Accept 'Mage' for Mage class."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.MAGE

    @patch('builtins.input', return_value="ROGUE")
    def test_class_selection_rogue_by_name_uppercase(self, mock_input):
        """Spec: Accept 'ROGUE' for Rogue class (case-insensitive)."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.ROGUE

    @patch('builtins.input', side_effect=["invalid", "1"])
    def test_class_selection_retry_on_invalid(self, mock_input):
        """Spec: Retry on invalid class input."""
        char_class = get_class_selection()
        assert char_class == CharacterClass.WARRIOR
        assert mock_input.call_count == 2

    @patch('builtins.input', return_value="cancel")
    def test_class_selection_cancel(self, mock_input):
        """Spec: Return None when user cancels."""
        char_class = get_class_selection()
        assert char_class is None


class TestCreateCharacterWithClass:
    """Spec: create_character() flow includes class selection step."""

    @patch('builtins.input', side_effect=["Hero", "1", "1", "10", "12", "8", "10", "yes"])
    def test_create_character_with_warrior_class(self, mock_input):
        """Spec: Character creation includes class selection after name."""
        character = create_character()
        assert character is not None
        assert character.name == "Hero"
        assert character.character_class == CharacterClass.WARRIOR
        # Warrior bonuses: STR +3, DEX +1, INT 0, CHA 0
        assert character.strength == 13  # 10 + 3
        assert character.dexterity == 13  # 12 + 1
        assert character.intelligence == 8  # 8 + 0
        assert character.charisma == 10  # 10 + 0

    @patch('builtins.input', side_effect=["Hero", "mage", "2", "yes"])
    def test_create_character_with_mage_class_random_stats(self, mock_input):
        """Spec: Character creation works with class + random stats."""
        character = create_character()
        assert character is not None
        assert character.character_class == CharacterClass.MAGE
        # Mage bonuses: STR 0, DEX +1, INT +3
        # Random stats are 8-15, so check bonuses are applied
        assert character.intelligence >= 11  # min 8 + 3

    @patch('builtins.input', side_effect=["Hero", "cancel"])
    def test_create_character_cancelled_at_class(self, mock_input):
        """Spec: Return None when user cancels at class selection."""
        character = create_character()
        assert character is None
