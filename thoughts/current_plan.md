# Implementation Plan: Issue 17 - AI-Generated Treasure Chests

## Spec

AI-generated areas (via `expand_area()` and `generate_subgrid_for_location()`) should include treasure chests that:
1. Scale with area size (1-3 chests based on number of rooms)
2. Are distributed across non-entry rooms (not clustered)
3. Match location category thematically (ancient weapons in ruins, crystals in caves)
4. Have lock difficulty that scales with distance from entry
5. Some chests are trap-protected (DEX check to open safely)

## Treasure Schema

Existing schema from `world.py` line 531-543:
```python
treasures=[
    {
        "name": "Mossy Chest",
        "description": "An ancient chest covered in moss...",
        "locked": True,
        "difficulty": 2,  # Lock difficulty (higher = harder)
        "opened": False,
        "items": [
            {"name": "...", "description": "...", "item_type": "misc"},
            {"name": "...", "description": "...", "item_type": "consumable", "heal_amount": 25}
        ],
        "requires_key": None  # Optional key name
    }
]
```

## Implementation Steps

### Step 1: Add Thematic Treasure Loot Tables
**File:** `src/cli_rpg/ai_world.py`

Add category-specific loot tables as a constant:
```python
TREASURE_LOOT_TABLES: dict[str, list[dict]] = {
    "dungeon": [
        {"name": "Ancient Blade", "item_type": "weapon", "damage_bonus": 4},
        {"name": "Rusted Key", "item_type": "misc"},
        {"name": "Health Potion", "item_type": "consumable", "heal_amount": 25},
    ],
    "cave": [
        {"name": "Glowing Crystal", "item_type": "misc"},
        {"name": "Cave Spider Venom", "item_type": "consumable", "heal_amount": 15},
        {"name": "Miner's Pickaxe", "item_type": "weapon", "damage_bonus": 3},
    ],
    "ruins": [
        {"name": "Ancient Tome", "item_type": "misc"},
        {"name": "Gilded Amulet", "item_type": "armor", "defense_bonus": 2},
        {"name": "Relic Dust", "item_type": "consumable", "mana_restore": 20},
    ],
    "temple": [
        {"name": "Holy Water", "item_type": "consumable", "heal_amount": 30},
        {"name": "Sacred Relic", "item_type": "misc"},
        {"name": "Blessed Medallion", "item_type": "armor", "defense_bonus": 3},
    ],
    "forest": [
        {"name": "Forest Gem", "item_type": "misc"},
        {"name": "Herbal Remedy", "item_type": "consumable", "heal_amount": 20},
        {"name": "Wooden Bow", "item_type": "weapon", "damage_bonus": 3},
    ],
}

TREASURE_CHEST_NAMES: dict[str, list[str]] = {
    "dungeon": ["Iron Chest", "Dusty Strongbox", "Forgotten Coffer"],
    "cave": ["Stone Chest", "Crystal Box", "Hidden Cache"],
    "ruins": ["Ancient Chest", "Ruined Coffer", "Gilded Box"],
    "temple": ["Sacred Chest", "Offering Box", "Blessed Container"],
    "forest": ["Mossy Chest", "Hollow Log Cache", "Vine-Covered Box"],
}
```

### Step 2: Add Treasure Placement Helper Function
**File:** `src/cli_rpg/ai_world.py`

Add `_place_treasures()` helper function (similar pattern to `_find_furthest_room()`):
```python
def _place_treasures(
    placed_locations: dict,
    entry_category: str,
) -> None:
    """Place treasures in non-entry rooms based on area size.

    Modifies placed_locations in-place by adding treasures to Location objects.

    Args:
        placed_locations: Dict mapping location names to placement data.
            Each entry has 'location' (Location), 'relative_coords', 'is_entry'.
        entry_category: Category of the entry location (dungeon, cave, etc.)

    Treasure distribution:
        - 1 chest for 2-3 rooms
        - 2 chests for 4-5 rooms
        - 3 chests for 6+ rooms
    """
```

Key logic:
1. Count non-entry rooms (exclude boss room)
2. Determine number of chests (1-3)
3. Select rooms with spread distribution (by distance from entry)
4. Generate thematic chest with items from loot table
5. Lock difficulty = distance from entry + random(0,1)

### Step 3: Integrate Treasure Placement into expand_area()
**File:** `src/cli_rpg/ai_world.py`

Add treasure placement after boss placement (around line 1280):
```python
# Place boss in furthest room for dungeon-type categories
if entry_category in BOSS_CATEGORIES:
    # ... existing boss code ...

# Place treasures in non-boss rooms
_place_treasures(placed_locations, entry_category)
```

### Step 4: Integrate Treasure Placement into generate_subgrid_for_location()
**File:** `src/cli_rpg/ai_world.py`

Add treasure placement after boss placement (around line 556):
```python
# Place boss in furthest room for dungeon-type categories
if location.category in BOSS_CATEGORIES and placed_locations:
    # ... existing boss code ...

# Place treasures in non-boss rooms
if placed_locations:
    _place_treasures(placed_locations, location.category or "dungeon")
```

## Tests

**File:** `tests/test_ai_world_treasure.py`

### Test: Treasure Loot Tables Exist
```python
def test_treasure_loot_tables_contains_dungeon():
    assert "dungeon" in TREASURE_LOOT_TABLES

def test_treasure_loot_tables_contains_cave():
    assert "cave" in TREASURE_LOOT_TABLES

def test_treasure_loot_tables_items_have_required_fields():
    for category, items in TREASURE_LOOT_TABLES.items():
        for item in items:
            assert "name" in item
            assert "item_type" in item
```

### Test: Treasure Placement Helper
```python
def test_place_treasures_adds_chest_to_location():
    """_place_treasures adds treasure to non-entry rooms."""

def test_place_treasures_excludes_entry_room():
    """Entry room should not receive treasures."""

def test_place_treasures_scales_with_room_count():
    """Number of chests scales: 1 for 2-3, 2 for 4-5, 3 for 6+."""

def test_place_treasures_spreads_across_rooms():
    """Treasures are distributed, not clustered in one room."""

def test_place_treasures_difficulty_scales_with_distance():
    """Lock difficulty increases with Manhattan distance from entry."""
```

### Test: Integration with expand_area()
```python
def test_expand_area_dungeon_has_treasures():
    """expand_area for dungeon category places treasures."""

def test_expand_area_cave_has_treasures():
    """expand_area for cave category places treasures."""

def test_expand_area_town_has_no_treasures():
    """Town areas should NOT have random treasures."""

def test_expand_area_treasure_thematically_matches_category():
    """Treasure items match the category loot table."""
```

### Test: Integration with generate_subgrid_for_location()
```python
def test_generate_subgrid_dungeon_has_treasures():
    """On-demand SubGrid generation includes treasures."""
```

## File Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/ai_world.py` | Add `TREASURE_LOOT_TABLES`, `TREASURE_CHEST_NAMES`, `_place_treasures()`, integrate into `expand_area()` and `generate_subgrid_for_location()` |
| `tests/test_ai_world_treasure.py` | New test file with ~15 tests |

## Verification

```bash
# Run treasure-specific tests
pytest tests/test_ai_world_treasure.py -v

# Run all AI world tests to ensure no regressions
pytest tests/test_ai_world*.py -v

# Full test suite
pytest
```
