# Implementation Plan: Enterable Sublocations on Overworld

## Problem Summary
Named locations (dungeons, caves, towns, ruins) are generated on the overworld but **never** have SubGrids attached, making them non-enterable. The `enter` command fails because `current.sub_grid` is always `None` for AI-generated named locations.

## Root Cause Analysis
1. **Named locations are flat**: `expand_area()` creates named locations with `is_overworld=True` but only creates a SubGrid when there are multiple area locations. Single named locations (the common case on overworld) have no SubGrid.

2. **No on-demand SubGrid creation**: When player uses `enter` on a named location, the code checks `current.sub_grid is not None` - if it's None (never populated), entry fails.

3. **ENTERABLE_CATEGORIES not defined**: There's no constant defining which location categories should be enterable. The `BOSS_CATEGORIES` in `ai_world.py` hints at this (dungeon, cave, ruins) but isn't used for determining enterability.

## Implementation

### 1. Define ENTERABLE_CATEGORIES constant
**File**: `src/cli_rpg/world_tiles.py`

Add a constant defining which location categories should be enterable:
```python
# Categories that should have enterable SubGrids
ENTERABLE_CATEGORIES = frozenset({
    "dungeon", "cave", "ruins", "temple",  # Adventure locations
    "town", "village", "city", "settlement",  # Settlements
    "tavern", "shop", "inn",  # Commercial buildings
})
```

### 2. Create helper to check if a location is enterable
**File**: `src/cli_rpg/world_tiles.py`

```python
def is_enterable_category(category: Optional[str]) -> bool:
    """Check if a location category should have an enterable SubGrid."""
    if category is None:
        return False
    return category.lower() in ENTERABLE_CATEGORIES
```

### 3. Create on-demand SubGrid generation function
**File**: `src/cli_rpg/ai_world.py`

Add a function to generate a SubGrid for a named location that doesn't have one:
```python
def generate_subgrid_for_location(
    location: Location,
    ai_service: Optional[AIService],
    theme: str,
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None,
) -> SubGrid:
    """Generate a SubGrid for an enterable named location on-demand."""
```

This function should:
- Get bounds from `get_subgrid_bounds(location.category)`
- Call `ai_service.generate_area_with_context()` to get interior layout
- Create SubGrid and populate with generated locations
- Mark entry location with `is_exit_point=True`
- Place boss in furthest room for BOSS_CATEGORIES
- Return the populated SubGrid

### 4. Modify `enter()` to generate SubGrid on-demand
**File**: `src/cli_rpg/game_state.py`

In `GameState.enter()`, after checking `current.is_overworld`, add logic to:
1. Check if location is enterable category but has no sub_grid
2. Generate SubGrid on-demand using the new function
3. Attach SubGrid to the location
4. Continue with normal entry flow

```python
def enter(self, target_name: Optional[str] = None) -> tuple[bool, str]:
    # ... existing code ...

    # If location is enterable category but has no sub_grid, generate one
    from cli_rpg.world_tiles import is_enterable_category
    if current.sub_grid is None and is_enterable_category(current.category):
        from cli_rpg.ai_world import generate_subgrid_for_location
        current.sub_grid = generate_subgrid_for_location(
            location=current,
            ai_service=self.ai_service,
            theme=self.theme,
            world_context=self.world_context,
            region_context=self.get_or_create_region_context(
                current.coordinates, current.terrain or "wilderness"
            ) if current.coordinates else None,
        )
        # Set entry_point from first is_exit_point location
        for loc in current.sub_grid._by_name.values():
            if loc.is_exit_point:
                current.entry_point = loc.name
                break

    # ... rest of existing code ...
```

### 5. Update `generate_fallback_location` for enterable categories
**File**: `src/cli_rpg/world.py`

When `is_named=True` and `category_hint` is an enterable category, set up `sub_locations` and `entry_point` for fallback generation (even if SubGrid is generated lazily later).

### 6. Display "Enter:" prompt for enterable locations
**File**: `src/cli_rpg/models/location.py`

Update `get_layered_description()` to show "Enter: <name>" for enterable categories even when sub_grid is None (indicating it will be generated on demand):

```python
# After existing sub_grid/sub_locations display logic:
elif is_enterable_category(self.category) and self.is_named:
    result += f"\nEnter: {colors.location(self.name)}"
```

## Tests

### File: `tests/test_enterable_sublocations.py`

```python
def test_enterable_categories_constant():
    """ENTERABLE_CATEGORIES contains expected categories."""

def test_is_enterable_category():
    """is_enterable_category returns correct values."""

def test_generate_subgrid_for_dungeon():
    """generate_subgrid_for_location creates SubGrid for dungeon."""

def test_generate_subgrid_for_cave():
    """generate_subgrid_for_location creates SubGrid for cave."""

def test_generate_subgrid_for_town():
    """generate_subgrid_for_location creates SubGrid for town."""

def test_enter_generates_subgrid_on_demand():
    """enter() generates SubGrid when needed for enterable location."""

def test_enter_uses_existing_subgrid():
    """enter() uses existing SubGrid if already populated."""

def test_enter_fails_for_non_enterable():
    """enter() fails for non-enterable category locations."""

def test_location_description_shows_enter_for_enterable():
    """get_layered_description shows Enter: for enterable locations."""

def test_subgrid_has_entry_point():
    """Generated SubGrid has is_exit_point location for exit."""

def test_boss_placed_in_dungeon_subgrid():
    """Boss is placed in furthest room for dungeon SubGrids."""
```

## Implementation Order

1. Add `ENTERABLE_CATEGORIES` and `is_enterable_category()` to `world_tiles.py`
2. Add `generate_subgrid_for_location()` to `ai_world.py`
3. Modify `GameState.enter()` to use on-demand generation
4. Update `Location.get_layered_description()` to show Enter: prompt
5. Write and run tests
6. Manual testing with different seeds
