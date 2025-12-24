# Implementation Plan: Character Persistence System (Save/Load)

## 1. SPECIFICATION

### 1.1 Core Requirements
- JSON-based character save/load system in `src/cli_rpg/persistence.py`
- Multiple character saves support with unique filenames
- Integration with main menu's "Load Character" option
- Leverage existing `Character.to_dict()` and `Character.from_dict()` methods

### 1.2 File Storage Spec
- **Save Directory**: `saves/` in project root (create if not exists)
- **File Format**: `{character_name}_{timestamp}.json` (e.g., `Gandalf_20240101_120000.json`)
- **File Content**: JSON with character data from `Character.to_dict()`

### 1.3 Function Specifications

#### `save_character(character: Character, save_dir: str = "saves") -> str`
- Saves character to JSON file
- Creates save directory if it doesn't exist
- Generates unique filename with timestamp
- Returns full path to saved file
- Raises `IOError` on write failure

#### `load_character(filepath: str) -> Character`
- Loads character from JSON file
- Validates file exists and is readable
- Deserializes using `Character.from_dict()`
- Raises `FileNotFoundError` if file doesn't exist
- Raises `ValueError` if JSON is invalid or character data is corrupted

#### `list_saves(save_dir: str = "saves") -> list[dict[str, str]]`
- Lists all available character saves in directory
- Returns list of dicts with keys: `name`, `filepath`, `timestamp`
- Returns empty list if directory doesn't exist or is empty
- Sorts by timestamp (most recent first)

#### `delete_save(filepath: str) -> bool`
- Deletes a save file
- Returns True if successful, False if file doesn't exist
- Raises `OSError` on permission errors

### 1.4 Integration Points
- `main.py`: Update option "2" to show save selection menu
- `main.py`: Add option to save character after creation
- Character creation flow: Optional auto-save after confirmation

## 2. TEST DEVELOPMENT (TDD - Write Tests First)

### 2.1 Create Test File: `tests/test_persistence.py`

#### Test Class: `TestSaveCharacter`
1. `test_save_character_creates_file` - Verify file is created with correct name
2. `test_save_character_returns_filepath` - Returns valid path string
3. `test_save_character_creates_directory` - Creates save dir if missing
4. `test_save_character_unique_filenames` - Multiple saves create unique files
5. `test_save_character_valid_json` - File contains valid JSON
6. `test_save_character_contains_correct_data` - JSON matches character data
7. `test_save_character_custom_directory` - Respects custom save_dir parameter
8. `test_save_character_io_error` - Handles permission/write errors gracefully
9. `test_save_character_filename_sanitization` - Handles special chars in names

#### Test Class: `TestLoadCharacter`
1. `test_load_character_success` - Loads valid saved character
2. `test_load_character_restores_all_attributes` - All stats match original
3. `test_load_character_damaged_health` - Preserves reduced health state
4. `test_load_character_file_not_found` - Raises FileNotFoundError
5. `test_load_character_invalid_json` - Raises ValueError for malformed JSON
6. `test_load_character_missing_required_fields` - Raises ValueError
7. `test_load_character_invalid_stat_values` - Validates character constraints
8. `test_load_character_empty_file` - Handles empty file gracefully

#### Test Class: `TestListSaves`
1. `test_list_saves_empty_directory` - Returns empty list
2. `test_list_saves_nonexistent_directory` - Returns empty list
3. `test_list_saves_single_save` - Returns list with one entry
4. `test_list_saves_multiple_saves` - Returns all saves
5. `test_list_saves_sorted_by_timestamp` - Most recent first
6. `test_list_saves_correct_structure` - Each dict has name, filepath, timestamp
7. `test_list_saves_ignores_non_json` - Ignores non-JSON files
8. `test_list_saves_custom_directory` - Respects custom save_dir parameter

#### Test Class: `TestDeleteSave`
1. `test_delete_save_success` - Returns True and removes file
2. `test_delete_save_file_not_found` - Returns False
3. `test_delete_save_permission_error` - Raises OSError

#### Test Class: `TestIntegrationSaveLoad`
1. `test_round_trip_save_and_load` - Save then load produces identical character
2. `test_multiple_characters_save_load` - Multiple characters don't interfere
3. `test_save_load_with_special_states` - Edge cases (0 health, max stats, etc.)

### 2.2 Test Fixtures (in `tests/test_persistence.py`)
```python
@pytest.fixture
def temp_save_dir(tmp_path):
    """Provide temporary save directory for tests"""
    save_dir = tmp_path / "test_saves"
    return str(save_dir)

@pytest.fixture
def sample_character():
    """Provide sample character for testing"""
    return Character(name="TestHero", strength=10, dexterity=12, intelligence=8)

@pytest.fixture
def damaged_character():
    """Provide character with reduced health"""
    char = Character(name="WoundedHero", strength=15, dexterity=10, intelligence=10)
    char.take_damage(50)
    return char
```

## 3. IMPLEMENTATION

### 3.1 Create `src/cli_rpg/persistence.py`

#### Imports
```python
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from cli_rpg.models.character import Character
```

#### Helper Functions
1. `_sanitize_filename(name: str) -> str`
   - Remove/replace invalid filesystem characters
   - Replace spaces with underscores
   - Limit length to reasonable max (50 chars)

2. `_generate_filename(character_name: str) -> str`
   - Format: `{sanitized_name}_{timestamp}.json`
   - Timestamp format: `%Y%m%d_%H%M%S`

#### Core Functions (implement in order)

1. **`save_character()`**
   - Create Path object for save_dir
   - Create directory with `mkdir(parents=True, exist_ok=True)`
   - Generate filename using helper
   - Serialize character with `character.to_dict()`
   - Write JSON with `json.dump(f, indent=2)`
   - Handle IOError with descriptive message
   - Return full filepath as string

2. **`load_character()`**
   - Check file exists with `Path(filepath).exists()`
   - Open and parse JSON with `json.load()`
   - Catch `json.JSONDecodeError` and raise ValueError
   - Validate required keys exist in data
   - Use `Character.from_dict()` to deserialize
   - Catch Character validation errors and re-raise as ValueError
   - Return Character instance

3. **`list_saves()`**
   - Create Path object for save_dir
   - Check if directory exists
   - Use `glob("*.json")` to find all save files
   - Parse each filename to extract character name and timestamp
   - Build list of dicts with metadata
   - Sort by timestamp (parse timestamp string)
   - Return sorted list

4. **`delete_save()`**
   - Create Path object for filepath
   - Check if file exists
   - Use `Path.unlink()` to delete
   - Return True on success
   - Return False if FileNotFoundError
   - Let OSError propagate for permission issues

### 3.2 Update `src/cli_rpg/main.py`

#### Add Import
```python
from cli_rpg.persistence import save_character, load_character, list_saves
```

#### Add Helper Function: `prompt_save_character(character: Character) -> None`
- Ask user if they want to save
- Call `save_character()` if yes
- Display success message with filepath
- Handle exceptions gracefully

#### Add Helper Function: `select_and_load_character() -> Optional[Character]`
- Call `list_saves()` to get available saves
- Display numbered list to user
- Show: index, character name, timestamp
- Allow user to select by number or cancel
- Call `load_character()` with selected filepath
- Display loaded character summary
- Handle exceptions and show error messages
- Return loaded Character or None

#### Update `main()` Function
- After option "1" (Create New Character):
  - Add prompt to save character after successful creation
  - Call `prompt_save_character(current_character)`
  
- Replace option "2" (Load Character):
  - Remove stub message
  - Call `select_and_load_character()`
  - Assign result to `current_character` if not None
  - Display success message with character details

### 3.3 Run Tests and Iterate
1. Run `pytest tests/test_persistence.py -v`
2. Fix failing tests one by one
3. Ensure all tests pass
4. Run full test suite: `pytest tests/ -v`
5. Verify no regressions in existing tests

## 4. VERIFICATION

### 4.1 Unit Test Verification
- All tests in `test_persistence.py` pass
- Code coverage for `persistence.py` > 95%
- Edge cases handled correctly

### 4.2 Integration Test Verification
Create `tests/test_integration_persistence.py`:
1. `test_create_save_load_workflow` - Full workflow from main menu
2. `test_multiple_saves_list_and_load` - Create multiple, list, load specific one
3. `test_save_overwrite_protection` - Verify unique filenames prevent overwrites

### 4.3 Manual Testing Checklist
- [ ] Create character and save successfully
- [ ] Load saved character and verify stats
- [ ] Create multiple characters with same name (unique files)
- [ ] List saves shows all characters correctly
- [ ] Load character with damaged health preserves state
- [ ] Handle missing save directory gracefully
- [ ] Handle corrupted JSON file gracefully
- [ ] Handle non-existent file selection gracefully
- [ ] Cancel operations work correctly
- [ ] Special characters in names handled properly

## 5. IMPLEMENTATION ORDER SUMMARY

### Phase 1: Tests (TDD)
1. Create `tests/test_persistence.py` with all test cases
2. Create test fixtures
3. Run tests (all should fail - no implementation yet)

### Phase 2: Core Implementation
4. Create `src/cli_rpg/persistence.py`
5. Implement helper functions
6. Implement `save_character()` - run tests, iterate until passing
7. Implement `load_character()` - run tests, iterate until passing
8. Implement `list_saves()` - run tests, iterate until passing
9. Implement `delete_save()` - run tests, iterate until passing

### Phase 3: Integration
10. Update `src/cli_rpg/main.py` with helper functions
11. Integrate save prompt after character creation
12. Replace load character stub with full implementation
13. Create integration tests in `tests/test_integration_persistence.py`
14. Run all tests, fix any issues

### Phase 4: Final Verification
15. Run complete test suite
16. Perform manual testing
17. Verify all requirements met
