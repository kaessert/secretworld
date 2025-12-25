# Implementation Plan: Improve Test Coverage

## Summary
Overall test coverage is excellent at 94%, with all 1205 tests passing. The focus will be on targeting specific uncovered code paths in modules with lower coverage to reach 95%+ overall coverage.

## Modules with Coverage Gaps (Priority Order)

| Module | Coverage | Missing Lines |
|--------|----------|---------------|
| `ai_service.py` | 90% | 44 lines - error handling, edge cases |
| `world.py` | 90% | 5 lines - AI import fallback, non-strict fallback |
| `main.py` | 92% | 52 lines - error paths, edge cases |
| `ai_world.py` | 93% | 14 lines - edge cases in grid generation |
| `ai_config.py` | 93% | 6 lines - error handling |

## Spec: Target Coverage Gaps

### 1. `world.py` (Lines 18-21, 142)
- Line 18-21: `ImportError` fallback when AI components unavailable
- Line 142: Non-strict mode AI failure fallback path

### 2. `main.py` (Lines 148-149, 157-159, 404-415, etc.)
- Lines 148-149, 157-159: Load character error paths (invalid selection, generic exception)
- Lines 404-415: `go` command path with movement success/failure
- Lines 434, 441, 446, 451: `unequip` command edge cases
- Lines 953-968: Combat status display and conversation routing

### 3. `ai_service.py` (Lines 630-631, 635, 639, etc.)
- JSON parse error handling paths
- Validation error paths for area generation
- Rate limiting and retry paths

### 4. `ai_world.py` (Lines 142, 146, 150-151)
- Duplicate location name handling
- Invalid grid direction handling

## Implementation Steps

### Step 1: Create `tests/test_world_coverage.py`
Add tests for `world.py` uncovered paths:
```python
# Test ImportError fallback (lines 18-21)
def test_world_without_ai_components():
    """Test fallback when AI components unavailable."""

# Test non-strict mode fallback (line 142)
def test_create_world_nonstrict_ai_failure():
    """Test non-strict mode falls back on AI error."""
```

### Step 2: Add tests to `tests/test_main_coverage.py`
Cover additional main.py error paths:
```python
# Test invalid save selection
def test_select_load_character_invalid_selection():
    """Test handling of out-of-range save selection."""

# Test generic exception during load
def test_select_load_character_generic_exception():
    """Test handling of unexpected exceptions during load."""

# Test go command with no args
def test_exploration_go_no_args():
    """Test 'go' without direction argument."""

# Test unequip edge cases
def test_unequip_invalid_slot():
    """Test unequip with invalid slot name."""
```

### Step 3: Add tests to `tests/test_ai_service.py`
Cover validation error paths:
```python
# Test JSON parse failure
def test_parse_area_response_invalid_json():
    """Test area response with invalid JSON."""

# Test missing required fields
def test_validate_area_location_missing_field():
    """Test validation with missing required field."""

# Test empty location array
def test_parse_area_response_empty_array():
    """Test area response with empty array."""
```

### Step 4: Add tests to `tests/test_ai_world.py` or `tests/test_ai_world_generation.py`
Cover grid generation edge cases:
```python
# Test duplicate location name
def test_generate_world_duplicate_location_name():
    """Test handling of duplicate location names during generation."""

# Test invalid direction handling
def test_generate_world_invalid_direction():
    """Test skipping of non-grid directions."""
```

## Test Execution
After implementing each step:
```bash
source venv/bin/activate && pytest --cov=src/cli_rpg --cov-report=term-missing -v tests/test_<new_file>.py
```

Final verification:
```bash
source venv/bin/activate && pytest --cov=src/cli_rpg --cov-report=term-missing
```

## Expected Outcome
- Overall coverage increase from 94% to 95-96%
- All identified uncovered error paths have test coverage
- Improved confidence in error handling behavior
