# Issue 16: AI-Generated Dungeon Bosses - Implementation Plan

## Overview
The `boss_enemy` field exists on Location but AI-generated areas via `expand_area()` never populate it. This makes dynamically generated dungeons feel empty and anticlimactic.

## Spec

**When `expand_area()` generates a dungeon/cave/ruins category area:**
1. Identify the room furthest from entry (max Manhattan distance from (0,0))
2. Generate a boss appropriate for the location category
3. Set `boss_enemy` on that room to a valid boss template name
4. Boss uses existing combat.py category-based spawning

**Boss categories eligible for auto-generation:**
- `dungeon`, `cave`, `ruins`

**Boss template assignment:**
- Uses the entry location's category for template selection
- combat.py's `spawn_boss()` already has category-based templates:
  - `dungeon`: "Lich Lord", "Dark Champion", "Demon Lord"
  - `cave`: "Cave Troll King", "Elder Wyrm", "Crystal Golem"
  - `ruins`: "Ancient Guardian", "Cursed Pharaoh", "Shadow King"
- We set `boss_enemy` to the category string (e.g., "dungeon"), letting spawn_boss pick randomly

## Implementation Steps

### 1. Add tests for boss placement in expand_area()
**File:** `tests/test_ai_world_boss.py` (new file)

Tests:
- `test_expand_area_dungeon_places_boss_in_furthest_room`
- `test_expand_area_cave_places_boss`
- `test_expand_area_ruins_places_boss`
- `test_expand_area_town_no_boss`
- `test_expand_area_boss_room_is_furthest_from_entry`
- `test_expand_area_single_location_no_boss` (no sub-locations = no boss)

### 2. Add boss placement helpers to ai_world.py
**File:** `src/cli_rpg/ai_world.py`

Add at module level:
```python
# Categories that should have bosses in deepest room
BOSS_CATEGORIES = frozenset({"dungeon", "cave", "ruins"})
```

Add helper function:
```python
def _find_furthest_room(placed_locations: dict) -> Optional[str]:
    """Find the room furthest from entry (0,0) for boss placement."""
    max_distance = -1
    furthest_name = None
    for name, data in placed_locations.items():
        if data.get("is_entry", False):
            continue
        rel_x, rel_y = data.get("relative_coords", (0, 0))
        distance = abs(rel_x) + abs(rel_y)
        if distance > max_distance:
            max_distance = distance
            furthest_name = name
    return furthest_name
```

### 3. Wire boss placement into expand_area()
**File:** `src/cli_rpg/ai_world.py` - modify `expand_area()` function

After SubGrid population (around line 1026), before adding to world:
```python
# Place boss in furthest room for dungeon-type areas
if entry_name and entry_loc.category in BOSS_CATEGORIES:
    boss_room_name = _find_furthest_room(placed_locations)
    if boss_room_name:
        boss_room = sub_grid.get_by_name(boss_room_name)
        if boss_room:
            boss_room.boss_enemy = entry_loc.category  # Category-based boss
```

## Verification

```bash
pytest tests/test_ai_world_boss.py -v
pytest tests/test_boss_combat.py -v
pytest tests/test_ai_world_subgrid.py -v
```

## Files Changed

1. `tests/test_ai_world_boss.py` - NEW (6 tests)
2. `src/cli_rpg/ai_world.py` - Add BOSS_CATEGORIES, _find_furthest_room(), wire into expand_area() (~20 lines)
