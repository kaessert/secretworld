# Implementation Plan: Step 3 - Update `go` Command to Use Terrain Passability

## Summary
Update the movement system to use WFC terrain passability (`is_passable()` from `world_tiles.py`) as the **primary** validation for movement, replacing `connections` dict checks. This enables implicit movement based on terrain rather than explicit connection management.

---

## Specification

### Current Behavior
Movement validation in `game_state.py:move()` follows this flow:
1. Check `current.has_connection(direction)` - **blocks if no explicit connection**
2. Use coordinates to find target location OR generate new location
3. Check WFC terrain passability only for **newly generated** locations

### Target Behavior
Movement validation should follow this flow:
1. Check WFC terrain passability **first** - blocks if impassable terrain
2. Find or generate location at target coordinates
3. `connections` dict used only for legacy saves (backward compatibility)

### Key Principles
- **Terrain is truth**: `ChunkManager.get_tile(x, y)` determines passability
- **Passability is binary**: Each terrain type is passable or impassable
- **Movement is implicit**: Player can always move to adjacent passable terrain
- **Backward compatible**: Non-WFC worlds and legacy saves still work

---

## Test Cases (TDD)

Create `tests/test_terrain_movement.py`:

### Test 1: Movement to passable terrain succeeds (no connection required)
```python
def test_move_to_passable_terrain_without_connection():
    """Player can move to passable terrain even without explicit connection."""
    # Setup: Location at (0,0), no connection north, but forest at (0,1)
    # Expected: Move succeeds, new location created/found
```

### Test 2: Movement to impassable terrain blocked (even with connection)
```python
def test_move_to_impassable_terrain_blocked():
    """Player cannot move to impassable terrain (water) even with connection."""
    # Setup: Location at (0,0), connection north, but water at (0,1)
    # Expected: Move fails with "The water ahead is impassable."
```

### Test 3: Movement without ChunkManager uses connections (legacy)
```python
def test_move_without_chunk_manager_uses_connections():
    """Without WFC, movement uses traditional connection-based logic."""
    # Setup: GameState without chunk_manager
    # Expected: Old behavior preserved
```

### Test 4: Movement blocked when terrain and connection both missing
```python
def test_move_blocked_no_terrain_no_connection():
    """Movement fails when no WFC terrain and no connection."""
    # Setup: No chunk_manager, no connection in direction
    # Expected: "You can't go that way."
```

### Test 5: All cardinal directions validated against terrain
```python
def test_all_directions_check_terrain():
    """All four directions check terrain passability."""
    # Test north, south, east, west with various terrain configurations
```

---

## Implementation Steps

### Step 1: Create test file `tests/test_terrain_movement.py`
- Add 5 test cases above
- Import `is_passable`, `get_valid_moves` from `world_tiles`
- Mock `ChunkManager` for controlled terrain returns

### Step 2: Modify `game_state.py:move()` method
**Location**: Lines 450-707

**Change 1**: Add WFC terrain check BEFORE connection check (around line 485-488)
```python
# NEW: Check WFC terrain passability first
if self.chunk_manager is not None and current.coordinates is not None:
    from cli_rpg.world_tiles import DIRECTION_OFFSETS, is_passable
    dx, dy = DIRECTION_OFFSETS.get(direction, (0, 0))
    target_coords = (current.coordinates[0] + dx, current.coordinates[1] + dy)
    terrain = self.chunk_manager.get_tile_at(*target_coords)
    if not is_passable(terrain):
        self.is_sneaking = False
        return (False, f"The {terrain} ahead is impassable.")
```

**Change 2**: Remove connection check for WFC mode (line 486-488)
- Current: `if not current.has_connection(direction):`
- New: Only check connections when `chunk_manager is None`

**Change 3**: Keep connection check for legacy mode (lines 571-606)
- This path already works, no changes needed

### Step 3: Update `_move_in_sub_grid()` method (lines 709-761)
- SubGrid movement should continue using connections (bounded interior spaces)
- No changes needed - SubGrids don't use WFC terrain

### Step 4: Ensure exit display matches movement capability
**Already done**: `get_filtered_directions()` in `location.py` filters exits by WFC passability

### Step 5: Run tests and verify
```bash
pytest tests/test_terrain_movement.py -v
pytest tests/test_terrain_passability.py -v
pytest tests/test_wfc_exit_display.py -v
pytest -x  # Full test suite
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `tests/test_terrain_movement.py` | **NEW** - 5 test cases for terrain-based movement |
| `src/cli_rpg/game_state.py` | Modify `move()` to check terrain passability before connections |

---

## Backward Compatibility

| Scenario | Behavior |
|----------|----------|
| WFC mode (chunk_manager present) | Terrain passability is primary, connections secondary |
| Non-WFC mode (chunk_manager=None) | Connections-based movement preserved |
| Legacy saves | Load without chunk_manager, use connection logic |
| SubGrid interior movement | Always uses connections (no WFC in interiors) |

---

## Success Criteria

- [ ] `go <direction>` checks `is_passable()` before connection dict (when WFC active)
- [ ] Movement to water returns "The water ahead is impassable."
- [ ] Movement to passable terrain works even without explicit connection
- [ ] Legacy saves and non-WFC mode work unchanged
- [ ] All existing 3591 tests still pass
- [ ] 5 new terrain movement tests pass
