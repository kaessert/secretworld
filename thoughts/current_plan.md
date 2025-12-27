# Issue 12: World State Evolution Implementation Plan

## Spec

**WorldStateManager** tracks persistent world changes from quest outcomes, combat victories, and player actions. Changes are stored as typed `WorldStateChange` records that can be queried by locations, NPCs, and event systems to create meaningful consequences.

### Core Data Model

```python
class WorldStateChangeType(Enum):
    LOCATION_DESTROYED = "location_destroyed"   # Location no longer exists
    LOCATION_TRANSFORMED = "location_transformed"  # Category/description changed
    NPC_KILLED = "npc_killed"                   # NPC removed from world
    NPC_MOVED = "npc_moved"                     # NPC relocated
    FACTION_ELIMINATED = "faction_eliminated"   # Faction no longer exists
    BOSS_DEFEATED = "boss_defeated"             # Boss permanently killed
    AREA_CLEARED = "area_cleared"               # All hostiles removed from location
    QUEST_WORLD_EFFECT = "quest_world_effect"   # Custom quest-triggered effect

@dataclass
class WorldStateChange:
    change_type: WorldStateChangeType
    target: str                    # Location/NPC/faction name
    description: str               # Human-readable summary
    timestamp: int                 # Game hour when change occurred
    caused_by: Optional[str]       # Quest name or action that caused it
    metadata: dict                 # Type-specific extra data
```

### WorldStateManager API

```python
class WorldStateManager:
    def __init__(self): ...

    # Recording changes
    def record_change(self, change: WorldStateChange) -> Optional[str]
    def record_location_transformed(self, name: str, new_category: str, desc: str, caused_by: str) -> Optional[str]
    def record_npc_killed(self, npc_name: str, location: str, caused_by: str) -> Optional[str]
    def record_boss_defeated(self, boss_name: str, location: str) -> Optional[str]
    def record_area_cleared(self, location: str, caused_by: str) -> Optional[str]

    # Querying changes
    def get_changes_for_location(self, location: str) -> list[WorldStateChange]
    def get_changes_by_type(self, change_type: WorldStateChangeType) -> list[WorldStateChange]
    def is_location_destroyed(self, location: str) -> bool
    def is_npc_killed(self, npc_name: str) -> bool
    def is_boss_defeated(self, location: str) -> bool
    def is_area_cleared(self, location: str) -> bool

    # Serialization
    def to_dict(self) -> dict
    @classmethod
    def from_dict(cls, data: dict) -> WorldStateManager
```

---

## Tests First (TDD)

### File: `tests/test_world_state.py`

1. **WorldStateChange dataclass**
   - Test creation with required fields
   - Test validation (non-empty target, valid type)
   - Test to_dict/from_dict serialization

2. **WorldStateManager recording**
   - Test record_change adds to history
   - Test record_location_transformed creates correct change
   - Test record_npc_killed creates correct change
   - Test record_boss_defeated creates correct change
   - Test record_area_cleared creates correct change

3. **WorldStateManager querying**
   - Test get_changes_for_location filters correctly
   - Test get_changes_by_type filters correctly
   - Test is_location_destroyed returns True/False correctly
   - Test is_npc_killed returns True/False correctly
   - Test is_boss_defeated returns True/False correctly
   - Test is_area_cleared returns True/False correctly

4. **Serialization**
   - Test WorldStateManager to_dict includes all changes
   - Test WorldStateManager from_dict restores all changes
   - Test backward compatibility (empty list if no world_state_manager in save)

---

## Implementation Steps

### Step 1: Create `tests/test_world_state.py`
Write all tests first per TDD approach.

### Step 2: Create `src/cli_rpg/models/world_state.py`

- Define `WorldStateChangeType` enum
- Define `WorldStateChange` dataclass with validation in `__post_init__`
- Define `WorldStateManager` class with:
  - `_changes: list[WorldStateChange]` storage
  - Recording methods (all return Optional[str] message)
  - Query methods (return bool or filtered lists)
  - to_dict/from_dict for serialization

### Step 3: Integrate into `game_state.py`

- Add `world_state_manager: WorldStateManager` attribute to `GameState.__init__`
- Initialize to `WorldStateManager()` in constructor
- Add serialization in `to_dict()`: `"world_state_manager": self.world_state_manager.to_dict()`
- Add deserialization in `from_dict()`: restore or create empty manager
- Update `mark_boss_defeated()` to call `world_state_manager.record_boss_defeated()`

---

## Files Changed

| File | Change |
|------|--------|
| `tests/test_world_state.py` | **NEW** - All tests for world state system |
| `src/cli_rpg/models/world_state.py` | **NEW** - WorldStateChangeType, WorldStateChange, WorldStateManager |
| `src/cli_rpg/game_state.py` | Add world_state_manager attribute, to_dict/from_dict updates, mark_boss_defeated hook |
