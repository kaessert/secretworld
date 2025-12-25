# Plan: Improve test coverage for `models/npc.py` from 79% to 100%

## Missing Coverage (Lines 7-8, 49-51, 62-65)

### Analysis
- **Lines 7-8**: TYPE_CHECKING imports for `Shop` and `Quest` - never executed at runtime
- **Lines 49-51**: `get_greeting()` when `self.greetings` has items (random.choice branch)
- **Lines 62-65**: `add_conversation()` method - adding entries and capping at 10

## Implementation Steps

1. **Exclude TYPE_CHECKING from coverage** (`pyproject.toml`)
   - Add `"if TYPE_CHECKING:"` to `exclude_lines` in `[tool.coverage.report]`

2. **Add test for `get_greeting()` with greetings list** (`tests/test_npc.py`)
   - Create NPC with `greetings=["Hello!", "Hi there!"]`
   - Call `get_greeting()` and verify it returns one of the greetings

3. **Add test for `add_conversation()` basic functionality** (`tests/test_npc.py`)
   - Create NPC, call `add_conversation("player", "Hello")`
   - Verify entry is added to `conversation_history`

4. **Add test for `add_conversation()` capping at 10 entries** (`tests/test_npc.py`)
   - Add 12 conversations, verify only 10 most recent entries remain

## Verification
```bash
pytest tests/test_npc.py -v --cov=cli_rpg.models.npc --cov-report=term-missing
```
