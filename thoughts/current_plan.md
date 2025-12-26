# Implementation Plan: AI World Generation Hierarchy Support

## Summary
Update `ai_world.py` to generate locations with hierarchy fields (`is_overworld`, `parent_location`, `sub_locations`, `is_safe_zone`, `entry_point`), enabling AI-generated areas to support hierarchical navigation (`enter`/`exit` commands).

## Spec

### Location Hierarchy Fields
- `is_overworld: bool` - True for landmark locations (cities, dungeons, forests)
- `parent_location: Optional[str]` - Parent landmark name for sub-locations
- `sub_locations: List[str]` - Child location names for landmarks
- `is_safe_zone: bool` - No random encounters if True (towns, inns, shops)
- `entry_point: Optional[str]` - Default sub-location when entering

### Category-to-Hierarchy Mapping
Safe zones: `town`, `village`, `settlement` → `is_safe_zone=True`
Danger zones: `dungeon`, `wilderness`, `ruins`, `cave`, `forest`, `mountain` → `is_safe_zone=False`

### AI Prompt Updates
1. Update `DEFAULT_LOCATION_PROMPT` in `ai_config.py` to request hierarchy metadata
2. Update `_build_area_prompt` in `ai_service.py` to request hierarchy for area generation

### Parsing Updates
1. Update `_parse_location_response()` to extract hierarchy fields
2. Update `_validate_area_location()` to extract hierarchy fields from area responses

### Location Creation Updates
3 creation points in `ai_world.py`:
1. `create_ai_world()` - Starting location (~line 159)
2. `expand_world()` - Single location expansion (~line 388)
3. `expand_area()` - Area location creation (~line 544)

## Tests

### File: `tests/test_ai_world_hierarchy.py`

1. **test_create_ai_world_starting_location_has_hierarchy_fields**
   - Verify starting location has `is_overworld=True`, `is_safe_zone=True` (for town category)

2. **test_expand_world_location_has_hierarchy_fields**
   - Verify expanded location inherits proper hierarchy from AI response

3. **test_expand_area_locations_have_hierarchy_fields**
   - Verify all area locations have appropriate hierarchy fields

4. **test_safe_zone_category_mapping**
   - Verify town/village/settlement categories → `is_safe_zone=True`
   - Verify dungeon/cave/wilderness categories → `is_safe_zone=False`

5. **test_hierarchy_fields_default_when_ai_missing**
   - Verify graceful defaults when AI response omits hierarchy fields

6. **test_area_entry_location_is_overworld**
   - Verify entry location in area has `is_overworld=True`

## Implementation Steps

### Step 1: Update AI Prompts

**File: `src/cli_rpg/ai_config.py`**
- Add hierarchy fields to `DEFAULT_LOCATION_PROMPT` JSON schema
- Add `is_overworld`, `is_safe_zone` to required response fields

### Step 2: Update AI Response Parsing

**File: `src/cli_rpg/ai_service.py`**
- `_parse_location_response()`: Extract `is_overworld`, `is_safe_zone` from response
- `_validate_area_location()`: Extract hierarchy fields from area location
- `_build_area_prompt()`: Add hierarchy requirements to area prompt

### Step 3: Update Location Creation in `ai_world.py`

**File: `src/cli_rpg/ai_world.py`**

1. **Helper function** `_infer_hierarchy_from_category()`:
   ```python
   def _infer_hierarchy_from_category(category: Optional[str]) -> tuple[bool, bool]:
       """Infer is_overworld and is_safe_zone from category."""
       safe_categories = {"town", "village", "settlement"}
       is_safe = category in safe_categories if category else False
       return (True, is_safe)  # All AI-generated are overworld by default
   ```

2. **Update `create_ai_world()`** (~line 159):
   - Set hierarchy fields on starting location based on category
   - Starting location defaults: `is_overworld=True`, `is_safe_zone=True`

3. **Update `expand_world()`** (~line 388):
   - Extract hierarchy fields from `location_data`
   - Pass to Location constructor

4. **Update `expand_area()`** (~line 544):
   - Entry location (rel 0,0): `is_overworld=True`
   - Other locations: `is_overworld=False`, `parent_location=entry_name`
   - Set `is_safe_zone` based on category
   - Set entry location's `sub_locations` list
   - Set entry location's `entry_point` to first sub-location

### Step 4: Write Tests

**File: `tests/test_ai_world_hierarchy.py`**
- Create test class `TestAIWorldHierarchy`
- Mock `AIService.generate_location()` to return responses with hierarchy data
- Test all 3 creation paths in `ai_world.py`
