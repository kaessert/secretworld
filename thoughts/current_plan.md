# Wire Layered Context into Location Generation Pipeline

## Problem
AI-generated location content frequently fails with JSON parsing errors, causing fallback to templates. The layered query architecture (WorldContext → RegionContext → Location → NPCs) was implemented but **not wired up** in the main integration point - `game_state.py:move()` calls `expand_area()` without passing the context parameters.

## Current State
- ✅ Models exist: `WorldContext`, `RegionContext` with serialization
- ✅ AIService methods: `generate_world_context()`, `generate_region_context()`, `generate_location_with_context()`, `generate_npcs_for_location()`
- ✅ Prompts defined: `DEFAULT_LOCATION_PROMPT_MINIMAL`, `DEFAULT_NPC_PROMPT_MINIMAL`, etc.
- ✅ GameState has caching: `world_context`, `region_contexts`, helper methods
- ✅ `expand_world()` and `expand_area()` accept context parameters
- ❌ **GAP**: `game_state.py:move()` doesn't pass contexts when calling `expand_area()`

## Implementation Steps

### 1. Update `game_state.py:move()` to pass layered contexts

In `move()` method (~line 575), when calling `expand_area()`, fetch/create contexts first:

```python
# Get layered context for AI generation
world_ctx = self.get_or_create_world_context()
region_ctx = self.get_or_create_region_context(target_coords, terrain or "wilderness")

expand_area(
    world=self.world,
    ai_service=self.ai_service,
    from_location=self.current_location,
    direction=direction,
    theme=self.theme,
    target_coords=target_coords,
    world_context=world_ctx,      # ADD
    region_context=region_ctx,    # ADD
    terrain_type=terrain,
)
```

### 2. Add test for context integration in `tests/test_layered_context_integration.py`

```python
"""Tests for layered context integration in location generation."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext

class TestLayeredContextInMove:
    """Tests that move() passes context to expand_area()."""

    @pytest.fixture
    def mock_chunk_manager(self):
        """Create mock ChunkManager that reports all terrain as passable."""
        cm = MagicMock()
        cm.get_tile_at.return_value = "plains"
        return cm

    @pytest.fixture
    def game_state_with_ai(self, mock_chunk_manager):
        """Create GameState with mock AI service."""
        char = Character(name="Test", class_type="warrior")
        start = Location(name="Start", description="Test", coordinates=(0, 0))
        world = {"Start": start}
        ai_service = MagicMock()
        gs = GameState(char, world, "Start", ai_service=ai_service, theme="fantasy")
        gs.chunk_manager = mock_chunk_manager
        return gs

    @patch("cli_rpg.game_state.expand_area")
    def test_move_passes_world_context_to_expand_area(
        self, mock_expand_area, game_state_with_ai
    ):
        """Verify move() passes world_context when generating new location."""
        gs = game_state_with_ai
        # Pre-create world context
        gs.world_context = WorldContext.default("fantasy")

        # Mock expand_area to create a location (otherwise move fails)
        new_loc = Location(name="New", description="Test", coordinates=(0, 1))
        def side_effect(*args, **kwargs):
            gs.world["New"] = new_loc
        mock_expand_area.side_effect = side_effect

        gs.move("north")

        # Verify expand_area was called with world_context
        mock_expand_area.assert_called_once()
        _, kwargs = mock_expand_area.call_args
        assert "world_context" in kwargs
        assert kwargs["world_context"] is not None

    @patch("cli_rpg.game_state.expand_area")
    def test_move_passes_region_context_to_expand_area(
        self, mock_expand_area, game_state_with_ai
    ):
        """Verify move() passes region_context when generating new location."""
        gs = game_state_with_ai

        new_loc = Location(name="New", description="Test", coordinates=(0, 1))
        def side_effect(*args, **kwargs):
            gs.world["New"] = new_loc
        mock_expand_area.side_effect = side_effect

        gs.move("north")

        mock_expand_area.assert_called_once()
        _, kwargs = mock_expand_area.call_args
        assert "region_context" in kwargs
        assert kwargs["region_context"] is not None
```

### 3. Run tests

```bash
pytest tests/test_layered_context_integration.py -v
pytest tests/test_game_state.py -v -k "move"
pytest -x  # Full suite
```

## Files to Modify
- `src/cli_rpg/game_state.py` - Pass world_context and region_context to `expand_area()`
- `tests/test_layered_context_integration.py` - NEW test file verifying integration

## Expected Outcome
- Location generation uses smaller, focused prompts with context
- Fewer JSON parsing failures (smaller responses = less truncation)
- Better thematic coherence (world/region context informs location names/descriptions)
- Context is cached, so only first generation per region incurs extra API call
