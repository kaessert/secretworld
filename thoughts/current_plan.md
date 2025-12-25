# Remove "up"/"down" Directions from 2D World Grid

## Spec

Remove vertical directions ("up"/"down") from the 2D world grid system to prevent:
- Player confusion from seeing impossible movement options
- Stuck states where only vertical exits exist

## Changes

### 1. `src/cli_rpg/models/location.py` (line 30)
```python
# Before
VALID_DIRECTIONS: ClassVar[set[str]] = {"north", "south", "east", "west", "up", "down"}

# After
VALID_DIRECTIONS: ClassVar[set[str]] = {"north", "south", "east", "west"}
```

Also update docstring (lines 16-17) to remove "up, down" reference.

### 2. `src/cli_rpg/world_grid.py` (lines 22-24)
```python
# Remove these two lines from OPPOSITE_DIRECTIONS:
    "up": "down",
    "down": "up",
```

### 3. `src/cli_rpg/ai_config.py` (line 25)
```python
# Before
3. Suggest 1-4 connections to other locations using valid directions: north, south, east, west, up, down

# After
3. Suggest 1-4 connections to other locations using valid directions: north, south, east, west
```

### 4. Test updates

| File | Changes |
|------|---------|
| `tests/test_model_coverage_gaps.py:356-357` | Remove "up"/"down" connection tests or change to expect ValueError |
| `tests/test_world_grid.py:503` | Remove "up"/"down" from non-cardinal connection test |
| `tests/test_game_state.py:430` | Keep "up" in invalid_dir list (now correctly invalid) |
| `tests/test_ai_service.py:513-630` | Keep tests - they verify filtering of invalid directions |
| `tests/test_ai_world_generation.py:330-331` | Remove up/down opposite direction assertions |
| `tests/test_e2e_world_expansion.py:54-55,63,181,723` | Remove up/down from test data |
| `tests/test_initial_world_dead_end_prevention.py:57` | Remove up/down from opposite map |

## Verification

Run: `pytest tests/test_location.py tests/test_world_grid.py tests/test_game_state.py tests/test_ai_service.py tests/test_ai_world_generation.py tests/test_e2e_world_expansion.py tests/test_initial_world_dead_end_prevention.py tests/test_model_coverage_gaps.py -v`
