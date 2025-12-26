# Fix: Talk Command Fails in SubGrid Sublocations

## Problem
The `talk` command doesn't find NPCs when inside SubGrid sublocations (e.g., inside buildings/dungeons). The `look` command shows NPCs present, but `talk` returns "There are no NPCs here to talk to."

## Root Cause
`src/cli_rpg/main.py` line 1147 uses:
```python
location = game_state.world.get(game_state.current_location)
```
This looks up from the main `world` dict, but SubGrid sublocations are stored in `game_state.current_sub_grid`, so it returns `None` for sublocations.

## Fix
**File**: `src/cli_rpg/main.py`, line 1147

**Change**:
```python
location = game_state.world.get(game_state.current_location)
```

**To**:
```python
location = game_state.get_current_location()
```

The `get_current_location()` method (defined in `game_state.py:289-302`) properly handles both overworld locations and SubGrid sublocations.

## Test
Add test in `tests/test_main_subgrid.py` (or similar existing test file):

```python
def test_talk_command_works_in_subgrid_sublocations(game_state):
    """Talk command should find NPCs inside SubGrid sublocations."""
    # Setup: Enter a sublocation with NPCs
    from cli_rpg.world_grid import SubGrid
    from cli_rpg.models.location import Location
    from cli_rpg.models.npc import NPC

    # Create sublocation with NPC
    sub_grid = SubGrid(center=(0, 0))
    npc = NPC(name="Test Merchant", description="A friendly merchant")
    sublocation = Location(
        name="Test Shop",
        description="A shop",
        coordinates=(0, 0),
        npcs=[npc]
    )
    sub_grid.set(sublocation)

    # Put player in sublocation
    game_state.current_sub_grid = sub_grid
    game_state.current_location = "Test Shop"
    game_state.in_sub_location = True

    # Test talk command finds NPC
    from cli_rpg.main import handle_exploration_command
    result = handle_exploration_command(game_state, "talk", [])

    # Should NOT return "no NPCs here" error
    assert "no NPCs here" not in result[1].lower()
```

## Verification
1. Run new test: `pytest tests/test_main_subgrid.py -v -k talk`
2. Run full suite: `pytest` (all tests should pass)
3. Manual test: Start game → enter Market → talk Merchant → should work
