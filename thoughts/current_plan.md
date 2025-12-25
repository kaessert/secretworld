# Tab Auto-completion Implementation

## Spec (from ISSUES.md lines 63-86)

1. Complete command names: `ta<tab>` -> `talk`
2. Complete arguments contextually:
   - `talk <tab>` -> shows NPCs at current location
   - `go <tab>` -> shows available directions
   - `equip <tab>` -> shows equippable items (WEAPON/ARMOR) in inventory
   - `use <tab>` -> shows usable items (CONSUMABLE) in inventory
   - `buy <tab>` -> shows shop items (when in shop)
3. Cycle through multiple matches with repeated tab
4. Show all options on double-tab when ambiguous

## Implementation

### 1. Create `src/cli_rpg/completer.py`

New module with:

```python
class CommandCompleter:
    """Readline-compatible completer for game commands."""

    def __init__(self):
        self._game_state: Optional[GameState] = None

    def set_game_state(self, game_state: Optional[GameState]) -> None:
        """Set current game state for contextual completions."""

    def complete(self, text: str, state: int) -> Optional[str]:
        """Readline completer callback."""
```

**Complete method logic:**
- Parse readline buffer to get current line
- If completing first word: complete command names from `KNOWN_COMMANDS`
- If completing argument: dispatch to command-specific completers

**Command-specific completers:**
- `_complete_go()`: return `location.get_available_directions()`
- `_complete_talk()`: return `[npc.name for npc in location.npcs]`
- `_complete_equip()`: return equippable items (WEAPON/ARMOR) from inventory
- `_complete_use()`: return consumable items from inventory
- `_complete_buy()`: return shop item names (if `current_shop` set)

### 2. Update `src/cli_rpg/input_handler.py`

Add to `init_readline()`:
```python
from cli_rpg.completer import completer  # module-level instance
readline.set_completer(completer.complete)
readline.parse_and_bind("tab: complete")
```

Add function to set game state:
```python
def set_completer_context(game_state: Optional[GameState]) -> None:
    """Update completer with current game state."""
    completer.set_game_state(game_state)
```

### 3. Update `src/cli_rpg/main.py`

In `run_game_loop()`, after game state is created and before loop:
```python
from cli_rpg.input_handler import set_completer_context
set_completer_context(game_state)
```

Also call `set_completer_context(None)` when exiting game loop.

## Tests - `tests/test_completer.py`

### Command completion tests
- `test_complete_command_prefix()`: "lo" -> "look"
- `test_complete_command_multiple_matches()`: "s" -> ["save", "sell", "shop", "status"]
- `test_complete_command_exact_match()`: "look" -> "look " (with trailing space)
- `test_complete_unknown_prefix()`: "xyz" -> None

### Contextual argument tests
- `test_complete_go_directions()`: "go n" -> "go north"
- `test_complete_talk_npc_names()`: "talk T" -> "talk Town Merchant"
- `test_complete_equip_weapon_armor()`: shows only WEAPON/ARMOR items
- `test_complete_use_consumables()`: shows only CONSUMABLE items
- `test_complete_buy_shop_items()`: shows shop inventory items

### Edge cases
- `test_complete_without_game_state()`: returns only commands, no args
- `test_complete_empty_location_npcs()`: "talk " -> no completions
- `test_complete_not_in_shop()`: "buy " -> no completions

## Verification

```bash
pytest tests/test_completer.py -v
pytest tests/test_input_handler.py -v
pytest  # Full suite
```

Manual test: Run game, type partial commands with tab.
