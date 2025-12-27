# Implementation Plan: Unified GenerationContext (Issue 5)

## Overview
Create a `GenerationContext` aggregator dataclass that combines all 6 context layers for prompt generation. This enables AI generation methods to access all available context through a single object with a unified `to_prompt_context()` method.

---

## 1. Create GenerationContext Model

**File**: `src/cli_rpg/models/generation_context.py`

```python
@dataclass
class GenerationContext:
    world: WorldContext                          # Layer 1 - always required
    region: Optional[RegionContext] = None       # Layer 2
    settlement: Optional[SettlementContext] = None  # Layer 5
    world_lore: Optional[LoreContext] = None     # Layer 6 (world-level)
    region_lore: Optional[LoreContext] = None    # Layer 6 (region-level)

    def to_prompt_context(self) -> dict:
        """Aggregate all layers into prompt-ready dict."""

    def to_dict(self) -> dict:
        """Serialize for save/load."""

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationContext":
        """Deserialize from save data."""
```

**Key fields in `to_prompt_context()` output**:
- `theme`, `theme_essence`, `naming_style`, `tone` (from WorldContext)
- `region_name`, `region_theme`, `danger_level`, `landmarks` (from RegionContext)
- `settlement_name`, `government_type`, `population_size`, `notable_families` (from SettlementContext)
- `historical_events`, `legendary_items`, `prophecies`, `deities` (from LoreContext)

---

## 2. Add Tests for GenerationContext

**File**: `tests/test_generation_context.py`

Tests to add:
1. `test_creation_with_world_only` - Minimal context
2. `test_creation_with_all_layers` - Full context
3. `test_to_prompt_context_world_only` - Verify output structure
4. `test_to_prompt_context_full` - All layers in output
5. `test_to_dict_serialization` - Round-trip serialization
6. `test_from_dict_deserialization` - Backward compatibility
7. `test_optional_layers_none` - Handle None gracefully

---

## 3. Add `get_generation_context()` to GameState

**File**: `src/cli_rpg/game_state.py`

```python
def get_generation_context(
    self,
    coords: Optional[tuple[int, int]] = None,
    settlement_name: Optional[str] = None,
) -> GenerationContext:
    """Build GenerationContext from cached layers.

    Args:
        coords: Coordinates for region lookup (defaults to current location)
        settlement_name: Name for settlement context lookup (if applicable)

    Returns:
        GenerationContext with available layers populated
    """
```

Logic:
1. Get/create WorldContext (always present)
2. Get/create RegionContext if coords provided
3. Lookup SettlementContext from cache if settlement_name provided
4. Lookup LoreContext (world/region) from caches if available
5. Return assembled GenerationContext

---

## 4. Integration Points (Future)

The GenerationContext will be passed to:
- `generate_enemy_with_context(context, location, level)` - Use region creatures
- `generate_item_with_context(context, location, level)` - Use region resources
- `generate_quest()` - Validate difficulty against danger_level
- `generate_settlement_context()` - Layer 5 generation
- `generate_lore_context()` - Layer 6 generation

**Note**: AI service integration is deferred to future work. This plan creates only the model and accessor.

---

## Implementation Order

1. Create `src/cli_rpg/models/generation_context.py` with dataclass
2. Create `tests/test_generation_context.py` with unit tests
3. Add import and `get_generation_context()` method to `game_state.py`
4. Run tests to verify: `pytest tests/test_generation_context.py -v`

---

## Files to Create
- `src/cli_rpg/models/generation_context.py`
- `tests/test_generation_context.py`

## Files to Modify
- `src/cli_rpg/game_state.py` - Add import and `get_generation_context()` method
