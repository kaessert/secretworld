# Character Creation System Implementation Plan

## 1. SPECIFICATION

### Character Model Requirements
- **Attributes**: name (str), health (int), max_health (int), strength (int), dexterity (int), intelligence (int), level (int, default=1)
- **Stat Constraints**: Base stats range 1-20, health calculated from strength (base_health = 100 + strength * 5)
- **Validation**: Name must be 2-30 characters, non-empty; stats must be positive integers within range
- **Methods**: 
  - `take_damage(amount: int)` - reduces health, min 0
  - `heal(amount: int)` - increases health, max = max_health
  - `is_alive() -> bool` - returns health > 0
  - `to_dict() -> dict` - serializes character data
  - `from_dict(data: dict) -> Character` - deserializes character (class method)

### Character Creation Flow Requirements
- **Interactive prompts**:
  1. Prompt for character name with validation
  2. Choose stat allocation method: "manual" or "random"
  3. Manual: Prompt for each stat (strength, dexterity, intelligence) with validation
  4. Random: Generate random stats within valid range (8-15 for balanced start)
  5. Display character summary with all stats
  6. Confirm creation (yes/no prompt)
  7. Return Character instance or None if cancelled
- **Input validation**: Retry on invalid input with clear error messages
- **User experience**: Clear prompts, helpful error messages, ability to cancel

## 2. TEST DEVELOPMENT

### File: `tests/test_character.py`

#### Test Cases for Character Model:
1. `test_character_creation_valid()` - Create character with valid attributes
2. `test_character_creation_with_defaults()` - Verify level defaults to 1
3. `test_character_health_calculation()` - Verify max_health = 100 + strength * 5
4. `test_character_name_validation_too_short()` - Reject name < 2 chars
5. `test_character_name_validation_too_long()` - Reject name > 30 chars
6. `test_character_name_validation_empty()` - Reject empty name
7. `test_character_stat_validation_below_min()` - Reject stats < 1
8. `test_character_stat_validation_above_max()` - Reject stats > 20
9. `test_character_take_damage()` - Reduce health by damage amount
10. `test_character_take_damage_cannot_go_negative()` - Health floors at 0
11. `test_character_heal()` - Increase health by heal amount
12. `test_character_heal_cannot_exceed_max()` - Health caps at max_health
13. `test_character_is_alive_when_healthy()` - Returns True when health > 0
14. `test_character_is_alive_when_dead()` - Returns False when health = 0
15. `test_character_to_dict()` - Serializes all attributes correctly
16. `test_character_from_dict()` - Deserializes to equivalent Character instance
17. `test_character_str_representation()` - Verify __str__ method output

### File: `tests/test_character_creation.py`

#### Test Cases for Creation Flow:
1. `test_create_character_manual_valid_input()` - Complete manual creation with valid inputs
2. `test_create_character_random_generation()` - Complete random stat generation
3. `test_create_character_name_retry_on_invalid()` - Retry prompt on invalid name
4. `test_create_character_stat_retry_on_invalid()` - Retry prompt on invalid stat value
5. `test_create_character_cancelled_by_user()` - Return None when user cancels
6. `test_create_character_invalid_allocation_method()` - Retry on invalid method choice
7. `test_create_character_display_summary()` - Verify character summary is displayed
8. `test_create_character_random_stats_in_range()` - Verify random stats are 8-15

### File: `tests/test_integration_character.py`

#### Integration Test Cases:
1. `test_full_character_lifecycle()` - Create, damage, heal, check alive status
2. `test_character_persistence()` - Create, serialize, deserialize, verify equality
3. `test_main_menu_character_creation_integration()` - Integrate creation flow into main menu

## 3. IMPLEMENTATION

### Step 1: Create Character Model
**File**: `src/cli_rpg/models/__init__.py`
```python
"""Models package for CLI RPG."""
```

**File**: `src/cli_rpg/models/character.py`
```python
"""Character model for CLI RPG."""
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Character:
    """Represents a player character in the RPG.
    
    Attributes:
        name: Character's name (2-30 characters)
        strength: Strength stat (1-20)
        dexterity: Dexterity stat (1-20)
        intelligence: Intelligence stat (1-20)
        level: Character level (default 1)
        health: Current health points
        max_health: Maximum health points (calculated from strength)
    """
    
    MIN_STAT: ClassVar[int] = 1
    MAX_STAT: ClassVar[int] = 20
    MIN_NAME_LENGTH: ClassVar[int] = 2
    MAX_NAME_LENGTH: ClassVar[int] = 30
    BASE_HEALTH: ClassVar[int] = 100
    HEALTH_PER_STRENGTH: ClassVar[int] = 5
    
    name: str
    strength: int
    dexterity: int
    intelligence: int
    level: int = 1
    
    def __post_init__(self):
        """Validate attributes and calculate derived stats."""
        # Validate name
        # Validate stats
        # Calculate max_health and health
    
    def take_damage(self, amount: int) -> None:
        """Reduce health by damage amount, minimum 0."""
        pass
    
    def heal(self, amount: int) -> None:
        """Increase health by heal amount, maximum max_health."""
        pass
    
    def is_alive(self) -> bool:
        """Check if character is alive."""
        pass
    
    def to_dict(self) -> dict:
        """Serialize character to dictionary."""
        pass
    
    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """Deserialize character from dictionary."""
        pass
    
    def __str__(self) -> str:
        """String representation of character."""
        pass
```

### Step 2: Implement Character Validation Logic
**File**: `src/cli_rpg/models/character.py` (implement methods in order)
1. Implement `__post_init__` with validation logic
2. Implement `take_damage` method
3. Implement `heal` method
4. Implement `is_alive` method
5. Implement `to_dict` method
6. Implement `from_dict` class method
7. Implement `__str__` method

### Step 3: Create Character Creation Module
**File**: `src/cli_rpg/character_creation.py`
```python
"""Character creation functionality for CLI RPG."""
import random
from typing import Optional
from cli_rpg.models.character import Character


def get_valid_name() -> Optional[str]:
    """Prompt user for valid character name.
    
    Returns:
        Valid name string or None if cancelled
    """
    pass


def get_allocation_method() -> Optional[str]:
    """Prompt user for stat allocation method.
    
    Returns:
        "manual" or "random", or None if cancelled
    """
    pass


def get_manual_stats() -> Optional[dict[str, int]]:
    """Prompt user for manual stat entry.
    
    Returns:
        Dictionary with strength, dexterity, intelligence or None if cancelled
    """
    pass


def generate_random_stats() -> dict[str, int]:
    """Generate random balanced stats.
    
    Returns:
        Dictionary with strength, dexterity, intelligence (8-15 range)
    """
    pass


def display_character_summary(character: Character) -> None:
    """Display character summary to user."""
    pass


def confirm_creation() -> bool:
    """Prompt user to confirm character creation.
    
    Returns:
        True if confirmed, False otherwise
    """
    pass


def create_character() -> Optional[Character]:
    """Interactive character creation flow.
    
    Returns:
        Created Character instance or None if cancelled
    """
    pass
```

### Step 4: Implement Character Creation Functions
**File**: `src/cli_rpg/character_creation.py` (implement functions in order)
1. Implement `get_valid_name()` with validation and retry logic
2. Implement `get_allocation_method()` with validation
3. Implement `get_manual_stats()` with individual stat prompts and validation
4. Implement `generate_random_stats()` with random number generation (8-15)
5. Implement `display_character_summary()` with formatted output
6. Implement `confirm_creation()` with yes/no prompt
7. Implement `create_character()` orchestrating the full flow

### Step 5: Integrate into Main Menu
**File**: `src/cli_rpg/main.py`
```python
"""Main entry point for CLI RPG."""
from cli_rpg.character_creation import create_character


def show_main_menu() -> str:
    """Display main menu and get user choice."""
    pass


def main() -> int:
    """Main function to start the CLI RPG game."""
    print("Welcome to CLI RPG!")
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            # Create new character
            character = create_character()
            if character:
                print(f"\n{character.name} has been created successfully!")
        elif choice == "2":
            print("Load character not yet implemented.")
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
    
    return 0
```

### Step 6: Update Package Exports
**File**: `src/cli_rpg/__init__.py`
```python
"""CLI RPG - An AI-generated role-playing game."""

__version__ = "0.1.0"

from cli_rpg.models.character import Character

__all__ = ["Character", "__version__"]
```

## 4. VERIFICATION

### Run Tests in Order:
1. `pytest tests/test_character.py -v` - Verify all Character model tests pass
2. `pytest tests/test_character_creation.py -v` - Verify creation flow tests pass
3. `pytest tests/test_integration_character.py -v` - Verify integration tests pass
4. `pytest tests/ -v` - Run full test suite
5. Manual testing: `python -m cli_rpg.main` - Test interactive flow

### Success Criteria:
- All unit tests pass (100% for character model)
- All integration tests pass
- Interactive character creation works end-to-end
- Invalid input handled gracefully with clear error messages
- Character can be created, serialized, and deserialized correctly
- Main menu integrates character creation option

## Implementation Order Summary:
1. Create `src/cli_rpg/models/__init__.py`
2. Create `src/cli_rpg/models/character.py` with class structure
3. Create `tests/test_character.py` with all unit tests
4. Implement Character class methods until all unit tests pass
5. Create `src/cli_rpg/character_creation.py` with function signatures
6. Create `tests/test_character_creation.py` with all creation flow tests
7. Implement character creation functions until tests pass
8. Create `tests/test_integration_character.py` with integration tests
9. Update `src/cli_rpg/main.py` with menu integration
10. Update `src/cli_rpg/__init__.py` with exports
11. Run full test suite and verify all tests pass
12. Manual testing of interactive flow
