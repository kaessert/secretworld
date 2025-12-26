# Implementation Plan: Add Millbrook Village Hierarchical Location

## Summary
Add Millbrook Village as a new overworld location with 3 sub-locations (Village Square, Inn, Blacksmith), following the established pattern from Town Square and Forest.

## Spec

### Millbrook Village Structure
```
🏠 Millbrook Village (SAFE, overworld at -1, 0 - west of Town Square)
├── Village Square (entry_point, with Elder NPC)
├── Inn (with Innkeeper NPC, recruitable)
└── Blacksmith (with Blacksmith NPC, merchant with weapons/armor)
```

### Location Fields
- **Millbrook Village**: `is_overworld=True`, `is_safe_zone=True`, `sub_locations=["Village Square", "Inn", "Blacksmith"]`, `entry_point="Village Square"`, `coordinates=(-1, 0)`
- **Sub-locations**: `parent_location="Millbrook Village"`, `is_safe_zone=True`, `connections={}`

### NPCs
1. **Elder** (Village Square): Wisdom/lore dialogue, not recruitable
2. **Innkeeper** (Inn): Friendly dialogue, `is_recruitable=True`
3. **Blacksmith** (Blacksmith): `is_merchant=True` with weapon/armor shop

## Tests

### File: `tests/test_world.py` (add to TestCreateDefaultWorld)

1. **test_default_world_has_12_locations** - Update count from 9 to 12
2. **test_default_world_millbrook_village_exists** - Village in world dict
3. **test_default_world_millbrook_village_is_overworld** - `is_overworld=True`, `is_safe_zone=True`, `sub_locations` length, `entry_point`
4. **test_default_world_millbrook_village_sub_locations_exist** - All 3 sub-locations in world
5. **test_default_world_millbrook_village_sub_locations_have_parent** - `parent_location="Millbrook Village"`, `is_safe_zone=True`
6. **test_default_world_millbrook_village_sub_locations_no_cardinal_exits** - Empty `connections`
7. **test_default_world_millbrook_village_connections** - `east->Town Square`
8. **test_default_world_town_square_has_west_connection** - `west->Millbrook Village`
9. **test_default_world_elder_in_village_square** - Elder NPC exists
10. **test_default_world_innkeeper_in_inn** - Innkeeper NPC, `is_recruitable=True`
11. **test_default_world_blacksmith_in_blacksmith** - Blacksmith NPC, `is_merchant=True`

## Implementation Steps

### Step 1: Write tests first
**File: `tests/test_world.py`**
- Update `test_default_world_location_count_with_sublocations` from 9 to 12
- Add 10 new test methods for Millbrook Village

### Step 2: Add Millbrook Village to world.py
**File: `src/cli_rpg/world.py`**

1. Create Millbrook Village Location (~line 170, after Forest):
```python
millbrook = Location(
    name="Millbrook Village",
    description="A small rural village surrounded by wheat fields. Smoke rises from cottage chimneys, and the sound of a blacksmith's hammer echoes through the air.",
    is_overworld=True,
    is_safe_zone=True,
    sub_locations=["Village Square", "Inn", "Blacksmith"],
    entry_point="Village Square"
)
```

2. Add to grid at (-1, 0) - west of Town Square (~line 183):
```python
grid.add_location(millbrook, -1, 0)
```

3. Create NPCs (~line 241, after Guard NPC):
```python
# Elder NPC
elder = NPC(
    name="Elder",
    description="A wise old woman who has lived in Millbrook all her life",
    dialogue="The old ways are not forgotten here, traveler.",
    greetings=[...]
)

# Innkeeper NPC
innkeeper = NPC(
    name="Innkeeper",
    description="A jovial man with a hearty laugh who runs the village inn",
    dialogue="Rest your weary bones, friend!",
    is_recruitable=True,
    greetings=[...]
)

# Blacksmith NPC with shop
blacksmith_shop = Shop(name="Village Smithy", inventory=[...])
blacksmith = NPC(
    name="Blacksmith",
    description="A muscular woman covered in soot, working the forge",
    dialogue="Looking for steel? You've come to the right place.",
    is_merchant=True,
    shop=blacksmith_shop,
    greetings=[...]
)
```

4. Create sub-locations (~line 300, after Forest sub-locations):
```python
village_square = Location(
    name="Village Square",
    description="A humble village square with a weathered wooden well at its center. Villagers go about their daily routines.",
    parent_location="Millbrook Village",
    is_safe_zone=True,
    connections={}
)
village_square.npcs.append(elder)

inn = Location(
    name="Inn",
    description="A cozy inn with a roaring fireplace. The smell of fresh bread and ale fills the air.",
    parent_location="Millbrook Village",
    is_safe_zone=True,
    connections={}
)
inn.npcs.append(innkeeper)

blacksmith_loc = Location(
    name="Blacksmith",
    description="A hot, smoky workshop filled with weapons, armor, and tools. The forge glows orange.",
    parent_location="Millbrook Village",
    is_safe_zone=True,
    connections={}
)
blacksmith_loc.npcs.append(blacksmith)
```

5. Add sub-locations to world dict (~line 320):
```python
world["Village Square"] = village_square
world["Inn"] = inn
world["Blacksmith"] = blacksmith_loc
```

### Step 3: Run tests
```bash
pytest tests/test_world.py -v
```
