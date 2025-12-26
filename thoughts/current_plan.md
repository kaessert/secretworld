# Implementation Plan: Add Hierarchical Sub-locations to Forest

## Goal
Expand the Forest location from a flat location into an overworld landmark with 3 sub-locations, validating that the hierarchical architecture works across multiple landmarks.

## Spec

Transform Forest into an overworld landmark (DANGEROUS - not safe zone):
- **Forest** (overworld landmark, `is_overworld=True`, `is_safe_zone=False`, entry_point="Forest Edge")
  - **Forest Edge** (sub-location, `is_safe_zone=False`) - the boundary area, slightly safer feeling
  - **Deep Woods** (sub-location, `is_safe_zone=False`) - dense, dark interior
  - **Ancient Grove** (sub-location, `is_safe_zone=False`) - mysterious clearing with old growth trees, contains Hermit NPC

Key differences from Town Square:
- Forest is a DANGER zone (random encounters enabled in all sub-locations)
- Contains recruitable NPC (Hermit) to add gameplay value
- Sub-locations have thematic dread-inducing atmosphere

## Tests (tests/test_world.py)

### Test 1: `test_default_world_forest_is_overworld`
```python
def test_default_world_forest_is_overworld(self):
    """Forest is an overworld landmark with sub-locations."""
    world, _ = create_default_world()
    forest = world["Forest"]
    assert forest.is_overworld is True
    assert forest.is_safe_zone is False  # Danger zone
    assert len(forest.sub_locations) >= 2
    assert forest.entry_point in forest.sub_locations
```

### Test 2: `test_default_world_forest_sub_locations_exist`
```python
def test_default_world_forest_sub_locations_exist(self):
    """All Forest sub-locations exist in world dict."""
    world, _ = create_default_world()
    forest = world["Forest"]
    for sub_name in forest.sub_locations:
        assert sub_name in world, f"Sub-location '{sub_name}' not in world"
```

### Test 3: `test_default_world_forest_sub_locations_have_parent`
```python
def test_default_world_forest_sub_locations_have_parent(self):
    """Forest sub-locations reference Forest as parent and are danger zones."""
    world, _ = create_default_world()
    forest = world["Forest"]
    for sub_name in forest.sub_locations:
        sub = world[sub_name]
        assert sub.parent_location == "Forest"
        assert sub.is_safe_zone is False  # All danger zones
```

### Test 4: `test_default_world_forest_sub_locations_no_cardinal_exits`
```python
def test_default_world_forest_sub_locations_no_cardinal_exits(self):
    """Forest sub-locations have no n/s/e/w exits (only enter/exit)."""
    world, _ = create_default_world()
    forest = world["Forest"]
    for sub_name in forest.sub_locations:
        sub = world[sub_name]
        assert len(sub.connections) == 0
```

### Test 5: `test_default_world_hermit_in_ancient_grove`
```python
def test_default_world_hermit_in_ancient_grove(self):
    """Hermit NPC is in Ancient Grove and is recruitable."""
    world, _ = create_default_world()
    grove = world["Ancient Grove"]
    hermit = grove.find_npc_by_name("Hermit")
    assert hermit is not None
    assert hermit.is_recruitable is True
```

### Test 6: `test_default_world_location_count_with_forest_sublocations`
```python
def test_default_world_location_count_with_forest_sublocations(self):
    """World has 9 locations: 3 overworld + 3 Town sub + 3 Forest sub."""
    world, _ = create_default_world()
    assert len(world) == 9
```

## Implementation (src/cli_rpg/world.py)

Update `create_default_world()`:

1. Modify Forest to be overworld landmark:
```python
forest = Location(
    name="Forest",
    description="A vast, dark forest stretches before you. Ancient trees tower overhead, their canopy blocking most sunlight. Multiple paths wind deeper into the woods.",
    is_overworld=True,
    is_safe_zone=False,  # Danger zone
    sub_locations=["Forest Edge", "Deep Woods", "Ancient Grove"],
    entry_point="Forest Edge"
)
```

2. Create Forest sub-locations:
```python
forest_edge = Location(
    name="Forest Edge",
    description="The forest boundary where civilization meets wilderness. Dappled sunlight still penetrates here, but the path ahead grows darker.",
    parent_location="Forest",
    is_safe_zone=False,
    category="forest",
    connections={}
)

deep_woods = Location(
    name="Deep Woods",
    description="Towering trees block out the sky. Strange sounds echo through the underbrush, and the air is thick with the scent of decay and growth.",
    parent_location="Forest",
    is_safe_zone=False,
    category="forest",
    connections={}
)

ancient_grove = Location(
    name="Ancient Grove",
    description="A mystical clearing surrounded by impossibly old trees. Soft moss covers the ground, and a weathered stone shrine sits at the center.",
    parent_location="Forest",
    is_safe_zone=False,
    category="forest",
    connections={}
)
```

3. Create Hermit NPC and add to Ancient Grove:
```python
hermit = NPC(
    name="Hermit",
    description="A weathered old man in tattered robes who has lived in the forest for decades",
    dialogue="The forest speaks to those who listen...",
    is_recruitable=True,
    greetings=[
        "The forest speaks to those who listen...",
        "Few venture this deep. You have courage... or foolishness.",
        "The trees have eyes, traveler. They've watched you since you entered.",
    ]
)
ancient_grove.npcs.append(hermit)
```

4. Add Forest sub-locations to world dict after grid:
```python
world = grid.as_dict()
# Town Square sub-locations
world["Market District"] = market_district
world["Guard Post"] = guard_post
world["Town Well"] = town_well
# Forest sub-locations
world["Forest Edge"] = forest_edge
world["Deep Woods"] = deep_woods
world["Ancient Grove"] = ancient_grove
```

## Existing Test Updates

Update `test_default_world_location_count_with_sublocations` from 6 to 9 expected locations.

## Files to Modify
- `src/cli_rpg/world.py` - Add Forest sub-locations to `create_default_world()`
- `tests/test_world.py` - Add 6 new tests, update location count test

## Verification
After implementation, verify:
1. `pytest tests/test_world.py -v` - All tests pass
2. Manual test: Start game, go north to Forest, `enter`, `exit` works
3. Manual test: `enter ancient` finds Hermit, `recruit hermit` works
