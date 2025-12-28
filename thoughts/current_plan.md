# Implementation Plan: Spreading Hazard System (Issue 25)

## Feature Spec

Implement spreading hazards (fire/flooding) that propagate through dungeon tiles over time, completing the Dynamic Interior Events feature (Issue 25).

### Behavior
- **Fire hazard**: Spawns at a random room, spreads to adjacent rooms over time, deals 4-8 damage per turn, can be mitigated by water-based items
- **Flooding hazard**: Spawns at a room, spreads to adjacent rooms, causes movement penalty (50% failure), increases tiredness +3 per turn
- Both spread 1 room per hour (integrated with `progress_interior_events`)
- Max spread radius of 3 rooms from origin
- Duration: 8-16 hours before dissipating
- Spawn chance: 5% on SubGrid entry (same as cave-ins)

### Data Model
Extend `InteriorEvent` with:
- `hazard_type: Optional[str]` - "fire" or "flooding"
- `spread_rooms: Optional[dict]` - Maps `(x,y,z)` -> turn added (for spread tracking)
- `max_spread_radius: int` - Maximum rooms from origin (default 3)

## Tests (TDD)

### File: `tests/test_spreading_hazard.py`

1. **Test spreading hazard model**: `InteriorEvent` has `hazard_type`, `spread_rooms`, `max_spread_radius` fields
2. **Test fire hazard spawning**: `check_for_spreading_hazard()` creates fire event with 5% chance
3. **Test flooding hazard spawning**: 50% fire, 50% flooding selection
4. **Test valid spawn categories**: Only dungeon/cave/ruins/temple (same as cave-ins)
5. **Test spread mechanics**: `spread_hazard()` adds adjacent rooms each hour
6. **Test spread limit**: Hazard stops spreading at `max_spread_radius`
7. **Test fire damage application**: `apply_spreading_hazard()` deals 4-8 damage for fire
8. **Test flooding effect**: Flooding causes 50% movement failure + 3 tiredness
9. **Test hazard expiry**: Hazard clears after `duration_hours`, removes all spread_rooms from affected locations
10. **Test location hazards updated**: Spread rooms have hazard added to `location.hazards` list
11. **Test serialization**: `spread_rooms` dict serializes/deserializes correctly
12. **Test integration with progress_interior_events**: Spreading occurs during time progression

## Implementation Steps

### Step 1: Extend InteriorEvent model
**File**: `src/cli_rpg/interior_events.py`

Add to `InteriorEvent` dataclass:
```python
hazard_type: Optional[str] = None  # "fire" or "flooding"
spread_rooms: Optional[dict] = None  # {(x,y,z): hour_added}
max_spread_radius: int = 3
```

Update `to_dict()` and `from_dict()` for new fields.

### Step 2: Add spreading hazard constants
**File**: `src/cli_rpg/interior_events.py`

```python
SPREADING_HAZARD_SPAWN_CHANCE = 0.05  # 5% on SubGrid entry
SPREADING_HAZARD_DURATION_RANGE = (8, 16)
SPREADING_HAZARD_CATEGORIES = CAVE_IN_CATEGORIES  # dungeon, cave, ruins, temple
FIRE_DAMAGE_RANGE = (4, 8)
FLOODING_TIREDNESS = 3
MAX_SPREAD_RADIUS = 3
```

### Step 3: Implement spawn function
**File**: `src/cli_rpg/interior_events.py`

```python
def check_for_spreading_hazard(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Check if a spreading hazard spawns on SubGrid entry."""
```

- 5% spawn chance
- Random room selection (not entry point)
- 50% fire, 50% flooding
- Create InteriorEvent with `hazard_type` and initial `spread_rooms`
- Add hazard to origin room's `location.hazards` list

### Step 4: Implement spread function
**File**: `src/cli_rpg/interior_events.py`

```python
def spread_hazard(
    sub_grid: "SubGrid",
    event: InteriorEvent,
    current_hour: int,
) -> List[str]:
    """Spread hazard to adjacent rooms."""
```

- Find frontier rooms (rooms at current max distance from origin)
- For each frontier room, check adjacent rooms within bounds
- Add new rooms to `spread_rooms` if within `max_spread_radius`
- Add hazard type to new room's `location.hazards` list
- Return messages about spread

### Step 5: Integrate with progress_interior_events
**File**: `src/cli_rpg/interior_events.py`

Update `progress_interior_events()` to:
- Call `spread_hazard()` for active spreading hazard events
- Handle expiry by removing hazard from all `spread_rooms` locations

### Step 6: Update hazards.py for spreading hazard effects
**File**: `src/cli_rpg/hazards.py`

Add to `HAZARD_TYPES`:
```python
"spreading_fire",
"spreading_flood",
```

Add to `CATEGORY_HAZARDS` (all enterable categories):
```python
# Note: These are added dynamically by spreading hazard system
```

Add effect functions:
```python
def apply_spreading_fire(character: "Character") -> str:
    """Apply spreading fire damage (4-8)."""

def apply_spreading_flood(character: "Character") -> Tuple[str, int]:
    """Apply spreading flood effects (50% movement fail, +3 tiredness)."""
```

Update `check_hazards_on_entry()` to handle new hazard types.

### Step 7: Integrate spawn on SubGrid entry
**File**: `src/cli_rpg/game_state.py`

In `enter()` method, after rival/ritual spawn checks:
```python
from cli_rpg.interior_events import check_for_spreading_hazard
hazard_spawn_message = check_for_spreading_hazard(self, self.current_sub_grid)
if hazard_spawn_message:
    message += f"\n{hazard_spawn_message}"
```

### Step 8: Update ISSUES.md
Mark "Spreading hazard" acceptance criteria as complete.
