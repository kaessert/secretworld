# SubGrid Exit Point Visual Indicator

## Summary
Display "Exit to: <overworld_location>" in location description when `is_exit_point=True`.

## Spec
When inside a SubGrid and viewing a location with `is_exit_point=True`, the location description should show "Exit to: <parent_name>" after the Exits line, similar to how "Enter:" is shown for enterable locations.

## Test (write first)

**File:** `tests/test_exit_points.py` - Add new test class

```python
class TestExitPointDisplay:
    """Tests for exit point visual indicator in location display."""

    def test_exit_point_shows_exit_to_in_description(self):
        """Test is_exit_point=True shows 'Exit to:' with parent name."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Abandoned Mines")
        entrance = Location(
            name="Mine Entrance",
            description="A dark opening in the rock.",
            is_exit_point=True
        )
        sub_grid.add_location(entrance, 0, 0)

        description = entrance.get_layered_description(sub_grid=sub_grid)
        assert "Exit to: Abandoned Mines" in description

    def test_non_exit_point_does_not_show_exit_to(self):
        """Test is_exit_point=False does not show 'Exit to:'."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Abandoned Mines")
        deep_room = Location(
            name="Deep Chamber",
            description="A dark chamber.",
            is_exit_point=False
        )
        sub_grid.add_location(deep_room, 0, 1)

        description = deep_room.get_layered_description(sub_grid=sub_grid)
        assert "Exit to:" not in description

    def test_exit_to_uses_color_formatting(self):
        """Test 'Exit to:' uses location color formatting."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Castle")
        entrance = Location(
            name="Castle Gate",
            description="The main gate.",
            is_exit_point=True
        )
        sub_grid.add_location(entrance, 0, 0)

        description = entrance.get_layered_description(sub_grid=sub_grid)
        # Should contain the ANSI color code for location (cyan)
        assert "\x1b[36m" in description  # CYAN for location color
        assert "Castle" in description
```

## Implementation

**File:** `src/cli_rpg/models/location.py`

In `get_layered_description()` method, after the exits line (around line 277) and before the "Enter:" logic, add:

```python
        # Show "Exit to:" for exit points inside SubGrids
        if self.is_exit_point and sub_grid is not None and sub_grid.parent_name:
            result += f"\nExit to: {colors.location(sub_grid.parent_name)}"
```

This should be inserted after line 277 (`result += "Exits: None"` block ends) and before line 279 (`# Show sub-locations if any exist`).

## Verification
1. `pytest tests/test_exit_points.py::TestExitPointDisplay -v`
2. `pytest tests/test_exit_points.py -v` (all exit point tests pass)
3. Demo mode test: `cli-rpg --demo --skip-character-creation`, then `go east`, `go north`, `enter mine entrance`, `look` - should show "Exit to: Abandoned Mines"
