# Discovery Milestone Game Loop Integration (Issue 24)

## Task
Wire `check_and_award_milestones()` into the game loop at three trigger points: secret discovery, treasure opening, and boss defeat.

## Implementation

### 1. Secret Discovery Milestone (main.py ~line 1113)
After `perform_active_search()` returns success, call milestone check:
```python
# After line 1113: return (True, f"\n{message}")
if found:
    milestone_msg = game_state.check_and_award_milestones("secret")
    if milestone_msg:
        message = f"{message}\n{milestone_msg}"
return (True, f"\n{message}")
```

### 2. Treasure Opening Milestone (main.py ~line 2467)
After chest is opened and items transferred, call milestone check:
```python
# After the "items_added" logic, before return
milestone_msg = game_state.check_and_award_milestones("treasure")
if milestone_msg:
    # Append to output message
```

### 3. Boss Defeat Milestone (main.py ~line 961)
After `game_state.mark_boss_defeated()`, call milestone check:
```python
# After line 961: game_state.mark_boss_defeated()
milestone_msg = game_state.check_and_award_milestones("boss")
if milestone_msg:
    output += f"\n{milestone_msg}"
```

## Files to Modify
- `src/cli_rpg/main.py` - Add 3 milestone check calls

## Tests
Add integration tests to verify milestone messages appear in game output:
- `tests/test_discovery_milestones.py` - Add tests for game loop integration:
  - Test secret milestone triggers on search command
  - Test treasure milestone triggers on open command
  - Test boss milestone triggers after boss defeat
