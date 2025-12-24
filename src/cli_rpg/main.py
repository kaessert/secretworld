"""Main entry point for CLI RPG."""
from typing import Optional
from cli_rpg.character_creation import create_character
from cli_rpg.models.character import Character


def show_main_menu() -> str:
    """Display main menu and get user choice.
    
    Returns:
        User's choice as a string
    """
    print("\n" + "=" * 50)
    print("MAIN MENU")
    print("=" * 50)
    print("1. Create New Character")
    print("2. Load Character")
    print("3. Exit")
    print("=" * 50)
    choice = input("Enter your choice: ").strip()
    return choice


def main() -> int:
    """Main function to start the CLI RPG game.
    
    Returns:
        Exit code (0 for success)
    """
    print("\n" + "=" * 50)
    print("Welcome to CLI RPG!")
    print("=" * 50)
    
    current_character: Optional[Character] = None
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            # Create new character
            character = create_character()
            if character:
                current_character = character
                print(f"\n✓ {character.name} has been created successfully!")
                print(f"Your character is ready for adventure!")
        elif choice == "2":
            print("\n⚠ Load character feature not yet implemented.")
        elif choice == "3":
            print("\nThank you for playing CLI RPG!")
            print("Goodbye!")
            break
        else:
            print("\n✗ Invalid choice. Please enter 1, 2, or 3.")
    
    return 0


if __name__ == "__main__":
    exit(main())
