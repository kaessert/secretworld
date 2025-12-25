# Ultra-short Movement Commands

## Spec
Add single-character (`n`, `s`, `e`, `w`) and two-character (`gn`, `gs`, `ge`, `gw`) shortcuts for movement.

**Behavior:**
- `n` / `gn` → `go north`
- `s` / `gs` → `go south` (but `s` alone conflicts with `status`)
- `e` / `ge` → `go east` (but `e` alone conflicts with `equip`)
- `w` / `gw` → `go west`

**Resolution:** Keep existing `s` → `status` and `e` → `equip` aliases. Add:
- Single-letter: `n` → go north, `w` → go west
- Two-character: `gn`, `gs`, `ge`, `gw` → go <direction>

## Tests (tests/test_game_state.py)

```python
def test_parse_command_movement_shortcuts_two_char(self):
    """Test ultra-short movement shortcuts (gn, gs, ge, gw)."""
    for shortcut, direction in [("gn", "north"), ("gs", "south"), ("ge", "east"), ("gw", "west")]:
        cmd, args = parse_command(shortcut)
        assert cmd == "go"
        assert args == [direction]

def test_parse_command_movement_shortcuts_single_char(self):
    """Test single-char movement shortcuts (n, w) - s/e have existing meanings."""
    for shortcut, direction in [("n", "north"), ("w", "west")]:
        cmd, args = parse_command(shortcut)
        assert cmd == "go"
        assert args == [direction]

def test_parse_command_s_still_means_status(self):
    """Confirm 's' still maps to 'status' (not 'go south')."""
    cmd, args = parse_command("s")
    assert cmd == "status"

def test_parse_command_e_still_means_equip(self):
    """Confirm 'e' still maps to 'equip' (not 'go east')."""
    cmd, args = parse_command("e")
    assert cmd == "equip"
```

## Implementation (src/cli_rpg/game_state.py)

**Step 1:** Add movement aliases to the `aliases` dict (around line 76):
```python
aliases = {
    # ... existing aliases ...
    # Ultra-short movement shortcuts
    "n": "go", "w": "go",
    "gn": "go", "gs": "go", "ge": "go", "gw": "go"
}
```

**Step 2:** Save raw command before alias expansion and add direction inference after line 83:
```python
command = parts[0]
raw_command = command  # Save for movement shortcut detection
original_command = command
args = parts[1:]

# Expand shorthand aliases
aliases = { ... }
command = aliases.get(command, command)

# Infer direction from movement shortcuts (when no args provided)
if command == "go" and not args:
    movement_directions = {
        "n": "north", "w": "west",
        "gn": "north", "gs": "south", "ge": "east", "gw": "west"
    }
    if raw_command in movement_directions:
        args = [movement_directions[raw_command]]
```

## Steps
1. Add tests to `tests/test_game_state.py`
2. Run tests (should fail)
3. Update `parse_command()` in `src/cli_rpg/game_state.py`
4. Run tests (should pass)
5. Run full test suite
