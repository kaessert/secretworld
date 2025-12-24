"""Main entry point for CLI RPG."""
from typing import Optional
from cli_rpg.character_creation import create_character, get_theme_selection
from cli_rpg.models.character import Character
from cli_rpg.persistence import save_character, load_character, list_saves, save_game_state, load_game_state, detect_save_type
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


def select_and_load_character() -> tuple[Optional[Character], Optional[GameState]]:
    """Display save selection menu and load chosen character or game state.
    
    Returns:
        Tuple of (Character, GameState) where:
        - (character, None) for character-only saves (backward compatibility)
        - (None, game_state) for full game state saves
        - (None, None) if cancelled/failed
    """
    saves = list_saves()
    
    if not saves:
        print("\n⚠ No saved characters found.")
        print("  Create a new character first!")
        return (None, None)
    
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
            return (None, None)
        
        if 1 <= choice_num <= len(saves):
            selected_save = saves[choice_num - 1]
            
            # Detect save type
            try:
                save_type = detect_save_type(selected_save['filepath'])
            except ValueError as e:
                print(f"\n✗ Corrupted save file: {e}")
                return (None, None)
            
            # Load based on save type
            if save_type == "game_state":
                # Load complete game state
                try:
                    game_state = load_game_state(selected_save['filepath'])
                    print(f"\n✓ Game state loaded successfully!")
                    print(f"  Location: {game_state.current_location}")
                    print(f"  Character: {game_state.current_character.name}")
                    print("\n" + str(game_state.current_character))
                    return (None, game_state)
                except Exception as e:
                    print(f"\n✗ Failed to load game state: {e}")
                    return (None, None)
            else:
                # Load character only (backward compatibility)
                try:
                    character = load_character(selected_save['filepath'])
                    print(f"\n✓ Character loaded successfully!")
                    print("\n" + str(character))
                    return (character, None)
                except Exception as e:
                    print(f"\n✗ Failed to load character: {e}")
                    return (None, None)
        else:
            print("\n✗ Invalid selection.")
            return (None, None)
            
    except ValueError:
        print("\n✗ Invalid input. Please enter a number.")
        return (None, None)
    except FileNotFoundError:
        print("\n✗ Save file not found.")
        return (None, None)
    except Exception as e:
        print(f"\n✗ Failed to load: {e}")
        return (None, None)


def handle_combat_command(game_state: GameState, command: str, args: list[str]) -> str:
    """Handle commands during combat.
    
    Args:
        game_state: Current game state
        command: Parsed command
        args: Command arguments
        
    Returns:
        Message string to display
    """
    if not game_state.is_in_combat():
        return "\n✗ Not in combat."
    
    combat = game_state.current_combat
    
    if command == "attack":
        victory, message = combat.player_attack()
        output = f"\n{message}"
        
        if victory:
            # Enemy defeated
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            game_state.current_combat = None
        else:
            # Enemy still alive, enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"
            
            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                game_state.current_combat = None
        
        return output
    
    elif command == "defend":
        _, message = combat.player_defend()
        output = f"\n{message}"
        
        # Enemy attacks
        enemy_message = combat.enemy_turn()
        output += f"\n{enemy_message}"
        
        # Check if player died
        if not game_state.current_character.is_alive():
            death_message = combat.end_combat(victory=False)
            output += f"\n{death_message}"
            output += "\n\n=== GAME OVER ==="
            game_state.current_combat = None
        
        return output
    
    elif command == "flee":
        success, message = combat.player_flee()
        output = f"\n{message}"
        
        if success:
            # Fled successfully
            game_state.current_combat = None
            combat.is_active = False
        else:
            # Flee failed, enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"
            
            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                game_state.current_combat = None
        
        return output
    
    elif command == "status":
        return "\n" + combat.get_status()
    
    else:
        return "\n✗ Can't do that during combat! Use: attack, defend, flee, or status"


def handle_exploration_command(game_state: GameState, command: str, args: list[str]) -> tuple[bool, str]:
    """Handle commands during exploration.
    
    Args:
        game_state: Current game state
        command: Parsed command
        args: Command arguments
        
    Returns:
        Tuple of (continue_game, message)
    """
    if command == "look":
        return (True, "\n" + game_state.look())
    
    elif command == "go":
        if not args:
            return (True, "\nGo where? Specify a direction (north, south, east, west, up, down)")
        
        direction = args[0]
        success, message = game_state.move(direction)
        output = f"\n{message}"
        
        if success:
            # Show new location
            output += "\n\n" + game_state.look()
        
        return (True, output)
    
    elif command == "status":
        return (True, "\n" + str(game_state.current_character))
    
    elif command == "save":
        try:
            filepath = save_game_state(game_state)
            return (True, f"\n✓ Game saved successfully!\n  Save location: {filepath}")
        except IOError as e:
            return (True, f"\n✗ Failed to save game: {e}")
    
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
        return (False, "")
    
    elif command in ["attack", "defend", "flee"]:
        return (True, "\n✗ Not in combat.")
    
    elif command == "unknown":
        return (True, "\n✗ Unknown command. Type 'look', 'go <direction>', 'status', 'save', or 'quit'")
    
    else:
        return (True, "\n✗ Unknown command. Type 'look', 'go <direction>', 'status', 'save', or 'quit'")


def run_game_loop(game_state: GameState) -> None:
    """Run the main gameplay loop.
    
    Args:
        game_state: The game state to run the loop for
    """
    # Main gameplay loop
    while True:
        # Check if player is alive (game over condition)
        if not game_state.current_character.is_alive():
            print("\n" + "=" * 50)
            print("GAME OVER - You have fallen in battle.")
            print("=" * 50)
            response = input("\nReturn to main menu? (y/n): ").strip().lower()
            if response == 'y':
                break
            else:
                # Allow continue even after death (for testing/fun)
                game_state.current_character.health = game_state.current_character.max_health
                print("\n✓ Health restored. Returning to town square...")
                game_state.current_location = "Town Square"
                game_state.current_combat = None
        
        print()
        command_input = input("> ").strip()
        
        if not command_input:
            continue
        
        # Parse command
        command, args = parse_command(command_input)
        
        # Route command based on combat state
        if game_state.is_in_combat():
            message = handle_combat_command(game_state, command, args)
            print(message)
            
            # Show combat status after each action if still in combat
            if game_state.is_in_combat() and game_state.current_combat is not None:
                print("\n" + game_state.current_combat.get_status())
        else:
            continue_game, message = handle_exploration_command(game_state, command, args)
            print(message)
            
            if not continue_game:
                break


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
    print("\nExploration Commands:")
    print("  look          - Look around at your surroundings")
    print("  go <direction> - Move in a direction (north, south, east, west)")
    print("  status        - View your character status")
    print("  save          - Save your game (not available during combat)")
    print("  quit          - Return to main menu")
    print("\nCombat Commands:")
    print("  attack        - Attack the enemy")
    print("  defend        - Take a defensive stance")
    print("  flee          - Attempt to flee from combat")
    print("  status        - View combat status")
    print("=" * 50)
    
    # Show starting location
    print("\n" + game_state.look())
    
    # Run the game loop
    run_game_loop(game_state)


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
            # Load character or game state
            character, game_state = select_and_load_character()
            
            if game_state:
                # Resume from saved game state
                print("\n✓ Resuming game from saved state...")
                # Re-attach AI service if available for continued world expansion
                game_state.ai_service = ai_service
                
                # Display welcome message
                print("\n" + "=" * 50)
                print(f"Welcome back, {game_state.current_character.name}!")
                print("=" * 50)
                print("\nExploration Commands:")
                print("  look          - Look around at your surroundings")
                print("  go <direction> - Move in a direction (north, south, east, west)")
                print("  status        - View your character status")
                print("  save          - Save your game (not available during combat)")
                print("  quit          - Return to main menu")
                print("\nCombat Commands:")
                print("  attack        - Attack the enemy")
                print("  defend        - Take a defensive stance")
                print("  flee          - Attempt to flee from combat")
                print("  status        - View combat status")
                print("=" * 50)
                
                # Show current location
                print("\n" + game_state.look())
                
                # Run game loop with restored state
                run_game_loop(game_state)
                
            elif character:
                # For backward compatibility, if loading an old character-only save,
                # start a new game with that character
                print("\n✓ Starting new adventure with loaded character...")
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
