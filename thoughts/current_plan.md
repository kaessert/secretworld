# Plan: Increase Test Coverage - Target ai_world.py (96% -> 99%+)

## Current State
- Overall coverage: 98.03% (1304 tests pass)
- `world.py`: 92% - 4 uncovered lines (18-21) are import-time fallback, hard to unit test
- `ai_world.py`: 96% - 8 uncovered lines representing testable runtime paths
- Focus: ai_world.py since its uncovered lines are runtime code paths

## Uncovered Lines in ai_world.py

| Lines | Description |
|-------|-------------|
| 146 | `continue` when suggested name already exists in grid |
| 150-151 | `logger.warning` + `continue` for non-grid direction |
| 292-294 | Adding bidirectional connection when target exists in world |
| 434 | Warning when no locations placed (fallback to single location) |
| 469 | Adding back-connection to entry when it doesn't have one |

## Implementation Steps

### 1. Read existing tests to understand patterns
File: `tests/test_ai_world_generation.py`

### 2. Add tests for uncovered paths

#### Test line 146 - duplicate name skipped
```python
def test_create_ai_world_skips_duplicate_name():
    """Test create_ai_world skips locations when name already exists."""
    # Mock AI to return location with name that conflicts with existing
```

#### Test lines 150-151 - non-grid direction warning
```python
def test_create_ai_world_warns_on_non_grid_direction(caplog):
    """Test create_ai_world logs warning for non-grid directions like 'up'."""
    # Mock location data to include 'up' or 'down' direction
```

#### Test lines 292-294 - bidirectional connection
```python
def test_expand_world_adds_bidirectional_connection_to_existing():
    """Test expand_world adds reverse connection when target exists."""
    # Setup world with target location, mock AI to return connection to it
```

#### Test line 434 - fallback when no locations placed
```python
def test_expand_area_falls_back_when_no_locations_placed():
    """Test expand_area falls back to single expand when none placed."""
    # Mock generate_area to return locations that can't be placed (all conflicts)
```

#### Test line 469 - back-connection addition
```python
def test_expand_area_adds_back_connection():
    """Test expand_area ensures entry has back-connection."""
    # Setup where entry location lacks opposite direction connection
```

### 3. Run tests and verify coverage

```bash
pytest tests/test_ai_world_generation.py -v --cov=src/cli_rpg/ai_world --cov-report=term-missing
```

## Files to Modify
- `tests/test_ai_world_generation.py` - Add 5 new tests
