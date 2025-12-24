# Implementation Plan: Fix Game State Loading in main.py

## Problem
The `select_and_load_character()` function (lines 32-73) only calls `load_character()` to restore character stats, but doesn't call `load_game_state()` to restore the full game state (world, location, theme). This causes players to lose their world progress when loading a saved game.

## Solution Approach
1. Detect save file type (character-only vs full game state) by inspecting JSON structure
2. Call appropriate loading function based on file type
3. Properly restore complete game state including world, location, and AI theme
4. Maintain backward compatibility with existing character-only saves
5. Include proper error handling

---

## Implementation Steps

### Step 1: Create Specification Document

**File**: `docs/save_file_detection_spec.md`

Create specification that defines:
- Save file type detection logic: Distinguish between character-only saves (contains only: name, strength, dexterity, intelligence, level, health, max_health) vs game state saves (contains: character, world, current_location, theme)
- Detection method: Check for presence of "world" key in JSON data
- Loading behavior for each type:
  - Character-only: Load character and start new game with default world
  - Game state: Load complete game state including world, location, and theme
- Backward compatibility: All existing character-only saves must continue to work
- Error handling: Handle corrupted files, missing keys, invalid data

### Step 2: Write Tests for Save File Detection

**File**: `tests/test_main_save_file_detection.py`

Create tests that verify:

1. **Test detect character-only save file**
   - Given: JSON file with character-only data (name, strength, dexterity, intelligence, level, health, max_health)
   - When: Detecting file type
   - Then: Returns "character" as file type

2. **Test detect game state save file**
   - Given: JSON file with game state data (character, world, current_location, theme)
   - When: Detecting file type
   - Then: Returns "game_state" as file type

3. **Test load character-only file starts new game**
   - Given: Character-only save file
   - When: Loading via select_and_load_character()
   - Then: Character is loaded with default world ("Town Square" as starting location)

4. **Test load game state file restores complete state**
   - Given: Game state save file with custom world and location
   - When: Loading via select_and_load_character()
   - Then: Complete game state is restored (character, world, exact location, theme)

5. **Test backward compatibility with existing saves**
   - Given: Real existing character-only save file (sasdf_20251224_011809.json)
   - When: Loading file
   - Then: Successfully loads without errors

6. **Test handle corrupted save file**
   - Given: Invalid/corrupted JSON file
   - When: Attempting to load
   - Then: Gracefully handles error with user-friendly message

7. **Test theme preservation in game state loads**
   - Given: Game state save with theme="sci-fi"
   - When: Loading game state
   - Then: Theme is restored and available to AI service

### Step 3: Write Tests for Modified select_and_load_character()

**File**: `tests/test_main_load_integration.py`

Create integration tests:

1. **Test select and load returns character for character-only save**
   - Verify character object is returned
   - Verify character has correct attributes

2. **Test select and load returns game state for full save**
   - Verify GameState object is returned
   - Verify game state has character, world, and location

3. **Test game continuation after loading character-only save**
   - Load character-only save
   - Pass character to start_game()
   - Verify game starts with default world

4. **Test game continuation after loading game state save**
   - Load game state save
   - Continue gameplay from saved location
   - Verify world and progress are preserved

5. **Test list_saves shows both save types**
   - Create one character-only and one game state save
   - Call list_saves()
   - Verify both appear in list

### Step 4: Implement Save File Type Detection

**File**: `src/cli_rpg/persistence.py`

Add new function after `list_saves()`:

```python
def detect_save_type(filepath: str) -> str:
    """Detect whether save file is character-only or full game state.
    
    Args:
        filepath: Path to save file
        
    Returns:
        "character" for character-only saves
        "game_state" for full game state saves
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    # Implementation:
    # 1. Check if file exists
    # 2. Load JSON data
    # 3. Check for presence of "world" key
    # 4. Return "game_state" if world key exists, else "character"
    # 5. Handle JSON decode errors with ValueError
```

### Step 5: Modify select_and_load_character() Function

**File**: `src/cli_rpg/main.py`

Modify `select_and_load_character()` function (lines 32-73):

1. **Change return type** from `Optional[Character]` to `tuple[Optional[Character], Optional[GameState]]`
   - Line 32: Update function signature
   - Update docstring to reflect new return type

2. **Add save type detection after user selects file** (after line 62):
   ```python
   # Detect save type
   from cli_rpg.persistence import detect_save_type
   try:
       save_type = detect_save_type(selected_save['filepath'])
   except ValueError as e:
       print(f"\n✗ Corrupted save file: {e}")
       return (None, None)
   ```

3. **Add conditional loading logic** (replace lines 63-69):
   ```python
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
   ```

4. **Update error handling** (lines 74-82):
   - Return `(None, None)` instead of `None` for all error cases
   - Keep existing error messages

### Step 6: Update main() to Handle Both Return Types

**File**: `src/cli_rpg/main.py`

Modify `main()` function at the load character branch (around line 368):

1. **Update call to select_and_load_character()** (line 373):
   ```python
   elif choice == "2":
       # Load character or game state
       character, game_state = select_and_load_character()
       
       if game_state:
           # Resume from saved game state
           print("\n✓ Resuming game from saved state...")
           # Re-attach AI service if available for continued world expansion
           game_state.ai_service = ai_service
           
           # Start game loop with restored state
           # Display welcome message
           print("\n" + "=" * 50)
           print(f"Welcome back, {game_state.current_character.name}!")
           print("=" * 50)
           # Display command help (copy from start_game)
           # Show current location
           print("\n" + game_state.look())
           
           # Run main gameplay loop (extract loop logic from start_game into helper)
           run_game_loop(game_state)
           
       elif character:
           # For backward compatibility, start new game with loaded character
           print("\n✓ Starting new adventure with loaded character...")
           start_game(character, ai_service=ai_service, theme="fantasy")
   ```

### Step 7: Extract Game Loop Logic to Helper Function

**File**: `src/cli_rpg/main.py`

Add new function before `start_game()`:

```python
def run_game_loop(game_state: GameState) -> None:
    """Run the main gameplay loop.
    
    Args:
        game_state: The game state to run the loop for
    """
    # Implementation:
    # 1. Copy the while loop logic from start_game() (lines ~299-330)
    # 2. Include game over check
    # 3. Include command parsing
    # 4. Include combat/exploration routing
    # 5. Do NOT include welcome message or initial setup
```

Modify `start_game()` function:
1. Keep initial setup (lines ~250-295)
2. Replace main loop with call to `run_game_loop(game_state)`

### Step 8: Update Imports

**File**: `src/cli_rpg/main.py`

Update import statement (line 5):
```python
from cli_rpg.persistence import save_character, load_character, list_saves, save_game_state, load_game_state, detect_save_type
```

### Step 9: Update Tests for Modified Function Signatures

**File**: `tests/test_main.py`

Update any tests that call `select_and_load_character()`:
- Change assertions to expect tuple return value
- Add tests for both return patterns

**File**: `tests/test_main_menu.py`

Update any menu flow tests:
- Handle tuple unpacking from select_and_load_character()
- Add test cases for loading game state saves

### Step 10: Add Integration Test for Complete Flow

**File**: `tests/test_main_complete_load_flow.py`

Create end-to-end test:

1. **Test complete save and load flow**
   - Create character
   - Start game (move to different location)
   - Save game state
   - Exit game
   - Load game state from main menu
   - Verify location and world are restored
   - Continue playing from restored state

2. **Test backward compatibility flow**
   - Create character
   - Save character only (using old save_character)
   - Exit
   - Load from main menu
   - Verify new game starts with loaded character

### Step 11: Verify All Tests Pass

Run test suite:
```bash
pytest tests/test_main_save_file_detection.py -v
pytest tests/test_main_load_integration.py -v
pytest tests/test_persistence.py -v
pytest tests/test_main.py -v
pytest tests/test_main_complete_load_flow.py -v
```

Ensure:
- All new tests pass
- All existing tests still pass
- No regressions in character loading
- Backward compatibility maintained

### Step 12: Manual Testing

Verify manually:
1. Load existing character-only save (sasdf_20251224_011809.json)
2. Verify it loads correctly and starts new game
3. Create new character, play game, save game state
4. Load game state save
5. Verify location, world, and progress are restored
6. Continue playing from restored state
7. Test with AI service enabled and disabled

---

## Verification Checklist

- [ ] detect_save_type() function correctly identifies save file types
- [ ] select_and_load_character() returns appropriate type based on save file
- [ ] Character-only saves start new game with default world
- [ ] Game state saves restore complete state (world, location, theme)
- [ ] Backward compatibility: existing saves work without modification
- [ ] Error handling for corrupted files
- [ ] Theme is preserved and passed to AI service
- [ ] AI service can be re-attached for continued world expansion
- [ ] All tests pass
- [ ] Manual testing confirms expected behavior
