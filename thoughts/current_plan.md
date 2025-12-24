# Fix Broken Navigation Link from Forest to Deep Woods

## Spec

Remove dangling exits from the default world that point to non-existent locations. Without AI service, these exits cause error messages ("Destination 'X' not found in world") that look like bugs.

**Fix approach**: Remove lines 64-66 in `world.py` that add dangling connections to "Deep Woods" and "Crystal Cavern". These exits serve no purpose without AI and create a poor user experience.

## Tests First

Add test to `tests/test_world.py`:
1. **test_default_world_all_exits_have_valid_destinations**: Verify every exit in every location points to a location that exists in the world

## Implementation

1. **Update `tests/test_world.py`**: Add test that iterates through all locations and their connections, asserting each destination exists in the world dict

2. **Update `src/cli_rpg/world.py`**: Remove lines 64-66:
   ```python
   # Add dangling exits for world expansion
   forest.add_connection("north", "Deep Woods")
   cave.add_connection("east", "Crystal Cavern")
   ```

3. **Update `ISSUES.md`**: Mark the issue as RESOLVED with description of the fix

## File Locations

- Test: `tests/test_world.py` (add new test to `TestCreateDefaultWorld` class)
- Fix: `src/cli_rpg/world.py` (remove lines 64-66)
- Doc: `ISSUES.md` (mark issue resolved)
