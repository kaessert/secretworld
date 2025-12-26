# Implementation Plan: Complete Layered AI Query Architecture (Steps 6-7)

## Spec

Complete the layered AI query architecture by:
1. Refactoring `generate_location()` to accept layered contexts (world/region) and use the minimal prompt
2. Adding `generate_npcs_for_location()` as a separate API call (Layer 4)
3. Caching WorldContext and RegionContext in GameState
4. Wiring up context caching in world generation flow

## Implementation Steps

### Step 1: Add `generate_location_with_context()` to AIService

**File:** `src/cli_rpg/ai_service.py`

Add new method that uses layered contexts:

```python
def generate_location_with_context(
    self,
    world_context: WorldContext,
    region_context: RegionContext,
    source_location: Optional[str] = None,
    direction: Optional[str] = None
) -> dict:
```

- Uses `location_prompt_minimal` template from config
- Returns dict with: name, description, connections, category (no NPCs)
- Add `_build_location_with_context_prompt()` helper
- Reuse `_parse_location_response()` (already handles optional npcs field)

### Step 2: Add `generate_npcs_for_location()` to AIService

**File:** `src/cli_rpg/ai_service.py`

Add new method for Layer 4 NPC generation:

```python
def generate_npcs_for_location(
    self,
    world_context: WorldContext,
    location_name: str,
    location_description: str,
    location_category: Optional[str] = None
) -> list[dict]:
```

- Uses `npc_prompt_minimal` template from config
- Returns list of NPC dicts: [{name, description, dialogue, role}]
- Add `_build_npc_prompt()` and `_parse_npc_only_response()` methods

### Step 3: Add context caching to GameState

**File:** `src/cli_rpg/game_state.py`

Add imports:
```python
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
```

Add attributes in `__init__`:
```python
self.world_context: Optional[WorldContext] = None
self.region_contexts: dict[tuple[int, int], RegionContext] = {}
```

Add methods:
```python
def get_or_create_world_context(self) -> WorldContext:
    """Get cached world context or generate/create default."""

def get_or_create_region_context(self, coords: tuple[int, int], terrain_hint: str = "wilderness") -> RegionContext:
    """Get cached region context or generate/create default."""
```

Update `to_dict()`:
- Add `world_context` serialization
- Add `region_contexts` serialization

Update `from_dict()`:
- Restore `world_context`
- Restore `region_contexts`

### Step 4: Wire up contexts in ai_world.py

**File:** `src/cli_rpg/ai_world.py`

Modify `expand_world()`:
- Accept optional `world_context: Optional[WorldContext]` parameter
- Accept optional `region_context: Optional[RegionContext]` parameter
- When contexts provided, use `ai_service.generate_location_with_context()`
- Call `ai_service.generate_npcs_for_location()` separately after location created

Modify `expand_area()`:
- Same pattern as `expand_world()`

## Test Plan

### Test file: `tests/test_ai_layered_generation.py`

```python
def test_generate_location_with_context_returns_valid_structure():
    """Test generate_location_with_context returns location without NPCs."""

def test_generate_location_with_context_uses_minimal_prompt():
    """Test that minimal prompt template is used with context."""

def test_generate_npcs_for_location_returns_valid_npcs():
    """Test generate_npcs_for_location returns list of valid NPCs."""

def test_generate_npcs_for_location_handles_empty_response():
    """Test empty NPC list is valid."""

def test_parse_npc_only_response_validates_fields():
    """Test NPC field validation."""
```

### Test file: `tests/test_game_state_context.py`

```python
def test_get_or_create_world_context_returns_default_without_ai():
    """Test fallback to default when no AI service."""

def test_get_or_create_world_context_caches_result():
    """Test world context is cached after first call."""

def test_get_or_create_region_context_caches_by_coords():
    """Test region contexts cached by coordinate tuple."""

def test_world_context_serialized_in_to_dict():
    """Test world_context included in save data."""

def test_region_contexts_serialized_in_to_dict():
    """Test region_contexts included in save data."""

def test_contexts_restored_from_dict():
    """Test contexts properly restored on load."""
```

## Files to Modify

1. `src/cli_rpg/ai_service.py` - Add `generate_location_with_context()`, `generate_npcs_for_location()`, helper methods
2. `src/cli_rpg/game_state.py` - Add `world_context`, `region_contexts`, `get_or_create_*` methods, update serialization
3. `src/cli_rpg/ai_world.py` - Wire up contexts in `expand_world()` and `expand_area()`
4. `tests/test_ai_layered_generation.py` - NEW: Tests for layered generation methods
5. `tests/test_game_state_context.py` - NEW: Tests for context caching in GameState
