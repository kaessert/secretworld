# Darkness Meter - Implementation Plan

## Feature Spec

The Darkness Meter is a psychological horror element that tracks **Dread** (0-100%). Dread builds in dangerous areas and has gameplay consequences at high levels.

### Core Mechanics
- **Dread value**: Integer 0-100 stored on Character
- **Dread builds from**:
  - Entering dungeon/cave/ruins locations (+5-15 based on category)
  - Combat encounters (+10 per combat)
  - Being at night (+5 per movement at night)
  - Low health (<30%) (+5 per action while injured)
- **Dread reduces from**:
  - Entering town locations (-15)
  - Resting (-20)
  - Talking to NPCs (-5 per conversation)
- **High dread effects** (threshold-based):
  - 50%+: Paranoid whispers appear (special dread whisper pool)
  - 75%+: -10% attack penalty (debuff applied in combat)
  - 100%: Shadow creature attack triggered OR random health damage

### Display
- Show dread bar in `status` command: `DREAD: ████████░░░░░░░░ 53%`
- Atmospheric messages on dread milestones (crossing 25%, 50%, 75%, 100%)

---

## Implementation Steps

### 1. Create DreadMeter model
**File**: `src/cli_rpg/models/dread.py`

```python
@dataclass
class DreadMeter:
    dread: int = 0  # 0-100

    def add_dread(self, amount: int) -> str | None  # Returns milestone message
    def reduce_dread(self, amount: int) -> None
    def get_display(self) -> str  # Bar display
    def get_penalty(self) -> float  # Attack modifier (1.0 or 0.9)
    def is_critical(self) -> bool  # 100%
    def to_dict() / from_dict()  # Persistence
```

### 2. Add dread to Character model
**File**: `src/cli_rpg/models/character.py`

- Add `dread_meter: DreadMeter` field
- Serialize/deserialize in `to_dict()` / `from_dict()`
- Modify `get_attack_power()` to apply dread penalty when >= 75

### 3. Integrate dread into gameplay
**File**: `src/cli_rpg/game_state.py`

- In `move()`: Add dread based on location category and time of day
- In `move()` to town: Reduce dread
- In `trigger_encounter()`: Add dread after combat starts

### 4. Integrate dread into main.py commands
**File**: `src/cli_rpg/main.py`

- In `handle_exploration_command("status")`: Display dread meter
- In `handle_exploration_command("talk")`: Reduce dread
- In `handle_exploration_command("rest")`: Reduce dread
- In combat victory handler: Check for 100% dread shadow attack

### 5. Add dread-aware whispers
**File**: `src/cli_rpg/whisper.py`

- Add `DREAD_WHISPERS` list for high-dread paranoid whispers
- Modify `get_whisper()` to use dread whispers when dread >= 50

### 6. Persistence compatibility
**File**: `src/cli_rpg/game_state.py`

- Dread is already on Character which serializes - just need from_dict backward compat

---

## Tests

### Unit Tests: `tests/test_dread.py`
1. `test_dread_meter_initialization` - starts at 0
2. `test_add_dread_clamps_to_100` - adding dread caps at 100
3. `test_reduce_dread_clamps_to_0` - reducing dread can't go negative
4. `test_dread_milestone_messages` - crossing thresholds returns messages
5. `test_dread_display_bar` - correct visual bar generation
6. `test_dread_attack_penalty_below_75` - no penalty below 75
7. `test_dread_attack_penalty_at_75` - 10% penalty at/above 75
8. `test_dread_serialization` - to_dict/from_dict roundtrip
9. `test_backward_compatibility_no_dread` - Character.from_dict handles missing dread

### Integration Tests: `tests/test_dread_integration.py`
10. `test_move_to_dungeon_increases_dread`
11. `test_move_to_town_decreases_dread`
12. `test_move_at_night_adds_extra_dread`
13. `test_combat_increases_dread`
14. `test_rest_decreases_dread`
15. `test_talk_decreases_dread`
16. `test_status_shows_dread_meter`
17. `test_high_dread_whispers_appear`
18. `test_critical_dread_triggers_event`

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/cli_rpg/models/dread.py` | CREATE |
| `src/cli_rpg/models/character.py` | MODIFY |
| `src/cli_rpg/game_state.py` | MODIFY |
| `src/cli_rpg/main.py` | MODIFY |
| `src/cli_rpg/whisper.py` | MODIFY |
| `tests/test_dread.py` | CREATE |
| `tests/test_dread_integration.py` | CREATE |
