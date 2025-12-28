# Plan: Fix Flaky `test_maze_layout_has_dead_ends` Test

## Problem
The test `tests/test_procedural_layouts.py::TestMazeLayout::test_maze_layout_has_dead_ends` is flaky. Running it 20 times shows it fails intermittently because the maze layout algorithm doesn't guarantee topological dead ends (nodes with exactly 1 neighbor).

## Root Cause
The `_generate_maze_layout()` method in `ai_service.py` (lines 3386-3426) uses a random walk with backtracking. However, with certain random seeds, the algorithm can produce compact clusters where all nodes have 2+ neighbors, resulting in zero dead ends.

---

## Fix Strategy
Modify `_generate_maze_layout()` to guarantee at least one dead end by ensuring the final node added is always a dead end (only one neighbor).

---

## Implementation Steps

### 1. Modify `src/cli_rpg/ai_service.py` `_generate_maze_layout()` method

After the main loop, add a post-processing step:
- Count dead ends in the generated coords
- If zero dead ends exist and size > 2, extend a random leaf node with a new dead-end cell
- Alternative: Track which nodes are "leaves" during generation and avoid filling them in

**Simpler approach**: After generation, if no dead ends exist, add one more cell extending from any node that has room for an unvisited neighbor. This guarantees at least one dead end.

```python
# After the while loop, ensure at least one dead end
dead_ends = sum(1 for x, y in coords
                if sum(1 for dx, dy in directions
                       if (x+dx, y+dy) in coord_set) == 1)

if dead_ends == 0 and len(coords) >= 3:
    # Find a cell with an unvisited neighbor and extend
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
```

---

## Tests

No new tests needed. The existing test `test_maze_layout_has_dead_ends` should pass consistently after the fix.

### Verification
Run the test 50+ times to confirm no flakiness:
```bash
pytest tests/test_procedural_layouts.py::TestMazeLayout::test_maze_layout_has_dead_ends -v --count=50
```

---

## Files to Modify
- `src/cli_rpg/ai_service.py` - Fix `_generate_maze_layout()` (around line 3426)
