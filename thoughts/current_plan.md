# Fix Rest Command Tiredness Threshold

## Issue
The rest command allows resting when tiredness > 0, but the documented behavior (README, model docstring, `can_sleep()` method, and tests) all specify that rest should require tiredness >= 30.

## Decision
**Option B (Fix Implementation)**: The `Tiredness.can_sleep()` method exists and is already tested. The implementation simply needs to use it.

## Changes

### 1. Update `src/cli_rpg/main.py` (rest command logic)

**Location**: Lines 2381-2385 in `handle_exploration_command`

**Current code**:
```python
no_tiredness = char.tiredness.current == 0

if at_full_health and at_full_stamina and no_dread and no_tiredness:
    return (True, "\nYou're already at full health, stamina, and feeling calm and rested!")
```

**New code**:
```python
can_sleep_for_tiredness = char.tiredness.can_sleep()  # True when tiredness >= 30

if at_full_health and at_full_stamina and no_dread and not can_sleep_for_tiredness:
    return (True, "\nYou're already at full health, stamina, and feeling calm and rested!")
```

**Also update the tiredness reduction block** (around line 2418-2431):
```python
# Reduce tiredness based on sleep quality
if can_sleep_for_tiredness:
    quality = char.tiredness.sleep_quality()
    # ... rest of logic unchanged
```

### 2. Add test in `tests/test_rest_command.py`

Add a new test to verify the 30% threshold:
```python
def test_rest_blocked_when_tiredness_below_30(self, game_state):
    """Spec: Cannot rest when tiredness < 30 (too alert to sleep)."""
    gs = game_state
    char = gs.current_character
    # Set tiredness to 20 (below 30 threshold)
    char.tiredness.current = 20
    # Reduce stamina so we're not at full
    char.stamina = 1

    cont, msg = handle_exploration_command(gs, "rest", [])

    # Tiredness should be unchanged since can't sleep
    assert char.tiredness.current == 20
```

### 3. Update ISSUES.md

Mark the issue as resolved.

## Test Plan
1. Run `pytest tests/test_rest_command.py -v` to verify new test passes
2. Run `pytest tests/test_tiredness.py -v` to ensure existing tiredness tests still pass
3. Run full test suite `pytest` to ensure no regressions
