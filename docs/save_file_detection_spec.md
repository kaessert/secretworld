# Save File Type Detection Specification

## Overview
This specification defines how the system detects and loads different types of save files to ensure proper game state restoration while maintaining backward compatibility.

## Save File Types

### 1. Character-Only Save
**Structure:**
```json
{
  "name": "string",
  "strength": "integer",
  "dexterity": "integer", 
  "intelligence": "integer",
  "level": "integer",
  "health": "integer",
  "max_health": "integer"
}
```

**Characteristics:**
- Contains only character attributes
- No world or location data
- Legacy format from original implementation

### 2. Game State Save
**Structure:**
```json
{
  "character": {
    "name": "string",
    "strength": "integer",
    "dexterity": "integer",
    "intelligence": "integer",
    "level": "integer",
    "health": "integer",
    "max_health": "integer"
  },
  "world": {
    "locations": [...],
    "connections": [...]
  },
  "current_location": "string",
  "theme": "string"
}
```

**Characteristics:**
- Contains complete game state
- Includes world structure and connections
- Includes current location name
- Includes AI theme setting
- New format for full game persistence

## Detection Method

### Algorithm
1. Load JSON data from save file
2. Check for presence of "world" key in root object
3. If "world" key exists → Game State Save
4. If "world" key does not exist → Character-Only Save

### Function Signature
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
        ValueError: If JSON is invalid or corrupted
    """
```

## Loading Behavior

### Character-Only Save Loading
**When:** File contains only character data (no "world" key)

**Behavior:**
1. Load character using `load_character(filepath)`
2. Return character object
3. Game starts new adventure with default world
4. Starting location: "Town Square"
5. Theme: "fantasy" (default)

**Use Case:** Backward compatibility with existing saves

### Game State Save Loading
**When:** File contains complete game state (has "world" key)

**Behavior:**
1. Load complete game state using `load_game_state(filepath)`
2. Return GameState object
3. Game resumes from exact saved location
4. World structure is preserved
5. Theme is restored
6. AI service can be re-attached for continued world expansion

**Use Case:** Full game progress restoration

## Backward Compatibility

### Requirements
- All existing character-only saves MUST continue to work
- No modification of existing save files required
- Graceful degradation: character-only saves start new game
- No breaking changes to existing functionality

### Validation
- Test with fixture files (e.g., `tests/fixtures/legacy_character_save.json`)
- Verify character attributes are correctly loaded
- Verify new game starts with loaded character
- No errors or warnings for legacy format

## Error Handling

### Corrupted JSON
**Scenario:** File exists but contains invalid JSON

**Handling:**
- Catch JSON decode exceptions
- Raise ValueError with descriptive message
- Display user-friendly error in CLI
- Do not crash application

### Missing Keys
**Scenario:** JSON is valid but missing required keys

**Handling:**
- Character-only: Validate presence of name, strength, dexterity, intelligence, level, health, max_health
- Game state: Validate presence of character, world, current_location
- Raise appropriate error if validation fails
- Display which keys are missing

### File Not Found
**Scenario:** Filepath doesn't exist

**Handling:**
- Raise FileNotFoundError
- Display user-friendly error in CLI
- Return to save selection menu

### Invalid Data Types
**Scenario:** JSON structure is correct but data types are wrong

**Handling:**
- Let existing validation in Character and GameState classes handle it
- Catch and display validation errors
- Do not create invalid game objects

## Integration Points

### main.py Changes
- Update `select_and_load_character()` return type to tuple
- Add save type detection after file selection
- Conditional loading based on detected type
- Update main menu to handle both return types

### Theme Preservation
- Game state saves include theme attribute
- Theme is restored when loading game state
- Theme is passed to AI service for consistent world generation
- Default to "fantasy" for character-only saves

### AI Service Re-attachment
- When loading game state, AI service can be re-attached
- Allows continued dynamic world expansion
- Maintains consistency with saved theme
- Works even if AI service was not available at save time

## Testing Requirements

### Unit Tests
- Detect character-only save correctly
- Detect game state save correctly
- Handle corrupted JSON gracefully
- Handle missing files gracefully
- Handle invalid data types

### Integration Tests
- Load character-only save and start new game
- Load game state save and resume from exact location
- Verify world structure is preserved
- Verify theme is restored
- Verify character attributes are correct

### Backward Compatibility Tests
- Load real existing character-only saves
- Verify no errors or breaking changes
- Verify character is correctly restored
- Verify new game starts properly

### End-to-End Tests
- Complete save and load cycle
- Play → Save game state → Load → Continue playing
- Verify game progress is fully preserved
- Test with and without AI service

## Success Criteria

1. ✓ Can detect and load character-only saves
2. ✓ Can detect and load game state saves
3. ✓ Character-only saves start new game with loaded character
4. ✓ Game state saves restore complete game state
5. ✓ Existing saves work without modification
6. ✓ Corrupted files handled gracefully
7. ✓ Theme is preserved in game state loads
8. ✓ AI service can be re-attached
9. ✓ All tests pass
10. ✓ No breaking changes to existing functionality
