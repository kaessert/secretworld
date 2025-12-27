# Plan: Enforce Natural Terrain Transitions in WFC Generation

## Summary
Integrate `NATURAL_TRANSITIONS` into WFC collapse to actively penalize unnatural terrain transitions (e.g., forest→desert) during generation, creating smoother biome gradients.

## Scope
**MEDIUM task** - Enhancing existing WFC distance penalty system to use `NATURAL_TRANSITIONS` data.

## Background

The codebase already has:
- `NATURAL_TRANSITIONS` dict defining which terrains can naturally border each other
- `is_natural_transition()` function for checking transition validity
- `get_distance_penalty()` function using `BIOME_GROUPS` and `INCOMPATIBLE_GROUPS`
- Both `wfc.py` and `wfc_chunks.py` use `get_distance_penalty()` during collapse

**Gap**: The distance penalty only considers biome group incompatibility (temperate vs arid), not the more granular `NATURAL_TRANSITIONS` data. For example:
- `get_distance_penalty("mountain", {"beach"})` returns 1.0 (no penalty) because both are in compatible groups (alpine/aquatic aren't in `INCOMPATIBLE_GROUPS`)
- But `is_natural_transition("mountain", "beach")` returns False because mountains don't naturally border beaches

## Spec

Enhance `get_distance_penalty()` to also check `NATURAL_TRANSITIONS`:
1. If terrain's group conflicts with nearby groups → 0.01x penalty (existing behavior)
2. If terrain is NOT in `NATURAL_TRANSITIONS` of ANY nearby terrain → apply moderate penalty (0.3x)
3. Otherwise → no penalty (1.0x)

This creates a two-tier penalty system:
- **Severe (0.01x)**: Biome group conflicts (forest near desert)
- **Moderate (0.3x)**: Unnatural direct adjacency (mountain next to beach)

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/world_tiles.py` | Update `get_distance_penalty()` to check `NATURAL_TRANSITIONS` |
| `tests/test_terrain_transitions.py` | Add tests for enhanced penalty calculation |

## Implementation Steps

### 1. Update `get_distance_penalty()` in `world_tiles.py`

Location: Lines 169-191

Current implementation only checks `INCOMPATIBLE_GROUPS`. Enhance to also check `NATURAL_TRANSITIONS`:

```python
def get_distance_penalty(terrain: str, nearby_terrains: Set[str]) -> float:
    """Calculate weight penalty based on nearby incompatible biomes.

    When collapsing a WFC cell, this function determines if the terrain type
    should receive a weight penalty based on incompatible biomes nearby.

    Two levels of penalty:
    - Severe (0.01): Biome group incompatibility (temperate near arid)
    - Moderate (0.3): Unnatural direct adjacency (mountain near beach)

    Args:
        terrain: The terrain type being considered for collapse
        nearby_terrains: Set of terrain types within penalty radius

    Returns:
        Multiplier (1.0 = no penalty, 0.3 = moderate penalty, 0.01 = severe penalty)
    """
    terrain_group = BIOME_GROUPS.get(terrain)
    if terrain_group == "neutral":
        return 1.0  # Neutral terrain is never penalized

    # Check for biome group incompatibility (severe penalty)
    for nearby in nearby_terrains:
        nearby_group = BIOME_GROUPS.get(nearby)
        if (terrain_group, nearby_group) in INCOMPATIBLE_GROUPS:
            return 0.01  # 99% weight reduction (very strong penalty)

    # Check for unnatural adjacency (moderate penalty)
    terrain_natural = NATURAL_TRANSITIONS.get(terrain, set())
    for nearby in nearby_terrains:
        # If terrain can't naturally border this nearby terrain
        if nearby not in terrain_natural:
            # Also check reverse (symmetric check)
            nearby_natural = NATURAL_TRANSITIONS.get(nearby, set())
            if terrain not in nearby_natural:
                return 0.3  # 70% weight reduction (moderate penalty)

    return 1.0
```

### 2. Add tests in `tests/test_terrain_transitions.py`

Add new test class after `TestTransitionWeightPenalty`:

```python
class TestNaturalTransitionPenalty:
    """Tests for NATURAL_TRANSITIONS integration in get_distance_penalty()."""

    def test_mountain_near_beach_gets_moderate_penalty(self):
        """Mountains near beaches get 0.3x penalty (unnatural adjacency)."""
        assert get_distance_penalty("mountain", {"beach"}) == 0.3
        assert get_distance_penalty("beach", {"mountain"}) == 0.3

    def test_mountain_near_swamp_gets_moderate_penalty(self):
        """Mountains near swamps get 0.3x penalty."""
        assert get_distance_penalty("mountain", {"swamp"}) == 0.3

    def test_water_near_desert_gets_moderate_penalty(self):
        """Water near desert gets 0.3x penalty."""
        assert get_distance_penalty("water", {"desert"}) == 0.3

    def test_natural_transition_no_penalty(self):
        """Natural transitions get no penalty."""
        # Forest near plains is natural
        assert get_distance_penalty("forest", {"plains"}) == 1.0
        # Mountain near foothills is natural
        assert get_distance_penalty("mountain", {"foothills"}) == 1.0
        # Beach near water is natural
        assert get_distance_penalty("beach", {"water"}) == 1.0

    def test_biome_conflict_trumps_natural_check(self):
        """Biome group conflicts still return 0.01 (more severe than 0.3)."""
        # Forest near desert is both unnatural AND group-incompatible
        assert get_distance_penalty("forest", {"desert"}) == 0.01

    def test_mixed_nearby_returns_worst_penalty(self):
        """When multiple nearby terrains, return worst applicable penalty."""
        # Forest near plains (natural) and desert (incompatible group)
        assert get_distance_penalty("forest", {"plains", "desert"}) == 0.01
        # Mountain near foothills (natural) and beach (unnatural but not incompatible)
        assert get_distance_penalty("mountain", {"foothills", "beach"}) == 0.3
```

## Verification

Run tests:
```bash
pytest tests/test_terrain_transitions.py -v
```

Expected: All tests pass, including new tests for natural transition penalties.

## Impact

After this change:
- Mountains won't appear directly next to beaches (0.3x penalty → rare but not impossible)
- Swamps won't border water directly (0.3x penalty)
- Natural gradients will be enforced: forest → plains → desert instead of forest → desert
- Biome group conflicts remain severely penalized (0.01x)

The 0.3x penalty is moderate enough to allow occasional edge cases while strongly discouraging them.
