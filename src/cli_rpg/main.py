"""Main entry point for CLI RPG."""
from typing import Optional
from cli_rpg.character_creation import create_character
from cli_rpg.models.character import Character
from cli_rpg.persistence import save_character, load_character, list_saves


def prompt_save_character(character: Character) -> None:
    """Prompt user to save character and handle save operation.
    
    Args:
        character: Character to save
    """
    print("\n" + "=" * 50)
    response = input("Would you like to save this character? (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            filepath = save_character(character)
            print(f"\n✓ Character saved successfully!")
            print(f"  Save location: {filepath}")
        except IOError as e:
            print(f"\n✗ Failed to save character: {e}")
    else:
        print("\nCharacter not saved.")


def select_and_load_character() -> Optional[Character]:
    """Display save selection menu and load chosen character.
    
    Returns:
        Loaded Character instance or None if cancelled/failed
    """
    saves = list_saves()
    
    if not saves:
        print("\n⚠ No saved characters found.")
        print("  Create a new character first!")
        return None
    
    print("\n" + "=" * 50)
    print("LOAD CHARACTER")
    print("=" * 50)
    print("\nAvailable saved characters:")
    
    for idx, save in enumerate(saves, start=1):
        print(f"{idx}. {save['name']} (saved: {save['timestamp']})")
    
    print(f"{len(saves) + 1}. Cancel")
    print("=" * 50)
    
    try:
        choice = input("Select character to load: ").strip()
        choice_num = int(choice)
        
        if choice_num == len(saves) + 1:
            print("\nLoad cancelled.")
            return None
        
        if 1 <= choice_num <= len(saves):
            selected_save = saves[choice_num - 1]
            character = load_character(selected_save['filepath'])
            
            print(f"\n✓ Character loaded successfully!")
            print("\n" + str(character))
            
            return character
        else:
            print("\n✗ Invalid selection.")
            return None
            
    except ValueError:
        print("\n✗ Invalid input. Please enter a number.")
        return None
    except FileNotFoundError:
        print("\n✗ Save file not found.")
        return None
    except Exception as e:
        print(f"\n✗ Failed to load character: {e}")
        return None


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
                # Prompt to save character
                prompt_save_character(character)
        elif choice == "2":
            # Load character
            character = select_and_load_character()
            if character:
                current_character = character
        elif choice == "3":
            print("\nThank you for playing CLI RPG!")
            print("Goodbye!")
            break
        else:
            print("\n✗ Invalid choice. Please enter 1, 2, or 3.")
    
    return 0


if __name__ == "__main__":
    exit(main())
