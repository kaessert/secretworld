# Plan: Validation Framework - Phase 3 (assertions.py)

## Spec

Create `scripts/validation/assertions.py` with core assertion types for automated validation of game state during playtesting. This is the foundation of the validation framework.

**Assertion Types (from ISSUES.md):**
- `STATE_EQUALS` - Exact match of state field to expected value
- `STATE_CONTAINS` - State field contains expected substring/element
- `STATE_RANGE` - State field value within min/max bounds
- `NARRATIVE_MATCH` - Regex pattern matching on narrative text
- `COMMAND_VALID` - Command was accepted (no error)
- `COMMAND_EFFECT` - Command produced expected state change
- `CONTENT_PRESENT` - AI-generated content exists (not empty/None)
- `CONTENT_QUALITY` - AI content meets quality threshold (future)

## Tests (in `tests/test_validation_assertions.py`)

### AssertionType enum
1. `test_assertion_type_has_all_types`: Enum has all 8 assertion types
2. `test_assertion_type_values_are_unique`: All enum values are distinct

### Assertion dataclass
3. `test_assertion_creation`: Assertion has type, field, expected, message
4. `test_assertion_serialization`: to_dict/from_dict roundtrip works

### AssertionResult dataclass
5. `test_assertion_result_passed`: Result stores passed=True, no error
6. `test_assertion_result_failed`: Result stores passed=False, error message
7. `test_assertion_result_serialization`: to_dict/from_dict roundtrip

### AssertionChecker class
8. `test_check_state_equals_passes`: Exact match returns passed=True
9. `test_check_state_equals_fails`: Mismatch returns passed=False, error
10. `test_check_state_equals_nested_field`: Dot notation for nested fields
11. `test_check_state_contains_passes`: Contains check for string
12. `test_check_state_contains_list`: Contains check for list element
13. `test_check_state_contains_fails`: Missing element returns failed
14. `test_check_state_range_passes`: Value within range
15. `test_check_state_range_below`: Value below min returns failed
16. `test_check_state_range_above`: Value above max returns failed
17. `test_check_narrative_match_passes`: Regex matches narrative text
18. `test_check_narrative_match_fails`: Regex doesn't match
19. `test_check_command_valid_passes`: No error message = valid
20. `test_check_command_valid_fails`: Error in output = invalid
21. `test_check_command_effect_passes`: Expected state change occurred
22. `test_check_command_effect_fails`: State change did not occur
23. `test_check_content_present_passes`: Non-empty content exists
24. `test_check_content_present_fails`: Empty or None content
25. `test_check_returns_result_object`: All checks return AssertionResult
26. `test_check_unknown_type_raises`: Invalid assertion type raises ValueError

## Implementation Steps

### Step 1: Create `scripts/validation/__init__.py`
- Package initialization with exports

### Step 2: Create `scripts/validation/assertions.py`

```python
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional
import re


class AssertionType(Enum):
    """Types of assertions for state validation."""
    STATE_EQUALS = auto()
    STATE_CONTAINS = auto()
    STATE_RANGE = auto()
    NARRATIVE_MATCH = auto()
    COMMAND_VALID = auto()
    COMMAND_EFFECT = auto()
    CONTENT_PRESENT = auto()
    CONTENT_QUALITY = auto()


@dataclass
class Assertion:
    """Single assertion to validate against game state."""
    type: AssertionType
    field: str  # State field to check (dot notation for nested)
    expected: Any  # Expected value/pattern/range
    message: str = ""  # Custom failure message


@dataclass
class AssertionResult:
    """Result of running an assertion."""
    assertion: Assertion
    passed: bool
    actual: Any = None
    error: str = ""


class AssertionChecker:
    """Checks assertions against game state."""

    def check(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any] = None,
        output: str = "",
    ) -> AssertionResult:
        """Check an assertion against the current state."""
        # Dispatch to type-specific checker
        ...
```

### Step 3: Implement `_get_field_value()` helper
- Parse dot notation (e.g., "character.health")
- Handle dict and object attribute access
- Return None for missing fields

### Step 4: Implement type-specific check methods
- `_check_state_equals()`: Compare with `==`
- `_check_state_contains()`: Use `in` operator
- `_check_state_range()`: Check `min <= value <= max`
- `_check_narrative_match()`: Use `re.search()`
- `_check_command_valid()`: Check for error patterns in output
- `_check_command_effect()`: Compare prev_state vs state
- `_check_content_present()`: Check not None/empty

### Step 5: Create tests in `tests/test_validation_assertions.py`
- Follow existing test patterns (see test_agent_memory.py)
- Use pytest, descriptive names, docstrings with "Spec:"

## Files to Create

1. **Create**: `scripts/validation/__init__.py`
2. **Create**: `scripts/validation/assertions.py`
3. **Create**: `tests/test_validation_assertions.py`
