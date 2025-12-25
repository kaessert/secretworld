"""Character creation functionality for CLI RPG."""
import random
import sys
from typing import Optional, Tuple
from cli_rpg.models.character import Character


def get_valid_name() -> Optional[str]:
    """Prompt user for valid character name.
    
    Returns:
        Valid name string or None if cancelled
    """
    while True:
        print("\nEnter character name (2-30 characters, or 'cancel' to exit):")
        name = input("> ").strip()
        
        if name.lower() == "cancel":
            return None
        
        # Validate name
        if not name:
            print("Error: Name cannot be empty. Please try again.")
            continue
        
        if len(name) < Character.MIN_NAME_LENGTH:
            print(f"Error: Name must be at least {Character.MIN_NAME_LENGTH} characters. Please try again.")
            continue
        
        if len(name) > Character.MAX_NAME_LENGTH:
            print(f"Error: Name must be at most {Character.MAX_NAME_LENGTH} characters. Please try again.")
            continue
        
        return name


def get_allocation_method() -> Optional[str]:
    """Prompt user for stat allocation method.
    
    Returns:
        "manual" or "random", or None if cancelled
    """
    while True:
        print("\nChoose stat allocation method:")
        print("1. Manual - Choose your own stats")
        print("2. Random - Randomly generate balanced stats")
        print("Type 'cancel' to exit")
        choice = input("> ").strip().lower()
        
        if choice == "cancel":
            return None
        
        if choice in ["1", "manual"]:
            return "manual"
        
        if choice in ["2", "random"]:
            return "random"
        
        print("Error: Invalid choice. Please enter 1, 2, 'manual', 'random', or 'cancel'.")


def get_manual_stats() -> Optional[dict[str, int]]:
    """Prompt user for manual stat entry.
    
    Returns:
        Dictionary with strength, dexterity, intelligence or None if cancelled
    """
    stats = {}
    stat_names = ["strength", "dexterity", "intelligence"]
    
    for stat_name in stat_names:
        while True:
            print(f"\nEnter {stat_name} ({Character.MIN_STAT}-{Character.MAX_STAT}, or 'cancel' to exit):")
            value = input("> ").strip().lower()
            
            if value == "cancel":
                return None
            
            try:
                stat_value = int(value)
                
                if stat_value < Character.MIN_STAT:
                    print(f"Error: {stat_name} must be at least {Character.MIN_STAT}. Please try again.")
                    continue
                
                if stat_value > Character.MAX_STAT:
                    print(f"Error: {stat_name} must be at most {Character.MAX_STAT}. Please try again.")
                    continue
                
                stats[stat_name] = stat_value
                break
            except ValueError:
                print("Error: Please enter a valid number.")
    
    return stats


def generate_random_stats() -> dict[str, int]:
    """Generate random balanced stats.
    
    Returns:
        Dictionary with strength, dexterity, intelligence (8-15 range)
    """
    return {
        "strength": random.randint(8, 15),
        "dexterity": random.randint(8, 15),
        "intelligence": random.randint(8, 15)
    }


def display_character_summary(character: Character) -> None:
    """Display character summary to user.
    
    Args:
        character: Character instance to display
    """
    print("\n" + "=" * 50)
    print("CHARACTER SUMMARY")
    print("=" * 50)
    print(str(character))
    print("=" * 50)


def confirm_creation() -> bool:
    """Prompt user to confirm character creation.
    
    Returns:
        True if confirmed, False otherwise
    """
    while True:
        print("\nConfirm character creation? (yes/no):")
        choice = input("> ").strip().lower()
        
        if choice in ["yes", "y"]:
            return True
        
        if choice in ["no", "n"]:
            return False
        
        print("Error: Please enter 'yes' or 'no'.")


def get_theme_selection() -> str:
    """Prompt user for world theme selection.
    
    Returns:
        Selected theme string (defaults to "fantasy")
    """
    print("\n" + "=" * 50)
    print("THEME SELECTION")
    print("=" * 50)
    print("Select world theme (or press Enter for default 'fantasy'):")
    print("1. Fantasy (default)")
    print("2. Sci-Fi")
    print("3. Cyberpunk")
    print("4. Horror")
    print("5. Steampunk")
    print("6. Custom")
    print("=" * 50)
    
    choice = input("> ").strip().lower()
    
    theme_map = {
        "1": "fantasy",
        "2": "sci-fi",
        "3": "cyberpunk",
        "4": "horror",
        "5": "steampunk",
        "fantasy": "fantasy",
        "sci-fi": "sci-fi",
        "scifi": "sci-fi",
        "cyberpunk": "cyberpunk",
        "horror": "horror",
        "steampunk": "steampunk"
    }
    
    if choice in theme_map:
        return theme_map[choice]
    elif choice == "6" or choice == "custom":
        custom = input("Enter custom theme: ").strip()
        return custom if custom else "fantasy"
    elif choice == "":
        return "fantasy"
    else:
        print("Invalid choice, defaulting to 'fantasy'")
        return "fantasy"


def create_character() -> Optional[Character]:
    """Interactive character creation flow.
    
    Returns:
        Created Character instance or None if cancelled
    """
    print("\n" + "=" * 50)
    print("CHARACTER CREATION")
    print("=" * 50)
    
    # Get character name
    name = get_valid_name()
    if name is None:
        print("Character creation cancelled.")
        return None
    
    # Get stat allocation method
    method = get_allocation_method()
    if method is None:
        print("Character creation cancelled.")
        return None
    
    # Get stats based on method
    if method == "manual":
        stats = get_manual_stats()
        if stats is None:
            print("Character creation cancelled.")
            return None
    else:  # random
        stats = generate_random_stats()
        print("\nRandomly generated stats:")
        print(f"Strength: {stats['strength']}")
        print(f"Dexterity: {stats['dexterity']}")
        print(f"Intelligence: {stats['intelligence']}")
    
    # Create character
    character = Character(
        name=name,
        strength=stats["strength"],
        dexterity=stats["dexterity"],
        intelligence=stats["intelligence"]
    )
    
    # Display summary
    display_character_summary(character)
    
    # Confirm creation
    if confirm_creation():
        return character
    else:
        print("Character creation cancelled.")
        return None


def create_character_non_interactive(json_mode: bool = False) -> Tuple[Optional[Character], Optional[str]]:
    """Non-interactive character creation flow.

    Reads character creation inputs from stdin without retry loops.
    Invalid inputs cause immediate error return.

    Args:
        json_mode: If True, errors are formatted for JSON output.

    Returns:
        Tuple of (Character, None) on success, or (None, error_message) on failure.
    """
    def read_line() -> Optional[str]:
        """Read a line from stdin, return None on EOF."""
        try:
            line = sys.stdin.readline()
            if not line:  # EOF
                return None
            return line.strip()
        except EOFError:
            return None

    # Step 1: Read and validate name
    name = read_line()
    if name is None:
        return (None, "Error: No character name provided.")

    if not name:
        return (None, "Error: Name cannot be empty.")

    if len(name) < Character.MIN_NAME_LENGTH:
        return (None, f"Error: Name must be at least {Character.MIN_NAME_LENGTH} characters.")

    if len(name) > Character.MAX_NAME_LENGTH:
        return (None, f"Error: Name must be at most {Character.MAX_NAME_LENGTH} characters.")

    # Step 2: Read and validate allocation method
    method_input = read_line()
    if method_input is None:
        return (None, "Error: No stat allocation method provided.")

    method_input = method_input.lower()
    if method_input in ["1", "manual"]:
        method = "manual"
    elif method_input in ["2", "random"]:
        method = "random"
    else:
        return (None, f"Error: Invalid stat allocation method '{method_input}'. Use '1'/'manual' or '2'/'random'.")

    # Step 3: Get stats based on method
    if method == "manual":
        stats = {}
        stat_names = ["strength", "dexterity", "intelligence"]

        for stat_name in stat_names:
            stat_input = read_line()
            if stat_input is None:
                return (None, f"Error: No {stat_name} value provided.")

            try:
                stat_value = int(stat_input)
            except ValueError:
                return (None, f"Error: {stat_name} must be a valid number, got '{stat_input}'.")

            if stat_value < Character.MIN_STAT:
                return (None, f"Error: {stat_name} must be at least {Character.MIN_STAT}.")

            if stat_value > Character.MAX_STAT:
                return (None, f"Error: {stat_name} must be at most {Character.MAX_STAT}.")

            stats[stat_name] = stat_value
    else:  # random
        stats = generate_random_stats()
        # Only print stats in non-JSON mode to avoid polluting JSON output
        if not json_mode:
            print(f"Randomly generated stats:")
            print(f"Strength: {stats['strength']}")
            print(f"Dexterity: {stats['dexterity']}")
            print(f"Intelligence: {stats['intelligence']}")

    # Step 4: Read confirmation
    confirm_input = read_line()
    if confirm_input is None:
        return (None, "Error: No confirmation provided.")

    confirm_input = confirm_input.lower()
    if confirm_input not in ["yes", "y"]:
        return (None, "Character creation cancelled.")

    # Create character
    character = Character(
        name=name,
        strength=stats["strength"],
        dexterity=stats["dexterity"],
        intelligence=stats["intelligence"]
    )

    # Display summary (only in non-JSON mode to avoid polluting JSON output)
    if not json_mode:
        display_character_summary(character)

    return (character, None)
