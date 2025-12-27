# Implementation Plan: Branching Quest Objectives

## Summary
Add alternative completion paths to quests, allowing moral complexity and player choice. Example: "Stop the Bandit" can be completed by killing, convincing to leave, or helping him raid.

## Spec

### New Model: QuestBranch
```python
@dataclass
class QuestBranch:
    """Alternative completion path for a quest."""
    id: str  # Unique identifier (e.g., "kill", "persuade", "help")
    name: str  # Display name (e.g., "Eliminate the Threat")
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    current_count: int = 0  # Track progress per branch
    description: str = ""  # Optional flavor text
    # Consequences
    faction_effects: Dict[str, int] = field(default_factory=dict)  # {"Militia": 10, "Outlaws": -5}
    gold_modifier: float = 1.0  # Multiplier on base reward
    xp_modifier: float = 1.0
```

### Quest Model Changes
```python
@dataclass
class Quest:
    # Existing fields...

    # NEW: Branching support
    alternative_branches: List[QuestBranch] = field(default_factory=list)
    completed_branch_id: Optional[str] = None  # Which path was chosen
```

### Completion Logic
- When ANY branch reaches its target count → quest becomes READY_TO_TURN_IN
- On turn-in, apply that branch's faction effects and reward modifiers
- Store `completed_branch_id` for quest memory/NPC reactions

## Tests (TDD)

### 1. tests/test_quest_branching.py
- `test_quest_with_no_branches_works_normally` - Backward compatibility
- `test_quest_branch_serialization_round_trip` - to_dict/from_dict
- `test_quest_branch_progress_independent` - Each branch tracks separately
- `test_quest_ready_when_any_branch_complete` - First branch to finish wins
- `test_completed_branch_id_set_on_completion` - Track which path taken
- `test_branch_faction_effects_applied` - Rewards differ by path
- `test_branch_reward_modifiers_applied` - Gold/XP scale by path
- `test_quest_display_shows_all_branches` - UI shows options

### 2. tests/test_quest_branch_validation.py
- `test_branch_target_validation_kill` - KILL branches validate enemy
- `test_branch_target_validation_talk` - TALK branches validate NPC
- `test_branch_requires_id` - Branch must have unique id
- `test_branch_requires_name` - Branch must have display name

## Implementation Steps

### Step 1: Create QuestBranch dataclass
**File**: `src/cli_rpg/models/quest.py`
- Add `QuestBranch` dataclass after `ObjectiveType` enum
- Include `to_dict()` and `from_dict()` methods
- Add validation in `__post_init__`

### Step 2: Add branching fields to Quest
**File**: `src/cli_rpg/models/quest.py`
- Add `alternative_branches: List[QuestBranch]` field
- Add `completed_branch_id: Optional[str]` field
- Update `to_dict()` to serialize branches
- Update `from_dict()` to deserialize branches

### Step 3: Add branch progress tracking in Character
**File**: `src/cli_rpg/models/character.py`
- Modify `record_kill()`, `record_talk()`, etc. to check branch targets
- When branch completes, set quest to READY_TO_TURN_IN
- Helper method: `_check_branch_progress(quest, objective_type, target)`

### Step 4: Update quest completion rewards
**File**: `src/cli_rpg/models/character.py`
- Modify `claim_quest_rewards()` to use completed branch's modifiers
- Apply branch-specific faction effects
- Set `completed_branch_id` on quest

### Step 5: Update quest display UI
**File**: `src/cli_rpg/main.py`
- In `quest` command handler (~line 1816-1851):
  - Show "Completion Paths:" section if branches exist
  - Display each branch with name, objective, and progress
  - Mark completed branch with ★

### Step 6: Update AI quest generation (optional enhancement)
**File**: `src/cli_rpg/ai_service.py`
- Add `alternative_branches` to quest generation prompt
- Validate branch targets same as main quest

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/models/quest.py` | Add QuestBranch class, extend Quest |
| `src/cli_rpg/models/character.py` | Branch-aware progress tracking |
| `src/cli_rpg/main.py` | Quest UI shows branches |
| `tests/test_quest_branching.py` | NEW - 8+ tests |
| `tests/test_quest_branch_validation.py` | NEW - 4+ tests |

## Example Quest with Branches

```python
Quest(
    name="The Bandit Problem",
    description="Deal with the bandit leader threatening the village.",
    objective_type=ObjectiveType.KILL,  # Primary/default path
    target="Bandit Leader",
    alternative_branches=[
        QuestBranch(
            id="kill",
            name="Eliminate the Threat",
            objective_type=ObjectiveType.KILL,
            target="Bandit Leader",
            description="Slay the bandit leader.",
            faction_effects={"Militia": 15},
            gold_modifier=1.0,
        ),
        QuestBranch(
            id="persuade",
            name="Peaceful Resolution",
            objective_type=ObjectiveType.TALK,
            target="Bandit Leader",
            description="Convince him to leave peacefully.",
            faction_effects={"Militia": 5, "Outlaws": 10},
            gold_modifier=0.5,  # Less gold for non-violent
            xp_modifier=1.5,   # More XP for diplomacy
        ),
        QuestBranch(
            id="betray",
            name="Join the Raiders",
            objective_type=ObjectiveType.KILL,
            target="Village Elder",
            description="Help raid the village for a cut of the loot.",
            faction_effects={"Militia": -20, "Outlaws": 25},
            gold_modifier=2.0,  # Double gold from raid
            xp_modifier=0.5,   # Less XP for evil path
        ),
    ],
)
```

## UI Display Example

```
=== The Bandit Problem ===
Status: Active
Quest Giver: Village Elder

Deal with the bandit leader threatening the village.

Completion Paths:
  • Eliminate the Threat - Kill Bandit Leader [0/1]
  • Peaceful Resolution - Talk to Bandit Leader [0/1]
  • Join the Raiders - Kill Village Elder [0/1]
```
