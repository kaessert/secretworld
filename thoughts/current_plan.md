# Implementation Plan: Shorthands for Movements

## Specification

Expand direction shorthands when using the `go` command:
- `n` → `north`, `s` → `south`, `e` → `east`, `w` → `west`
- Works with command shorthand: `g n` → `go north`
- Works with full command: `go s` → `go south`
- Case-insensitive: `G N` → `go north`

## Implementation Steps

### 1. Update `src/cli_rpg/game_state.py` - `parse_command()` function

After expanding command aliases (line 55), add direction alias expansion for the `go` command:

```python
# After command = aliases.get(command, command)

# Expand direction shorthands for go command
if command == "go" and args:
    direction_aliases = {"n": "north", "s": "south", "e": "east", "w": "west"}
    args[0] = direction_aliases.get(args[0], args[0])
```

### 2. Add tests to `tests/test_shorthand_commands.py`

Add new test class `TestDirectionShorthands`:

```python
class TestDirectionShorthands:
    """Test direction shorthand expansion for go command."""

    def test_g_n_expands_to_go_north(self):
        cmd, args = parse_command("g n")
        assert cmd == "go"
        assert args == ["north"]

    def test_g_s_expands_to_go_south(self):
        cmd, args = parse_command("g s")
        assert cmd == "go"
        assert args == ["south"]

    def test_g_e_expands_to_go_east(self):
        cmd, args = parse_command("g e")
        assert cmd == "go"
        assert args == ["east"]

    def test_g_w_expands_to_go_west(self):
        cmd, args = parse_command("g w")
        assert cmd == "go"
        assert args == ["west"]

    def test_go_n_expands_to_go_north(self):
        cmd, args = parse_command("go n")
        assert cmd == "go"
        assert args == ["north"]

    def test_direction_shorthand_case_insensitive(self):
        cmd, args = parse_command("G N")
        assert cmd == "go"
        assert args == ["north"]

    def test_full_direction_still_works(self):
        cmd, args = parse_command("g north")
        assert cmd == "go"
        assert args == ["north"]
```

## Verification

Run: `pytest tests/test_shorthand_commands.py -v`
