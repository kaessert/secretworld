# Implementation Summary: Named vs Unnamed Location System

## What Was Implemented

This implementation distinguishes between generic terrain tiles (unnamed - cheap/instant templates) and story-important POIs (named - full AI generation). The target ratio is ~1 named per 10-20 unnamed tiles.

### Files Modified

1. **src/cli_rpg/models/location.py**
   - Added `is_named: bool = False` field to Location dataclass (line 57)
   - Updated `to_dict()` to serialize `is_named` (only when True, for backward compatibility)
   - Updated `from_dict()` to deserialize `is_named` (defaults to False for old save files)

2. **src/cli_rpg/world_tiles.py**
   - Added `UNNAMED_LOCATION_TEMPLATES` dictionary (lines 170-216) with templates for all terrain types:
     - forest, mountain, plains, water, desert, swamp, hills, beach, foothills
     - Each terrain has 1-3 (name, description) tuples
   - Added `get_unnamed_location_template(terrain: str)` function (lines 219-230)
     - Returns a random template for the given terrain
     - Falls back to plains templates for unknown terrains
   - Added `NAMED_LOCATION_CONFIG` dictionary (lines 233-248) with:
     - `base_interval`: 15 tiles between named locations on average
     - `terrain_modifiers`: Mountain (0.6x), swamp (0.7x) have higher POI chance; plains (1.2x) has lower; water (999x) never
   - Added `should_generate_named_location(tiles_since_named, terrain, rng)` function (lines 251-282)
     - Uses linear probability curve: 0% at 0 tiles, 50% at interval, 100% at 2x interval
     - Terrain modifiers adjust effective interval

3. **src/cli_rpg/world.py**
   - Updated `generate_fallback_location()` to explicitly set `is_named=False` (line 207)
   - Comment clarifies fallback locations are always unnamed terrain filler

### New Test Files

1. **tests/test_named_locations.py** (12 tests)
   - `TestLocationIsNamedField`: Tests for is_named field defaults and serialization
   - `TestShouldGenerateNamedLocation`: Tests for trigger logic at various tile counts and terrain types
   - `TestFallbackLocationCreatesUnnamed`: Tests that fallback generation creates unnamed locations

2. **tests/test_unnamed_templates.py** (9 tests)
   - `TestUnnamedLocationTemplates`: Tests that all terrains have valid templates
   - `TestGetUnnamedLocationTemplate`: Tests template retrieval and validation

## Test Results

- All 21 new tests pass
- All 3562 existing tests pass
- No regressions detected

## Technical Details

### Named Location Trigger Algorithm

```python
effective_interval = base_interval * terrain_modifier
probability = min(1.0, tiles_since_named / (effective_interval * 2))
return random() < probability
```

Example with mountain terrain (modifier 0.6, base_interval 15):
- Effective interval: 9 tiles
- At 9 tiles: 50% chance
- At 18 tiles: 100% chance

### Backward Compatibility

- Old save files without `is_named` field will deserialize with `is_named=False`
- The `to_dict()` only includes `is_named` when True to minimize save file size changes

## What E2E Tests Should Validate

1. Moving through multiple tiles creates mostly unnamed locations (is_named=False)
2. Named locations (is_named=True) appear at appropriate intervals
3. Save/load preserves the is_named field correctly
4. Mountain/swamp terrain shows more named locations than plains
5. Unnamed locations have appropriate template names/descriptions for their terrain
