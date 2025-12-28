# Implementation Plan: E2E Test Infrastructure & Enterable Location Fix

## Problem Summary
AI-generated worlds never produce enterable locations (dungeons, caves, ruins, temples). Despite extensive SubGrid infrastructure, the `enter` command never has valid targets because:
1. AI prompts don't explicitly request enterable location categories
2. No forced spawn mechanism ensures enterable locations appear after N tiles
3. No E2E test infrastructure exists to validate AI generation behavior

## Implementation Steps

### 1. Create E2E Test Infrastructure

**Files to create:**
- `tests/e2e/__init__.py`
- `tests/e2e/conftest.py`
- `tests/e2e/test_enterable_locations.py`

**Modify:**
- `conftest.py` (root) - Add `--e2e` pytest option

**Root `conftest.py` additions:**
```python
def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", default=False,
                     help="Run E2E tests with live AI service")
```

**`tests/e2e/conftest.py`:**
```python
import os
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring API key")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--e2e"):
        skip_e2e = pytest.mark.skip(reason="E2E tests skipped (use --e2e to run)")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)

@pytest.fixture
def ai_game_state():
    """Create GameState with live AI service for E2E testing."""
```

**`tests/e2e/test_enterable_locations.py`:**
```python
@pytest.mark.e2e
class TestEnterableLocationGeneration:
    def test_enterable_category_within_30_tiles(self, ai_game_state):
        """Walk 30 tiles, at least one enterable location must appear."""

    def test_enter_command_works_on_dungeon(self, ai_game_state):
        """Find dungeon, enter it, verify SubGrid created."""

    def test_subgrid_has_expected_content(self, ai_game_state):
        """Enter dungeon, verify boss/treasure/secrets populated."""
```

### 2. Fix AI Prompts to Request Enterable Categories

**File:** `src/cli_rpg/ai_config.py`

**Changes to `DEFAULT_LOCATION_PROMPT` (line ~23-52):**

Update category instruction to emphasize enterable types:
```
3. Include a category for the location type:
   - ENTERABLE (player can explore inside): dungeon, cave, ruins, temple, shrine, town, village, city, settlement
   - NON-ENTERABLE (terrain only): wilderness, forest, mountain

   IMPORTANT: For named locations with landmarks, prefer ENTERABLE categories (dungeon, cave, ruins, temple) ~30% of the time.
```

**Changes to `DEFAULT_LOCATION_PROMPT_MINIMAL` (line ~326-349):**

Same update - add explicit instruction for enterable category preference.

### 3. Add Forced Enterable Location Spawn

**File:** `src/cli_rpg/world_tiles.py`

Add constants and function at end of file:
```python
# Maximum tiles between enterable locations (forces dungeon/cave spawn)
MAX_TILES_WITHOUT_ENTERABLE = 25

# Enterable category pools by terrain for forced spawn
FORCED_ENTERABLE_BY_TERRAIN: Dict[str, List[str]] = {
    "forest": ["ruins", "cave", "temple"],
    "mountain": ["cave", "dungeon", "monastery"],
    "plains": ["ruins", "dungeon", "temple"],
    "desert": ["tomb", "ruins", "temple"],
    "swamp": ["ruins", "cave", "shrine"],
    "hills": ["cave", "ruins", "dungeon"],
    "beach": ["cave", "ruins"],
    "foothills": ["cave", "dungeon"],
}

def should_force_enterable_category(tiles_since_enterable: int) -> bool:
    """Check if an enterable location should be forced."""
    return tiles_since_enterable >= MAX_TILES_WITHOUT_ENTERABLE

def get_forced_enterable_category(terrain: str) -> str:
    """Get a random enterable category appropriate for the terrain."""
    import random
    categories = FORCED_ENTERABLE_BY_TERRAIN.get(terrain, ["dungeon", "cave", "ruins"])
    return random.choice(categories)
```

**File:** `src/cli_rpg/game_state.py`

Add tracking field in `__init__` (~line 300):
```python
self.tiles_since_enterable: int = 0  # Tracks tiles since last enterable location
```

Modify named location generation (~line 680-730) to use forced category:
```python
from cli_rpg.world_tiles import (
    should_force_enterable_category,
    get_forced_enterable_category,
    ENTERABLE_CATEGORIES,
)

# Check if we need to force an enterable category
if should_force_enterable_category(self.tiles_since_enterable):
    category_hint = get_forced_enterable_category(terrain or "plains")
    logger.info(f"Forcing enterable category '{category_hint}' after {self.tiles_since_enterable} tiles")
```

Update counter based on generated location category:
```python
if target_location.category in ENTERABLE_CATEGORIES:
    self.tiles_since_enterable = 0
else:
    self.tiles_since_enterable += 1
```

### 4. Add Unit Tests for Forced Spawn Logic

**File:** `tests/test_enterable_spawn.py`

```python
"""Tests for enterable location forced spawn logic."""
import pytest
from cli_rpg.world_tiles import (
    should_force_enterable_category,
    get_forced_enterable_category,
    MAX_TILES_WITHOUT_ENTERABLE,
    FORCED_ENTERABLE_BY_TERRAIN,
    ENTERABLE_CATEGORIES,
)

class TestEnterableSpawnLogic:
    def test_should_force_below_threshold(self):
        """Returns False when tiles_since_enterable < MAX."""
        assert not should_force_enterable_category(0)
        assert not should_force_enterable_category(24)

    def test_should_force_at_threshold(self):
        """Returns True when tiles_since_enterable >= MAX."""
        assert should_force_enterable_category(25)
        assert should_force_enterable_category(50)

    def test_forced_category_is_enterable(self):
        """get_forced_enterable_category returns enterable categories."""
        for terrain in FORCED_ENTERABLE_BY_TERRAIN:
            category = get_forced_enterable_category(terrain)
            assert category in ENTERABLE_CATEGORIES

    def test_forced_category_matches_terrain(self):
        """Returned category is from terrain's valid list."""
        category = get_forced_enterable_category("mountain")
        assert category in FORCED_ENTERABLE_BY_TERRAIN["mountain"]

    def test_unknown_terrain_fallback(self):
        """Unknown terrain falls back to default categories."""
        category = get_forced_enterable_category("lava")
        assert category in ["dungeon", "cave", "ruins"]
```

## Test Commands
```bash
# Run E2E tests (requires OPENAI_API_KEY or ANTHROPIC_API_KEY)
pytest tests/e2e/ -v --e2e

# Run unit tests for spawn logic
pytest tests/test_enterable_spawn.py -v

# Full test suite (excludes E2E by default)
pytest
```

## Files Modified/Created

**Created:**
- `tests/e2e/__init__.py`
- `tests/e2e/conftest.py`
- `tests/e2e/test_enterable_locations.py`
- `tests/test_enterable_spawn.py`

**Modified:**
- `conftest.py` (root) - Add `--e2e` option
- `src/cli_rpg/ai_config.py` - Update prompts to request enterable categories
- `src/cli_rpg/world_tiles.py` - Add forced enterable spawn logic
- `src/cli_rpg/game_state.py` - Add counter and forced spawn integration

## Verification
1. E2E test `test_enterable_category_within_30_tiles` passes
2. Unit tests for `should_force_enterable_category` pass
3. Existing 4960 tests continue to pass
4. Manual playtest: Walk 30+ tiles with AI, verify at least one dungeon/cave/ruins appears
