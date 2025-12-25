# Echo Choices Foundation Implementation Plan

## Overview
Add a minimal "choice tracking" foundation to record significant player decisions. This is the prerequisite data structure for all Phase 2 "Consequence" features (NPC reactions, world state changes, reputation effects).

## Spec

**Choice Data Structure:**
- `choices: list[dict]` field added to `GameState`
- Each choice dict contains:
  - `choice_type: str` - category of choice (e.g., "combat_mercy", "dialogue", "quest")
  - `choice_id: str` - unique identifier (e.g., "spare_bandit_001")
  - `description: str` - human-readable description
  - `timestamp: int` - game time (hour) when choice was made
  - `location: str` - location name where choice occurred
  - `target: Optional[str]` - NPC/enemy name involved (if applicable)

**Recording API:**
```python
def record_choice(self, choice_type: str, choice_id: str, description: str, target: Optional[str] = None) -> None
def has_choice(self, choice_id: str) -> bool  # Check if specific choice was made
def get_choices_by_type(self, choice_type: str) -> list[dict]  # Filter by type
```

**Persistence:**
- `choices` serialized in `GameState.to_dict()` and restored in `from_dict()`
- Backward compatible: old saves default to empty list

---

## Implementation Steps

### 1. Add choices field to GameState (`src/cli_rpg/game_state.py`)
- Add `choices: list[dict] = []` in `__init__`
- Implement `record_choice()`, `has_choice()`, `get_choices_by_type()` methods
- Update `to_dict()` to include `"choices": self.choices`
- Update `from_dict()` to restore `choices` with backward compat default `[]`

### 2. Add first choice point: flee from combat (`src/cli_rpg/main.py`)
- When player flees combat, record choice: `game_state.record_choice("combat_flee", f"flee_{enemy_name}", f"Fled from {enemy_name}", enemy_name)`
- This is a simple integration point to validate the system works

---

## Test Plan (`tests/test_choices.py`)

### GameState Choice Tracking
- `test_record_choice_adds_to_list` - choice appears in choices list
- `test_record_choice_includes_all_fields` - all fields populated correctly
- `test_has_choice_returns_true_for_recorded` - returns True for existing choice
- `test_has_choice_returns_false_for_missing` - returns False for non-existent
- `test_get_choices_by_type_filters_correctly` - only returns matching type
- `test_get_choices_by_type_empty_when_no_matches` - empty list if none match

### Persistence
- `test_choices_persist_in_save` - save/load roundtrip preserves choices
- `test_choices_backward_compatibility` - old saves load with empty choices list

### Integration
- `test_flee_combat_records_choice` - fleeing combat records a choice

---

## Files to Modify
- `src/cli_rpg/game_state.py` - add choices field, methods, serialization
- `src/cli_rpg/main.py` - record choice on flee
- `tests/test_choices.py` - new test file
