# Fix Key Placement Algorithm (test_key_placed_before_locked_door)

## Problem

The `_place_keys_in_earlier_rooms` function places keys at locations with distance greater than their corresponding locked doors, violating the spec that keys must be accessible before doors.

**Root Cause**: Distance is calculated from origin `(0, 0)` instead of from the entry room's actual coordinates. When the entry room is not at `(0, 0)` (e.g., entry at `(0, 3, 0)`), the distance calculations become incorrect.

**Example**:
- Entry at `(0, 3, 0)` → distance from origin = 3
- Room A at `(-3, -2, 0)` → distance from origin = 5
- But actual distance from entry = `|(-3) - 0| + |(-2) - 3|` = 8

## Spec

Keys for LOCKED_DOOR puzzles must be placed in rooms that are **closer to the entry point** than the door, so players can find the key before encountering the locked door.

## Implementation

### 1. Modify `generate_subgrid_for_location()` in `src/cli_rpg/ai_world.py`

**Find entry coordinates first** (before iterating over locations):
```python
# Find entry coordinates for distance calculations
entry_coords = (0, 0, 0)
for loc in sub_grid._by_name.values():
    if loc.is_exit_point:
        entry_coords = loc.coordinates or (0, 0, 0)
        break
entry_x, entry_y, entry_z = entry_coords
```

**Update distance calculation** (line ~1020):
```python
# Calculate distance from entry, not from origin
distance = abs(x - entry_x) + abs(y - entry_y)
```

### 2. Update `_place_keys_in_earlier_rooms()` in `src/cli_rpg/ai_world.py`

Add `entry_coords` parameter and calculate distances correctly:
```python
def _place_keys_in_earlier_rooms(
    placed_locations: dict,
    keys_to_place: list[tuple[str, str, int]],
    entry_coords: tuple[int, int, int] = (0, 0, 0),  # NEW
) -> None:
```

**Update distance calculation** (line ~618-622):
```python
entry_x, entry_y, _ = entry_coords
rel = data.get("relative_coords", (0, 0, 0))
if len(rel) == 2:
    dist = abs(rel[0] - entry_x) + abs(rel[1] - entry_y)
else:
    dist = abs(rel[0] - entry_x) + abs(rel[1] - entry_y)
```

### 3. Update call site

Pass entry coordinates to `_place_keys_in_earlier_rooms()`:
```python
if all_keys_to_place:
    _place_keys_in_earlier_rooms(placed_locations, all_keys_to_place, entry_coords)
```

### 4. Update `expand_area()` if applicable

Check if `expand_area()` (line ~1713) also needs the same fix for its puzzle/key placement logic.

## Test Verification

Run the failing test:
```bash
pytest tests/test_ai_puzzle_generation.py::TestSubGridPuzzleIntegration::test_key_placed_before_locked_door -v
```

Run full puzzle test suite:
```bash
pytest tests/test_ai_puzzle_generation.py -v
```
