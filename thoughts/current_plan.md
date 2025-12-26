# Implementation Plan: Fix Confusing Camp Error Message

**Priority**: ACTIVE UX Issue
**Scope**: Improve error message when player tries to camp at overworld landmark with sub-locations

## Spec

When a player runs `camp` at an overworld location (like "Forest") that has sub-locations:
- Instead of: "You can't camp here. Find a wilderness location."
- Show: "You can't camp at this overworld location. Use 'enter <name>' to find a suitable campsite in <sub-locations>."

This guides the user to use the `enter` command to access a sub-location where camping is allowed.

## Tests

### File: `tests/test_camping.py` (extend existing)

Add test for overworld location error message:

1. **`test_camp_at_overworld_shows_enter_hint`**: Create an overworld location with `is_overworld=True` and `sub_locations=["Forest Edge", "Deep Woods"]`. Run `camp` command. Verify error message mentions `enter` and lists sub-locations.

## Implementation Steps

1. **Add test to `tests/test_camping.py`**:
   - Create fixture for overworld forest location with sub-locations
   - Test that camp command returns helpful message with enter hint

2. **Modify `execute_camp()` in `src/cli_rpg/camping.py`** (line 336):
   - Before returning generic "Find a wilderness location" message
   - Check if `location.is_overworld` and `location.sub_locations` are set
   - If so, return message like: "You can't camp at overworld landmarks. Use 'enter <name>' to find a suitable campsite in: Forest Edge, Deep Woods."

## Files to Modify

| File | Action | Changes |
|------|--------|---------|
| `tests/test_camping.py` | EXTEND | Add `test_camp_at_overworld_shows_enter_hint` |
| `src/cli_rpg/camping.py` | MODIFY | Update error handling in `execute_camp()` around line 336 |

## Verification

```bash
pytest tests/test_camping.py::test_camp_at_overworld_shows_enter_hint -v
pytest tests/test_camping.py -v  # All camping tests still pass
```
