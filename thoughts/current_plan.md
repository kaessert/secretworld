# Implementation Plan: Connect Terrain to Location Generation

## Summary
Pass WFC terrain type to AI prompts so generated locations match their terrain. A "Desert Oasis" should only spawn on desert tiles, not forest.

## Current State Analysis

**What exists:**
- `ChunkManager.get_tile_at(x, y)` returns terrain type at coordinates (forest, desert, mountain, etc.)
- `game_state.move()` already queries terrain and stores it: `terrain = self.chunk_manager.get_tile_at(*target_coords)` (line 510)
- `game_state.move()` sets `target_location.terrain = terrain` after generation (line 536)
- Layered generation uses `generate_location_with_context()` which takes `world_context` and `region_context`
- `get_or_create_region_context()` already accepts a `terrain_hint` parameter
- `generate_region_context()` passes `terrain_hint` to the prompt

**The gap:**
1. `expand_area()` and `expand_world()` in `ai_world.py` don't receive terrain info
2. The `location_prompt_minimal` template doesn't include terrain type
3. `game_state.move()` calls `expand_area()` without passing terrain

## Implementation Steps

### Step 1: Update ai_world.py to accept terrain_type parameter

**File: `src/cli_rpg/ai_world.py`**

1. Add `terrain_type: Optional[str] = None` parameter to `expand_world()` (around line 358)
2. Add `terrain_type: Optional[str] = None` parameter to `expand_area()` (around line 502)
3. Pass terrain_type to `get_or_create_region_context()` as `terrain_hint` when generating locations

### Step 2: Update prompt template to include terrain

**File: `src/cli_rpg/ai_config.py`**

1. Add `{terrain_type}` placeholder to `DEFAULT_LOCATION_PROMPT_MINIMAL` (around line 306)
2. Add instruction: "The terrain at this location is {terrain_type}. Generate a location that fits this terrain."

### Step 3: Update AI service to use terrain in prompt

**File: `src/cli_rpg/ai_service.py`**

1. Add `terrain_type: Optional[str] = None` to `generate_location_with_context()` signature (around line 2406)
2. Add `terrain_type: Optional[str] = None` to `_build_location_with_context_prompt()` (around line 2464)
3. Pass `terrain_type` to the prompt format call (around line 2487)

### Step 4: Update game_state.move() to pass terrain

**File: `src/cli_rpg/game_state.py`**

1. In `move()`, pass `terrain` to `expand_area()` call (around line 523)
2. The terrain is already retrieved at line 510: `terrain = self.chunk_manager.get_tile_at(*target_coords)`

### Step 5: Write Tests

**File: `tests/test_terrain_location_coherence.py`** (new file)

```python
"""Tests for terrain-to-location generation coherence."""

import pytest
from unittest.mock import Mock, patch
import json

from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import AIService
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext


@pytest.fixture
def basic_config(tmp_path):
    return AIConfig(
        api_key="test-key",
        model="gpt-3.5-turbo",
        cache_file=str(tmp_path / "cache.json"),
    )


@pytest.fixture
def world_context():
    return WorldContext(
        theme="fantasy",
        theme_essence="A mystical fantasy realm",
        naming_style="Celtic-inspired",
        tone="adventurous",
    )


@pytest.fixture
def region_context():
    return RegionContext(
        name="The Sunbaked Expanse",
        theme="arid desert with ancient ruins",
        danger_level="moderate",
        landmarks=["The Obelisk"],
        coordinates=(10, 10),
    )


class TestTerrainInPrompt:
    """Test that terrain type is included in location generation prompts."""

    @patch("cli_rpg.ai_service.OpenAI")
    def test_terrain_included_in_prompt(
        self, mock_openai_class, basic_config, world_context, region_context
    ):
        """Verify terrain_type appears in the AI prompt."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        valid_response = {
            "name": "Desert Oasis",
            "description": "A refreshing oasis amid the dunes.",
            "connections": {"south": "Caravan Route"},
            "category": "wilderness",
        }
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(valid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_location_with_context(
            world_context=world_context,
            region_context=region_context,
            terrain_type="desert",
        )

        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args[1]["messages"][0]["content"]

        assert "desert" in prompt.lower()

    @patch("cli_rpg.ai_service.OpenAI")
    def test_terrain_none_uses_default(
        self, mock_openai_class, basic_config, world_context, region_context
    ):
        """Verify prompt works when terrain_type is None."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        valid_response = {
            "name": "Mysterious Path",
            "description": "A winding path through unknown lands.",
            "connections": {},
            "category": "wilderness",
        }
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(valid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        # Should not raise with terrain_type=None
        result = service.generate_location_with_context(
            world_context=world_context,
            region_context=region_context,
            terrain_type=None,
        )

        assert result["name"] == "Mysterious Path"
```

**Add integration test to `tests/test_ai_world_generation.py`:**

```python
class TestTerrainPassthrough:
    """Test that terrain is passed through world expansion."""

    @patch("cli_rpg.ai_world.expand_area")
    def test_expand_area_receives_terrain(self, mock_expand_area, ...):
        """Verify expand_area receives terrain_type from move()."""
        # Set up game state with chunk_manager
        # Move to coordinates with known terrain
        # Assert expand_area was called with terrain_type parameter
        pass
```

## Code Changes Summary

| File | Change |
|------|--------|
| `ai_config.py` | Add `{terrain_type}` to `DEFAULT_LOCATION_PROMPT_MINIMAL` |
| `ai_service.py` | Add `terrain_type` param to `generate_location_with_context()` and `_build_location_with_context_prompt()` |
| `ai_world.py` | Add `terrain_type` param to `expand_world()` and `expand_area()` |
| `game_state.py` | Pass `terrain` to `expand_area()` in `move()` |
| `tests/test_terrain_location_coherence.py` | New test file |

## Verification

1. Run existing tests: `pytest tests/test_ai_layered_generation.py -v`
2. Run new tests: `pytest tests/test_terrain_location_coherence.py -v`
3. Run full suite: `pytest`
4. Manual test: Start game with WFC enabled, move to desert tile, verify generated location fits desert theme
