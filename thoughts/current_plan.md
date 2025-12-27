# Pre-generated Test World Implementation Plan

## Feature Spec

Create a pre-generated test world fixture and `--demo` mode that enables:
- Automated testing without AI API costs
- Reproducible bug reports with known game state
- CI/CD integration with deterministic tests
- Demo mode for showcasing gameplay

## Implementation Steps

### 1. Create Test World Fixture Data
**File:** `tests/fixtures/test_world.json`

Generate a comprehensive test world JSON containing:
- **Character**: Level 3 Warrior with balanced stats, some inventory items, 1-2 active quests
- **World**: 5 named overworld locations at coordinates (0,0), (0,1), (1,0), (-1,0), (0,-1)
  - Starting village with merchant NPC and quest giver
  - Forest area with enemy spawns
  - Cave entrance (enterable, with 3x3 SubGrid)
  - Abandoned ruins
  - Crossroads
- **NPCs**: 3-4 NPCs with shops, quests, dialogue
- **SubGrid**: One dungeon interior with 3x3 layout, exit point, treasure, boss
- **Factions**: Default factions from `get_default_factions()`
- **GameTime/Weather**: Day 1, morning, clear weather

### 2. Create Fixture Loading Utility
**File:** `src/cli_rpg/test_world.py`

```python
def load_test_world() -> dict:
    """Load pre-generated test world from fixtures."""

def create_demo_game_state(ai_service=None) -> GameState:
    """Create GameState from pre-generated test world."""
```

### 3. Add Pytest Fixture
**File:** `tests/conftest.py`

Add fixture:
```python
@pytest.fixture
def pregenerated_game_state():
    """Load fresh copy of pre-generated test world for each test."""
```

### 4. Add --demo CLI Flag
**File:** `src/cli_rpg/main.py`

- Add `--demo` argument to `parse_args()`
- In `main()`, when `--demo` is set:
  - Skip character creation
  - Load test world via `create_demo_game_state()`
  - Skip AI service initialization (no API calls)

### 5. Create Fixture Generation Script
**File:** `scripts/generate_test_world.py`

Script that:
- Creates a GameState programmatically (no AI)
- Populates with known test data
- Exports via `game_state.to_dict()`
- Writes to `tests/fixtures/test_world.json`

This allows regenerating the fixture if models change.

## Test Plan

### Unit Tests
**File:** `tests/test_test_world.py`

1. `test_load_test_world_returns_valid_dict()` - Fixture loads as valid JSON
2. `test_create_demo_game_state_returns_game_state()` - GameState.from_dict() succeeds
3. `test_demo_game_state_has_character()` - Character exists with expected stats
4. `test_demo_game_state_has_locations()` - World has expected named locations
5. `test_demo_game_state_has_npcs()` - NPCs exist with shops/quests
6. `test_demo_game_state_navigation_works()` - Can move between locations
7. `test_demo_game_state_look_works()` - look() returns valid output
8. `test_demo_game_state_subgrid_entry()` - Can enter/exit dungeon SubGrid

### Integration Tests
**File:** `tests/test_demo_mode.py`

1. `test_demo_flag_skips_character_creation()` - No prompts in demo mode
2. `test_demo_mode_gameplay_loop()` - Can execute commands without AI
3. `test_demo_mode_no_ai_calls()` - AI service not invoked

## Files to Create/Modify

| File | Action |
|------|--------|
| `tests/fixtures/test_world.json` | Create (~50-100KB) |
| `src/cli_rpg/test_world.py` | Create (~50 lines) |
| `scripts/generate_test_world.py` | Create (~150 lines) |
| `tests/conftest.py` | Add 1 fixture (~10 lines) |
| `src/cli_rpg/main.py` | Add --demo flag (~15 lines) |
| `tests/test_test_world.py` | Create (~100 lines) |
| `tests/test_demo_mode.py` | Create (~50 lines) |

## Implementation Order

1. `scripts/generate_test_world.py` - Build the fixture generator
2. `tests/fixtures/test_world.json` - Generate the fixture
3. `src/cli_rpg/test_world.py` - Loading utility
4. `tests/test_test_world.py` - Tests for fixture loading
5. `tests/conftest.py` - Pytest fixture
6. `src/cli_rpg/main.py` - --demo flag
7. `tests/test_demo_mode.py` - Demo mode tests
