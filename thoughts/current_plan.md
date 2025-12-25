# Add "stats" Alias for Status Command

## Spec
Add "stats" as an alias for the "status" command in the command parser. Players naturally try "stats" as an alternative to "status", so this improves discoverability.

## Tests (add to tests/test_shorthand_commands.py)

```python
# Spec: stats → status (word alias, not single-letter)
def test_stats_expands_to_status(self):
    cmd, args = parse_command("stats")
    assert cmd == "status"
    assert args == []
```

## Implementation

1. **src/cli_rpg/game_state.py** (line ~51-56):
   - Add `"stats": "status"` to the `aliases` dict in `parse_command()`

2. **src/cli_rpg/main.py** (line ~26):
   - Update help text from `"  status (s)         - View your character status"` to `"  status (s, stats)  - View your character status"`

3. **src/cli_rpg/main.py** (line ~54):
   - Update combat help from `"  status (s)    - View combat status"` to `"  status (s, stats) - View combat status"`

4. **tests/test_shorthand_commands.py**:
   - Add test for "stats" alias as shown above
