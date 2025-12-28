# Implementation Plan: Integrate ContentLayer with NPC and Quest Generation

## Summary
Update NPC and quest generation flows to use the ContentLayer pipeline with ContentCache and FallbackContentProvider, completing Phase 5 Step 16 of the Procedural World Generation initiative.

## Context
The ContentLayer already handles room content generation (`generate_room_content()`), but NPC and quest generation in `ai_world.py` still use the old direct-to-AI pattern without leveraging:
- `FallbackContentProvider.get_npc_content()` and `get_quest_content()` for deterministic fallbacks
- `ContentCache` for deterministic caching by coordinates
- Typed request/response models from `content_request.py`

## Current State
- `ai_world._create_npcs_from_data()` takes AI-parsed NPC dicts directly
- `ai_world._generate_quest_for_npc()` calls `AIService.generate_quest()` directly
- No fallback path when AI is unavailable - NPCs/quests simply aren't generated
- No coordinate-based caching for deterministic NPC/quest content

## Spec
Add NPC and quest generation methods to ContentLayer that:
1. Try AI generation if available
2. Fall back to FallbackContentProvider on failure
3. Use ContentCache for deterministic keying

## Implementation Steps

### Step 1: Add NPC generation method to ContentLayer

**File**: `src/cli_rpg/content_layer.py`

Add `generate_npc_content()` method:
```python
def generate_npc_content(
    self,
    role: str,
    category: str,
    coords: tuple[int, int, int],
    ai_service: Optional["AIService"],
    generation_context: Optional["GenerationContext"],
    seed: int,
) -> dict:
    """Generate NPC name, description, and dialogue.

    Tries AI first, falls back to FallbackContentProvider.
    """
```

### Step 2: Add quest generation method to ContentLayer

**File**: `src/cli_rpg/content_layer.py`

Add `generate_quest_content()` method:
```python
def generate_quest_content(
    self,
    category: str,
    coords: tuple[int, int, int],
    ai_service: Optional["AIService"],
    generation_context: Optional["GenerationContext"],
    seed: int,
    npc_name: str = "",
    valid_locations: Optional[set[str]] = None,
    valid_npcs: Optional[set[str]] = None,
) -> Optional[dict]:
    """Generate quest name, description, and objectives.

    Tries AI first, falls back to FallbackContentProvider.
    """
```

### Step 3: Add NPC population to ContentLayer.populate_subgrid()

**File**: `src/cli_rpg/content_layer.py`

Extend `_create_location_from_template()` to optionally generate NPCs for settlement categories:
- Use role distribution based on room type (quest_giver in CHAMBER, merchant in ENTRY for towns)
- Call `generate_npc_content()` for each NPC

### Step 4: Update ai_world.py to use ContentLayer for SubGrid NPCs

**File**: `src/cli_rpg/ai_world.py`

Modify `generate_subgrid_for_location()` to pass NPC generation through ContentLayer pipeline instead of direct AI calls.

### Step 5: Write integration tests

**File**: `tests/test_content_layer_npc_quest.py`

Tests:
1. ContentLayer generates NPCs with fallback when AI unavailable
2. ContentLayer generates quests with fallback when AI unavailable
3. Same seed produces identical NPC content (determinism)
4. Same seed produces identical quest content (determinism)
5. AI-generated NPC content used when available
6. AI-generated quest content used when available

## Files to Modify
- `src/cli_rpg/content_layer.py` - Add NPC/quest generation methods
- `src/cli_rpg/ai_world.py` - Use ContentLayer for SubGrid NPCs (optional, for full integration)

## Files to Create
- `tests/test_content_layer_npc_quest.py` - Integration tests

## Test Commands
```bash
# Run new tests
pytest tests/test_content_layer_npc_quest.py -v

# Run related tests to ensure no regression
pytest tests/test_content_layer.py tests/test_fallback_content.py -v

# Run full suite
pytest tests/ -v
```

## Implementation Details

### ContentLayer.generate_npc_content()

```python
def generate_npc_content(
    self,
    role: str,
    category: str,
    coords: tuple[int, int, int],
    ai_service: Optional["AIService"],
    generation_context: Optional["GenerationContext"],
    rng: random.Random,
) -> dict:
    """Generate NPC name, description, and dialogue.

    Args:
        role: NPC role (merchant, guard, quest_giver, villager, etc.)
        category: Location category for context
        coords: 3D coordinates for deterministic seeding
        ai_service: Optional AI service for content generation
        generation_context: Optional context for AI generation
        rng: Random number generator for determinism

    Returns:
        Dict with 'name', 'description', 'dialogue' keys
    """
    # TODO: Add AI generation path when AIService has generate_npc_content()
    # For now, use fallback directly

    # Fallback to procedural names using FallbackContentProvider
    provider = FallbackContentProvider(seed=rng.randint(0, 2**31))
    return provider.get_npc_content(role, category)
```

### ContentLayer.generate_quest_content()

```python
def generate_quest_content(
    self,
    category: str,
    coords: tuple[int, int, int],
    ai_service: Optional["AIService"],
    generation_context: Optional["GenerationContext"],
    rng: random.Random,
    npc_name: str = "",
    valid_locations: Optional[set[str]] = None,
    valid_npcs: Optional[set[str]] = None,
) -> Optional[dict]:
    """Generate quest name, description, and objectives.

    Args:
        category: Location category for thematic quests
        coords: 3D coordinates for deterministic seeding
        ai_service: Optional AI service for content generation
        generation_context: Optional context for AI generation
        rng: Random number generator for determinism
        npc_name: Name of quest-giving NPC for context
        valid_locations: Optional set of valid location names for EXPLORE quests
        valid_npcs: Optional set of valid NPC names for TALK quests

    Returns:
        Dict with 'name', 'description', 'objective_type', 'target' keys,
        or None if generation fails
    """
    # Try AI generation if available
    if ai_service is not None and generation_context is not None:
        try:
            world_context = generation_context.world
            region_context = generation_context.region
            theme = world_context.theme if world_context else "fantasy"

            quest_data = ai_service.generate_quest(
                theme=theme,
                npc_name=npc_name,
                player_level=1,
                location_name="",
                valid_locations=valid_locations,
                valid_npcs=valid_npcs,
                world_context=world_context,
                region_context=region_context,
            )
            return quest_data
        except Exception as e:
            logger.debug(f"AI quest generation failed: {e}")

    # Fallback to FallbackContentProvider
    provider = FallbackContentProvider(seed=rng.randint(0, 2**31))
    return provider.get_quest_content(category)
```

## Success Criteria
1. All 5195+ existing tests continue to pass
2. New tests for ContentLayer NPC/quest generation pass
3. SubGrid locations can generate NPCs/quests without AI available
4. Same seed produces identical NPC/quest content
5. AI-generated content is used when available

## Notes
- This is a non-breaking change - existing code paths continue to work
- Full integration with `ai_world.py` is optional for this increment
- ContentCache integration can be added in a follow-up for coordinate-based caching
