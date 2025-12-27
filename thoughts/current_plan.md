# Plan: Natural Terrain Transition Validation

## Summary
Add terrain transition validation to prevent abrupt biome jumps (e.g., forest directly adjacent to desert) by extending the existing `BIOME_GROUPS` and `INCOMPATIBLE_GROUPS` system with a public API for checking transition naturalness.

## Scope
**MEDIUM task** - Adding a validation function and enhancing the existing biome compatibility system.

## Spec

The existing `world_tiles.py` already has:
- `BIOME_GROUPS` dict mapping terrain types to biome categories (temperate, arid, alpine, aquatic, neutral)
- `INCOMPATIBLE_GROUPS` set of conflicting biome pairs (temperate<->arid)
- `get_distance_penalty()` function used during WFC collapse

**New additions:**
1. `NATURAL_TRANSITIONS` dict - defines which terrain types can naturally transition to each other
2. `is_natural_transition(from_terrain, to_terrain)` function - public API for checking transition validity
3. `get_transition_warning(from_terrain, to_terrain)` function - returns warning message for unnatural transitions

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/world_tiles.py` | Add `NATURAL_TRANSITIONS`, `is_natural_transition()`, `get_transition_warning()` |
| `tests/test_terrain_transitions.py` | NEW - Test all transition validation logic |

## Implementation Steps

### 1. Add `NATURAL_TRANSITIONS` dict to `world_tiles.py`
Location: After `INCOMPATIBLE_GROUPS` (~line 149)

```python
# Natural terrain transitions - which terrains flow naturally into each other
# Based on geographic realism: forests border plains, not deserts
# Key = terrain type, Value = set of terrains it can naturally border
NATURAL_TRANSITIONS: Dict[str, Set[str]] = {
    "forest": {"forest", "plains", "hills", "swamp", "foothills"},  # Temperate transitions
    "plains": {"plains", "forest", "hills", "desert", "beach", "foothills"},  # Universal connector
    "hills": {"hills", "forest", "plains", "mountain", "foothills", "desert"},  # Elevation transitions
    "mountain": {"mountain", "hills", "foothills"},  # Alpine only
    "foothills": {"foothills", "hills", "mountain", "plains", "forest"},  # Bridge terrain
    "desert": {"desert", "plains", "hills", "beach"},  # Arid transitions
    "swamp": {"swamp", "forest", "water", "plains"},  # Wetland transitions
    "water": {"water", "beach", "swamp"},  # Aquatic transitions
    "beach": {"beach", "water", "plains", "forest", "desert"},  # Coastal transitions
}
```

Note: This differs from `ADJACENCY_RULES` which is more permissive for WFC flexibility. `NATURAL_TRANSITIONS` represents what "feels right" geographically.

### 2. Add `is_natural_transition()` function
Location: After `get_distance_penalty()` (~line 175)

```python
def is_natural_transition(from_terrain: str, to_terrain: str) -> bool:
    """Check if transitioning between two terrain types feels natural.

    Uses NATURAL_TRANSITIONS to determine if terrain A can naturally
    border terrain B. Symmetric - if A->B is natural, B->A is also natural.

    Args:
        from_terrain: Source terrain type
        to_terrain: Target terrain type

    Returns:
        True if the transition is natural, False if jarring
    """
    # Same terrain is always natural
    if from_terrain == to_terrain:
        return True

    # Check if to_terrain is in from_terrain's natural neighbors
    natural_neighbors = NATURAL_TRANSITIONS.get(from_terrain, set())
    if to_terrain in natural_neighbors:
        return True

    # Check reverse (symmetric transitions)
    reverse_neighbors = NATURAL_TRANSITIONS.get(to_terrain, set())
    return from_terrain in reverse_neighbors
```

### 3. Add `get_transition_warning()` function
Location: After `is_natural_transition()`

```python
def get_transition_warning(from_terrain: str, to_terrain: str) -> Optional[str]:
    """Get a warning message for unnatural terrain transitions.

    Args:
        from_terrain: Source terrain type
        to_terrain: Target terrain type

    Returns:
        Warning message string if transition is unnatural, None if natural
    """
    if is_natural_transition(from_terrain, to_terrain):
        return None

    return f"Unnatural terrain transition: {from_terrain} -> {to_terrain}"
```

### 4. Create `tests/test_terrain_transitions.py`

```python
"""Tests for terrain transition validation."""

import pytest
from cli_rpg.world_tiles import (
    NATURAL_TRANSITIONS,
    is_natural_transition,
    get_transition_warning,
    TerrainType,
)


class TestNaturalTransitionsDict:
    """Tests for NATURAL_TRANSITIONS data structure."""

    def test_all_terrain_types_have_entries(self):
        """Every TerrainType has an entry in NATURAL_TRANSITIONS."""
        for terrain in TerrainType:
            assert terrain.value in NATURAL_TRANSITIONS

    def test_self_transitions_allowed(self):
        """Every terrain can transition to itself."""
        for terrain in TerrainType:
            assert terrain.value in NATURAL_TRANSITIONS[terrain.value]

    def test_transitions_are_symmetric(self):
        """If A->B is natural, B->A should also be natural."""
        for terrain, neighbors in NATURAL_TRANSITIONS.items():
            for neighbor in neighbors:
                assert terrain in NATURAL_TRANSITIONS.get(neighbor, set()), \
                    f"{terrain}->{neighbor} allowed but {neighbor}->{terrain} not"


class TestIsNaturalTransition:
    """Tests for is_natural_transition() function."""

    def test_same_terrain_always_natural(self):
        """Transitioning to same terrain is always natural."""
        for terrain in TerrainType:
            assert is_natural_transition(terrain.value, terrain.value)

    def test_forest_to_plains_natural(self):
        """Forest borders plains naturally."""
        assert is_natural_transition("forest", "plains")
        assert is_natural_transition("plains", "forest")

    def test_forest_to_desert_unnatural(self):
        """Forest directly adjacent to desert is jarring."""
        assert not is_natural_transition("forest", "desert")
        assert not is_natural_transition("desert", "forest")

    def test_mountain_to_beach_unnatural(self):
        """Mountains don't border beaches."""
        assert not is_natural_transition("mountain", "beach")

    def test_swamp_to_desert_unnatural(self):
        """Wetlands don't border arid terrain."""
        assert not is_natural_transition("swamp", "desert")

    def test_plains_bridges_forest_to_desert(self):
        """Plains can connect otherwise incompatible biomes."""
        assert is_natural_transition("forest", "plains")
        assert is_natural_transition("plains", "desert")

    def test_foothills_bridges_plains_to_mountain(self):
        """Foothills provide natural elevation transition."""
        assert is_natural_transition("plains", "foothills")
        assert is_natural_transition("foothills", "mountain")

    def test_unknown_terrain_returns_false(self):
        """Unknown terrain types return False (safe default)."""
        assert not is_natural_transition("lava", "forest")
        assert not is_natural_transition("forest", "void")


class TestGetTransitionWarning:
    """Tests for get_transition_warning() function."""

    def test_natural_transition_returns_none(self):
        """No warning for natural transitions."""
        assert get_transition_warning("forest", "plains") is None
        assert get_transition_warning("hills", "mountain") is None

    def test_unnatural_transition_returns_message(self):
        """Warning message for unnatural transitions."""
        warning = get_transition_warning("forest", "desert")
        assert warning is not None
        assert "forest" in warning
        assert "desert" in warning

    def test_same_terrain_no_warning(self):
        """No warning when transitioning to same terrain."""
        assert get_transition_warning("forest", "forest") is None
```

## Verification

Run tests:
```bash
pytest tests/test_terrain_transitions.py -v
```

Expected: All tests pass, validating that:
1. `NATURAL_TRANSITIONS` covers all terrain types
2. `is_natural_transition()` correctly identifies jarring transitions
3. `get_transition_warning()` provides useful feedback

## Future Use

This validation API can be used by:
1. **Map renderer** - Show warnings when displaying the map
2. **WFC chunk generation** - Add stronger penalties for unnatural transitions
3. **Debug tools** - Validate generated worlds for coherence issues
4. **Region planning** - Ensure region themes don't create jarring borders
