# Environmental Storytelling for Dungeon Interiors

## Overview
Add environmental storytelling elements (corpses, bloodstains, journals) to SubGrid location descriptions. This addresses Issue 27's "Environmental storytelling" acceptance criteria and also touches on the "Environmental storytelling" item in the Secrets issue.

## Spec
- Non-entry SubGrid rooms in dungeon/cave/ruins/temple categories get 0-2 environmental details
- Details are selected from category-specific pools and distance-scaled (deeper = darker)
- Details appear in location descriptions after the main description
- 40% base chance, scaling with distance from entry

### Environmental Detail Types
1. **Corpses**: Previous adventurer remains with thematic descriptions
2. **Bloodstains**: Combat evidence, aged or fresh
3. **Journals/Notes**: Fragmentary lore hints, warnings from past explorers

### Category-Specific Pools
- **Dungeon**: Skeletal prisoners, tortured victims, desperate messages scratched on walls
- **Cave**: Mauled hunters, trapped explorers, mineral-stained bones
- **Ruins**: Ancient corpses, preserved by magic or decay, stone tablets with warnings
- **Temple**: Sacrificial victims, corrupted priests, profane scripture

## Implementation

### 1. Create environmental_storytelling.py module
Location: `src/cli_rpg/environmental_storytelling.py`

```python
STORYTELLING_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple"})
BASE_STORYTELLING_CHANCE = 0.40

ENVIRONMENTAL_DETAILS = {
    "dungeon": [
        {"type": "corpse", "desc": "A skeleton slumps against the wall, rusted chains still binding its wrists."},
        {"type": "corpse", "desc": "The remains of an adventurer lie here, their sword still gripped in bony fingers."},
        {"type": "bloodstain", "desc": "Dark stains splatter across the floor, long since dried."},
        {"type": "bloodstain", "desc": "A trail of dried blood leads to a dark corner."},
        {"type": "journal", "desc": "A torn page reads: 'The deeper we go, the worse the whispers get...'"},
        {"type": "journal", "desc": "Scratched into the stone: 'DON'T TRUST THE SHADOWS'"},
    ],
    # ... more categories
}
```

### 2. Add function to generate storytelling elements
```python
def get_environmental_details(category: str, distance: int = 0, z_level: int = 0) -> list[str]:
    """Generate 0-2 environmental storytelling elements for a location."""
```

### 3. Integrate into ai_world.py
In `generate_subgrid_for_location()` and `expand_area()`, call `get_environmental_details()` for non-entry rooms and store in a new `Location.environmental_details` field.

### 4. Update Location model
Add `environmental_details: List[str]` field to Location dataclass with serialization.

### 5. Update location display
Modify `get_layered_description()` to include environmental details after description.

## Test Plan
File: `tests/test_environmental_storytelling.py`

1. **test_get_environmental_details_returns_list** - Returns list of 0-2 strings
2. **test_storytelling_categories_get_details** - dungeon/cave/ruins/temple get details
3. **test_non_storytelling_categories_empty** - town/village return empty list
4. **test_distance_scaling** - Further from entry = higher chance
5. **test_depth_scaling** - Deeper z-level = higher chance
6. **test_dungeon_details_thematic** - Details match dungeon theme
7. **test_cave_details_thematic** - Details match cave theme
8. **test_location_serialization** - environmental_details serializes correctly
9. **test_location_description_includes_details** - Details appear in display
10. **test_integration_with_subgrid_generation** - SubGrid rooms get details

## Files to Modify
- `src/cli_rpg/environmental_storytelling.py` (NEW)
- `src/cli_rpg/models/location.py` - Add `environmental_details` field
- `src/cli_rpg/ai_world.py` - Integrate detail generation
- `tests/test_environmental_storytelling.py` (NEW)

## Acceptance Criteria
- [x] Environmental details appear in non-entry SubGrid rooms
- [x] Details are category-appropriate (dungeon ≠ cave ≠ temple)
- [x] Distance/depth scaling affects detail intensity
- [x] Details serialize/deserialize correctly for save/load
- [x] 10 tests pass
