# Implementation Plan: Named vs Unnamed Location System

## Summary
Distinguish between generic terrain tiles (unnamed - cheap/instant templates) and story-important POIs (named - full AI generation). Target ratio: ~1 named per 10-20 unnamed tiles.

## Spec

**Core Concept:**
- **Unnamed locations**: Generic terrain (forest, plains, road) - use template descriptions, no AI calls
- **Named locations**: Story POIs (towns, dungeons, temples) - full AI generation with LayeredContext

**Location Model Changes:**
- Add `is_named: bool = False` field (True for POIs, False for terrain filler)
- Add `terrain_type: Optional[str] = None` field (from WFC: "forest", "plains", etc.)
- Unnamed locations get template descriptions based on terrain_type

**Named Location Triggers:**
1. Every N tiles (configurable, default 15)
2. Special terrain (mountains, swamps → higher POI chance)
3. Region landmarks (town every ~50 tiles)
4. Player-discovered secrets

## Test Plan (TDD)

**File: `tests/test_named_locations.py`**

| Test | Description |
|------|-------------|
| `test_location_is_named_defaults_false` | Location.is_named defaults to False |
| `test_location_terrain_type_defaults_none` | Location.terrain_type defaults to None |
| `test_location_serialization_with_is_named` | is_named survives to_dict/from_dict |
| `test_location_serialization_with_terrain_type` | terrain_type survives to_dict/from_dict |
| `test_unnamed_template_forest` | Unnamed forest location gets forest template |
| `test_unnamed_template_plains` | Unnamed plains location gets plains template |
| `test_should_generate_named_every_n_tiles` | Named location triggers every N tiles |
| `test_should_generate_named_mountain_terrain` | Mountain terrain has higher named chance |
| `test_fallback_creates_unnamed_location` | `generate_fallback_location` creates unnamed |

**File: `tests/test_unnamed_templates.py`**

| Test | Description |
|------|-------------|
| `test_get_unnamed_template_forest` | Returns forest-themed description |
| `test_get_unnamed_template_plains` | Returns plains-themed description |
| `test_get_unnamed_template_all_terrains` | All terrain types have templates |
| `test_unnamed_template_has_valid_name` | Template name is 2-50 chars |
| `test_unnamed_template_has_valid_description` | Template description is 1-500 chars |

## Implementation Steps

### Step 1: Add Location Model Fields

**File: `src/cli_rpg/models/location.py`**

Add after line 56 (`terrain: Optional[str] = None`):
```python
is_named: bool = False  # True for story-important POIs, False for terrain filler
```

Update `to_dict()` (around line 375):
```python
if self.is_named:
    data["is_named"] = self.is_named
```

Update `from_dict()` (around line 427):
```python
is_named = data.get("is_named", False)
```

And add to the constructor call.

### Step 2: Create Unnamed Location Templates

**File: `src/cli_rpg/world_tiles.py`**

Add after line 101 (after TERRAIN_TO_CATEGORY):

```python
# Unnamed location templates by terrain type
# Each terrain has a list of (name_template, description_template) tuples
UNNAMED_LOCATION_TEMPLATES: Dict[str, List[tuple[str, str]]] = {
    "forest": [
        ("Dense Woods", "Tall trees crowd together, their canopy blocking most sunlight."),
        ("Wooded Trail", "A narrow path winds through towering oaks and elms."),
        ("Forest Clearing", "A small gap in the trees lets dappled light through."),
    ],
    "mountain": [
        ("Rocky Pass", "Jagged peaks rise on either side of this narrow mountain trail."),
        ("Steep Cliffs", "The path hugs a sheer rock face, wind howling past."),
        ("Alpine Meadow", "A grassy plateau offers respite between stone peaks."),
    ],
    "plains": [
        ("Open Grassland", "Tall grass sways in the wind under an open sky."),
        ("Rolling Hills", "Gentle slopes covered in wildflowers stretch to the horizon."),
        ("Dusty Road", "A well-worn path cuts through the flat landscape."),
    ],
    "water": [
        ("Riverbank", "The sound of rushing water fills the air."),
    ],
    "desert": [
        ("Sand Dunes", "Endless waves of golden sand shimmer in the heat."),
        ("Rocky Desert", "Cracked earth and scattered boulders dot the wasteland."),
        ("Desert Trail", "A faint path marks where others have crossed before."),
    ],
    "swamp": [
        ("Murky Bog", "Dark water pools between twisted, moss-covered trees."),
        ("Fetid Marsh", "The air hangs thick with moisture and decay."),
        ("Swamp Trail", "Rotting planks form a rickety path over the mire."),
    ],
    "hills": [
        ("Grassy Knoll", "A gentle slope offers a view of the surrounding land."),
        ("Hilltop Path", "The trail winds up and down rolling terrain."),
        ("Valley Floor", "You walk between two grass-covered rises."),
    ],
    "beach": [
        ("Sandy Shore", "Waves lap at the golden sand beneath your feet."),
        ("Rocky Beach", "Tide pools dot the coast between weathered stones."),
        ("Coastal Path", "A trail follows the line where land meets sea."),
    ],
    "foothills": [
        ("Mountain Base", "The terrain rises sharply toward distant peaks."),
        ("Foothill Trail", "A winding path leads up from the lowlands."),
        ("Rocky Slope", "Scattered boulders mark the transition to mountains."),
    ],
}

def get_unnamed_location_template(terrain: str) -> tuple[str, str]:
    """Get a random unnamed location template for a terrain type.

    Args:
        terrain: Terrain type (forest, plains, mountain, etc.)

    Returns:
        Tuple of (name, description) for the unnamed location
    """
    import random
    templates = UNNAMED_LOCATION_TEMPLATES.get(terrain, UNNAMED_LOCATION_TEMPLATES["plains"])
    return random.choice(templates)
```

### Step 3: Add Named Location Trigger Logic

**File: `src/cli_rpg/world_tiles.py`**

Add after the template function:

```python
# Configuration for named location generation
NAMED_LOCATION_CONFIG = {
    "base_interval": 15,  # Generate named location every N tiles on average
    "terrain_modifiers": {
        # Terrain types more likely to have POIs
        "mountain": 0.6,  # 60% of base interval → more POIs
        "swamp": 0.7,
        "foothills": 0.8,
        "forest": 1.0,  # Normal
        "plains": 1.2,  # Slightly fewer POIs
        "hills": 1.0,
        "beach": 0.8,
        "desert": 0.9,
        "water": 999.0,  # Never (impassable)
    },
}

def should_generate_named_location(
    tiles_since_named: int,
    terrain: str,
    rng: Optional[random.Random] = None
) -> bool:
    """Determine if a named location should be generated.

    Uses a probability curve that increases with tiles since last named.
    Terrain type modifies the effective interval.

    Args:
        tiles_since_named: Number of tiles traveled since last named location
        terrain: Current terrain type
        rng: Optional random number generator for determinism

    Returns:
        True if a named location should be generated
    """
    if rng is None:
        rng = random.Random()

    base_interval = NAMED_LOCATION_CONFIG["base_interval"]
    modifier = NAMED_LOCATION_CONFIG["terrain_modifiers"].get(terrain, 1.0)
    effective_interval = base_interval * modifier

    # Probability increases linearly from 0 at tile 0 to 100% at 2x interval
    # At interval, probability is 50%
    probability = min(1.0, tiles_since_named / (effective_interval * 2))

    return rng.random() < probability
```

### Step 4: Update Fallback Generation to Create Unnamed Locations

**File: `src/cli_rpg/world.py`**

Modify `generate_fallback_location()` to create unnamed locations:

```python
def generate_fallback_location(
    direction: str,
    source_location: Location,
    target_coords: tuple[int, int],
    terrain: Optional[str] = None,
    chunk_manager: Optional["ChunkManager"] = None,
    tiles_since_named: int = 0,  # NEW parameter
) -> Location:
    """Generate a fallback location when AI is unavailable.

    Creates unnamed terrain locations by default. Named locations are
    generated based on tile count and terrain type.
    """
    from cli_rpg.world_tiles import (
        get_unnamed_location_template,
        should_generate_named_location,
        TERRAIN_TO_CATEGORY,
    )

    # Determine if this should be a named location
    is_named = should_generate_named_location(tiles_since_named, terrain or "plains")

    if is_named:
        # Generate a named location (existing behavior with templates)
        # ... existing named location logic ...
    else:
        # Generate an unnamed terrain location
        name, description = get_unnamed_location_template(terrain or "plains")
        # Make name unique by appending coordinates
        unique_name = f"{name} ({target_coords[0]}, {target_coords[1]})"

        category = TERRAIN_TO_CATEGORY.get(terrain, "wilderness")

        return Location(
            name=unique_name,
            description=description,
            connections={get_opposite_direction(direction): source_location.name},
            coordinates=target_coords,
            category=category,
            terrain=terrain,
            is_named=False,
        )
```

### Step 5: Track tiles_since_named in GameState

**File: `src/cli_rpg/game_state.py`**

Add tracking field (around line 280):
```python
self.tiles_since_named: int = 0  # Tiles traveled since last named location
```

Update in `move()` method after successful move:
```python
# Track tiles for named location generation
if not target_location.is_named:
    self.tiles_since_named += 1
else:
    self.tiles_since_named = 0
```

Add to `to_dict()` and `from_dict()` for persistence.

### Step 6: Update AI Generation to Mark Locations as Named

**File: `src/cli_rpg/ai_world.py`**

In `expand_world()` and `expand_area()`, set `is_named=True` for AI-generated locations:

```python
new_location = Location(
    name=location_data["name"],
    description=location_data["description"],
    # ... other fields ...
    is_named=True,  # AI-generated locations are always named
)
```

## Files to Modify

| File | Change |
|------|--------|
| `tests/test_named_locations.py` | NEW - Tests for is_named field and triggers |
| `tests/test_unnamed_templates.py` | NEW - Tests for template system |
| `src/cli_rpg/models/location.py` | Add `is_named` field, serialization |
| `src/cli_rpg/world_tiles.py` | Add templates and trigger logic |
| `src/cli_rpg/world.py` | Update fallback to create unnamed locations |
| `src/cli_rpg/game_state.py` | Track `tiles_since_named`, pass to generation |
| `src/cli_rpg/ai_world.py` | Mark AI-generated locations as `is_named=True` |
