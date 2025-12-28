# Implementation Plan: Ritual in Progress Event (Issue 25)

## Spec

**Goal**: Add a "Ritual in progress" interior event that creates a time-limited boss encounter in dungeons.

**Behavior**:
1. On SubGrid entry (15% chance, same as rivals), spawn a ritual event at a room away from entry
2. Ritual countdown starts at 8-12 turns
3. Each player move decrements the counter with warning messages at 75%, 50%, 25%
4. If countdown reaches 0: Ritual completes, empowered boss spawns at ritual location
5. If player reaches ritual room before countdown: Standard boss fight, ritual interrupted
6. Empowered boss has 1.5x stats compared to normal boss

**Integration**:
- Uses existing `InteriorEvent` model with new fields
- Follows same patterns as rival adventurers
- Triggers boss combat via existing `spawn_boss()` function

---

## Tests First (TDD)

### File: `tests/test_ritual_events.py`

```python
"""Tests for ritual in progress interior event (Issue 25)."""

# Test InteriorEvent model with ritual fields
- test_event_creation_with_ritual_fields: ritual_room, ritual_countdown, ritual_completed
- test_event_serialization_with_ritual_fields: to_dict/from_dict

# Test ritual spawn mechanics
- test_ritual_spawn_chance_15_percent: RITUAL_SPAWN_CHANCE == 0.15
- test_ritual_spawn_only_in_valid_categories: RITUAL_CATEGORIES matches CAVE_IN_CATEGORIES
- test_ritual_countdown_range: RITUAL_COUNTDOWN_RANGE == (8, 12)
- test_check_for_ritual_spawn_creates_event: creates event with correct fields

# Test ritual progression
- test_progress_ritual_decrements_countdown: countdown -= 1 per turn
- test_progress_ritual_warning_at_75_percent: message at 75%
- test_progress_ritual_warning_at_50_percent: message at 50%
- test_progress_ritual_warning_at_25_percent: message at 25%
- test_ritual_completes_when_countdown_zero: ritual_completed = True

# Test ritual combat triggers
- test_get_ritual_encounter_before_completion: returns event, standard boss
- test_get_ritual_encounter_after_completion: returns event, empowered_boss = True
- test_spawn_ritual_boss_empowered: 1.5x stats when empowered
- test_spawn_ritual_boss_standard: normal stats when interrupted
```

---

## Implementation Steps

### Step 1: Add ritual fields to InteriorEvent model
**File**: `src/cli_rpg/interior_events.py`

Add to `InteriorEvent` dataclass:
```python
# Ritual event fields
ritual_room: Optional[str] = None
ritual_countdown: int = 0
ritual_completed: bool = False
```

Update `to_dict()` to serialize new fields.
Update `from_dict()` to deserialize with backward-compatible defaults.

### Step 2: Add ritual constants
**File**: `src/cli_rpg/interior_events.py`

```python
# Ritual event constants
RITUAL_SPAWN_CHANCE = 0.15  # Same as rivals
RITUAL_COUNTDOWN_RANGE = (8, 12)
RITUAL_CATEGORIES = CAVE_IN_CATEGORIES  # dungeon, cave, ruins, temple
RITUAL_WARNING_MESSAGES = {
    75: "An ominous chanting echoes through the corridors...",
    50: "Dark energy pulses through the walls! The ritual grows stronger!",
    25: "Reality flickers - the ritual nears completion!",
}
RITUAL_COMPLETE_MESSAGE = "The ritual is complete! An empowered being has been summoned!"
```

### Step 3: Add check_for_ritual_spawn function
**File**: `src/cli_rpg/interior_events.py`

```python
def check_for_ritual_spawn(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Check if a ritual should spawn on SubGrid entry.

    Spawns a ritual event at a room distant from entry.
    Prefers non-boss rooms to avoid conflict with existing boss.
    """
```

- Find suitable ritual room (not entry, not boss room, not treasure room)
- Calculate countdown based on distance from entry
- Create InteriorEvent with event_type="ritual"

### Step 4: Add progress_ritual function
**File**: `src/cli_rpg/interior_events.py`

```python
def progress_ritual(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Advance ritual countdown by 1 turn. Returns warning/completion message."""
```

- Decrement countdown
- Check for warning thresholds (75%, 50%, 25%)
- If countdown reaches 0, set ritual_completed = True

### Step 5: Add ritual encounter functions
**File**: `src/cli_rpg/interior_events.py`

```python
def get_active_ritual_event(sub_grid: "SubGrid") -> Optional[InteriorEvent]:
    """Get the active ritual event, if any."""

def get_ritual_encounter_at_location(
    sub_grid: "SubGrid",
    location: "Location",
) -> Optional[Tuple[InteriorEvent, bool]]:
    """Check if player entered the ritual room.
    Returns (event, is_empowered) if ritual room, None otherwise."""
```

### Step 6: Add ritual boss spawning
**File**: `src/cli_rpg/combat.py`

Add to `spawn_boss()` function:
```python
def spawn_boss(
    location_name: str,
    level: int,
    location_category: Optional[str] = None,
    boss_type: Optional[str] = None,
    empowered: bool = False,  # NEW: 1.5x stats if True
) -> Enemy:
```

When empowered=True, apply 1.5x multiplier to base stats.

### Step 7: Integrate into game_state.py
**File**: `src/cli_rpg/game_state.py`

In `enter()` method, after rival spawn check:
```python
from cli_rpg.interior_events import check_for_ritual_spawn
ritual_message = check_for_ritual_spawn(self, sub_grid)
if ritual_message:
    messages.append(ritual_message)
```

In `_move_in_sub_grid()` method, after rival progress:
```python
from cli_rpg.interior_events import progress_ritual, get_ritual_encounter_at_location
ritual_message = progress_ritual(self, self.current_sub_grid)
if ritual_message:
    message += f"\n{ritual_message}"

# Check for ritual encounter
ritual_result = get_ritual_encounter_at_location(self.current_sub_grid, destination)
if ritual_result:
    ritual_event, is_empowered = ritual_result
    boss = spawn_boss(
        destination.name,
        level=self.current_character.level,
        location_category=destination.category,
        boss_type="ritual_summoned",
        empowered=is_empowered,
    )
    # Start combat with ritual boss
```

### Step 8: Add ritual_summoned boss template
**File**: `src/cli_rpg/combat.py`

Add to `spawn_boss()`:
```python
if boss_type == "ritual_summoned":
    # Dark entity summoned by ritual
    base_health = (40 + level * 25) * 2
    base_attack = (5 + level * 3) * 2
    base_defense = (2 + level * 2) * 2

    if empowered:
        base_health = int(base_health * 1.5)
        base_attack = int(base_attack * 1.5)
        base_defense = int(base_defense * 1.5)

    # Special attacks for ritual summoned entity
    ...
```

### Step 9: Update ISSUES.md
**File**: `ISSUES.md`

Mark "Ritual in progress" as complete under Issue 25.

---

## Files Modified

1. `src/cli_rpg/interior_events.py` - New ritual event logic
2. `src/cli_rpg/combat.py` - empowered parameter and ritual_summoned boss
3. `src/cli_rpg/game_state.py` - Integration with enter() and _move_in_sub_grid()
4. `tests/test_ritual_events.py` - New test file (20+ tests)
5. `ISSUES.md` - Update Issue 25 status
