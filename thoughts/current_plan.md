# Fix: Allow quit command during combat

## Summary
Add `quit` command support to `handle_combat_command()` in `main.py` so players can exit the game during combat with an unsaved progress warning.

## Spec
- During combat, `quit` command should prompt user about unsaved progress
- User can choose to save before quitting or quit without saving
- After handling, return `False` (via a signal) to exit the game loop
- Update combat command error message to include `quit` as valid option

## Implementation

### 1. Add test first
**File:** `tests/test_main_combat_integration.py`

Add test in `TestCombatCommandRouting` class:
```python
def test_quit_command_during_combat_exits_game(self):
    """Spec: When in combat, quit command should allow exiting the game."""
```
- Mock `input()` to return 'n' (no save)
- Call `handle_combat_command(game_state, "quit", [])`
- Assert return value signals game should exit (need to check return type)

### 2. Modify handle_combat_command to support quit
**File:** `src/cli_rpg/main.py`, function `handle_combat_command()` (line ~117)

**Change needed:** The function currently returns only a string. To support `quit`, it needs to return a tuple `(continue_game: bool, message: str)` like `handle_exploration_command()`.

**Steps:**
1. Change return type to `tuple[bool, str]` (line 126)
2. Update all existing returns from `return message` to `return (True, message)`
3. Add `quit` command handler before the `else` clause (around line 236):
```python
elif command == "quit":
    print("\n" + "=" * 50)
    print("⚠️  Warning: You are in combat! Progress may be lost.")
    response = input("Save before quitting? (y/n): ").strip().lower()
    if response == 'y':
        try:
            filepath = save_game_state(game_state)
            print(f"\n✓ Game saved successfully!")
            print(f"  Save location: {filepath}")
        except IOError as e:
            print(f"\n✗ Failed to save game: {e}")
    print("\nReturning to main menu...")
    return (False, "")
```

4. Update error message (line 237) to include `quit`:
```python
return (True, "\n✗ Can't do that during combat! Use: attack, defend, cast, flee, status, or quit")
```

### 3. Update run_game_loop to handle new return type
**File:** `src/cli_rpg/main.py`, function `run_game_loop()` (line ~460)

Change:
```python
if game_state.is_in_combat():
    message = handle_combat_command(game_state, command, args)
    print(message)
```

To:
```python
if game_state.is_in_combat():
    continue_game, message = handle_combat_command(game_state, command, args)
    print(message)
    if not continue_game:
        break
```

### 4. Run tests
```bash
pytest tests/test_main_combat_integration.py -v
pytest -x  # Full suite
```
