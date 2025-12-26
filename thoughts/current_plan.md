# Fix Fallback Location Names Including Coordinates

**Issue**: WFC Playtesting Issues #4 - HIGH PRIORITY
**Problem**: Location names like "Vast Prairie (-1, 0)" expose internal coordinates to players, breaking immersion.

## Spec

When AI generation fails and fallback location generation is used, location names should be immersive (not include coordinates). Names must still be unique within the world to avoid collisions.

**Approach**: Use direction-based suffixes for uniqueness instead of coordinates:
- First location: "Vast Prairie"
- Same base name at different location: "Vast Prairie East", "Vast Prairie North", etc.
- If direction suffix already used: "Vast Prairie Far East", "Vast Prairie Northern", etc.

## Changes

### 1. Add test for coordinate-free names
**File**: `tests/test_infinite_world_without_ai.py`

Add test to `TestGenerateFallbackLocation`:
```python
def test_fallback_location_name_excludes_coordinates(self):
    """Fallback names should NOT include coordinates (immersion).

    Spec: Location names must not expose internal grid coordinates.
    """
    source = Location(
        name="Town Square",
        description="A town square.",
        coordinates=(0, 0)
    )

    new_location = generate_fallback_location(
        direction="north",
        source_location=source,
        target_coords=(0, 1)
    )

    # Name should not contain coordinate patterns like "(0, 1)" or "(-1, 2)"
    import re
    coord_pattern = r'\(-?\d+,\s*-?\d+\)'
    assert not re.search(coord_pattern, new_location.name), \
        f"Location name '{new_location.name}' should not include coordinates"
```

### 2. Modify generate_fallback_location in world.py
**File**: `src/cli_rpg/world.py`

Replace lines 165-168:
```python
# Generate unique name with coordinate suffix to ensure uniqueness
base_name = random.choice(template["name_patterns"])
# Add coordinate suffix for uniqueness (e.g., "Wilderness (1, 2)")
location_name = f"{base_name} ({target_coords[0]}, {target_coords[1]})"
```

With direction-based naming:
```python
# Generate name with direction suffix for uniqueness (no coordinates)
base_name = random.choice(template["name_patterns"])

# Direction suffixes for uniqueness without exposing coordinates
DIRECTION_SUFFIXES = {
    "north": " North",
    "south": " South",
    "east": " East",
    "west": " West",
    "northeast": " Northeast",
    "northwest": " Northwest",
    "southeast": " Southeast",
    "southwest": " Southwest",
}

# Use direction as suffix if provided, otherwise just use base name
suffix = DIRECTION_SUFFIXES.get(direction, "")
location_name = f"{base_name}{suffix}"
```

## Test Command

```bash
pytest tests/test_infinite_world_without_ai.py::TestGenerateFallbackLocation -v
```
