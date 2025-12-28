# Implementation Plan: Integrate Procedural Layout + ContentLayer in generate_subgrid_for_location()

## Summary
Modify `generate_subgrid_for_location()` in `ai_world.py` to use procedural layout generators (`procedural_interiors.py`) + ContentLayer (`content_layer.py`) instead of the existing AI-based or fallback interior generation.

## Current Architecture
- `generate_subgrid_for_location()` (lines 980-1143): Uses AI's `generate_area_with_context()` or `generate_area()` for layout, then `_generate_fallback_interior()` as fallback
- `ContentLayer.populate_subgrid()`: Transforms `RoomTemplate` list -> `SubGrid` with AI or fallback content
- `procedural_interiors.generate_interior_layout()`: Returns `list[RoomTemplate]` based on category

## Target Architecture
1. Generate layout using `generate_interior_layout(category, bounds, seed)`
2. Populate content using `ContentLayer.populate_subgrid(room_templates, ...)`
3. Apply existing post-processing (boss placement, treasures, puzzles, secrets, hazards)

## Implementation Steps

### 1. Add Imports to `ai_world.py`
```python
from cli_rpg.procedural_interiors import generate_interior_layout
from cli_rpg.content_layer import ContentLayer
from cli_rpg.models.generation_context import GenerationContext
```

### 2. Modify `generate_subgrid_for_location()` Signature
Add optional `seed` parameter for deterministic generation:
```python
def generate_subgrid_for_location(
    location: Location,
    ai_service: Optional[AIService],
    theme: str,
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None,
    seed: Optional[int] = None,  # NEW PARAMETER
) -> SubGrid:
```

### 3. Replace Function Body
Key changes:
1. Derive seed from coordinates if not provided (for determinism)
2. Call `generate_interior_layout()` instead of AI's `generate_area_with_context()`
3. Use `ContentLayer.populate_subgrid()` for room content
4. Apply post-processing (secrets, puzzles, hazards, treasures, boss)

### 4. Post-Processing Logic
After ContentLayer populates the SubGrid, iterate over locations to add:
- Hidden secrets via `_generate_secrets_for_location()`
- Environmental storytelling via `get_environmental_details()`
- Puzzles via `_generate_puzzles_for_location()`
- Hazards via `get_hazards_for_category()`
- Treasure distribution via `_place_treasures()`
- Key placement via `_place_keys_in_earlier_rooms()`

### 5. Backward Compatibility
- Existing tests work without `seed` parameter (derives from location.coordinates or random)
- Boss placement, treasure, puzzle tests should pass unchanged
- ContentLayer already handles boss_room and treasure room types

## Files to Modify
1. `src/cli_rpg/ai_world.py` - Main integration (lines 980-1143)

## Tests to Verify
```bash
pytest tests/test_enterable_sublocations.py -v  # Existing SubGrid tests
pytest tests/test_ai_world_treasure.py -v       # Treasure placement
pytest tests/test_ai_puzzle_generation.py -v    # Puzzle generation
pytest tests/test_multi_level_generation.py -v  # Multi-level support
pytest tests/test_environmental_storytelling.py -v  # Env details
```

## Detailed Implementation

```python
def generate_subgrid_for_location(
    location: Location,
    ai_service: Optional[AIService],
    theme: str,
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None,
    seed: Optional[int] = None,
) -> SubGrid:
    """Generate a SubGrid using procedural layout + ContentLayer."""
    from cli_rpg.procedural_interiors import generate_interior_layout
    from cli_rpg.content_layer import ContentLayer

    # 1. Derive seed if not provided
    if seed is None:
        if location.coordinates:
            seed = hash(location.coordinates) & 0x7FFFFFFF
        else:
            seed = random.randint(0, 2**31 - 1)

    # 2. Get bounds from category
    bounds = get_subgrid_bounds(location.category)

    # 3. Generate procedural layout
    room_templates = generate_interior_layout(
        category=location.category or "dungeon",
        bounds=bounds,
        seed=seed,
    )

    # 4. Build generation context
    generation_context = None
    if world_context is not None or region_context is not None:
        from cli_rpg.models.generation_context import GenerationContext
        generation_context = GenerationContext(
            world_context=world_context,
            region_context=region_context,
        )

    # 5. Populate via ContentLayer
    content_layer = ContentLayer()
    sub_grid = content_layer.populate_subgrid(
        room_templates=room_templates,
        parent_location=location,
        ai_service=ai_service,
        generation_context=generation_context,
        seed=seed,
    )

    # 6. Post-processing: secrets, puzzles, hazards, treasures
    placed_locations = {}
    all_keys_to_place = []
    category = location.category or "dungeon"

    for loc in sub_grid.all_locations():
        coords = sub_grid.get_coordinates(loc)
        if coords is None:
            continue
        x, y, z = coords

        placed_locations[loc.name] = {
            "location": loc,
            "relative_coords": (x, y, z),
            "is_entry": loc.is_exit_point,
        }

        if not loc.is_exit_point:
            distance = abs(x) + abs(y)

            # Secrets
            secrets = _generate_secrets_for_location(category, distance, z)
            loc.hidden_secrets.extend(secrets)

            # Environmental storytelling
            from cli_rpg.environmental_storytelling import get_environmental_details
            env_details = get_environmental_details(category, distance, z)
            loc.environmental_details.extend(env_details)

            # Puzzles
            puzzles, blocked, keys = _generate_puzzles_for_location(
                category, distance, z
            )
            loc.puzzles.extend(puzzles)
            loc.blocked_directions.extend(blocked)
            for key_name, key_cat in keys:
                all_keys_to_place.append((key_name, key_cat, distance))

            # Hazards (avoid duplicates)
            from cli_rpg.hazards import get_hazards_for_category
            if not loc.hazards:
                hazards = get_hazards_for_category(category, distance)
                loc.hazards.extend(hazards)

    # Place treasures
    if placed_locations:
        _place_treasures(placed_locations, category)

    # Place keys
    if all_keys_to_place:
        _place_keys_in_earlier_rooms(placed_locations, all_keys_to_place)

    return sub_grid
```
