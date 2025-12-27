# Plan: Fix "Enter" Command to Only Show Entry Point

## Problem
When at an overworld location with a sub_grid, all sub-locations are shown in the "Enter:" prompt, allowing players to teleport directly into any room. Players should only be able to enter through the designated entry point (marked with `is_exit_point=True`), then navigate internally.

## Spec
- **Display**: When displaying "Enter:" options, show only the entry point (`entry_point` field or first sub-location in sub_grid with `is_exit_point=True`)
- **Command**: The `enter` command should only allow entering the entry point location when a sub_grid exists
- Preserve backward compatibility for locations using the legacy `sub_locations` list without `sub_grid`

## Implementation Steps

### 1. Update `Location.get_layered_description()` (src/cli_rpg/models/location.py, ~line 258-261)
**Current**: Shows all sub_locations in "Enter:" line
**Change**: When `self.sub_grid` exists, show only the `self.entry_point` (or find the first location with `is_exit_point=True` from sub_grid). Fall back to showing all `sub_locations` when no sub_grid exists.

```python
# Current (~line 258-261):
if self.sub_locations:
    sub_loc_names = [colors.location(name) for name in self.sub_locations]
    result += f"\nEnter: {', '.join(sub_loc_names)}"

# Change to:
if self.sub_grid is not None:
    # Only show entry point for sub_grid locations
    if self.entry_point:
        result += f"\nEnter: {colors.location(self.entry_point)}"
    else:
        # Find first is_exit_point location in sub_grid
        for loc in self.sub_grid._by_name.values():
            if loc.is_exit_point:
                result += f"\nEnter: {colors.location(loc.name)}"
                break
elif self.sub_locations:
    sub_loc_names = [colors.location(name) for name in self.sub_locations]
    result += f"\nEnter: {', '.join(sub_loc_names)}"
```

### 2. Update `Location.__str__()` (src/cli_rpg/models/location.py, ~line 460-461)
Apply same pattern for consistency in string representation.

### 3. Update `GameState.enter()` (src/cli_rpg/game_state.py, ~line 820-835)
**Current**: Searches all sub_grid locations for name match
**Change**: When entering from overworld with sub_grid, only allow entry to the entry_point location. Reject attempts to enter other sub-locations directly.

```python
# After finding sub_grid_location (~line 827), add validation:
if sub_grid_location is not None and not sub_grid_location.is_exit_point:
    return (False, f"You can't enter {matched_location} directly. Enter through {current.entry_point}.")
```

## Tests to Add (tests/test_enter_entry_point.py)

1. **test_enter_shows_only_entry_point** - `get_layered_description()` with sub_grid shows only entry_point
2. **test_enter_command_allows_entry_point** - `enter()` succeeds for entry_point location
3. **test_enter_command_rejects_non_entry_point** - `enter("Council Chamber")` fails with helpful message
4. **test_enter_legacy_sub_locations_still_works** - locations without sub_grid still show all sub_locations
5. **test_enter_str_shows_only_entry_point** - `__str__()` shows only entry point when sub_grid exists

## Files to Modify
1. `src/cli_rpg/models/location.py` - `get_layered_description()` and `__str__()` methods
2. `src/cli_rpg/game_state.py` - `enter()` method
3. `tests/test_enter_entry_point.py` - new test file
