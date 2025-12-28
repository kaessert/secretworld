# Implement World State Changes from Quest Completion

## Overview
Connect quest completion to WorldStateManager to record permanent world changes (e.g., cleared dungeons, defeated bosses, transformed locations).

## Key Files
- `src/cli_rpg/models/quest.py` - Add `world_effects` field
- `src/cli_rpg/models/world_state.py` - Add `record_quest_world_effect()` helper
- `src/cli_rpg/main.py` - Apply world effects on quest completion (~line 1820)
- `tests/test_quest_world_effects.py` - New test file

## Implementation Steps

### 1. Add WorldEffect dataclass to quest model
In `src/cli_rpg/models/quest.py`:
```python
@dataclass
class WorldEffect:
    """Effect on world state when quest completes."""
    effect_type: str  # "area_cleared", "location_transformed", "npc_moved", etc.
    target: str       # Location/NPC name
    description: str  # Human-readable description
    metadata: dict = field(default_factory=dict)  # Extra data (new_category, etc.)
```

Add to Quest dataclass:
```python
world_effects: List["WorldEffect"] = field(default_factory=list)
```

Add serialization in `to_dict()` and `from_dict()`.

### 2. Add convenience method to WorldStateManager
In `src/cli_rpg/models/world_state.py`:
```python
def record_quest_world_effect(
    self,
    effect: "WorldEffect",  # From quest model
    quest_name: str,
    timestamp: int,
) -> Optional[str]:
    """Record a world effect from quest completion."""
```

### 3. Apply effects on quest completion
In `src/cli_rpg/main.py` after line 1820 (`matching_quest.status = QuestStatus.COMPLETED`):
```python
# Apply world effects from quest completion
for effect in matching_quest.world_effects:
    game_state.world_state_manager.record_quest_world_effect(
        effect=effect,
        quest_name=matching_quest.name,
        timestamp=game_state.game_time.total_hours,
    )
```

### 4. Write tests
New file `tests/test_quest_world_effects.py`:
- Test WorldEffect dataclass creation and validation
- Test serialization round-trip
- Test quest completion applies world effects
- Test world_state_manager records QUEST_WORLD_EFFECT changes
- Test is_area_cleared() after quest completion

## Verification
```bash
pytest tests/test_quest_world_effects.py -v
pytest tests/test_world_state.py -v
pytest tests/test_quest.py -v
```
