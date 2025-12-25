# Implementation Plan: ASCII Art for Locations

## Summary
Add ASCII art display for locations when players enter/look, following the established pattern from monster ASCII art (commit 74b71f2).

## Files to Modify/Create

### 1. Model: `src/cli_rpg/models/location.py`
- Add `ascii_art: str = ""` field to `Location` dataclass (after `category` field)
- Add `ascii_art` to `to_dict()` serialization (only when non-empty, for backward compatibility)
- Add `ascii_art` to `from_dict()` with `.get("ascii_art", "")` fallback
- Update `__str__()` to display ASCII art after name, before description

### 2. Fallback Templates: `src/cli_rpg/location_art.py` (new file)
Create category-based fallback templates (similar to combat.py enemy art):
```python
# Templates for each location category:
# - town: buildings/houses
# - village: small settlement
# - forest: trees
# - dungeon: dark entrance/walls
# - cave: cavern opening
# - ruins: crumbling structures
# - mountain: peaks
# - wilderness: open landscape
# - settlement: mixed buildings

def get_fallback_location_ascii_art(category: Optional[str], location_name: str) -> str
```
- 5-10 lines tall, max 50 chars wide (slightly larger than enemy art)
- Match on category first, then fall back to name-based detection

### 3. AI Config: `src/cli_rpg/ai_config.py`
Add prompt template:
```python
DEFAULT_LOCATION_ASCII_ART_PROMPT = """Generate ASCII art for a {theme} RPG location.

Location Name: {location_name}
Category: {location_category}
Description: {location_description}

Requirements:
1. Create ASCII art that is 6-10 lines tall
2. Maximum 50 characters wide per line
3. Use only ASCII characters
4. Represent the location's key visual features
5. Keep it simple but atmospheric

Respond with ONLY the ASCII art, no explanation."""
```

### 4. AI Service: `src/cli_rpg/ai_service.py`
Add method:
```python
def generate_location_ascii_art(
    self,
    location_name: str,
    location_description: str,
    location_category: Optional[str],
    theme: str
) -> str:
```
- Similar implementation to `generate_ascii_art()` for enemies
- Use `_parse_location_ascii_art_response()` with validation (min 3 lines, max 10 lines, max 50 chars width)

### 5. AI World: `src/cli_rpg/ai_world.py`
Modify location creation to generate ASCII art:
- In `create_ai_world()`: After creating location, call AI to generate art (or fallback)
- In `expand_world()`: Same pattern
- In `expand_area()`: Same pattern for each location

Import `get_fallback_location_ascii_art` for fallback when AI unavailable.

### 6. Tests: `tests/test_location_ascii_art.py` (new file)
Mirror test structure from `tests/test_ascii_art.py`:
- `TestLocationModelAsciiArt`: field storage, to_dict, from_dict, default value
- `TestFallbackLocationAsciiArt`: each category produces valid art
- `TestLocationDisplayAsciiArt`: `__str__()` includes art when present
- `TestAILocationAsciiArtGeneration`: mocked AI generation

## Implementation Order

1. **Tests first** (`tests/test_location_ascii_art.py`):
   - Write tests for Location model `ascii_art` field
   - Write tests for fallback art function
   - Write tests for display in `__str__()`
   - Write tests for AI generation (mocked)

2. **Location model** (`src/cli_rpg/models/location.py`):
   - Add `ascii_art` field
   - Update serialization
   - Update `__str__()` display

3. **Fallback templates** (`src/cli_rpg/location_art.py`):
   - Create 9 category templates
   - Implement `get_fallback_location_ascii_art()`

4. **AI config** (`src/cli_rpg/ai_config.py`):
   - Add `DEFAULT_LOCATION_ASCII_ART_PROMPT`

5. **AI service** (`src/cli_rpg/ai_service.py`):
   - Add `generate_location_ascii_art()` method
   - Add `_parse_location_ascii_art_response()` helper

6. **AI world integration** (`src/cli_rpg/ai_world.py`):
   - Add ASCII art generation to location creation
   - Add fallback handling

7. **Run all tests** to verify nothing breaks

## Key Patterns to Follow

- Use empty string default for backward compatibility with existing saves
- Only serialize when non-empty (like coordinates/category)
- AI generation with graceful fallback to templates
- Templates matched by category first, then name keywords
- Validation: min 3 lines, max 10 lines, max 50 chars width
