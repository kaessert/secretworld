# Issue 24: Exploration Progress Tracking - Implementation Plan

## Spec

Track visited rooms in SubGrids, show exploration percentage in `map` command, and award XP/gold bonus when fully explored.

### Acceptance Criteria
- [ ] Track visited rooms in SubGrid (persisted in save)
- [ ] "Fully explored" bonus (XP + gold) when all rooms visited
- [ ] Exploration percentage visible in `map` command
- [ ] Visited rooms marked differently on map

## Implementation Steps

### 1. Add visited_rooms tracking to SubGrid

**File: `src/cli_rpg/world_grid.py`**

Add to `SubGrid` class:
- `visited_rooms: set[tuple[int, int, int]]` field (default empty set)
- `mark_visited(x, y, z)` method to add coordinates to visited set
- `get_exploration_stats() -> tuple[int, int, float]` method returning (visited_count, total_rooms, percentage)
- `is_fully_explored() -> bool` method
- Update `to_dict()` to serialize visited_rooms as list of coordinate tuples
- Update `from_dict()` to deserialize visited_rooms (default empty for backward compat)

### 2. Track room visits during SubGrid movement

**File: `src/cli_rpg/game_state.py`**

In `_move_in_sub_grid()` method:
- After successful move, call `self.current_sub_grid.mark_visited(*destination.coordinates)`

In `enter()` method:
- After entering SubGrid, mark initial room as visited

### 3. Award exploration bonus when fully explored

**File: `src/cli_rpg/game_state.py`**

In `_move_in_sub_grid()`:
- After marking visited, check `is_fully_explored()`
- If newly fully explored (check visited count before/after), award bonus:
  - XP: 50 * SubGrid total rooms
  - Gold: 25 * SubGrid total rooms
- Return bonus message appended to movement result

### 4. Display exploration percentage in SubGrid map

**File: `src/cli_rpg/map_renderer.py`**

In `_render_sub_grid_map()`:
- Call SubGrid's `get_exploration_stats()` method
- Add "Explored: X/Y rooms (Z%)" line after the map header
- Mark visited rooms with different styling (visited = bright, unvisited = dim)

### 5. Pass visited_rooms to map renderer

The SubGrid already passed to `_render_sub_grid_map()` will have `visited_rooms`, no additional changes needed.

## Tests

### File: `tests/test_exploration_tracking.py`

**SubGrid visited tracking tests:**
1. `test_subgrid_visited_rooms_starts_empty` - New SubGrid has empty visited_rooms
2. `test_subgrid_mark_visited` - mark_visited adds coordinates to set
3. `test_subgrid_mark_visited_idempotent` - Marking same room twice doesn't duplicate
4. `test_subgrid_get_exploration_stats` - Returns correct (visited, total, percentage)
5. `test_subgrid_is_fully_explored_false` - Returns False when rooms remain
6. `test_subgrid_is_fully_explored_true` - Returns True when all visited
7. `test_subgrid_serialization_with_visited_rooms` - to_dict/from_dict preserves visited_rooms
8. `test_subgrid_deserialization_backward_compat` - Old saves without visited_rooms load correctly

**GameState movement tracking tests:**
9. `test_move_in_sub_grid_marks_visited` - Movement marks destination as visited
10. `test_enter_marks_initial_room_visited` - Entering SubGrid marks entry point
11. `test_fully_explored_awards_xp_and_gold` - Completing exploration gives bonus
12. `test_fully_explored_bonus_only_once` - Bonus not given on subsequent visits

**Map renderer tests:**
13. `test_subgrid_map_shows_exploration_percentage` - "Explored: X/Y (Z%)" appears
14. `test_subgrid_map_visited_rooms_styling` - Visited vs unvisited rooms look different

## File Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/world_grid.py` | Add visited_rooms field, mark_visited(), get_exploration_stats(), is_fully_explored(), serialization |
| `src/cli_rpg/game_state.py` | Track visits in _move_in_sub_grid(), enter(); award bonus on full exploration |
| `src/cli_rpg/map_renderer.py` | Show exploration % in _render_sub_grid_map(), style visited rooms |
| `tests/test_exploration_tracking.py` | 14 new tests |
