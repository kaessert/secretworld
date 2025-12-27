# Quest Memory & NPC Reactions Implementation Plan

## Overview
When quests complete, NPCs should remember and react to past quest outcomes in their dialogue. This adds immersion by making the world feel responsive to player actions.

## Current State Analysis
- `game_state.choices` tracks combat decisions (flee/kill) but NOT quest outcomes
- `NPC.get_greeting()` already references `choices` for reputation-based greetings
- Quest completion happens in `main.py:1752-1756` - rewards claimed, status set to COMPLETED
- No `QuestOutcome` model exists; quest completion method is not tracked

## Implementation Steps

### 1. Create QuestOutcome Model
**File**: `src/cli_rpg/models/quest_outcome.py` (NEW)

```python
@dataclass
class QuestOutcome:
    quest_name: str
    quest_giver: str  # NPC who gave the quest
    completion_method: str  # "main", "branch_<id>", "expired", "abandoned"
    completed_branch_name: Optional[str] = None  # Branch name if completed via branch
    timestamp: int = 0  # Game hour when completed
    affected_npcs: List[str] = field(default_factory=list)  # NPCs involved
    faction_changes: Dict[str, int] = field(default_factory=dict)  # Faction reputation changes
```

### 2. Add quest_outcomes to GameState
**File**: `src/cli_rpg/game_state.py`

- Add `quest_outcomes: list[QuestOutcome] = []` attribute (~line 277)
- Add serialization in `to_dict()` and `from_dict()` (with backward compat)
- Add helper: `record_quest_outcome(quest, method, branch_name=None)`
- Add helper: `get_quest_outcomes_for_npc(npc_name) -> list[QuestOutcome]`

### 3. Record Quest Outcomes on Completion
**File**: `src/cli_rpg/main.py`

In the `complete` command handler (~line 1756), after `matching_quest.status = QuestStatus.COMPLETED`:
```python
game_state.record_quest_outcome(
    quest=matching_quest,
    method="branch" if matching_quest.completed_branch_id else "main",
    branch_name=completed_branch_name if matching_quest.completed_branch_id else None
)
```

Also record for FAILED quests (expired) in `game_state.check_expired_quests()`.

### 4. Extend NPC.get_greeting() for Quest Reactions
**File**: `src/cli_rpg/models/npc.py`

Update `get_greeting()` signature and logic:
```python
def get_greeting(
    self,
    choices: Optional[List[dict]] = None,
    quest_outcomes: Optional[List["QuestOutcome"]] = None
) -> str:
```

Add quest-based greeting selection:
- Check if NPC was quest_giver for any completed quests
- Check if NPC was affected by any quest outcomes
- Generate appropriate greeting based on outcome method

Add `_get_quest_reaction_greeting(outcome: QuestOutcome) -> str` method with templates.

### 5. Pass quest_outcomes to NPC Greetings
**File**: `src/cli_rpg/main.py`

In `talk` command handler (~line 1272), update:
```python
relevant_outcomes = game_state.get_quest_outcomes_for_npc(npc.name)
greeting = npc.get_greeting(
    choices=game_state.choices,
    quest_outcomes=relevant_outcomes
)
```

### 6. Add Tests
**File**: `tests/test_quest_outcomes.py` (NEW)

Test cases:
- QuestOutcome model creation and serialization
- GameState.record_quest_outcome() records correctly
- GameState.get_quest_outcomes_for_npc() filters correctly
- GameState serialization with quest_outcomes (and backward compat)
- NPC.get_greeting() reacts to quest outcomes
- Integration: complete quest -> NPC references it in greeting

## Files to Modify
| File | Changes |
|------|---------|
| `src/cli_rpg/models/quest_outcome.py` | NEW - QuestOutcome dataclass |
| `src/cli_rpg/game_state.py` | Add quest_outcomes list and helpers |
| `src/cli_rpg/main.py` | Record outcomes on quest complete |
| `src/cli_rpg/models/npc.py` | Extend get_greeting() for quest reactions |
| `tests/test_quest_outcomes.py` | NEW - Test coverage |

## Quest Reaction Templates

```python
QUEST_COMPLETION_REACTIONS = {
    "quest_giver_success": [
        "Well done! I knew I could count on you to handle {quest_name}.",
        "You've proven yourself. {quest_name} is complete, thanks to you.",
        "Ah, the hero who completed {quest_name}! What brings you back?",
    ],
    "quest_giver_branch_violent": [
        "I heard how you... dealt with things. Effective, if brutal.",
        "The job's done, though some say your methods were... harsh.",
    ],
    "quest_giver_branch_peaceful": [
        "I'm impressed you found a peaceful solution. Not many would.",
        "You showed mercy. That takes courage.",
    ],
    "affected_npc_positive": [
        "I heard what you did. You have my gratitude.",
        "Word spreads fast. Thank you for your help with {quest_name}.",
    ],
    "affected_npc_negative": [
        "I know what you did. Don't expect any favors from me.",
        "After {quest_name}? We have nothing to discuss.",
    ],
}
```

## Estimated Test Count
~15-20 new tests covering:
- QuestOutcome model (5 tests)
- GameState integration (5 tests)
- NPC greeting integration (5 tests)
- End-to-end flow (3 tests)
