# Plan: Make All Named Locations Enterable

## Summary
Add wilderness enterable categories (grove, waystation, campsite, hollow, overlook) and ensure named locations always use an enterable category so players never encounter "You cannot enter here" on named locations.

## Scope
**MEDIUM** - Updates to world_tiles.py, world_grid.py, and location generation logic

---

## Spec

### Problem
Named locations (`is_named=True`) may have non-enterable categories like "forest", "wilderness", "mountain", causing players to see "There's nothing to enter here. This is open wilderness." when trying to enter a named POI.

### Solution
1. Add new wilderness enterable categories for small exploration areas
2. Ensure named locations always assign an enterable category
3. Update SUBGRID_BOUNDS for new categories

### Acceptance Criteria
- [ ] All named locations can be entered (no "You cannot enter here" for named places)
- [ ] New wilderness categories: grove, waystation, campsite, hollow, overlook
- [ ] SubGrid bounds defined for new categories (small 3x3 or 5x5)
- [ ] Existing tests pass; new test validates named → enterable invariant

---

## Implementation Steps

### 1. Add New Enterable Categories
**File**: `src/cli_rpg/world_tiles.py`

Add to `ENTERABLE_CATEGORIES`:
```python
ENTERABLE_CATEGORIES: frozenset = frozenset({
    # Adventure locations
    "dungeon", "cave", "ruins", "temple", "tomb", "mine", "crypt", "tower",
    # Sacred/ancient locations
    "monastery", "shrine",
    # Settlements
    "town", "village", "city", "settlement", "outpost", "camp",
    # Commercial buildings
    "tavern", "shop", "inn",
    # NEW: Wilderness POIs (small explorable areas)
    "grove",       # Forest clearing with druid/hermit
    "waystation",  # Mountain/road rest stop
    "campsite",    # Wilderness camp
    "hollow",      # Hidden forest area
    "overlook",    # Scenic viewpoint with structure
})
```

### 2. Add SubGrid Bounds for New Categories
**File**: `src/cli_rpg/world_grid.py`

Add to `SUBGRID_BOUNDS`:
```python
SUBGRID_BOUNDS: Dict[str, Tuple[int, int, int, int, int, int]] = {
    # ... existing entries ...
    # NEW: Tiny wilderness POIs (3x3, single level)
    "grove": (-1, 1, -1, 1, 0, 0),      # Forest clearing
    "waystation": (-1, 1, -1, 1, 0, 0), # Road rest stop
    "campsite": (-1, 1, -1, 1, 0, 0),   # Wilderness camp
    "hollow": (-1, 1, -1, 1, 0, 0),     # Hidden area
    "overlook": (-1, 1, -1, 1, 0, 0),   # Viewpoint
}
```

### 3. Create Category Mapping for Terrain → Enterable Fallback
**File**: `src/cli_rpg/world_tiles.py`

Add new mapping from non-enterable to enterable categories:
```python
# Maps non-enterable categories to appropriate enterable alternatives
# Used when a named location has a non-enterable category
WILDERNESS_ENTERABLE_FALLBACK: Dict[str, str] = {
    "forest": "grove",       # Forest → grove clearing
    "wilderness": "campsite", # Generic wilderness → campsite
    "mountain": "waystation", # Mountain → waystation
    "desert": "campsite",    # Desert → oasis campsite
    "swamp": "hollow",       # Swamp → hidden hollow
    "beach": "campsite",     # Beach → coastal campsite
    "plains": "waystation",  # Plains → road waystation
    "hills": "overlook",     # Hills → scenic overlook
}

def get_enterable_category(category: Optional[str], terrain: Optional[str] = None) -> str:
    """Get an enterable category, converting non-enterable if needed.

    If category is already enterable, returns it unchanged.
    If category is not enterable, uses terrain-based fallback.
    If no fallback found, defaults to "campsite".

    Args:
        category: Location category (may be non-enterable)
        terrain: Terrain type for fallback selection

    Returns:
        An enterable category string
    """
    if category is not None and is_enterable_category(category):
        return category

    # Try terrain-based fallback
    if terrain is not None:
        fallback = WILDERNESS_ENTERABLE_FALLBACK.get(terrain.lower())
        if fallback:
            return fallback

    # Try category as terrain fallback
    if category is not None:
        fallback = WILDERNESS_ENTERABLE_FALLBACK.get(category.lower())
        if fallback:
            return fallback

    # Default fallback
    return "campsite"
```

### 4. Update Named Location Generation to Use Enterable Categories
**File**: `src/cli_rpg/game_state.py`

In the `move()` method where named locations are created, ensure category is enterable:

```python
# After line ~870, before creating fallback location:
from cli_rpg.world_tiles import get_enterable_category

# Ensure named locations have enterable categories
if is_named:
    category_hint = get_enterable_category(category_hint, terrain)
```

**File**: `src/cli_rpg/world.py`

In `generate_fallback_location()`:
```python
# After determining category, ensure it's enterable for named locations
if is_named:
    from cli_rpg.world_tiles import get_enterable_category
    category = get_enterable_category(category, terrain)
```

### 5. Update AI Area Generation to Use Enterable Categories
**File**: `src/cli_rpg/ai_world.py`

In `expand_area()` and `expand_world()`, ensure AI-generated named locations use enterable categories:
```python
# When processing AI response for named locations:
if new_is_named:
    from cli_rpg.world_tiles import get_enterable_category
    new_category = get_enterable_category(new_category, terrain_type)
```

### 6. Add Fallback Room Templates for New Categories
**File**: `src/cli_rpg/fallback_content.py`

Add templates for new wilderness categories:
```python
# In ROOM_CONTENT dict, add entries for grove, waystation, etc.
"grove": {
    RoomType.ENTRY: [
        ("Clearing Edge", "A small clearing opens in the forest canopy."),
        ("Grove Entrance", "Ancient trees form a natural archway."),
    ],
    # ... other room types
},
"waystation": {
    RoomType.ENTRY: [
        ("Rest Stop", "A simple shelter offers respite from travel."),
        ("Traveler's Post", "A weathered signpost marks this waystation."),
    ],
},
# ... similar for campsite, hollow, overlook
```

### 7. Write Test for Named → Enterable Invariant
**File**: `tests/test_named_locations_enterable.py`

```python
"""Test that all named locations have enterable categories."""
import pytest
from cli_rpg.world_tiles import ENTERABLE_CATEGORIES, get_enterable_category
from cli_rpg.models.location import Location


def test_get_enterable_category_returns_enterable():
    """Verify get_enterable_category always returns an enterable category."""
    test_cases = [
        ("dungeon", None),      # Already enterable
        ("forest", "forest"),    # Non-enterable → grove
        ("wilderness", "plains"), # Non-enterable → waystation
        (None, "swamp"),         # No category → hollow
        (None, None),            # No info → campsite
    ]

    for category, terrain in test_cases:
        result = get_enterable_category(category, terrain)
        assert result.lower() in ENTERABLE_CATEGORIES, \
            f"get_enterable_category({category!r}, {terrain!r}) = {result!r} not enterable"


def test_wilderness_categories_in_enterable():
    """Verify new wilderness categories are in ENTERABLE_CATEGORIES."""
    wilderness_categories = {"grove", "waystation", "campsite", "hollow", "overlook"}
    for cat in wilderness_categories:
        assert cat in ENTERABLE_CATEGORIES, f"{cat} not in ENTERABLE_CATEGORIES"


def test_all_wilderness_fallbacks_are_enterable():
    """Verify WILDERNESS_ENTERABLE_FALLBACK values are all enterable."""
    from cli_rpg.world_tiles import WILDERNESS_ENTERABLE_FALLBACK

    for source, target in WILDERNESS_ENTERABLE_FALLBACK.items():
        assert target in ENTERABLE_CATEGORIES, \
            f"Fallback {source} → {target} is not enterable"
```

---

## Files Changed
1. `src/cli_rpg/world_tiles.py` - Add new categories, fallback mapping, helper function
2. `src/cli_rpg/world_grid.py` - Add SUBGRID_BOUNDS for new categories
3. `src/cli_rpg/game_state.py` - Ensure named locations use enterable categories
4. `src/cli_rpg/world.py` - Update generate_fallback_location for named locations
5. `src/cli_rpg/ai_world.py` - Update expand_area/expand_world for named locations
6. `src/cli_rpg/fallback_content.py` - Add room templates for new categories
7. `tests/test_named_locations_enterable.py` - New test file

## Verification
```bash
# Run existing tests to verify no regressions
pytest tests/ -v

# Run new test
pytest tests/test_named_locations_enterable.py -v

# Manual verification with demo mode
cli-rpg --demo
# Navigate to named locations and verify 'enter' works
```

## Notes
- This change is backward compatible - existing saves with old categories will work
- SubGrid generation for new categories uses existing procedural generation
- The small 3x3 bounds for wilderness POIs keeps them quick to explore
- Players get meaningful content (NPCs, secrets, treasures) even in wilderness areas
