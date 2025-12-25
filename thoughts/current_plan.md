# Companion Dismiss Confirmation Dialog

## Summary
Add a confirmation prompt before dismissing companions to prevent accidental loss of high-bond companions.

## Spec
- When player runs `dismiss <name>`, show confirmation prompt with companion's name and bond level
- For high-bond companions (TRUSTED/DEVOTED), emphasize the bond investment being lost
- Confirm with y/n input; only proceed with dismissal on 'y'
- In non-interactive mode, skip confirmation and dismiss immediately (consistent with quit behavior)

## Implementation Steps

### 1. Update `handle_exploration_command` in `main.py` (lines 1113-1125)

Current code:
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

Updated code:
```python
elif command == "dismiss":
    if not args:
        return (True, "\nDismiss whom? Specify a companion name.")

    companion_name = " ".join(args).lower()
    matching = [c for c in game_state.companions if c.name.lower() == companion_name]

    if not matching:
        return (True, f"\nNo companion named '{' '.join(args)}' in your party.")

    companion = matching[0]

    # Show confirmation with bond info
    if non_interactive:
        # Skip confirmation in non-interactive mode
        game_state.companions.remove(companion)
        return (True, f"\n{companion.name} has left your party.")

    # Build confirmation message based on bond level
    from cli_rpg.models.companion import BondLevel
    bond_level = companion.get_bond_level()
    if bond_level in (BondLevel.TRUSTED, BondLevel.DEVOTED):
        print(f"\n⚠️  {companion.name} is {bond_level.value} ({companion.bond_points}% bond).")
        print("Dismissing will reduce their bond significantly if you meet again.")
    else:
        print(f"\n{companion.name} ({bond_level.value}, {companion.bond_points}% bond)")

    sys.stdout.flush()
    response = input(f"Dismiss {companion.name}? (y/n): ").strip().lower()

    if response == 'y':
        game_state.companions.remove(companion)
        return (True, f"\n{companion.name} has left your party.")
    else:
        return (True, f"\n{companion.name} remains in your party.")
```

### 2. Add tests in `tests/test_companion_commands.py`

Add new test class `TestDismissConfirmation`:

```python
class TestDismissConfirmation:
    """Tests for dismiss confirmation dialog."""

    def test_dismiss_high_bond_requires_confirmation(self, monkeypatch):
        """Test dismissing trusted companion shows warning and requires confirmation."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=60  # TRUSTED level
        )
        game_state = create_test_game_state(companions=[companion])

        # Simulate user typing 'y'
        inputs = iter(['y'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        success, message = handle_exploration_command(game_state, "dismiss", ["Elara"])

        assert success is True
        assert len(game_state.companions) == 0
        assert "left" in message.lower()

    def test_dismiss_cancelled_on_no(self, monkeypatch):
        """Test dismissing companion cancelled when user types 'n'."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=30
        )
        game_state = create_test_game_state(companions=[companion])

        # Simulate user typing 'n'
        inputs = iter(['n'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        success, message = handle_exploration_command(game_state, "dismiss", ["Elara"])

        assert success is True
        assert len(game_state.companions) == 1
        assert "remains" in message.lower()

    def test_dismiss_non_interactive_skips_confirmation(self):
        """Test dismiss in non-interactive mode skips confirmation."""
        companion = Companion(
            name="Elara",
            description="A wandering minstrel",
            recruited_at="Town Square",
            bond_points=75  # DEVOTED level
        )
        game_state = create_test_game_state(companions=[companion])

        # non_interactive=True should skip confirmation
        success, message = handle_exploration_command(
            game_state, "dismiss", ["Elara"], non_interactive=True
        )

        assert success is True
        assert len(game_state.companions) == 0
```

## Verification
1. Run existing tests: `pytest tests/test_companion_commands.py -v`
2. Run new confirmation tests: `pytest tests/test_companion_commands.py::TestDismissConfirmation -v`
3. Manual test: Start game, recruit companion, build bond, try dismiss - verify prompt appears
