# Fix: "Can't go that way" even though map shows valid exits (Bug #5)

## Summary
Fix desync between displayed exits and actual traversability when WFC terrain blocks movement.

## Root Cause Analysis

The bug occurs in WFC mode when:

1. **Exit Display**: `Location.get_layered_description()` shows exits from `location.connections` dict
2. **Movement**: `GameState.move()` checks WFC terrain passability AFTER checking connections

**Flow causing the bug:**
```
1. Player at location (1, 11) with connections = {"east": "Unexplored East", ...}
2. Map shows: "Exits: east, south, west" (from connections dict)
3. Player types: "go east"
4. move() checks: current.has_connection("east") → True ✓
5. move() calculates target coords: (2, 11)
6. move() checks WFC terrain at (2, 11) → "water"
7. move() returns: "The water ahead is impassable."
```

But the bug report says "You can't go that way" - which means the check at step 4 fails. This happens when:
- The location's connection points to a name ("Unexplored East")
- But coordinate-based lookup finds nothing at target coords
- AND AI/fallback generation fails silently

The real issue: **Exits are displayed based on `connections` dict, but movement uses coordinates**. When a location has a dangling connection but WFC blocks that direction, the exit is shown but unusable.

## Solution

Filter displayed exits to exclude directions blocked by WFC terrain BEFORE display.

### Option A: Filter at Display Time (Chosen)
Add WFC terrain check in `Location.get_available_directions()` or `get_layered_description()`.

**Pros**: Single point of change, always consistent
**Cons**: Location needs access to ChunkManager (coupling)

### Option B: Don't Create Blocked Connections
Modify `generate_fallback_location()` to check WFC before adding dangling exits.

**Pros**: Cleaner data model
**Cons**: Existing dangling connections still broken

**Decision**: Option A with Option B for new locations.

## Implementation Steps

### 1. Add WFC-aware exit filtering to map display

Modify `map_renderer.py:render_map()` exits display:
- Check each exit direction against WFC terrain
- Only display exits where terrain is passable

### 2. Add WFC-aware exit filtering to Location display

Modify `Location.get_layered_description()`:
- Accept optional `chunk_manager` parameter
- Filter connections by terrain passability when chunk_manager provided

### 3. Fix fallback location generation

Modify `world.py:generate_fallback_location()`:
- Accept optional `chunk_manager` parameter
- Only add dangling exits where WFC terrain is passable

### 4. Wire chunk_manager through to display calls

Modify callers:
- `game_state.py:look()` - pass chunk_manager to get_layered_description
- `main.py` map command - pass chunk_manager to render_map

## Test Plan

1. **Unit test**: `test_location_filters_exits_by_wfc_terrain`
   - Create location with exits to passable and impassable terrain
   - Verify get_layered_description() excludes blocked exits

2. **Unit test**: `test_fallback_location_no_water_exits`
   - Generate fallback location where some directions are water
   - Verify no connections point toward water tiles

3. **Integration test**: `test_displayed_exits_match_traversable_directions`
   - In WFC mode, verify all displayed exits can be traversed

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/models/location.py` | Add `get_filtered_directions(chunk_manager, coords)` method |
| `src/cli_rpg/game_state.py` | Pass chunk_manager to look() display |
| `src/cli_rpg/world.py` | Check WFC before adding dangling exits |
| `src/cli_rpg/map_renderer.py` | Filter exits in render_map() |
| `tests/test_wfc_exit_display.py` | NEW - test exit filtering |
