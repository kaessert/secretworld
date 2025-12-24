# Implementation Plan: Shorthand Commands

## Spec

Add single-letter aliases for common commands:
- `g` → `go`
- `l` → `look`
- `a` → `attack`
- `c` → `cast`
- `d` → `defend`
- `f` → `flee`
- `s` → `status`
- `i` → `inventory`
- `m` → `map`
- `h` → `help`
- `t` → `talk`
- `u` → `use`
- `e` → `equip`

Aliases should:
1. Be expanded to full command in `parse_command()` before validation
2. Preserve all arguments (e.g., `g north` → `go north`)
3. Be case-insensitive
4. Be documented in help output

## Tests

Create `tests/test_shorthand_commands.py`:

```python
from cli_rpg.game_state import parse_command

class TestShorthandCommands:
    def test_g_expands_to_go(self):
        cmd, args = parse_command("g north")
        assert cmd == "go"
        assert args == ["north"]

    def test_l_expands_to_look(self):
        cmd, args = parse_command("l")
        assert cmd == "look"
        assert args == []

    def test_a_expands_to_attack(self):
        cmd, args = parse_command("a")
        assert cmd == "attack"
        assert args == []

    def test_c_expands_to_cast(self):
        cmd, args = parse_command("c")
        assert cmd == "cast"
        assert args == []

    def test_d_expands_to_defend(self):
        cmd, args = parse_command("d")
        assert cmd == "defend"
        assert args == []

    def test_f_expands_to_flee(self):
        cmd, args = parse_command("f")
        assert cmd == "flee"
        assert args == []

    def test_s_expands_to_status(self):
        cmd, args = parse_command("s")
        assert cmd == "status"
        assert args == []

    def test_i_expands_to_inventory(self):
        cmd, args = parse_command("i")
        assert cmd == "inventory"
        assert args == []

    def test_m_expands_to_map(self):
        cmd, args = parse_command("m")
        assert cmd == "map"
        assert args == []

    def test_h_expands_to_help(self):
        cmd, args = parse_command("h")
        assert cmd == "help"
        assert args == []

    def test_t_expands_to_talk(self):
        cmd, args = parse_command("t merchant")
        assert cmd == "talk"
        assert args == ["merchant"]

    def test_u_expands_to_use(self):
        cmd, args = parse_command("u potion")
        assert cmd == "use"
        assert args == ["potion"]

    def test_e_expands_to_equip(self):
        cmd, args = parse_command("e sword")
        assert cmd == "equip"
        assert args == ["sword"]

    def test_shorthand_case_insensitive(self):
        cmd, args = parse_command("G NORTH")
        assert cmd == "go"
        assert args == ["north"]
```

## Implementation Steps

### 1. Update `parse_command()` in `src/cli_rpg/game_state.py`

Add alias expansion after line 44 (after extracting command), before line 48 (known_commands validation):

```python
# Expand shorthand aliases
aliases = {
    "g": "go", "l": "look", "a": "attack", "c": "cast",
    "d": "defend", "f": "flee", "s": "status", "i": "inventory",
    "m": "map", "h": "help", "t": "talk", "u": "use", "e": "equip"
}
command = aliases.get(command, command)
```

### 2. Update `get_command_reference()` in `src/cli_rpg/main.py`

Add shorthand hints to command descriptions (lines 21-46):

```python
"Exploration Commands:",
"  look (l)           - Look around at your surroundings",
"  go (g) <direction> - Move in a direction (north, south, east, west)",
"  status (s)         - View your character status",
"  inventory (i)      - View your inventory and equipped items",
"  equip (e) <item>   - Equip a weapon or armor from inventory",
"  unequip <slot>     - Unequip weapon or armor (slot: weapon/armor)",
"  use (u) <item>     - Use a consumable item",
"  talk (t) <npc>     - Talk to an NPC",
"  shop               - View shop inventory (when at a shop)",
"  buy <item>         - Buy an item from the shop",
"  sell <item>        - Sell an item to the shop",
"  map (m)            - Display a map of explored areas",
"  help (h)           - Display this command reference",
"  save               - Save your game (not available during combat)",
"  quit               - Return to main menu",
"",
"Combat Commands:",
"  attack (a)        - Attack the enemy",
"  defend (d)        - Take a defensive stance",
"  cast (c)          - Cast a magic attack (intelligence-based)",
"  flee (f)          - Attempt to flee from combat",
"  use (u) <item>    - Use a consumable item",
"  status (s)        - View combat status",
```

### 3. Run tests

```bash
pytest tests/test_shorthand_commands.py -v
pytest tests/test_game_state.py::TestParseCommand -v
```
