# Implementation Plan: Crafting System Foundation

## Overview
Add the foundation for a crafting system: gatherable resources in wilderness locations and a `gather` command. This leverages the existing `forage` pattern from `camping.py` while introducing a distinct resource collection mechanic for future crafting.

## Spec

**Gather mechanics:**
- **Command**: `gather` (alias: `ga`)
- **Location restriction**: Forest/wilderness only (same as forage/hunt)
- **Cooldown**: 1 hour (like forage)
- **Success chance**: 40% base + (PER × 2%) (same formula as forage)
- **Time cost**: 1 hour

**Resource types (MVP set):**
- **Iron Ore** - Found in cave/dungeon areas, for weapons/armor
- **Wood** - Found in forest areas, for tools/handles
- **Fiber** - Found in wilderness/forest, for rope/cloth
- **Stone** - Found in cave/dungeon/wilderness, for tools/building

**Resource item:**
- New `ItemType.RESOURCE` enum value
- Resources are MISC items with a `resource_type` field (for future crafting recipes)

**Why this design:**
- Minimal scope: Uses existing patterns (forage), adds one command
- Future-proof: Resource type field enables recipe system later
- Location-specific: Different areas yield different resources (encourages exploration)
- Compatible: Works with existing inventory, persistence, and shop systems

## Tests (tests/test_crafting.py)

1. `test_gather_in_forest_succeeds` - gather in forest category returns resource
2. `test_gather_in_town_fails` - gather in safe zone returns error
3. `test_gather_in_dungeon_succeeds` - gather works in dungeon/cave
4. `test_gather_respects_cooldown` - fails if cooldown active
5. `test_gather_advances_time` - advances game time by 1 hour
6. `test_gather_adds_item_to_inventory` - resource added to inventory
7. `test_gather_fails_when_inventory_full` - returns full message
8. `test_gather_success_scales_with_per` - higher PER = higher success
9. `test_resource_item_serialization` - resource items serialize/deserialize
10. `test_forest_yields_wood_or_fiber` - forest gives wood/fiber resources
11. `test_cave_yields_ore_or_stone` - cave gives ore/stone resources

## Implementation Steps

### 1. Add `RESOURCE` to ItemType enum (src/cli_rpg/models/item.py)
- Add `RESOURCE = "resource"` after `MISC = "misc"` (line ~15)

### 2. Create crafting.py module (src/cli_rpg/crafting.py)
Following the pattern from `camping.py`:

```python
"""Crafting and resource gathering system."""

GATHERABLE_CATEGORIES = {"forest", "wilderness", "cave", "dungeon", "ruins"}
GATHER_BASE_CHANCE = 40
GATHER_PER_BONUS = 2
GATHER_COOLDOWN = 1
GATHER_TIME_HOURS = 1

# Resource templates by location category
RESOURCE_BY_CATEGORY = {
    "forest": [
        {"name": "Wood", "description": "A sturdy branch...", "resource_type": "wood"},
        {"name": "Fiber", "description": "Plant fibers...", "resource_type": "fiber"},
    ],
    "wilderness": [
        {"name": "Stone", "description": "A chunk of rock...", "resource_type": "stone"},
        {"name": "Fiber", "description": "Plant fibers...", "resource_type": "fiber"},
    ],
    "cave": [
        {"name": "Iron Ore", "description": "Raw iron ore...", "resource_type": "ore"},
        {"name": "Stone", "description": "A chunk of rock...", "resource_type": "stone"},
    ],
    "dungeon": [
        {"name": "Iron Ore", "description": "Raw iron ore...", "resource_type": "ore"},
        {"name": "Stone", "description": "A chunk of rock...", "resource_type": "stone"},
    ],
    "ruins": [
        {"name": "Stone", "description": "Ancient masonry...", "resource_type": "stone"},
        {"name": "Iron Ore", "description": "Rusted ore...", "resource_type": "ore"},
    ],
}

def is_gatherable_location(location) -> bool:
    """Check if location supports resource gathering."""

def execute_gather(game_state) -> Tuple[bool, str]:
    """Execute the gather command."""
```

### 3. Add gather_cooldown to GameState (src/cli_rpg/game_state.py)
- Add `self.gather_cooldown: int = 0` in `__init__` (near forage_cooldown, ~line 248)
- Add serialization in `to_dict()` and `from_dict()` (with backward compatibility)

### 4. Add gather command to main.py (src/cli_rpg/main.py)
- Add to command reference (~line 57): `  gather (ga)         - Gather resources in wilderness/caves`
- Add `elif command == "gather":` handler after hunt handler (import and call execute_gather)

### 5. Add gather to KNOWN_COMMANDS and aliases (src/cli_rpg/game_state.py)
- Add `"gather"` to KNOWN_COMMANDS set (line ~63)
- Add `"ga": "gather"` to aliases dict (line ~137)

### 6. Decrement gather_cooldown in camping.py
- Update `decrement_cooldowns()` to include `game_state.gather_cooldown`

### 7. Update ISSUES.md
- Add "gather command MVP IMPLEMENTED" under Crafting and gathering system section
