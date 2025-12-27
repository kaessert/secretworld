# Implementation Plan: Complete BLOCKER - Remove `connections` Field

## Summary
The `connections` field was already removed from the Location dataclass. The remaining work is cleanup: remove one test file's legacy usage and update ISSUES.md to mark the success criteria as complete.

## Status Assessment
- **`Location.connections` field**: Already removed from model ✅
- **Source code**: No `.connections` references in `/src/cli_rpg/` ✅
- **Test cleanup needed**: 1 test file still sets `.connections` dynamically

## Implementation Steps

### 1. Fix test_npc_persistence_navigation.py (lines 234-244)

**File**: `tests/test_npc_persistence_navigation.py`

**Problem**: The `test_npc_names_never_show_question_marks` test dynamically sets `.connections` on Location objects (lines 234-244). This is unnecessary because:
- Navigation uses coordinate adjacency, not connections
- The test already sets coordinates correctly on each location

**Fix**: Remove the connection-setting code (lines 234-244). The test will continue to pass because movement is coordinate-based.

**Before**:
```python
        # Set up connections
        locations["Center"].connections = {
            "north": "North",
            "south": "South",
            "east": "East",
            "west": "West",
        }
        locations["North"].connections = {"south": "Center"}
        locations["South"].connections = {"north": "Center"}
        locations["East"].connections = {"west": "Center"}
        locations["West"].connections = {"east": "Center"}
```

**After**: Delete these lines entirely.

### 2. Update ISSUES.md Success Criteria

**File**: `ISSUES.md`

**Changes**:
- Line 133: Change `[ ] `Location.connections` field removed entirely` to `[x]`
- Line 138: Change `[ ] No code references "connections" for movement logic` to `[x]`, and remove the parenthetical note

### 3. Run Tests to Verify

```bash
pytest tests/test_npc_persistence_navigation.py -v
pytest -x  # Full suite
```

## Verification
- All 3573+ tests continue to pass
- No `.connections` references remain in source or tests
- ISSUES.md BLOCKER has all success criteria checked
