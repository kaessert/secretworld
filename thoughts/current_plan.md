# Implementation Plan: AI-Powered World Generation Integration

## 1. SPECIFICATION

### 1.1 Feature Requirements
- Import `load_ai_config`, `AIService`, and `create_world` into `main.py`
- Load AI config at game start (during `main()` initialization)
- Pass AI service to `create_world()` when creating worlds
- Pass AI service and theme to `GameState` constructor
- Add optional theme selection during character creation or game start
- Maintain backward compatibility with existing functionality
- All existing tests must continue to pass
- Default to "fantasy" theme when AI is not available or theme not selected

### 1.2 Integration Points
**File: `src/cli_rpg/main.py`**
- `main()` function: Load AI config at startup
- `start_game()` function: Replace `create_default_world()` with `create_world(ai_service, theme)`
- Add theme selection flow (optional, after character creation)
- Pass `ai_service` and `theme` to `GameState` constructor

**File: `src/cli_rpg/character_creation.py`**
- Add `get_theme_selection()` function for optional theme input
- Integrate theme selection into character creation flow or as separate step

### 1.3 API Contracts
```python
# main.py changes
def start_game(character: Character, ai_service: Optional[AIService] = None, theme: str = "fantasy") -> None:
    world = create_world(ai_service=ai_service, theme=theme)
    game_state = GameState(character, world, ai_service=ai_service, theme=theme)
    # ... existing gameplay loop ...

def main() -> int:
    # Load AI config at startup
    ai_config = load_ai_config()
    ai_service = AIService(ai_config) if ai_config else None
    # ... existing menu loop, pass ai_service where needed ...
```

### 1.4 Success Criteria
- AI service loaded when OPENAI_API_KEY is available
- Theme selection available during character creation flow
- `create_world()` uses AI when available, falls back to default world
- `GameState` receives AI service for dynamic world expansion
- All 251+ existing tests pass
- New E2E test validates complete flow with mocked AI service

---

## 2. TEST DEVELOPMENT

### 2.1 Create E2E Test File
**File: `tests/test_e2e_ai_integration.py`**

Test cases to verify complete AI integration flow:

1. **Test: AI config loading at startup**
   - Mock `load_ai_config()` to return valid config
   - Mock `AIService` initialization
   - Verify `main()` loads config without errors
   - Verify AI service is passed through to game components

2. **Test: Theme selection during character creation**
   - Mock input for character creation
   - Add theme selection input
   - Verify theme is captured and passed to `start_game()`

3. **Test: World creation with AI service**
   - Mock `create_world()` with AI service
   - Verify AI service and theme are passed correctly
   - Verify world is created with AI-generated locations

4. **Test: GameState initialization with AI service**
   - Mock character creation and theme selection
   - Verify `GameState` receives AI service and theme
   - Verify dynamic world expansion is enabled

5. **Test: Complete E2E flow with mocked AI**
   - Mock entire flow from startup to gameplay
   - Mock AI service responses
   - Verify: config load → character creation → theme selection → world creation → gameplay with AI expansion
   - Verify user can play game with AI-generated world

6. **Test: Graceful fallback when AI unavailable**
   - Mock `load_ai_config()` to return None
   - Verify game uses default world
   - Verify all features work without AI

7. **Test: Theme persistence in save/load**
   - Create character with AI and custom theme
   - Start game with AI-generated world
   - Save game state
   - Load game state
   - Verify theme is preserved
   - Verify AI service can be re-attached after load

### 2.2 Update Existing Tests
**File: `tests/test_main.py`**
- Update test fixtures to handle optional AI service parameter
- Add test for `main()` loading AI config
- Add test for `start_game()` accepting optional ai_service and theme parameters

**File: `tests/test_character_creation.py`**
- Add tests for theme selection flow if integrated into character creation

---

## 3. IMPLEMENTATION

### 3.1 Add Theme Selection to Character Creation
**File: `src/cli_rpg/character_creation.py`**

```python
def get_theme_selection() -> str:
    """Prompt user for world theme selection.
    
    Returns:
        Selected theme string (defaults to "fantasy")
    """
    print("\nSelect world theme (or press Enter for default 'fantasy'):")
    print("1. Fantasy (default)")
    print("2. Sci-Fi")
    print("3. Cyberpunk")
    print("4. Horror")
    print("5. Steampunk")
    print("6. Custom")
    
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
```

**Integration point:** Add theme selection after character confirmation, before returning from `create_character()`.

### 3.2 Integrate AI into Main Entry Point
**File: `src/cli_rpg/main.py`**

**Step 3.2.1: Add imports**
```python
from typing import Optional
from cli_rpg.config import load_ai_config
from cli_rpg.ai_service import AIService
from cli_rpg.world import create_world
# Keep create_default_world import for backward compatibility fallback
```

**Step 3.2.2: Update start_game() signature and implementation**
```python
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
    
    # ... rest of existing implementation unchanged ...
```

**Step 3.2.3: Update main() to load AI config and pass to start_game**
```python
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
                    from cli_rpg.character_creation import get_theme_selection
                    theme = get_theme_selection()
                    print(f"\n✓ Selected theme: {theme}")
                
                print(f"Your character is ready for adventure!")
                
                # Start the game with AI service and theme
                start_game(character, ai_service=ai_service, theme=theme)
                
        elif choice == "2":
            # Load character
            character = select_and_load_character()
            if character:
                # For backward compatibility: loaded saves may have theme info
                # Start with AI service available for dynamic expansion
                start_game(character, ai_service=ai_service, theme="fantasy")
                
        elif choice == "3":
            print("\nThank you for playing CLI RPG!")
            print("Goodbye!")
            break
        else:
            print("\n✗ Invalid choice. Please enter 1, 2, or 3.")
    
    return 0
```

### 3.3 Handle Game State Loading with AI
**File: `src/cli_rpg/main.py`**

**Step 3.3.1: Update select_and_load_character() to use load_game_state**

When loading a saved game, we should load the full game state (not just character) and restore with AI service:

```python
def select_and_load_game() -> Optional[tuple[Character, str]]:
    """Display save selection menu and load chosen game state.
    
    Returns:
        Tuple of (Character, theme) or None if cancelled/failed
    """
    saves = list_saves()
    
    if not saves:
        print("\n⚠ No saved games found.")
        print("  Create a new character first!")
        return None
    
    print("\n" + "=" * 50)
    print("LOAD GAME")
    print("=" * 50)
    print("\nAvailable saved games:")
    
    for idx, save in enumerate(saves, start=1):
        print(f"{idx}. {save['name']} (saved: {save['timestamp']})")
    
    print(f"{len(saves) + 1}. Cancel")
    print("=" * 50)
    
    try:
        choice = input("Select game to load: ").strip()
        choice_num = int(choice)
        
        if choice_num == len(saves) + 1:
            print("\nLoad cancelled.")
            return None
        
        if 1 <= choice_num <= len(saves):
            selected_save = saves[choice_num - 1]
            
            # Try to load as game state first
            try:
                game_state = load_game_state(selected_save['filepath'])
                print(f"\n✓ Game loaded successfully!")
                print(f"\n{game_state.current_character}")
                return (game_state.current_character, game_state.theme)
            except:
                # Fallback: load as character only (backward compatibility)
                character = load_character(selected_save['filepath'])
                print(f"\n✓ Character loaded successfully!")
                print(f"\n{character}")
                return (character, "fantasy")
        else:
            print("\n✗ Invalid selection.")
            return None
            
    except ValueError:
        print("\n✗ Invalid input. Please enter a number.")
        return None
    except Exception as e:
        print(f"\n✗ Failed to load game: {e}")
        return None
```

**Step 3.3.2: Update main() to use new load function**
Replace `select_and_load_character()` call with new implementation.

---

## 4. VERIFICATION

### 4.1 Run Test Suite
```bash
# Run all existing tests - should all pass
pytest tests/ -v

# Run specific E2E test
pytest tests/test_e2e_ai_integration.py -v

# Check test coverage
pytest tests/ --cov=src/cli_rpg --cov-report=term-missing
```

### 4.2 Manual Testing Scenarios

**Scenario 1: With AI enabled**
1. Set OPENAI_API_KEY environment variable
2. Run `python -m cli_rpg.main`
3. Create new character
4. Select custom theme (e.g., "cyberpunk")
5. Play game and move through locations
6. Verify AI generates new locations dynamically
7. Save game
8. Exit and reload game
9. Verify theme and world state persist

**Scenario 2: Without AI (fallback)**
1. Unset OPENAI_API_KEY
2. Run game
3. Verify default world is used
4. Verify all core features work
5. Verify can save/load without AI

**Scenario 3: AI generation failure handling**
1. Set invalid OPENAI_API_KEY
2. Verify graceful fallback to default world
3. Verify error messages are user-friendly

### 4.3 Success Validation Checklist
- [ ] AI config loads at startup when API key available
- [ ] Theme selection appears after character creation
- [ ] World created with AI service when available
- [ ] GameState receives AI service and theme
- [ ] Dynamic world expansion works during gameplay
- [ ] Save/load preserves theme
- [ ] Graceful fallback when AI unavailable
- [ ] All 251+ existing tests pass
- [ ] New E2E test passes
- [ ] No breaking changes to existing functionality
- [ ] User-friendly error messages

---

## 5. IMPLEMENTATION ORDER

1. **Write E2E test file** (`tests/test_e2e_ai_integration.py`)
   - Create all test cases with mocked AI service
   - Tests should fail initially (TDD approach)

2. **Update character_creation.py**
   - Add `get_theme_selection()` function
   - Add unit tests for theme selection

3. **Update main.py imports**
   - Add necessary imports for AI components

4. **Update start_game() function**
   - Add ai_service and theme parameters
   - Replace create_default_world() with create_world()
   - Pass parameters to GameState

5. **Update main() function**
   - Load AI config at startup
   - Initialize AIService if config available
   - Pass ai_service to start_game()
   - Integrate theme selection flow

6. **Update select_and_load functions**
   - Handle game state loading with theme
   - Maintain backward compatibility

7. **Run all tests**
   - Verify existing tests pass
   - Verify new E2E test passes

8. **Manual testing**
   - Test with and without AI
   - Verify save/load with themes
   - Verify error handling

---

## DEPENDENCIES

**Existing Code (No Changes Required):**
- `src/cli_rpg/ai_config.py` - Already implemented
- `src/cli_rpg/ai_service.py` - Already implemented  
- `src/cli_rpg/ai_world.py` - Already implemented
- `src/cli_rpg/world.py` - Already has `create_world()` function
- `src/cli_rpg/game_state.py` - Already supports ai_service and theme
- `src/cli_rpg/config.py` - Already has `load_ai_config()`

**Files to Modify:**
- `src/cli_rpg/main.py` - Main integration point
- `src/cli_rpg/character_creation.py` - Add theme selection

**Files to Create:**
- `tests/test_e2e_ai_integration.py` - New E2E test suite
