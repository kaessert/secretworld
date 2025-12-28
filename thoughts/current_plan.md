# AI Content Quality Validation Implementation Plan

## Overview
Implement `CONTENT_QUALITY` assertion type in `scripts/validation/assertions.py` and create `scripts/validation/ai_quality.py` to validate AI-generated content meets quality standards.

## Spec

### ContentQualityCheck Types
Quality checks for different AI-generated content:
- **Location**: name length (3-50 chars), description length (20-500 chars), valid category
- **NPC**: name length (2-40 chars), description non-empty, dialogue non-empty
- **Quest**: name non-empty, description length (10-300 chars), valid objective_type
- **Item**: name non-empty, description non-empty, valid item_type

### Quality Dimensions
- `min_length` / `max_length` - String length bounds
- `non_empty` - Content is not empty/None
- `valid_values` - Value is in allowed set
- `coherence` - Content relates to context (category/theme)
- `no_placeholder` - No "Unknown", "TODO", "placeholder" text

### CONTENT_QUALITY Assertion
```python
# Expected format in assertion:
expected = {
    "content_type": "location",  # location, npc, quest, item
    "checks": ["min_length", "max_length", "valid_values"],
    "thresholds": {"min_length": 20, "max_length": 500}
}
```

## Tests (scripts/validation/)

### test_ai_quality.py
1. `test_content_type_enum_values` - Verify ContentType enum has location, npc, quest, item
2. `test_quality_check_location_valid` - Location with valid name/desc/category passes
3. `test_quality_check_location_short_name` - Location with 2-char name fails
4. `test_quality_check_location_invalid_category` - Location with bad category fails
5. `test_quality_check_npc_valid` - NPC with name/desc/dialogue passes
6. `test_quality_check_npc_empty_dialogue` - NPC with empty dialogue fails
7. `test_quality_check_quest_valid` - Quest with valid fields passes
8. `test_quality_check_item_valid` - Item with valid fields passes
9. `test_quality_check_placeholder_detection` - Content with "Unknown Chamber" fails
10. `test_quality_checker_batch` - Batch check returns all results
11. `test_quality_result_serialization` - QualityResult to_dict/from_dict roundtrip

### test_validation_assertions.py (update)
12. `test_check_content_quality_passes` - CONTENT_QUALITY with valid content passes
13. `test_check_content_quality_fails` - CONTENT_QUALITY with invalid content fails

## Implementation Steps

### 1. Create `scripts/validation/ai_quality.py`
```python
# New file with:
class ContentType(Enum):
    LOCATION = auto()
    NPC = auto()
    QUEST = auto()
    ITEM = auto()

@dataclass
class QualityResult:
    passed: bool
    content_type: ContentType
    checks_passed: list[str]
    checks_failed: list[str]
    details: dict[str, str]

class ContentQualityChecker:
    # Constants for thresholds
    LOCATION_NAME_MIN = 3
    LOCATION_NAME_MAX = 50
    LOCATION_DESC_MIN = 20
    LOCATION_DESC_MAX = 500
    NPC_NAME_MIN = 2
    NPC_NAME_MAX = 40
    QUEST_DESC_MIN = 10
    QUEST_DESC_MAX = 300

    # Placeholder patterns to detect
    PLACEHOLDER_PATTERNS = [
        r"^unknown",
        r"^todo",
        r"placeholder",
        r"^test\s",
        r"^example\s",
    ]

    def check_location(self, content: dict) -> QualityResult
    def check_npc(self, content: dict) -> QualityResult
    def check_quest(self, content: dict) -> QualityResult
    def check_item(self, content: dict) -> QualityResult
    def check(self, content_type: ContentType, content: dict) -> QualityResult
    def check_batch(self, items: list[tuple[ContentType, dict]]) -> list[QualityResult]
```

### 2. Update `scripts/validation/assertions.py`
Add `_check_content_quality` method to `AssertionChecker`:
```python
def _check_content_quality(
    self,
    assertion: Assertion,
    state: Any,
    prev_state: Optional[Any],
    output: str,
) -> AssertionResult:
    """Check CONTENT_QUALITY assertion using ContentQualityChecker."""
    from scripts.validation.ai_quality import ContentQualityChecker, ContentType

    content = self._get_field_value(state, assertion.field)
    config = assertion.expected or {}
    content_type_str = config.get("content_type", "location")
    content_type = ContentType[content_type_str.upper()]

    checker = ContentQualityChecker()
    result = checker.check(content_type, content)

    if result.passed:
        return AssertionResult(assertion=assertion, passed=True, actual=content)
    else:
        error = f"Quality checks failed: {', '.join(result.checks_failed)}"
        return AssertionResult(assertion=assertion, passed=False, actual=content, error=error)
```

Add to checkers dict in `check()` method:
```python
AssertionType.CONTENT_QUALITY: self._check_content_quality,
```

### 3. Update `scripts/validation/__init__.py`
Add exports:
```python
from .ai_quality import (
    ContentQualityChecker,
    ContentType,
    QualityResult,
)
```

### 4. Write tests
- Create `tests/test_ai_quality.py` with 11 tests
- Update `tests/test_validation_assertions.py` - change line 528 test expectation

## Files to Modify
1. `scripts/validation/ai_quality.py` - NEW (ContentQualityChecker, ContentType, QualityResult)
2. `scripts/validation/assertions.py` - Add _check_content_quality method
3. `scripts/validation/__init__.py` - Add ai_quality exports
4. `tests/test_ai_quality.py` - NEW (11 tests)
5. `tests/test_validation_assertions.py` - Update CONTENT_QUALITY test (line 514-528)

## Verification
```bash
pytest tests/test_ai_quality.py tests/test_validation_assertions.py -v
```
