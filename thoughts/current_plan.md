# Implementation Plan: Cluster Similar Locations Together

## Spec Summary
When generating named locations (POIs), cluster similar location types together spatially. This means that settlements should spawn near other settlements, dungeon entrances near other dungeons, etc., rather than being scattered randomly.

## Design Approach

**Core Idea**: When `should_generate_named_location()` returns True and we're about to generate a named location, bias the **location category** selection based on nearby existing named locations of similar types.

### Location Category Groupings
Similar location types that should cluster together:

| Cluster Group | Location Categories |
|--------------|---------------------|
| Settlements | village, town, city, settlement |
| Dungeons | dungeon, cave, ruins |
| Wilderness POIs | forest, wilderness, grove |
| Sacred Sites | temple, shrine, monastery |
| Commerce | shop, tavern, inn, merchant_camp |

### Implementation Strategy

1. **Track named location positions**: Use existing `world` dictionary which has coordinates
2. **Detect nearby similar locations**: When generating a new named location, check for existing named locations within a radius and their categories
3. **Bias category selection**: If there are nearby named locations, weight towards generating the same category
4. **Apply in fallback generation**: Modify `generate_fallback_location()` to accept optional category bias
5. **Apply in AI generation**: Pass category hint to expand_area when clustering applies

## Implementation Steps

### 1. Define clustering constants in `world_tiles.py`

```python
# Location category clustering groups
LOCATION_CLUSTER_GROUPS: Dict[str, str] = {
    # Settlements
    "village": "settlements",
    "town": "settlements",
    "city": "settlements",
    "settlement": "settlements",
    # Dungeons
    "dungeon": "dungeons",
    "cave": "dungeons",
    "ruins": "dungeons",
    # Wilderness POIs
    "forest": "wilderness_pois",
    "wilderness": "wilderness_pois",
    "grove": "wilderness_pois",
    # Sacred
    "temple": "sacred",
    "shrine": "sacred",
    "monastery": "sacred",
    # Commerce
    "shop": "commerce",
    "tavern": "commerce",
    "inn": "commerce",
}

# Cluster radius in world tiles
CLUSTER_RADIUS = 10

# Probability of clustering (vs generating any random type)
CLUSTER_PROBABILITY = 0.6
```

### 2. Add clustering helper function in `world_tiles.py`

```python
def get_cluster_category_bias(
    world: Dict[str, Location],
    target_coords: Tuple[int, int],
    radius: int = CLUSTER_RADIUS,
    rng: Optional[random.Random] = None,
) -> Optional[str]:
    """Determine if new location should cluster with nearby similar locations.

    Scans for named locations within radius and returns a category bias
    if clustering should occur.

    Args:
        world: World dictionary with locations
        target_coords: Coordinates for new location
        radius: Search radius for nearby named locations
        rng: Optional RNG for determinism

    Returns:
        Category string to bias towards, or None if no clustering
    """
```

### 3. Integrate into `game_state.py` move() method

In the section where `generate_named = True`:
- Before calling `generate_fallback_location()` or `expand_area()`, call `get_cluster_category_bias()`
- Pass the bias as a hint to the generation functions

### 4. Modify `generate_fallback_location()` in `world.py`

Add optional `category_hint` parameter:
- If provided and matches a terrain template, prefer that template
- Ensures fallback generation respects clustering

### 5. Modify AI prompt/expand_area in `ai_world.py`

Add optional `category_hint` parameter to `expand_area()`:
- Include hint in AI prompt to guide location category generation

## Test Plan

### Unit Tests (in `tests/test_location_clustering.py`)

1. **test_cluster_groups_defined**: Verify LOCATION_CLUSTER_GROUPS contains expected mappings
2. **test_get_cluster_category_bias_no_nearby**: Returns None when no named locations nearby
3. **test_get_cluster_category_bias_finds_nearby**: Returns category when similar location within radius
4. **test_get_cluster_category_bias_respects_probability**: Clustering happens ~60% of time
5. **test_get_cluster_category_bias_radius_boundary**: Location at exactly radius edge counts
6. **test_get_cluster_category_bias_outside_radius**: Location beyond radius ignored
7. **test_generate_fallback_respects_category_hint**: Verify fallback uses hint when provided
8. **test_cluster_groups_cover_common_categories**: Verify all common categories are mapped

### Integration Tests

9. **test_move_applies_clustering_bias**: Verify move() passes bias to generation
10. **test_clustering_persists_patterns**: Verify multiple moves create clustered patterns

## Files to Modify

1. `src/cli_rpg/world_tiles.py` - Add constants and `get_cluster_category_bias()`
2. `src/cli_rpg/world.py` - Add `category_hint` param to `generate_fallback_location()`
3. `src/cli_rpg/game_state.py` - Call clustering logic before named location generation
4. `src/cli_rpg/ai_world.py` - Add `category_hint` to `expand_area()` (optional enhancement)
5. `tests/test_location_clustering.py` - New test file

## Implementation Order

1. Add constants and `get_cluster_category_bias()` to `world_tiles.py`
2. Write unit tests for the new function
3. Add `category_hint` to `generate_fallback_location()`
4. Integrate into `game_state.py` move() method
5. Write integration tests
6. (Optional) Add to AI prompt in `expand_area()`
