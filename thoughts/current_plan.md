# Implementation Plan: Convert Default World Sub-locations to SubGrid

**Priority**: P0 BLOCKER - Phase 1, Step 6 of SubGrid migration
**Status**: Ready for implementation

## Summary

Convert the default world's sub-locations (Town Square, Forest, Millbrook Village, Abandoned Mines, Ironhold City) from the legacy `sub_locations` list pattern to the new SubGrid-based architecture. This enables proper bounded interior grids with exit points.

---

## Current State

The default world in `src/cli_rpg/world.py` currently:
1. Creates overworld landmarks with `sub_locations: List[str]` containing sub-location names
2. Creates sub-locations as standalone `Location` objects with `parent_location` set
3. Adds all locations (overworld + sub-locations) to the world dict directly

**Problem**: Sub-locations don't use SubGrid, so they lack:
- Bounded coordinate systems
- Proper exit point enforcement
- Grid-based internal navigation

---

## Implementation Steps

### 1. Create SubGrid instances for each overworld landmark

For each landmark (Town Square, Forest, Millbrook, Abandoned Mines, Ironhold City):
- Create a `SubGrid` with appropriate bounds
- Set `parent_name` to the landmark name

**Bounds by location**:
| Location | Sub-locations | Bounds |
|----------|--------------|--------|
| Town Square | 3 | (-1, 1, -1, 1) 3x3 |
| Forest | 3 | (-1, 1, -1, 1) 3x3 |
| Millbrook Village | 3 | (-1, 1, -1, 1) 3x3 |
| Abandoned Mines | 4 | (-1, 1, -1, 2) 3x4 |
| Ironhold City | 4 | (-1, 1, -1, 1) 3x3 |

### 2. Add sub-locations to SubGrid instead of world dict

For each sub-location:
- Set `is_exit_point=True` for entry points (first sub-location of each landmark)
- Call `sub_grid.add_location(location, x, y)` with appropriate coordinates
- Do NOT add sub-locations to `world` dict

**Coordinate layout for each landmark (entry at 0,0)**:

**Town Square** (3 locations):
```
         (0,1) Town Well
           |
         (0,0) Market District - (1,0) Guard Post
         (entry, exit_point)
```

**Forest** (3 locations):
```
         (0,1) Deep Woods
           |
         (0,0) Forest Edge - (1,0) Ancient Grove
         (entry, exit_point)
```

**Millbrook Village** (3 locations):
```
         (0,1) Blacksmith
           |
         (0,0) Village Square - (1,0) Inn
         (entry, exit_point)
```

**Abandoned Mines** (4 locations):
```
                (0,2) Boss Chamber
                  |
                (0,1) Flooded Level
                  |
         (0,0) Mine Entrance - (1,0) Upper Tunnels
         (entry, exit_point)
```

**Ironhold City** (4 locations):
```
         (0,1) Temple Quarter
           |
         (0,0) Ironhold Market - (1,0) Castle Ward
         (entry, exit_point)
           |
         (0,-1) Slums
```

### 3. Attach SubGrid to overworld landmarks

For each landmark:
```python
landmark.sub_grid = sub_grid
```

### 4. Update world dict to exclude sub-locations

Remove these lines from `create_default_world()`:
```python
# Remove: world["Market District"] = market_district
# Remove: world["Guard Post"] = guard_post
# etc.
```

Sub-locations should ONLY be accessible via their parent's SubGrid.

---

## Code Changes

**File**: `src/cli_rpg/world.py`

### Change 1: Create Town Square SubGrid

After creating `town_square`, `market_district`, `guard_post`, `town_well`:

```python
# Create SubGrid for Town Square interiors
town_square_grid = SubGrid(bounds=(-1, 1, -1, 1), parent_name="Town Square")

# Mark entry location as exit point
market_district.is_exit_point = True

# Add locations to SubGrid (entry at 0,0)
town_square_grid.add_location(market_district, 0, 0)
town_square_grid.add_location(guard_post, 1, 0)
town_square_grid.add_location(town_well, 0, 1)

# Attach SubGrid to overworld landmark
town_square.sub_grid = town_square_grid
```

### Change 2: Create Forest SubGrid

```python
# Create SubGrid for Forest interiors
forest_grid = SubGrid(bounds=(-1, 1, -1, 1), parent_name="Forest")

# Mark entry location as exit point
forest_edge.is_exit_point = True

# Add locations to SubGrid
forest_grid.add_location(forest_edge, 0, 0)
forest_grid.add_location(deep_woods, 0, 1)
forest_grid.add_location(ancient_grove, 1, 0)

# Attach SubGrid
forest.sub_grid = forest_grid
```

### Change 3: Create Millbrook SubGrid

```python
# Create SubGrid for Millbrook Village interiors
millbrook_grid = SubGrid(bounds=(-1, 1, -1, 1), parent_name="Millbrook Village")

# Mark entry location as exit point
village_square.is_exit_point = True

# Add locations to SubGrid
millbrook_grid.add_location(village_square, 0, 0)
millbrook_grid.add_location(inn, 1, 0)
millbrook_grid.add_location(blacksmith_loc, 0, 1)

# Attach SubGrid
millbrook.sub_grid = millbrook_grid
```

### Change 4: Create Abandoned Mines SubGrid

```python
# Create SubGrid for Abandoned Mines interiors
mines_grid = SubGrid(bounds=(-1, 1, -1, 2), parent_name="Abandoned Mines")

# Mark entry location as exit point
mine_entrance.is_exit_point = True

# Add locations to SubGrid (linear dungeon progression)
mines_grid.add_location(mine_entrance, 0, 0)
mines_grid.add_location(upper_tunnels, 1, 0)
mines_grid.add_location(flooded_level, 0, 1)
mines_grid.add_location(boss_chamber, 0, 2)

# Attach SubGrid
abandoned_mines.sub_grid = mines_grid
```

### Change 5: Create Ironhold SubGrid

```python
# Create SubGrid for Ironhold City interiors
ironhold_grid = SubGrid(bounds=(-1, 1, -1, 1), parent_name="Ironhold City")

# Mark entry location as exit point
ironhold_market.is_exit_point = True

# Add locations to SubGrid
ironhold_grid.add_location(ironhold_market, 0, 0)
ironhold_grid.add_location(castle_ward, 1, 0)
ironhold_grid.add_location(temple_quarter, 0, 1)
ironhold_grid.add_location(slums, 0, -1)

# Attach SubGrid
ironhold_city.sub_grid = ironhold_grid
```

### Change 6: Remove sub-locations from world dict

Remove these lines at the end of `create_default_world()`:
```python
# DELETE all these lines:
# world["Market District"] = market_district
# world["Guard Post"] = guard_post
# world["Town Well"] = town_well
# world["Forest Edge"] = forest_edge
# world["Deep Woods"] = deep_woods
# world["Ancient Grove"] = ancient_grove
# world["Village Square"] = village_square
# world["Inn"] = inn
# world["Blacksmith"] = blacksmith_loc
# world["Mine Entrance"] = mine_entrance
# world["Upper Tunnels"] = upper_tunnels
# world["Flooded Level"] = flooded_level
# world["Boss Chamber"] = boss_chamber
# world["Ironhold Market"] = ironhold_market
# world["Castle Ward"] = castle_ward
# world["Slums"] = slums
# world["Temple Quarter"] = temple_quarter
```

---

## Tests

**File**: `tests/test_default_world_subgrid.py`

### Test cases:

1. **test_town_square_has_sub_grid** - Town Square has sub_grid attached
2. **test_town_square_sub_grid_entry_is_exit_point** - Market District is exit point
3. **test_town_square_sub_grid_contains_all_locations** - 3 locations in grid
4. **test_town_square_sub_locations_not_in_world_dict** - No sub-locations in world

5. **test_forest_has_sub_grid** - Forest has sub_grid attached
6. **test_forest_sub_grid_entry_is_exit_point** - Forest Edge is exit point
7. **test_forest_sub_grid_contains_all_locations** - 3 locations in grid

8. **test_millbrook_has_sub_grid** - Millbrook Village has sub_grid attached
9. **test_millbrook_sub_grid_entry_is_exit_point** - Village Square is exit point

10. **test_abandoned_mines_has_sub_grid** - Abandoned Mines has sub_grid attached
11. **test_abandoned_mines_sub_grid_entry_is_exit_point** - Mine Entrance is exit point
12. **test_abandoned_mines_sub_grid_contains_all_locations** - 4 locations in grid

13. **test_ironhold_has_sub_grid** - Ironhold City has sub_grid attached
14. **test_ironhold_sub_grid_entry_is_exit_point** - Ironhold Market is exit point

15. **test_sub_grid_navigation_works** - Can enter and move within sub-grid
16. **test_exit_from_entry_point_works** - Exit works from entry
17. **test_exit_from_non_entry_blocked** - Exit blocked from other rooms

---

## Verification

Run tests:
```bash
pytest tests/test_default_world_subgrid.py -v
pytest tests/test_subgrid_navigation.py -v
pytest tests/test_game_state.py -v
```

Manual verification:
```bash
cli-rpg --skip-character-creation
> enter Market District
> go east  # Should go to Guard Post
> exit     # Should fail (not exit point)
> go west  # Back to Market District
> exit     # Should succeed
```
