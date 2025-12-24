# Implementation Plan: Add Colors to Output

## Specification

Add color highlighting to CLI output to improve user experience:
- **Enemies**: Red (during combat messages)
- **Locations**: Cyan/blue (location names in look/move output)
- **NPCs**: Yellow (NPC names in dialogue/location display)
- **Items**: Green (item names in inventory/loot/shop)
- **Player stats**: Magenta (status display headers)
- **Damage/health loss**: Red
- **Healing/gains**: Green
- **Gold**: Yellow
- **Map markers**: Various colors for visual distinction

Use ANSI escape codes directly (no external dependency) with a disable flag via environment variable `CLI_RPG_NO_COLOR=true` for terminals that don't support colors.

## Implementation Steps

### 1. Create `src/cli_rpg/colors.py` - Color utility module

```python
# Define color constants and helper functions
RESET, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, BOLD = ANSI codes
color_enabled() -> bool  # Check CLI_RPG_NO_COLOR env var
colorize(text, color) -> str  # Wrap text in color codes if enabled
# Semantic helpers: enemy(), location(), npc(), item(), gold(), damage(), heal()
```

### 2. Update `src/cli_rpg/combat.py` - Combat messages

- `CombatEncounter.start()`: Color enemy name red
- `player_attack()`, `player_cast()`: Color enemy name red, damage values
- `enemy_turn()`: Color enemy name red, damage red, remaining HP
- `end_combat()`: Color victory green, defeat red, XP/gold gains
- `get_status()`: Color headers, HP values (green for healthy, red for low)
- `generate_loot()`: Item names colored green

### 3. Update `src/cli_rpg/models/location.py` - Location display

- `__str__()`: Color location name cyan, NPC names yellow, exits

### 4. Update `src/cli_rpg/main.py` - Command output

- `handle_combat_command()`: Ensure combat messages preserve colors
- `handle_exploration_command()`:
  - `talk`: Color NPC name yellow
  - `shop`/`buy`/`sell`: Color item names green, gold yellow
  - `equip`/`use`: Color item names green
- `get_command_reference()`: Color section headers

### 5. Update `src/cli_rpg/game_state.py` - Movement messages

- `move()`: Color direction and destination location name

### 6. Update `src/cli_rpg/map_renderer.py` - Map display

- Color `@` (player marker) bold cyan
- Color other location markers appropriately

### 7. Update `src/cli_rpg/models/character.py` - Character display

- `__str__()`: Color stat labels, HP (conditional on health %), gold

### 8. Update `src/cli_rpg/models/inventory.py` - Inventory display

- `__str__()`: Color item names, equipped items highlighted

## Test Plan

### Create `tests/test_colors.py`

1. `test_color_enabled_default` - Colors enabled when CLI_RPG_NO_COLOR not set
2. `test_color_disabled_via_env` - Colors disabled when CLI_RPG_NO_COLOR=true
3. `test_colorize_returns_colored_when_enabled` - Verify ANSI codes present
4. `test_colorize_returns_plain_when_disabled` - Verify no ANSI codes
5. `test_semantic_helpers_return_correct_colors` - enemy(), location(), npc(), item()
6. `test_reset_always_appended` - Ensure RESET code terminates colored text

### Existing test considerations

- Existing tests compare exact string output - they will continue to pass if run with `CLI_RPG_NO_COLOR=true`
- Add a pytest fixture in `conftest.py` to disable colors during test runs by default
