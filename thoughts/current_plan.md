# Implementation Plan: AI Location Category Generation

## Summary
Update the AI service to include `category` field when generating locations, completing the Location Categories feature so combat's `spawn_enemy()` can leverage location-appropriate enemies during AI-generated world exploration.

## Spec

The AI location generation must return a `category` field alongside `name`, `description`, and `connections`. Valid categories are: `town`, `dungeon`, `wilderness`, `settlement`, `ruins`, `cave`, `forest`, `mountain`, `village`. The category should be contextually appropriate based on the location's name/description and world theme.

**Note:** The `Location` model already has the `category` field (line 37) and `combat.py` already uses it (lines 298-348). This plan focuses on having the AI populate this field.

## Test Plan (TDD)

### File: `tests/test_ai_location_category.py`

1. **Test AI returns category field** - Verify `generate_location()` returns dict with `category` key
2. **Test AI validates category values** - Valid categories accepted; invalid/missing defaults to `None`
3. **Test category passed to Location in create_ai_world** - `ai_world.py` creates Location with category
4. **Test category passed to Location in expand_world** - expansion preserves category from AI
5. **Test area generation includes category** - `generate_area()` returns category for each location
6. **Test prompt includes category instruction** - Verify prompt template asks for category field

## Implementation Steps

### Step 1: Update `ai_config.py` - Modify Default Prompt Templates

**File:** `src/cli_rpg/ai_config.py`
**Location:** Lines 14-37 (`DEFAULT_LOCATION_PROMPT`)

Add to requirements section:
```
7. Include a category for the location type (one of: town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village)
```

Update JSON response format:
```json
{
  "name": "Location Name",
  "description": "A detailed description...",
  "connections": {"direction": "location_name"},
  "category": "wilderness"
}
```

### Step 2: Update `ai_service.py` - Parse and Validate Category

**File:** `src/cli_rpg/ai_service.py`

**2a. Update `_parse_location_response()` (lines 331-398)**
- Extract `category` from response (optional field)
- Define valid categories constant: `VALID_LOCATION_CATEGORIES`
- Validate category is in allowed list, else set to `None`
- Include `category` in returned dict

**2b. Update `_validate_area_location()` (lines 669-740)**
- Apply same category extraction/validation for area generation
- Include `category` in returned dict for each location

### Step 3: Update Area Generation Prompt

**File:** `src/cli_rpg/ai_service.py`
**Location:** `_build_area_prompt()` (lines 561-632)

Add category requirement and update JSON format in the area generation prompt.

### Step 4: Update `ai_world.py` - Pass Category to Location

**File:** `src/cli_rpg/ai_world.py`

**4a. Update `create_ai_world()` (around line 82-86)**
```python
starting_location = Location(
    name=starting_data["name"],
    description=starting_data["description"],
    connections={},
    category=starting_data.get("category")
)
```

**4b. Update `create_ai_world()` (around line 162-166)**
Same for locations generated during initial world creation loop.

**4c. Update `expand_world()` (around line 269-274)**
```python
new_location = Location(
    name=location_data["name"],
    description=location_data["description"],
    connections={},
    coordinates=new_coordinates,
    category=location_data.get("category")
)
```

**4d. Update `expand_area()` (around line 412-417)**
```python
new_loc = Location(
    name=loc_data["name"],
    description=loc_data["description"],
    connections={},
    coordinates=(abs_x, abs_y),
    category=loc_data.get("category")
)
```

## Validation

```bash
# Run new tests
pytest tests/test_ai_location_category.py -v

# Run existing AI tests to ensure no regression
pytest tests/test_ai_service.py -v
pytest tests/test_ai_world_generation.py -v

# Full test suite
pytest --cov=src/cli_rpg
```
