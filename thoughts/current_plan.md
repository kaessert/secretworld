# Seasonal Events and Festivals Implementation Plan

## Spec

Add a **seasonal calendar system** that tracks the current season and triggers **festivals** - special world events that occur during specific times of year. Festivals provide gameplay bonuses, special NPCs, and atmospheric content.

### Season System
- 4 seasons: **Spring, Summer, Autumn, Winter** (each 30 in-game days = 720 hours)
- Track current day (1-120, wrapping) derived from total elapsed hours
- Display in status command: "Day 45 (Summer)"
- Season affects dread modifiers: Winter +2, Autumn +1, Spring -1, Summer 0

### Festival Events
- Festivals are special WorldEvents with `event_type="festival"`
- Triggered automatically when entering appropriate season/day range
- Duration: 24-72 hours (persist across saves)
- Each festival has: name, description, season, day range, gameplay effects

**Initial Festivals (4 total)**:
1. **Spring Festival** (Spring, days 10-12): Shop prices -20%, dread reduction doubled
2. **Midsummer Night** (Summer, days 15-16): Night whispers have +50% chance, special mysterious encounters
3. **Harvest Moon** (Autumn, days 20-22): Merchants have +50% gold, XP gain +25%
4. **Winter Solstice** (Winter, days 15-17): Dread immunity in towns, special "warm hearth" rest bonus (+25 HP)

### Integration Points
- Festival check on movement (like world events)
- Festival modifiers applied in: shop system, combat XP, dread system, rest command
- Festivals shown in `events` command with [FESTIVAL] tag
- Status command shows season alongside time

---

## Tests (TDD) - `tests/test_seasons.py`

### Season Model Tests
1. `test_season_defaults_to_spring_day_1` - New GameTime starts at Spring Day 1
2. `test_get_season_spring_days_1_30` - Days 1-30 return "spring"
3. `test_get_season_summer_days_31_60` - Days 31-60 return "summer"
4. `test_get_season_autumn_days_61_90` - Days 61-90 return "autumn"
5. `test_get_season_winter_days_91_120` - Days 91-120 return "winter"
6. `test_day_wraps_after_120` - Day 121 becomes Day 1
7. `test_get_season_display` - Returns "Day 45 (Summer)" format
8. `test_season_dread_modifiers` - Winter +2, Autumn +1, Spring -1, Summer 0
9. `test_season_serialization` - to_dict/from_dict preserves total_hours

### Festival Spawn Tests
10. `test_spring_festival_spawns_on_day_10` - Festival triggers at correct day
11. `test_festival_not_duplicate_if_active` - Same festival doesn't spawn twice
12. `test_festival_has_correct_duration` - 24-72 hour duration
13. `test_festival_appears_in_events_list` - Shows with [FESTIVAL] tag

### Festival Effect Tests
14. `test_spring_festival_reduces_shop_prices` - 20% discount applied
15. `test_harvest_moon_increases_xp` - 25% XP bonus in combat
16. `test_winter_solstice_rest_bonus` - Extra 25 HP on rest in town
17. `test_midsummer_night_whisper_chance` - 50% increased whisper rate

### Persistence Tests
18. `test_total_hours_persists_on_save_load` - Season state survives save/load
19. `test_active_festival_persists_on_save_load` - Festival events survive save/load

---

## Implementation Steps

### Step 1: Extend GameTime Model
**File**: `src/cli_rpg/models/game_time.py`

Add fields and methods:
```python
total_hours: int = 0  # Track total elapsed time

def advance(self, hours: int) -> None:
    self.hour = (self.hour + hours) % 24
    self.total_hours += hours  # NEW: accumulate total

def get_day(self) -> int:
    """Get current day (1-120, wrapping)."""
    return (self.total_hours // 24 % 120) + 1

def get_season(self) -> str:
    """Get current season based on day."""
    day = self.get_day()
    if day <= 30: return "spring"
    elif day <= 60: return "summer"
    elif day <= 90: return "autumn"
    else: return "winter"

def get_season_display(self) -> str:
    """Get 'Day X (Season)' display string."""
    return f"Day {self.get_day()} ({self.get_season().capitalize()})"

SEASON_DREAD_MODIFIERS = {"spring": -1, "summer": 0, "autumn": 1, "winter": 2}

def get_season_dread_modifier(self) -> int:
    return SEASON_DREAD_MODIFIERS.get(self.get_season(), 0)

# Update to_dict/from_dict to include total_hours
```

### Step 2: Create Festival Templates
**File**: `src/cli_rpg/seasons.py` (new)

```python
FESTIVAL_TEMPLATES = {
    "spring_festival": {
        "name": "Spring Festival",
        "description": "The town celebrates the return of warmth...",
        "season": "spring",
        "day_start": 10,
        "day_end": 12,
        "duration_hours": 48,
        "effects": {"shop_discount": 0.20, "dread_reduction_multiplier": 2.0}
    },
    "midsummer_night": {...},
    "harvest_moon": {...},
    "winter_solstice": {...}
}

def check_for_festival(game_state) -> Optional[str]:
    """Check if a festival should spawn based on current day/season."""

def get_active_festival(game_state) -> Optional[WorldEvent]:
    """Get currently active festival event, if any."""

def apply_festival_effect(game_state, effect_type: str) -> float:
    """Get festival modifier for given effect type (returns 1.0 if no festival)."""
```

### Step 3: Integrate Festival Checks into GameState
**File**: `src/cli_rpg/game_state.py`

1. Import `check_for_festival` from seasons module
2. In `move()` method, after `check_for_new_event()`:
   ```python
   festival_message = check_for_festival(self)
   if festival_message:
       message += f"\n{festival_message}"
   ```
3. In `_update_dread_on_move()`: Add season dread modifier

### Step 4: Apply Festival Effects to Systems

**Shop System** (`src/cli_rpg/models/shop.py`):
- In `buy()` method, check for `shop_discount` effect

**Combat** (`src/cli_rpg/combat.py`):
- In XP calculation, check for `xp_multiplier` effect

**Rest Command** (in main.py or game_state.py):
- Check for `rest_bonus` effect when calculating HP restored

**Whisper System** (`src/cli_rpg/whisper.py`):
- Check for `whisper_chance_multiplier` effect

### Step 5: Update Status Display
**File**: `src/cli_rpg/main.py` (status command handler)

Add season display to status output:
```
Time: 14:00 (Day) | Day 45 (Summer)
Weather: Clear ☀
```

### Step 6: Update Events Display
**File**: `src/cli_rpg/world_events.py`

In `get_active_events_display()`:
- Add `[FESTIVAL]` tag for festival events with distinct color (gold)

---

## File Changes Summary

| File | Change Type |
|------|-------------|
| `src/cli_rpg/models/game_time.py` | Modify - add total_hours, season methods |
| `src/cli_rpg/seasons.py` | **New** - festival templates and logic |
| `src/cli_rpg/game_state.py` | Modify - integrate festival checks |
| `src/cli_rpg/world_events.py` | Modify - festival display in events |
| `src/cli_rpg/models/shop.py` | Modify - festival discount |
| `src/cli_rpg/combat.py` | Modify - festival XP bonus |
| `src/cli_rpg/whisper.py` | Modify - festival whisper chance |
| `src/cli_rpg/main.py` | Modify - status display, rest bonus |
| `tests/test_seasons.py` | **New** - all season/festival tests |
