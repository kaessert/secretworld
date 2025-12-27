# Fix Failing Tests (5 issues: 3 failures, 2 errors)

## Summary

Fix 5 broken tests caused by recent architecture changes (Location model removing `connections`, movement requiring coordinates/ChunkManager).

---

## Issue 1: TestCaravanEvent fixture TypeError (2 errors)

**File**: `tests/test_world_events.py` line 388

**Problem**: Location constructor passes `{}` as third positional argument (old `connections` dict) plus `npcs=[]` keyword arg, causing "multiple values for argument 'npcs'"

**Fix**: Remove `{}` and `npcs=[]` - the Location signature is now `Location(name, description, npcs=[], coordinates=None, ...)`

```python
# Before
"Town": Location("Town", "A town", {}, coordinates=(0, 0), npcs=[]),

# After
"Town": Location("Town", "A town", coordinates=(0, 0)),
```

---

## Issue 2: test_validate_area_location_invalid_connections (1 failure)

**File**: `tests/test_ai_service.py` line 1174-1202

**Problem**: Test expects `AIGenerationError` when connections is a list, but `_validate_area_location()` no longer validates connections (line 1046-1047 comments say connections are ignored)

**Fix**: Delete this test. The validation no longer exists because connections are ignored in coordinate-based navigation.

---

## Issue 3: Movement tests fail without ChunkManager (2 failures)

**Files**:
- `tests/test_game_state_combat.py` line 175-208 (`test_move_can_trigger_encounter`)
- `tests/test_main_game_loop_state_handling.py` line 37-60 (`test_random_encounter_triggers_combat_state`)

**Problem**: Tests create simple worlds without coordinates, but `move()` now requires:
1. Current location to have coordinates (line 493-495 returns error if None)
2. Or fallback fails silently

**Fix**: Add coordinates to test locations and add explicit connections or mock the ChunkManager passability check.

For `test_game_state_combat.py`:
```python
world = {
    "Town Square": Location(
        name="Town Square",
        description="A bustling town square",
        coordinates=(0, 0)
    ),
    "Forest Path": Location(
        name="Forest Path",
        description="A path through the forest",
        coordinates=(0, 1)  # North of Town Square
    )
}
```

For `test_main_game_loop_state_handling.py`:
```python
world = {
    "Town": Location(name="Town", description="A town", coordinates=(0, 0)),
    "Forest": Location(name="Forest", description="A forest", coordinates=(0, 1))
}
```

---

## Implementation Steps

1. **Fix test_world_events.py** (line 388): Remove `{}` positional arg and `npcs=[]` keyword arg from Location constructor
2. **Delete test_validate_area_location_invalid_connections** from test_ai_service.py (lines 1173-1202)
3. **Fix test_game_state_combat.py** (line 183-192): Add coordinates to Location constructors
4. **Fix test_main_game_loop_state_handling.py** (line 42-45): Add coordinates to Location constructors

---

## Verification

```bash
pytest tests/test_world_events.py::TestCaravanEvent -v
pytest tests/test_ai_service.py::test_validate_area_location_invalid_connections -v
pytest tests/test_game_state_combat.py::TestMoveWithCombat::test_move_can_trigger_encounter -v
pytest tests/test_main_game_loop_state_handling.py::TestExplorationToCombatTransition::test_random_encounter_triggers_combat_state -v
```

Final verification:
```bash
pytest
```
