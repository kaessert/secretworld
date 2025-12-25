# Implementation Plan: `dismiss <companion>` Command

## Spec
Add a `dismiss` command that removes a companion from the party. This completes the companion management lifecycle (recruit → travel with → dismiss).

**Behavior:**
- `dismiss <name>` - Removes companion matching `<name>` from `game_state.companions`
- Case-insensitive name matching (like `recruit`)
- Error cases: no arg provided, companion not in party
- Success message acknowledging the departure

## Tests

Add to `tests/test_companion_commands.py`:

```python
class TestDismissCommand:
    """Tests for the 'dismiss' command."""

    def test_dismiss_no_companion_specified(self):
        """Test dismiss command without companion name shows error."""
        game_state = create_test_game_state()
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "dismiss", [])

        assert success is True
        assert "dismiss" in message.lower() or "specify" in message.lower()

    def test_dismiss_companion_not_in_party(self):
        """Test dismiss command with nonexistent companion shows error."""
        game_state = create_test_game_state()
        game_state.companions = []

        success, message = handle_exploration_command(game_state, "dismiss", ["Elara"])

        assert success is True
        assert "no companion" in message.lower() or "not" in message.lower()

    def test_dismiss_success_removes_companion(self):
        """Test successful dismiss removes companion from party."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=30
        )
        game_state = create_test_game_state(companions=[companion])

        success, message = handle_exploration_command(game_state, "dismiss", ["Elara"])

        assert success is True
        assert len(game_state.companions) == 0
        assert "left" in message.lower() or "dismiss" in message.lower()

    def test_dismiss_case_insensitive(self):
        """Test dismiss command is case-insensitive."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square"
        )
        game_state = create_test_game_state(companions=[companion])

        success, message = handle_exploration_command(game_state, "dismiss", ["elara"])

        assert success is True
        assert len(game_state.companions) == 0


class TestDismissInKnownCommands:
    """Test that dismiss is in KNOWN_COMMANDS."""

    def test_dismiss_in_known_commands(self):
        """Test that 'dismiss' is a recognized command."""
        from cli_rpg.game_state import KNOWN_COMMANDS
        assert "dismiss" in KNOWN_COMMANDS
```

## Implementation

1. **Add "dismiss" to KNOWN_COMMANDS** in `src/cli_rpg/game_state.py` (line ~56)

2. **Add command handler** in `src/cli_rpg/main.py` after the `recruit` handler (~line 1099):
```python
elif command == "dismiss":
    if not args:
        return (True, "\nDismiss whom? Specify a companion name.")

    companion_name = " ".join(args).lower()
    matching = [c for c in game_state.companions if c.name.lower() == companion_name]

    if not matching:
        return (True, f"\nNo companion named '{' '.join(args)}' in your party.")

    companion = matching[0]
    game_state.companions.remove(companion)
    return (True, f"\n{companion.name} has left your party.")
```

3. **Add to help text** in `get_command_reference()` (~line 50):
```python
"  dismiss <name>     - Dismiss a companion from your party",
```
