# Fix: Invalid "down" connection in AI-generated locations

## Problem
The AI world generator creates locations with `down` (and `up`) as exit directions, but the game's grid-based movement system only supports cardinal directions (north, south, east, west). The `DIRECTION_OFFSETS` in `world_grid.py` only has entries for the 4 cardinal directions, so `up`/`down` connections cannot be placed on the grid.

Example from ISSUES.md:
```
Neon Nexus
Exits: down, north, south
```

## Root Cause Analysis

1. **`Location.VALID_DIRECTIONS`** includes 6 directions: `{"north", "south", "east", "west", "up", "down"}`
2. **`ai_service._parse_location_response()`** validates against `Location.VALID_DIRECTIONS`, so it accepts `up`/`down`
3. **`DIRECTION_OFFSETS`** in `world_grid.py` only has 4 cardinal directions
4. **`ai_world.py`** has some filtering (e.g., `if direction in DIRECTION_OFFSETS`) but not consistently applied

The fix should be applied at the parsing/validation layer in `ai_service.py` to reject non-cardinal directions before they ever enter the system.

## Implementation Plan

### 1. Add constant for grid-valid directions in `ai_service.py`

```python
# Valid directions for grid-based movement (subset of Location.VALID_DIRECTIONS)
GRID_DIRECTIONS: set[str] = {"north", "south", "east", "west"}
```

### 2. Modify `_parse_location_response()` to filter invalid directions

In `ai_service.py`, update the connection validation to:
1. Filter out non-cardinal directions instead of raising an error (graceful handling)
2. Log a warning when filtering occurs

```python
# Filter connections to only include cardinal directions
filtered_connections = {}
for direction, target in connections.items():
    if direction in GRID_DIRECTIONS:
        filtered_connections[direction] = target
    else:
        # Log but don't fail - AI sometimes generates up/down
        logger.warning(
            f"Filtered non-grid direction '{direction}' from location '{name}'"
        )

# Return filtered connections
return {
    "name": name,
    "description": description,
    "connections": filtered_connections
}
```

### 3. Update `_validate_area_location()` similarly

The area generation validation at line 620 already correctly uses `valid_directions = {"north", "south", "east", "west"}` but raises an error. Change to filter instead of raise:

```python
# Filter connections to only cardinal directions (no up/down)
valid_directions = {"north", "south", "east", "west"}
filtered_connections = {}
for direction, target in connections.items():
    if direction in valid_directions:
        filtered_connections[direction] = target
    # Non-cardinal directions are silently dropped
```

## Tests

### File: `tests/test_ai_service.py`

Add tests:

1. **`test_generate_location_filters_non_cardinal_directions()`**
   - Mock AI response with `{"north": "A", "down": "B", "east": "C"}`
   - Verify returned connections only contains `{"north": "A", "east": "C"}`

2. **`test_generate_location_filters_up_direction()`**
   - Mock AI response with `{"up": "Sky Tower", "south": "Ground Floor"}`
   - Verify returned connections only contains `{"south": "Ground Floor"}`

3. **`test_generate_area_filters_non_cardinal_directions()`**
   - Mock area response with locations containing `down` exits
   - Verify all returned locations have only cardinal directions

## Files to Modify

1. `src/cli_rpg/ai_service.py` - Add filtering in `_parse_location_response()` and `_validate_area_location()`
2. `tests/test_ai_service.py` - Add 3 new tests
