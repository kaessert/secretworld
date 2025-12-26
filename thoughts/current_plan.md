# Implementation Plan: Improve `enter` Command Error Messages

## Summary
The case-insensitive matching for `enter` already works correctly. The remaining issue is that error messages show lowercased location names and don't suggest available options. Fix the error message to be more helpful.

## Current State Analysis

**What works correctly:**
- Case-insensitive matching in `game_state.enter()` (lines 788-807)
- SubGrid lookup: `loc.name.lower().startswith(target_lower)` (line 796)
- Traditional lookup: `sub_name.lower().startswith(target_lower)` (line 804)
- All 7 existing enter tests pass

**The actual issue:**
- Error message at line 810: `f"No such location: {target_name}"` shows lowercased name
- User types `enter Spectral Grove` → gets `No such location: spectral grove`
- No suggestion of available locations to enter

## Implementation Steps

### Step 1: Add test for case-insensitive matching with multi-word location names

**File: `tests/test_game_state.py`**

Add to `TestEnterExitCommands` class:

```python
def test_enter_case_insensitive_multiword_name(self, monkeypatch):
    """Test that enter works with multi-word location names in any case.

    Spec: 'enter spectral grove' should match 'Spectral Grove' case-insensitively.
    This tests the full command flow where input is lowercased before reaching enter().
    """
    monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

    character = Character("Hero", strength=10, dexterity=10, intelligence=10)

    overworld = Location(
        "Ancient Forest",
        "A mystical forest",
        is_overworld=True,
        sub_locations=["Spectral Grove", "Moonlit Clearing"],
    )
    spectral = Location("Spectral Grove", "A ghostly grove", parent_location="Ancient Forest")
    moonlit = Location("Moonlit Clearing", "A clearing bathed in moonlight", parent_location="Ancient Forest")

    world = {"Ancient Forest": overworld, "Spectral Grove": spectral, "Moonlit Clearing": moonlit}
    game_state = GameState(character, world, "Ancient Forest")

    # Test lowercase input (as parse_command would provide)
    success, _ = game_state.enter("spectral grove")
    assert success is True
    assert game_state.current_location == "Spectral Grove"
```

### Step 2: Improve error message to show available locations

**File: `src/cli_rpg/game_state.py`**

Change line 810 from:
```python
return (False, f"No such location: {target_name}")
```

To:
```python
# Build helpful error message with available locations
available = []
if current.sub_grid is not None:
    available.extend(current.sub_grid._by_name.keys())
if current.sub_locations:
    available.extend(current.sub_locations)
# Remove duplicates while preserving order
available = list(dict.fromkeys(available))

if available:
    return (False, f"No such location: {target_name}. Available: {', '.join(available)}")
else:
    return (False, f"There are no locations to enter here.")
```

### Step 3: Add test for improved error message

**File: `tests/test_game_state.py`**

Add to `TestEnterExitCommands` class:

```python
def test_enter_invalid_location_shows_available(self, monkeypatch):
    """Test that entering invalid location shows available options.

    Spec: Error message should list available sub-locations for discoverability.
    """
    monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

    character = Character("Hero", strength=10, dexterity=10, intelligence=10)

    overworld = Location(
        "City",
        "A bustling city",
        is_overworld=True,
        sub_locations=["Tavern", "Market"],
    )
    tavern = Location("Tavern", "A tavern", parent_location="City")
    market = Location("Market", "A market", parent_location="City")

    world = {"City": overworld, "Tavern": tavern, "Market": market}
    game_state = GameState(character, world, "City")

    success, message = game_state.enter("nonexistent")
    assert success is False
    assert "Available:" in message
    assert "Tavern" in message
    assert "Market" in message
```

## Code Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/game_state.py` | Improve error message to show available locations (line 810) |
| `tests/test_game_state.py` | Add test for multi-word case-insensitive matching |
| `tests/test_game_state.py` | Add test for improved error message |

## Verification

1. Run enter tests: `pytest tests/test_game_state.py -k "enter" -v`
2. Run subgrid tests: `pytest tests/test_subgrid_navigation.py -k "enter" -v`
3. Run full suite: `pytest`
