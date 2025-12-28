# Fix Maze Layout Tests

## Problem
Two failing tests in `tests/test_procedural_layouts.py`:
1. `test_maze_layout_has_dead_ends` - finds 0 dead ends (expects ≥1)
2. `test_maze_layout_respects_size` - returns 11 coords when 10 requested

## Root Cause
In `src/cli_rpg/ai_service.py` lines 3433-3444, the dead-end fix logic adds an extra coord WITHOUT checking if we've already reached the size limit, causing the size to exceed the requested amount.

## Implementation

### Fix `_generate_maze_layout()` at line 3433

Change the dead-end fix to respect size constraints:

```python
if dead_ends == 0 and len(coords) >= 3:
    if len(coords) < size:
        # Room to add a dead end
        for x, y in coords:
            for dx, dy in directions:
                neighbor = (x + dx, y + dy)
                if neighbor not in coord_set:
                    coords.append(neighbor)
                    coord_set.add(neighbor)
                    break
            else:
                continue
            break
    elif len(coords) > 3:
        # At size limit - replace last coord with a dead end
        removed = coords.pop()
        coord_set.remove(removed)
        for x, y in coords:
            for dx, dy in directions:
                neighbor = (x + dx, y + dy)
                if neighbor not in coord_set:
                    coords.append(neighbor)
                    coord_set.add(neighbor)
                    break
            else:
                continue
            break

return coords[:size]  # Guarantee exact size
```

### Verify
```bash
pytest tests/test_procedural_layouts.py::TestMazeLayout -v
```

## File to Modify
- `src/cli_rpg/ai_service.py` - lines 3433-3446
