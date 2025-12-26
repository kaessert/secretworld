"""Tests for main menu integration."""
from unittest.mock import patch
from cli_rpg.main import show_main_menu, main


class TestShowMainMenu:
    """Test main menu display."""
    
    @patch('builtins.input', return_value="1")
    def test_show_main_menu_returns_choice(self, mock_input):
        """Test: Main menu returns user choice"""
        choice = show_main_menu()
        assert choice == "1"
    
    @patch('builtins.input', return_value="3")
    def test_show_main_menu_exit(self, mock_input):
        """Test: Main menu accepts exit choice"""
        choice = show_main_menu()
        assert choice == "3"


class TestMainFunction:
    """Test main function integration."""
    
    @patch('builtins.input', side_effect=["1", "Hero", "1", "1", "10", "12", "8", "10", "10", "yes", "quit", "n", "3"])
    def test_main_create_character_then_exit(self, mock_input):
        """Test: Main menu character creation integration (spec requirement)
        Flow: menu(1) -> name -> class(1) -> method(1) -> stats (str, dex, int, cha, per) -> confirm -> quit -> no save -> exit
        """
        result = main(args=[])
        assert result == 0

    @patch('cli_rpg.main.list_saves', return_value=[])  # Ensure no saves exist for this test
    @patch('builtins.input', side_effect=["2", "3"])
    def test_main_load_character_no_saves(self, mock_input, mock_list_saves):
        """Test: Load character shows message when no saves exist"""
        result = main(args=[])
        assert result == 0

    @patch('builtins.input', side_effect=["3"])
    def test_main_exit_immediately(self, mock_input):
        """Test: Can exit immediately from main menu"""
        result = main(args=[])
        assert result == 0

    @patch('builtins.input', side_effect=["99", "3"])
    def test_main_invalid_choice(self, mock_input):
        """Test: Invalid menu choice is handled gracefully"""
        result = main(args=[])
        assert result == 0

    @patch('builtins.input', side_effect=["1", "cancel", "3"])
    def test_main_cancelled_character_creation(self, mock_input):
        """Test: Cancelled character creation returns to menu"""
        result = main(args=[])
        assert result == 0
