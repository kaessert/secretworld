# Implementation Plan: Fix Confusing `enter` Command Error Message

## Problem Summary
When a user types `enter Dark Cave` at the "Dark Cave" location, they get:
```
No such location: dark cave. Available: Cave Entrance, Dark Passage, Spider Den, Hidden Alcove
```

This is confusing because:
1. User typed the location name they see ("Dark Cave")
2. Error lists internal SubGrid rooms, not helpful guidance
3. Should suggest using `enter Cave Entrance` instead

## Solution: Accept Parent Location Name as Alias

When `enter <name>` fails to match a SubGrid room, check if `<name>` matches the current overworld location's name. If so, redirect to the entry_point automatically.

This is the better UX: users naturally type what they see, so we should accept it.

---

## Implementation Steps

### 1. Write Test First
**File**: `tests/test_game_state.py`

Add test case in `TestEnterCommand` class (~line 1188):
```python
def test_enter_accepts_parent_location_name(self, monkeypatch):
    """Test that enter accepts the parent location name as alias for entry_point."""
    # Setup: Overworld "Dark Cave" with SubGrid containing "Cave Entrance" (entry_point)
    # Action: enter("Dark Cave")
    # Assert: Successfully enters through Cave Entrance
```

### 2. Implement Fix in `enter()` Method
**File**: `src/cli_rpg/game_state.py` (lines 1435-1448)

Insert after line 1435 (`if matched_location is None:`), before building error:

```python
# Check if user typed the current location's name - redirect to entry_point
current_name_lower = current.name.lower()
if target_lower == current_name_lower or current_name_lower.startswith(target_lower):
    if current.entry_point and current.sub_grid is not None:
        for loc in current.sub_grid._by_name.values():
            if loc.name == current.entry_point:
                matched_location = loc.name
                sub_grid_location = loc
                break
```

### 3. Run Tests
```bash
pytest tests/test_game_state.py::TestEnterCommand -v
pytest tests/test_game_state.py -v
```

---

## Files Changed
- `tests/test_game_state.py` - Add test for parent name alias
- `src/cli_rpg/game_state.py` - Modify `enter()` (~line 1435)

## Acceptance Criteria
- `enter Dark Cave` at Dark Cave enters through Cave Entrance
- `enter dark` at Dark Cave enters through Cave Entrance (partial match)
- Original error preserved for genuinely invalid names
- Existing tests pass
