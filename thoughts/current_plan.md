# Fix: NPCs Show as "???" When Revisiting Locations in WFC Mode

## Summary
Bug report states that when revisiting a location in WFC mode, NPC names display as "???" instead of actual names. The reproduction steps are: Start at Whispering Woods → Go east → Return west → NPCs now show as "???, ???, ???".

## Investigation Findings

After thorough analysis:

1. **No code generates "???" for NPCs**: The codebase explicitly tests that NPCs should NEVER show as "???" (see `test_weather.py` lines 472-493 and 577-580).

2. **The docstring is outdated**: `test_weather.py` line 361 has a stale comment mentioning "obscures NPC names with '???'" but the actual tests verify this does NOT happen.

3. **NPC serialization is correct**: Both `Location.to_dict()/from_dict()` and `NPC.to_dict()/from_dict()` properly preserve NPC data.

4. **SubGrid serialization is correct**: NPCs in SubGrid locations are properly preserved.

5. **Fallback locations have no NPCs**: `generate_fallback_location()` creates locations without NPCs, which is intentional.

## Hypothesis

The bug report may be:
1. **A user misunderstanding**: The user may have confused exit direction names being hidden in fog with NPC names
2. **A stale/fixed bug**: This bug may have already been resolved
3. **A different manifestation**: NPCs might be missing entirely (not showing "???") due to AI generation issues

## Verification Steps

Before implementing a fix, we need to verify if the bug still exists:

1. Add a regression test that explicitly checks NPC persistence when navigating away and back
2. Check if any WFC-specific code path could cause NPC loss

## Implementation Plan

### Step 1: Add regression test to verify bug existence
File: `tests/test_npc_persistence_navigation.py`

```python
"""Test that NPCs persist when navigating away from and back to a location."""

def test_npcs_persist_after_leaving_and_returning():
    """NPCs should be present when revisiting a location."""
    from cli_rpg.game_state import GameState
    from cli_rpg.models.character import Character
    from cli_rpg.models.location import Location
    from cli_rpg.models.npc import NPC

    char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

    # Create two connected locations
    loc_a = Location(
        name="Location A",
        description="Test location A",
        coordinates=(0, 0),
        connections={"east": "Location B"}
    )
    loc_a.npcs = [NPC(name="TestNPC", description="A test NPC", dialogue="Hello")]

    loc_b = Location(
        name="Location B",
        description="Test location B",
        coordinates=(1, 0),
        connections={"west": "Location A"}
    )

    world = {"Location A": loc_a, "Location B": loc_b}
    game_state = GameState(char, world, starting_location="Location A")

    # Verify NPC is present initially
    look_result = game_state.look()
    assert "TestNPC" in look_result
    assert "???" not in look_result

    # Move east
    game_state.move("east")

    # Move back west
    game_state.move("west")

    # Verify NPC is still present
    look_result = game_state.look()
    assert "TestNPC" in look_result
    assert "???" not in look_result

def test_npcs_persist_wfc_fallback_generation():
    """NPCs persist when navigating through WFC-generated fallback locations."""
    from cli_rpg.game_state import GameState
    from cli_rpg.models.character import Character
    from cli_rpg.models.location import Location
    from cli_rpg.models.npc import NPC
    from cli_rpg.wfc_chunks import ChunkManager
    from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY

    char = Character(name="Test", strength=10, dexterity=10, intelligence=10)

    # Create starting location with NPC
    start = Location(
        name="Start",
        description="Starting location",
        coordinates=(0, 0),
        connections={"east": "Unexplored East"}
    )
    start.npcs = [NPC(name="HomeNPC", description="An NPC at home", dialogue="Welcome!")]

    world = {"Start": start}
    chunk_manager = ChunkManager(tile_registry=DEFAULT_TILE_REGISTRY, world_seed=42)
    chunk_manager.sync_with_locations(world)

    game_state = GameState(char, world, starting_location="Start", chunk_manager=chunk_manager)

    # Verify NPC is present
    assert "HomeNPC" in game_state.look()

    # Move east (generates new fallback location)
    game_state.move("east")

    # Move back west
    game_state.move("west")

    # Verify original NPC is still present
    look_result = game_state.look()
    assert "HomeNPC" in look_result
    assert "???" not in look_result
```

### Step 2: Fix docstring in test_weather.py
Remove outdated reference to "???" for NPCs from line 361.

**Before:**
```python
    - Fog: Hides some exits (50% chance each exit hidden), obscures NPC names with "???"
```

**After:**
```python
    - Fog: Hides some exits (50% chance each exit hidden)
```

### Step 3: If bug is verified, investigate and fix
If the regression tests fail:
1. Add debug logging to track NPC list during navigation
2. Check if world dict is being modified unexpectedly
3. Check if coordinate-based location lookup is returning a different object

## Files to Modify

| File | Changes |
|------|---------|
| `tests/test_npc_persistence_navigation.py` | NEW - Regression tests for NPC persistence |
| `tests/test_weather.py` | Fix stale docstring about NPC "???" |

## Test Plan

1. Run new regression tests: `pytest tests/test_npc_persistence_navigation.py -v`
2. If tests pass, the bug may already be fixed or the report was inaccurate
3. If tests fail, investigate the root cause and implement a fix
