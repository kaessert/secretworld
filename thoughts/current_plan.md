# Issue 26: Environmental Hazards Implementation Plan

## Overview
Add non-combat environmental challenges to dungeon interiors: poison gas, darkness, unstable ground, extreme temperatures, and flooded rooms. Builds on existing SubGrid and interior events infrastructure.

## Spec

### Hazard Types
1. **Poison Gas** - DOT damage per move, mitigated by antidotes (existing `is_cure` item property)
2. **Darkness** - Reduces perception by 50%, requires active light (existing `light_remaining`)
3. **Unstable Ground** - DEX check or take fall damage (5-15 HP)
4. **Extreme Cold/Heat** - +5 tiredness per move in hazard room
5. **Flooded Rooms** - 50% chance to fail movement (slowed)

### Location Integration
- Add `hazards: List[str]` field to Location model (e.g., `["poison_gas", "darkness"]`)
- Hazards assigned during SubGrid room generation in `ai_world.py`
- Category-specific hazard pools (caves get darkness/flooding, temples get poison gas)

### Mitigation
- **Ranger**: Ignores unstable_ground and extreme_cold/heat (wilderness affinity)
- **Antidote**: Clears poison_gas effect (extend `is_cure` to handle hazard effects)
- **Torch/Light**: Negates darkness penalty while active
- **No mitigation for flooded**: Just bad luck, keep trying

## Files to Create
- `src/cli_rpg/hazards.py` - Hazard definitions, spawn logic, effect processing

## Files to Modify

### 1. `src/cli_rpg/models/location.py`
- Add `hazards: List[str] = field(default_factory=list)` field
- Add serialization in `to_dict()` / `from_dict()`

### 2. `src/cli_rpg/hazards.py` (new)
```python
# Constants
HAZARD_TYPES = {"poison_gas", "darkness", "unstable_ground", "extreme_cold", "extreme_heat", "flooded"}
CATEGORY_HAZARDS = {
    "dungeon": ["poison_gas", "darkness", "unstable_ground"],
    "cave": ["darkness", "flooded", "extreme_cold"],
    "ruins": ["unstable_ground", "darkness"],
    "temple": ["poison_gas", "darkness"],
}

# Functions
- check_hazards_on_entry(game_state, location) -> List[str]: Process hazards, return messages
- apply_poison_gas(character) -> str: Apply DOT if no antidote active
- check_darkness_penalty(character) -> float: Return perception multiplier (0.5 or 1.0)
- check_unstable_ground(character) -> Tuple[bool, int]: DEX check, return (fell, damage)
- apply_temperature_effect(character, hazard_type) -> str: Add tiredness
- check_flooded_movement(character) -> bool: Return True if movement fails
- can_mitigate_hazard(character, hazard_type) -> bool: Check Ranger class or items
```

### 3. `src/cli_rpg/game_state.py`
- In `_move_in_sub_grid()`: Call `check_hazards_on_entry()` after successful move
- Append hazard messages to move result

### 4. `src/cli_rpg/ai_world.py`
- In SubGrid room generation: Assign hazards based on category and distance from entry
- Deeper rooms have higher hazard chance (similar to puzzle scaling)

## Tests to Create
- `tests/test_hazards.py`:
  - Test each hazard type effect
  - Test Ranger mitigation for unstable_ground/temperature
  - Test light source negates darkness
  - Test antidote clears poison (via is_cure)
  - Test hazard assignment by category
  - Test serialization of hazards in Location

## Implementation Order
1. Add `hazards` field to Location model with serialization
2. Create `hazards.py` with hazard type definitions and effect functions
3. Integrate hazard checks into `_move_in_sub_grid()`
4. Add hazard generation in `ai_world.py` SubGrid creation
5. Write tests for all hazard types and mitigations
