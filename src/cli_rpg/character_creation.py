"""Character creation functionality for CLI RPG."""
import random
from typing import Optional
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
