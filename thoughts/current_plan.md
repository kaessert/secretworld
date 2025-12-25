# Implementation Plan: Terminal Bell Sound Effects

## Spec

Add terminal bell (`\a`) sound effects for important game events:
- **Combat victory** - Player wins a fight
- **Level up** - Player gains a level
- **Player death** - Game over
- **Quest completion** - Quest turned in for rewards

Bell sounds will be disabled in `--non-interactive` and `--json` modes, following the same pattern as `text_effects.py`.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/cli_rpg/sound_effects.py` | Create new module |
| `src/cli_rpg/main.py` | Disable sounds in non-interactive/JSON; add death/quest sounds |
| `src/cli_rpg/combat.py` | Add victory sound |
| `src/cli_rpg/models/character.py` | Add level-up sound |
| `tests/test_sound_effects.py` | Create tests |

## Implementation Steps

### 1. Create `src/cli_rpg/sound_effects.py`

New module mirroring `text_effects.py` pattern:
- `set_sound_enabled(enabled: Optional[bool])` - global toggle
- `sound_enabled() -> bool` - check if enabled (follows `color_enabled()` when None)
- `bell(file)` - output `\a` if enabled
- Semantic helpers: `sound_victory()`, `sound_level_up()`, `sound_death()`, `sound_quest_complete()`

### 2. Create `tests/test_sound_effects.py`

Tests for:
- `bell()` outputs `\a` when enabled
- `bell()` outputs nothing when disabled
- `sound_enabled()` follows `color_enabled()` when not explicitly set
- Explicit override works

### 3. Update `src/cli_rpg/main.py`

- Import `set_sound_enabled` from `sound_effects`
- In `run_json_mode()`: add `set_sound_enabled(False)` (line ~1479)
- In `run_non_interactive()`: add `set_sound_enabled(False)` (line ~1678)
- In `handle_combat_command()` player death: add `sound_death()` call
- In `handle_exploration_command()` "complete" command: add `sound_quest_complete()` call

### 4. Update `src/cli_rpg/combat.py`

- Import `sound_victory`
- In `end_combat(victory=True)`: add `sound_victory()` call

### 5. Update `src/cli_rpg/models/character.py`

- Import `sound_level_up`
- In `gain_xp()` when `level_ups > 0`: add `sound_level_up()` call

## Test Commands

```bash
pytest tests/test_sound_effects.py -v
pytest --cov=src/cli_rpg/sound_effects
```
