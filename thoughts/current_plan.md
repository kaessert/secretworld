# Implementation Plan: Quest Chains & Prerequisites

## Spec

Add chain support fields to the Quest model enabling narrative arcs:

```python
@dataclass
class Quest:
    # ... existing fields ...
    chain_id: Optional[str] = None              # Groups related quests (e.g., "goblin_war")
    chain_position: int = 0                      # Order in chain (0 = standalone, 1 = first, etc.)
    prerequisite_quests: List[str] = field(default_factory=list)  # Quest names that must be COMPLETED first
    unlocks_quests: List[str] = field(default_factory=list)       # Quest names unlocked on completion
```

**Behavior**:
- Quests with prerequisites cannot be accepted until all prerequisite quests have status COMPLETED
- When a quest is completed, quests in `unlocks_quests` become available (if they exist on the NPC)
- `chain_id` + `chain_position` are metadata for display/sorting (e.g., "Part 2 of Goblin War")
- All new fields are optional with safe defaults for backward compatibility

---

## Tests (in `tests/test_quest.py`)

### New Test Class: `TestQuestChainFields`
1. `test_quest_chain_fields_default_to_none_and_empty` - New fields have safe defaults
2. `test_quest_with_chain_id_and_position` - Chain metadata set correctly
3. `test_quest_with_prerequisites` - prerequisite_quests list stored correctly
4. `test_quest_with_unlocks` - unlocks_quests list stored correctly
5. `test_chain_fields_serialization_roundtrip` - to_dict/from_dict preserves all chain fields

### New Test Class: `TestPrerequisiteValidation` (in `tests/test_quest.py`)
1. `test_prerequisites_met_with_no_prerequisites` - Always returns True when list empty
2. `test_prerequisites_met_with_completed_quest` - Returns True when all prereqs COMPLETED
3. `test_prerequisites_not_met_with_active_quest` - Returns False when prereq still ACTIVE
4. `test_prerequisites_not_met_with_missing_quest` - Returns False when prereq not in player's quests

### New Test Class: `TestQuestAcceptPrerequisites` (in `tests/test_main.py` or new `tests/test_quest_chains.py`)
1. `test_accept_quest_with_unmet_prerequisites_fails` - Rejects with message listing missing prereqs
2. `test_accept_quest_with_met_prerequisites_succeeds` - Accepts normally when prereqs complete

---

## Implementation Steps

### Step 1: Add chain fields to Quest model
**File**: `src/cli_rpg/models/quest.py`

Add after `required_reputation` field (line ~67):
```python
chain_id: Optional[str] = field(default=None)
chain_position: int = field(default=0)
prerequisite_quests: List[str] = field(default_factory=list)
unlocks_quests: List[str] = field(default_factory=list)
```

### Step 2: Add `prerequisites_met()` method to Quest
**File**: `src/cli_rpg/models/quest.py`

Add method after `is_complete` property:
```python
def prerequisites_met(self, completed_quests: List[str]) -> bool:
    """Check if all prerequisite quests have been completed.

    Args:
        completed_quests: List of completed quest names (case-insensitive)

    Returns:
        True if no prerequisites or all are in completed list
    """
    if not self.prerequisite_quests:
        return True
    completed_lower = {q.lower() for q in completed_quests}
    return all(prereq.lower() in completed_lower for prereq in self.prerequisite_quests)
```

### Step 3: Update `to_dict()` serialization
**File**: `src/cli_rpg/models/quest.py`

Add to the return dict in `to_dict()` (after line ~156):
```python
"chain_id": self.chain_id,
"chain_position": self.chain_position,
"prerequisite_quests": self.prerequisite_quests,
"unlocks_quests": self.unlocks_quests,
```

### Step 4: Update `from_dict()` deserialization
**File**: `src/cli_rpg/models/quest.py`

Add to the `cls()` call in `from_dict()` (after `required_reputation`):
```python
chain_id=data.get("chain_id"),
chain_position=data.get("chain_position", 0),
prerequisite_quests=data.get("prerequisite_quests", []),
unlocks_quests=data.get("unlocks_quests", []),
```

### Step 5: Add prerequisite check to quest acceptance
**File**: `src/cli_rpg/main.py`

In the `accept` command handler (around line 1650, after faction reputation check):
```python
# Check prerequisite quests
if matching_quest.prerequisite_quests:
    completed_names = [
        q.name for q in game_state.current_character.quests
        if q.status == QuestStatus.COMPLETED
    ]
    if not matching_quest.prerequisites_met(completed_names):
        missing = [p for p in matching_quest.prerequisite_quests
                   if p.lower() not in {c.lower() for c in completed_names}]
        return (True, f"\nYou must first complete: {', '.join(missing)}")
```

### Step 6: Update quest display to show chain info
**File**: `src/cli_rpg/main.py`

In the `quest` command handler (around line 1815), add chain display:
```python
if quest.chain_id:
    chain_info = f"Part {quest.chain_position}" if quest.chain_position > 0 else "Prologue"
    lines.append(f"Chain: {quest.chain_id} ({chain_info})")
if quest.prerequisite_quests:
    lines.append(f"Prerequisites: {', '.join(quest.prerequisite_quests)}")
```

---

## Verification

1. Run existing quest tests: `pytest tests/test_quest.py -v`
2. Run new chain tests after adding them
3. Run full test suite: `pytest`
4. Manual test: Create quests with prerequisites, verify accept blocks/allows correctly
