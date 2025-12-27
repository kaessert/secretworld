# Implementation Plan: Multi-Stage Quest Objectives

## Spec

Add sequential stages to quests, enabling multi-step narrative quests (e.g., "First find the witness, then investigate the crime scene, then confront the suspect"). Each stage has its own objective that must be completed before advancing.

**New Dataclass - QuestStage:**
```python
@dataclass
class QuestStage:
    """A single stage within a multi-stage quest."""
    name: str                           # Stage title (e.g., "Find the Witness")
    description: str                    # Stage-specific flavor text
    objective_type: ObjectiveType       # KILL, TALK, EXPLORE, etc.
    target: str                         # Target name
    target_count: int = 1               # How many to complete
    current_count: int = 0              # Progress tracking
```

**New Fields on Quest:**
- `stages: List[QuestStage] = []` - Ordered list of stages (empty = single-objective quest)
- `current_stage: int = 0` - Index of active stage (0-based)

**Behavior:**
- When `stages` is non-empty, quest progress uses stages instead of root objective
- Completing a stage auto-advances to next stage
- Quest becomes READY_TO_TURN_IN when final stage completes
- Root `objective_type/target/target_count` used for backward compat when `stages` is empty

## Tests (TDD)

Create `tests/test_quest_stages.py`:

### 1. QuestStage Model Tests
- `test_quest_stage_creation` - basic creation with required fields
- `test_quest_stage_defaults` - target_count=1, current_count=0
- `test_quest_stage_is_complete` - property returns True when current >= target
- `test_quest_stage_progress` - increments count, returns completion status
- `test_quest_stage_validation_empty_name` - rejects empty name
- `test_quest_stage_validation_empty_target` - rejects empty target
- `test_quest_stage_validation_negative_count` - rejects negative target_count

### 2. QuestStage Serialization Tests
- `test_quest_stage_to_dict` - serializes all fields
- `test_quest_stage_from_dict` - deserializes correctly
- `test_quest_stage_from_dict_defaults` - handles missing optional fields

### 3. Quest with Stages Tests
- `test_quest_stages_defaults_empty` - new quests have empty stages list
- `test_quest_current_stage_defaults_zero` - starts at stage 0
- `test_quest_without_stages_works_normally` - backward compat
- `test_quest_with_stages_uses_stage_objective` - active stage determines objective
- `test_quest_get_active_stage_returns_current` - helper method
- `test_quest_get_active_stage_returns_none_when_no_stages` - edge case

### 4. Stage Progression Tests
- `test_stage_completion_advances_to_next` - completing stage 0 moves to stage 1
- `test_final_stage_completion_marks_quest_ready` - last stage -> READY_TO_TURN_IN
- `test_middle_stage_completion_not_ready` - completing stage 1/3 keeps ACTIVE

### 5. Character Progress Recording Tests
- `test_record_kill_progresses_active_stage` - kill updates current stage
- `test_record_talk_progresses_active_stage` - talk updates current stage
- `test_record_explore_progresses_active_stage` - explore updates current stage
- `test_record_kill_ignores_wrong_stage_target` - different target no progress
- `test_stage_progress_message_includes_stage_name` - feedback mentions stage

### 6. Quest Serialization with Stages
- `test_quest_to_dict_includes_stages` - stages serialized
- `test_quest_to_dict_includes_current_stage` - current_stage serialized
- `test_quest_from_dict_restores_stages` - stages deserialized
- `test_quest_from_dict_handles_missing_stages` - backward compat

### 7. UI Display Tests
- `test_quest_details_shows_all_stages` - quest command shows stage list
- `test_quest_details_highlights_current_stage` - marks active stage
- `test_quest_journal_shows_stage_progress` - quests command shows "Stage 2/3"

## Implementation Steps

### Step 1: Add QuestStage dataclass
**File:** `src/cli_rpg/models/quest.py`

Add after QuestBranch class (around line 127):
```python
@dataclass
class QuestStage:
    """A single stage within a multi-stage quest.

    Attributes:
        name: Stage title (2-50 characters)
        description: Stage-specific flavor text
        objective_type: Type of objective (KILL, TALK, EXPLORE, etc.)
        target: The target name
        target_count: How many to complete (default 1)
        current_count: Current progress (default 0)
    """
    name: str
    description: str
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    current_count: int = 0

    def __post_init__(self) -> None:
        """Validate stage attributes."""
        if not self.name or not self.name.strip():
            raise ValueError("Stage name cannot be empty")
        if not self.target or not self.target.strip():
            raise ValueError("Stage target cannot be empty")
        if self.target_count < 1:
            raise ValueError("Stage target_count must be at least 1")
        if self.current_count < 0:
            raise ValueError("Stage current_count must be non-negative")
        self.name = self.name.strip()
        self.target = self.target.strip()

    @property
    def is_complete(self) -> bool:
        """Check if this stage's objective has been met."""
        return self.current_count >= self.target_count

    def progress(self) -> bool:
        """Increment current_count and check if stage is complete."""
        self.current_count += 1
        return self.is_complete

    def to_dict(self) -> dict:
        """Serialize the stage to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "objective_type": self.objective_type.value,
            "target": self.target,
            "target_count": self.target_count,
            "current_count": self.current_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestStage":
        """Create a stage from a dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            objective_type=ObjectiveType(data["objective_type"]),
            target=data["target"],
            target_count=data.get("target_count", 1),
            current_count=data.get("current_count", 0),
        )
```

### Step 2: Add stages fields to Quest
**File:** `src/cli_rpg/models/quest.py`

Add fields after `accepted_at` (around line 183):
```python
# Multi-stage quest fields
stages: List["QuestStage"] = field(default_factory=list)
current_stage: int = field(default=0)
```

Add helper methods after `get_time_remaining`:
```python
def get_active_stage(self) -> Optional["QuestStage"]:
    """Return the currently active stage, or None if no stages."""
    if not self.stages or self.current_stage >= len(self.stages):
        return None
    return self.stages[self.current_stage]

def advance_stage(self) -> bool:
    """Advance to next stage. Returns True if quest is now complete."""
    if not self.stages:
        return False
    self.current_stage += 1
    return self.current_stage >= len(self.stages)

def get_active_objective(self) -> Tuple[ObjectiveType, str, int, int]:
    """Return (objective_type, target, target_count, current_count) for active objective.

    Uses current stage if stages exist, otherwise uses root quest fields.
    """
    stage = self.get_active_stage()
    if stage:
        return (stage.objective_type, stage.target, stage.target_count, stage.current_count)
    return (self.objective_type, self.target, self.target_count, self.current_count)
```

### Step 3: Update Quest serialization
**File:** `src/cli_rpg/models/quest.py`

In `to_dict()` add after `accepted_at`:
```python
"stages": [s.to_dict() for s in self.stages],
"current_stage": self.current_stage,
```

In `from_dict()` add deserialization and constructor args:
```python
# Deserialize stages
stages_data = data.get("stages", [])
stages = [QuestStage.from_dict(s) for s in stages_data]
```
Add to constructor:
```python
stages=stages,
current_stage=data.get("current_stage", 0),
```

### Step 4: Update Character.record_* methods for stages
**File:** `src/cli_rpg/models/character.py`

Add helper method `_check_stage_progress`:
```python
def _check_stage_progress(
    self, quest: "Quest", objective_type: "ObjectiveType", target_name: str
) -> Optional[str]:
    """Check and progress active stage for staged quests.

    Returns stage name if stage completed, None otherwise.
    """
    from cli_rpg.models.quest import QuestStatus

    stage = quest.get_active_stage()
    if not stage:
        return None

    if stage.objective_type != objective_type:
        return None
    if stage.target.lower() != target_name.lower():
        return None

    stage_complete = stage.progress()
    if not stage_complete:
        return None

    stage_name = stage.name
    quest_complete = quest.advance_stage()
    if quest_complete:
        quest.status = QuestStatus.READY_TO_TURN_IN

    return stage_name
```

Modify `record_kill` to check stages first (before branches):
```python
# Check staged quests first
if quest.stages:
    stage_name = self._check_stage_progress(quest, ObjectiveType.KILL, enemy_name)
    if stage_name:
        if quest.status == QuestStatus.READY_TO_TURN_IN:
            messages.append(f"Quest '{quest.name}' complete! Return to turn in.")
        else:
            messages.append(f"Stage complete: {stage_name}")
            next_stage = quest.get_active_stage()
            if next_stage:
                messages.append(f"Next: {next_stage.name}")
    continue
```

Apply same pattern to `record_talk`, `record_explore`, `record_collection`, `record_drop`, `record_use`.

### Step 5: Update quest UI display
**File:** `src/cli_rpg/main.py`

In `quest` command (around line 1886), after showing basic progress, add stage display:
```python
# Show stages if multi-stage quest
if quest.stages:
    lines.append("")
    lines.append("Stages:")
    for i, stage in enumerate(quest.stages):
        if i < quest.current_stage:
            status = "✓"  # Completed
        elif i == quest.current_stage:
            status = "→"  # Current
        else:
            status = "○"  # Pending
        progress = f"[{stage.current_count}/{stage.target_count}]" if i == quest.current_stage else ""
        lines.append(f"  {status} {stage.name} {progress}")
        if i == quest.current_stage and stage.description:
            lines.append(f"      {stage.description}")
```

In `quests` journal (around line 1838), show stage progress for staged quests:
```python
if quest.stages:
    stage_info = f" (Stage {quest.current_stage + 1}/{len(quest.stages)})"
else:
    stage_info = ""
lines.append(f"  {diff_icon} {quest.name} [{quest.current_count}/{quest.target_count}]{stage_info}{time_info}")
```

### Step 6: Update quest acceptance to clone stages
**File:** `src/cli_rpg/main.py`

In accept command (around line 1694), when creating new_quest, add:
```python
stages=[
    QuestStage(
        name=s.name,
        description=s.description,
        objective_type=s.objective_type,
        target=s.target,
        target_count=s.target_count,
        current_count=0,  # Reset progress
    ) for s in matching_quest.stages
],
current_stage=0,
```

Add import at top of main.py:
```python
from cli_rpg.models.quest import QuestStage
```

## Files to Modify

1. `src/cli_rpg/models/quest.py` - Add QuestStage, add stages/current_stage to Quest, methods, serialization
2. `src/cli_rpg/models/character.py` - Add _check_stage_progress, update all record_* methods
3. `src/cli_rpg/main.py` - Display stages in quest/quests commands, clone stages on accept
4. `tests/test_quest_stages.py` - New test file with all tests above
