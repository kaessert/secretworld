# Plan: Fix Inconsistent Save Behavior During Combat

## Problem Summary
During combat, `save` is correctly blocked, but `quit + y` allows saving and loses combat state - enabling players to exploit this to escape losing fights.

## Spec
- Quit command during combat should NOT offer to save (matching the `save` command behavior)
- Players should be warned that progress will be lost
- On reload, combat state is not preserved (this is acceptable as saving during combat is disallowed)

## Changes

### 1. Modify `handle_combat_command()` quit handler in `main.py` (lines 299-311)

**Current behavior:**
```python
elif command == "quit":
    print("\n" + "=" * 50)
    print("Warning: You are in combat! Progress may be lost.")
    response = input("Save before quitting? (y/n): ").strip().lower()
    if response == 'y':
        # saves the game (allowing exploit)
    print("\nReturning to main menu...")
    return (False, "")
```

**New behavior:**
```python
elif command == "quit":
    print("\n" + "=" * 50)
    print("Warning: You are in combat! Saving is disabled during combat.")
    print("If you quit now, your combat progress will be lost.")
    response = input("Quit without saving? (y/n): ").strip().lower()
    if response == 'y':
        print("\nReturning to main menu...")
        return (False, "")
    return (True, "")  # Cancel quit, continue combat
```

### 2. Update existing test in `tests/test_main_combat_integration.py`

Modify `test_quit_command_with_save_saves_game()` to verify:
- Save is NOT offered during combat quit
- User is warned about losing combat progress
- Quitting exits without saving

### 3. Add new test: `test_quit_during_combat_does_not_offer_save()`

Verify:
- No save prompt is shown
- Warning about combat and lost progress is displayed
- `save_game_state` is NOT called when quitting during combat
