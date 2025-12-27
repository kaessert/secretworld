# Implementation Plan: Issue 25 - Rival Adventurers

## Spec

**Feature**: Rival adventurer parties that race the player to boss rooms and treasure chests within SubGrid interiors.

**Behavior**:
1. On SubGrid entry, 15% chance to spawn a rival adventurer party (1-3 NPCs)
2. Rivals have a **target** (boss room or treasure room) and a **progress counter** (turns until arrival)
3. Each player move inside the SubGrid advances rival progress by 1 turn
4. If rivals reach target before player:
   - Boss room: Boss is already defeated, rival party is present (taunts player)
   - Treasure room: Chest is already opened/empty, rival party is present
5. If player reaches target first: normal gameplay (rivals never appear)
6. Rivals can be fought if encountered (combat encounter), defeating them stops the race
7. Visual warning messages show rival progress ("You hear voices echoing ahead...")

**Constants**:
- `RIVAL_SPAWN_CHANCE = 0.15` (15% on SubGrid entry)
- `RIVAL_PROGRESS_PER_TURN = 1` (rivals advance 1 step per player move)
- `RIVAL_PARTY_SIZE_RANGE = (1, 3)` (1-3 rival adventurers)

## Tests (TDD)

Create `tests/test_rival_adventurers.py`:

1. **TestRivalAdventurerEvent** (model tests):
   - `test_event_creation`: RivalEvent with event_id, party, target_room, progress, arrival_turns
   - `test_event_serialization`: to_dict/from_dict including NPC party serialization
   - `test_arrival_check`: is_arrived() returns True when progress >= arrival_turns

2. **TestRivalSpawning**:
   - `test_spawn_chance_15_percent`: Only spawns when random < 0.15
   - `test_spawn_only_in_valid_categories`: Spawn in dungeon/cave/ruins/temple only
   - `test_spawn_creates_party`: Spawns 1-3 rival NPCs with combat stats
   - `test_spawn_selects_target`: Target is boss_room or treasure room (preferring boss)
   - `test_no_spawn_if_no_targets`: No rivals if no boss/treasure rooms exist

3. **TestRivalProgress**:
   - `test_progress_on_player_move`: progress_rival_party() increments progress
   - `test_warning_messages_by_progress`: Different messages at 25%, 50%, 75%
   - `test_rivals_arrive_at_boss`: When arrived, boss_defeated=True, rivals present at location
   - `test_rivals_arrive_at_treasure`: When arrived, treasure opened=True, rivals present

4. **TestRivalCombat**:
   - `test_encounter_rivals_in_room`: Player entering room with rivals triggers combat
   - `test_defeating_rivals_stops_race`: On combat victory, rival event marked inactive

5. **TestRivalIntegration**:
   - `test_subgrid_serialization_with_rivals`: SubGrid saves/loads rival events
   - `test_backward_compatible_load`: Old SubGrid without rivals loads with empty list

## Implementation Steps

### Step 1: Extend InteriorEvent model
**File**: `src/cli_rpg/interior_events.py`

Add new event type and helper data structure:
```python
# Constants
RIVAL_SPAWN_CHANCE = 0.15
RIVAL_PARTY_SIZE_RANGE = (1, 3)
RIVAL_CATEGORIES = CAVE_IN_CATEGORIES  # Same: dungeon, cave, ruins, temple

# InteriorEvent already supports event_type - add "rival_adventurers"
# Add new optional fields to InteriorEvent:
#   - rival_party: Optional[List[dict]] = None  # Serialized NPC data
#   - target_room: Optional[str] = None  # Name of target room
#   - progress: int = 0  # Current progress toward target
#   - arrival_turns: int = 0  # Turns until rivals arrive
```

### Step 2: Add rival spawn function
**File**: `src/cli_rpg/interior_events.py`

```python
def check_for_rival_spawn(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Check if rival adventurers should spawn on SubGrid entry.

    Only called once when player first enters a SubGrid.
    Selects target (boss room preferred, then treasure room).
    Calculates arrival_turns based on distance from entry.
    """
```

### Step 3: Add rival progress function
**File**: `src/cli_rpg/interior_events.py`

```python
def progress_rival_party(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Advance rival party progress by 1 turn.

    Called after each player move in SubGrid.
    Returns warning message based on progress percentage.
    If rivals arrive, updates target room (defeats boss/opens treasure)
    and places rival party NPCs at target location.
    """

def get_active_rival_event(sub_grid: "SubGrid") -> Optional[InteriorEvent]:
    """Get the active rival adventurer event, if any."""
```

### Step 4: Create rival NPC templates
**File**: `src/cli_rpg/interior_events.py`

```python
RIVAL_PARTY_NAMES = [
    "The Iron Seekers", "Shadow Company", "Fortune's Edge",
    "The Blade Collective", "Crimson Oath", "The Wanderers"
]

RIVAL_ADVENTURER_TEMPLATES = [
    {"name": "Rival Warrior", "hp": 30, "attack": 8, "defense": 4},
    {"name": "Rival Mage", "hp": 20, "attack": 10, "defense": 2},
    {"name": "Rival Rogue", "hp": 25, "attack": 9, "defense": 3},
]
```

### Step 5: Integrate into GameState
**File**: `src/cli_rpg/game_state.py`

In `enter()` method (after SubGrid generation):
```python
# Check for rival spawn (15% chance, once per entry)
from cli_rpg.interior_events import check_for_rival_spawn
rival_message = check_for_rival_spawn(self, current.sub_grid)
if rival_message:
    message += f"\n{rival_message}"
```

In `_move_in_sub_grid()` method (after hazards check):
```python
# Progress rival party and check for arrival
from cli_rpg.interior_events import progress_rival_party
rival_message = progress_rival_party(self, self.current_sub_grid)
if rival_message:
    message += f"\n{rival_message}"

# Check for rival encounter at destination
from cli_rpg.interior_events import get_rival_encounter_at_location
rival_encounter = get_rival_encounter_at_location(self.current_sub_grid, destination)
if rival_encounter:
    # Start combat with rival party
    self.current_combat = CombatEncounter(...)
    return (True, f"...{combat_message}")
```

### Step 6: Update SubGrid serialization
**File**: `src/cli_rpg/world_grid.py`

Already supports interior_events list - no changes needed (InteriorEvent.to_dict/from_dict handles new fields).

## File Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/interior_events.py` | Add rival constants, templates, spawn/progress functions |
| `src/cli_rpg/game_state.py` | Integrate rival spawn in enter(), progress in _move_in_sub_grid() |
| `tests/test_rival_adventurers.py` | New test file with ~20 tests |
