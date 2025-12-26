# Implementation Plan: Hierarchical Town Generation in world.py

## Goal
Update `create_default_world()` in `world.py` to generate Town Square as a complete hierarchical landmark with 2-3 sub-locations, so the implemented `enter`/`exit` commands have actual content to work with.

## Spec

Transform Town Square from a flat location into an overworld landmark containing:
- **Town Square** (overworld landmark, safe zone, entry_point="Market District")
  - **Market District** (sub-location, safe zone) - contains Merchant NPC and shop
  - **Guard Post** (sub-location, safe zone) - contains Guard NPC
  - **Town Well** (sub-location, safe zone) - atmospheric location

The existing connections (north->Forest, east->Cave) remain on Town Square. Sub-locations have no cardinal connections (only accessible via enter/exit).

## Tests (test_world.py)

### Test 1: `test_default_world_town_square_is_overworld`
```python
def test_default_world_town_square_is_overworld(self):
    """Town Square is an overworld landmark with sub-locations."""
    world, _ = create_default_world()
    town_square = world["Town Square"]
    assert town_square.is_overworld is True
    assert town_square.is_safe_zone is True
    assert len(town_square.sub_locations) >= 2
    assert town_square.entry_point in town_square.sub_locations
```

### Test 2: `test_default_world_sub_locations_exist`
```python
def test_default_world_sub_locations_exist(self):
    """All Town Square sub-locations exist in world dict."""
    world, _ = create_default_world()
    town_square = world["Town Square"]
    for sub_name in town_square.sub_locations:
        assert sub_name in world, f"Sub-location '{sub_name}' not in world"
```

### Test 3: `test_default_world_sub_locations_have_parent`
```python
def test_default_world_sub_locations_have_parent(self):
    """Sub-locations reference Town Square as parent."""
    world, _ = create_default_world()
    town_square = world["Town Square"]
    for sub_name in town_square.sub_locations:
        sub = world[sub_name]
        assert sub.parent_location == "Town Square"
        assert sub.is_safe_zone is True
```

### Test 4: `test_default_world_sub_locations_have_no_cardinal_connections`
```python
def test_default_world_sub_locations_have_no_cardinal_connections(self):
    """Sub-locations have no n/s/e/w exits (only enter/exit navigation)."""
    world, _ = create_default_world()
    town_square = world["Town Square"]
    for sub_name in town_square.sub_locations:
        sub = world[sub_name]
        assert len(sub.connections) == 0
```

### Test 5: `test_default_world_merchant_in_market_district`
```python
def test_default_world_merchant_in_market_district(self):
    """Merchant NPC is in Market District sub-location."""
    world, _ = create_default_world()
    market = world["Market District"]
    merchant = market.find_npc_by_name("Merchant")
    assert merchant is not None
    assert merchant.is_merchant is True
```

### Test 6: `test_default_world_location_count_with_sublocations`
```python
def test_default_world_location_count_with_sublocations(self):
    """World has 6 locations: Town Square, Forest, Cave, + 3 sub-locations."""
    world, _ = create_default_world()
    assert len(world) == 6
```

## Implementation (world.py)

Update `create_default_world()` to:

1. Create Town Square as overworld landmark:
   ```python
   town_square = Location(
       name="Town Square",
       description="A bustling town square with a fountain in the center. Pathways lead to various districts.",
       is_overworld=True,
       is_safe_zone=True,
       sub_locations=["Market District", "Guard Post", "Town Well"],
       entry_point="Market District"
   )
   ```

2. Create sub-locations with parent reference:
   ```python
   market_district = Location(
       name="Market District",
       description="Colorful market stalls line the cobblestone streets. The smell of fresh bread mingles with exotic spices.",
       parent_location="Town Square",
       is_safe_zone=True,
       connections={}  # No cardinal exits
   )
   # Add Merchant NPC here

   guard_post = Location(
       name="Guard Post",
       description="A fortified stone building where the town guard keeps watch. Weapons and armor hang on the walls.",
       parent_location="Town Square",
       is_safe_zone=True,
       connections={}
   )
   # Add Guard NPC here

   town_well = Location(
       name="Town Well",
       description="An ancient stone well in a quiet corner of town. Moss grows between the weathered stones.",
       parent_location="Town Square",
       is_safe_zone=True,
       connections={}
   )
   ```

3. Move NPCs to sub-locations:
   - Move Merchant NPC to Market District
   - Move Guard NPC to Guard Post
   - Town Square itself has no NPCs (they're in sub-locations)

4. Add sub-locations to world dict:
   ```python
   world = {
       "Town Square": town_square,
       "Market District": market_district,
       "Guard Post": guard_post,
       "Town Well": town_well,
       "Forest": forest,
       "Cave": cave
   }
   ```

5. Keep Town Square on grid at (0,0) with north/east connections to Forest/Cave.

## Files to Modify
- `src/cli_rpg/world.py` - Update `create_default_world()`
- `tests/test_world.py` - Add 6 new tests, update `test_default_world_has_three_locations` to expect 6 locations
