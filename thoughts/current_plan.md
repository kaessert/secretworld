# Plan: Phase 1 - Save/Load Infrastructure for Automated Playtesting

**Task**: Create agent checkpoint system for save/restore capabilities during simulations.

## Spec

The checkpoint system allows:
1. Saving agent state + game state at key points (quest accept, dungeon entry, boss fights)
2. Resuming interrupted sessions from crash recovery
3. Branching exploration from any checkpoint

## Implementation Steps

### Step 1: Create `scripts/agent_checkpoint.py` with AgentCheckpoint dataclass

```python
@dataclass
class AgentCheckpoint:
    """Complete agent state for persistence."""
    current_goal: str                    # AgentGoal enum value
    visited_coordinates: list[tuple]     # Exploration history
    current_coords: tuple[int, int]      # Position estimate
    direction_history: list[str]
    talked_this_location: list[str]
    sub_location_moves: int
    stats: dict                          # SessionStats.to_dict()
    checkpoint_type: str                 # auto, quest, boss, dungeon, branch
    game_save_path: str                  # Link to game save file
    seed: int
    timestamp: str
    command_index: int

    def to_dict() -> dict
    def from_dict(data: dict) -> AgentCheckpoint
```

### Step 2: Create `scripts/checkpoint_triggers.py` with CheckpointTrigger enum

```python
class CheckpointTrigger(Enum):
    QUEST_ACCEPT = auto()
    QUEST_COMPLETE = auto()
    DUNGEON_ENTRY = auto()
    DUNGEON_EXIT = auto()
    BOSS_ENCOUNTER = auto()
    BOSS_DEFEAT = auto()
    DEATH = auto()
    LEVEL_UP = auto()
    INTERVAL = auto()       # Every 50 commands
    CRASH_RECOVERY = auto()

def detect_trigger(prev_state, curr_state, command_count) -> Optional[CheckpointTrigger]
```

### Step 3: Create `scripts/agent_persistence.py` with SessionManager

```python
class SessionManager:
    """Manages checkpoint directories and files."""

    def __init__(self, base_dir: str = "simulation_saves")
    def create_session(self, seed: int) -> str  # Returns session_id
    def save_checkpoint(self, checkpoint: AgentCheckpoint, trigger: CheckpointTrigger)
    def load_checkpoint(self, checkpoint_id: str) -> AgentCheckpoint
    def list_checkpoints(self, session_id: str) -> list[dict]
    def get_crash_recovery(self) -> Optional[AgentCheckpoint]
    def update_crash_recovery(self, checkpoint: AgentCheckpoint)
```

### Step 4: Add checkpoint methods to Agent class in `scripts/ai_agent.py`

```python
# In Agent class:
def to_checkpoint_dict(self) -> dict
def restore_from_checkpoint(self, data: dict) -> None
```

### Step 5: Integrate checkpointing into GameSession

```python
# In GameSession:
def _create_checkpoint(self, trigger: CheckpointTrigger) -> None
def _check_triggers(self, prev_state: AgentState) -> Optional[CheckpointTrigger]

@classmethod
def from_checkpoint(cls, checkpoint_id: str) -> "GameSession"
```

### Step 6: Add CLI flags to `scripts/run_simulation.py`

- `--recover` - Resume from last crash recovery
- `--from-checkpoint=ID` - Resume from specific checkpoint
- `--no-checkpoints` - Disable automatic checkpointing

## Test Plan

Create `tests/test_agent_checkpoint.py`:
1. Test AgentCheckpoint serialization roundtrip
2. Test CheckpointTrigger detection for each trigger type
3. Test SessionManager save/load/list operations
4. Test Agent.to_checkpoint_dict/restore_from_checkpoint
5. Test GameSession.from_checkpoint recovery

## Files to Create/Modify

| File | Action |
|------|--------|
| `scripts/agent_checkpoint.py` | CREATE |
| `scripts/checkpoint_triggers.py` | CREATE |
| `scripts/agent_persistence.py` | CREATE |
| `scripts/ai_agent.py` | MODIFY - add checkpoint methods |
| `scripts/run_simulation.py` | MODIFY - add CLI flags |
| `tests/test_agent_checkpoint.py` | CREATE |
