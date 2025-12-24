"""Main entry point for CLI RPG."""
from typing import Optional
from cli_rpg.character_creation import create_character, get_theme_selection
from cli_rpg.models.character import Character
from cli_rpg.persistence import save_character, load_character, list_saves, save_game_state, load_game_state
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.world import create_world
from cli_rpg.config import load_ai_config
from cli_rpg.ai_service import AIService


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


def start_game(
    character: Character,
    ai_service: Optional[AIService] = None,
    theme: str = "fantasy"
) -> None:
    """Start the gameplay loop with the given character.
    
    Args:
        character: The player's character to start the game with
        ai_service: Optional AIService for AI-powered world generation
        theme: World theme for generation (default: "fantasy")
    """
    # Create game state with AI-powered or default world
    world = create_world(ai_service=ai_service, theme=theme)
    game_state = GameState(
        character, 
        world, 
        ai_service=ai_service, 
        theme=theme
    )
    
    # Display welcome message
    print("\n" + "=" * 50)
    print(f"Welcome to the adventure, {character.name}!")
    if ai_service:
        print(f"Exploring a {theme} world powered by AI...")
    print("=" * 50)
    print("\nCommands:")
    print("  look          - Look around at your surroundings")
    print("  go <direction> - Move in a direction (north, south, east, west)")
    print("  save          - Save your game")
    print("  quit          - Return to main menu")
    print("=" * 50)
    
    # Show starting location
    print("\n" + game_state.look())
    
    # Main gameplay loop
    while True:
        print()
        command_input = input("> ").strip()
        
        if not command_input:
            continue
        
        # Parse command
        command, args = parse_command(command_input)
        
        # Handle commands
        if command == "look":
            print("\n" + game_state.look())
            
        elif command == "go":
            if not args:
                print("\nGo where? Specify a direction (north, south, east, west, up, down)")
                continue
            
            direction = args[0]
            success, message = game_state.move(direction)
            print(f"\n{message}")
            
            if success:
                # Show new location
                print("\n" + game_state.look())
                
        elif command == "save":
            try:
                filepath = save_game_state(game_state)
                print(f"\n✓ Game saved successfully!")
                print(f"  Save location: {filepath}")
            except IOError as e:
                print(f"\n✗ Failed to save game: {e}")
                
        elif command == "quit":
            print("\n" + "=" * 50)
            response = input("Save before quitting? (y/n): ").strip().lower()
            if response == 'y':
                try:
                    filepath = save_game_state(game_state)
                    print(f"\n✓ Game saved successfully!")
                    print(f"  Save location: {filepath}")
                except IOError as e:
                    print(f"\n✗ Failed to save game: {e}")
            
            print("\nReturning to main menu...")
            break
            
        elif command == "unknown":
            print("\n✗ Unknown command. Type 'look', 'go <direction>', 'save', or 'quit'")
            
        else:
            print("\n✗ Unknown command. Type 'look', 'go <direction>', 'save', or 'quit'")


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
    
    # Load AI configuration at startup
    ai_config = load_ai_config()
    ai_service = None
    if ai_config:
        try:
            ai_service = AIService(ai_config)
            print("\n✓ AI world generation enabled!")
            print("  Set OPENAI_API_KEY to use AI features.")
        except Exception as e:
            print(f"\n⚠ AI initialization failed: {e}")
            print("  Falling back to default world generation.")
    else:
        print("\n⚠ AI world generation not available.")
        print("  Set OPENAI_API_KEY to enable AI features.")
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            # Create new character
            character = create_character()
            if character:
                print(f"\n✓ {character.name} has been created successfully!")
                
                # Theme selection (if AI is available)
                theme = "fantasy"
                if ai_service:
                    theme = get_theme_selection()
                    print(f"\n✓ Selected theme: {theme}")
                
                print(f"Your character is ready for adventure!")
                
                # Start the game with AI service and theme
                start_game(character, ai_service=ai_service, theme=theme)
                
        elif choice == "2":
            # Load character - note: this will load game state files now
            character = select_and_load_character()
            if character:
                # For backward compatibility, if loading an old character-only save,
                # start a new game with that character
                # Start with AI service available for dynamic expansion
                start_game(character, ai_service=ai_service, theme="fantasy")
                
        elif choice == "3":
            print("\nThank you for playing CLI RPG!")
            print("Goodbye!")
            break
        else:
            print("\n✗ Invalid choice. Please enter 1, 2, or 3.")
    
    return 0


if __name__ == "__main__":
    exit(main())
