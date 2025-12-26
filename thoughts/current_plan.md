# Implementation Plan: Add Abandoned Mines Hierarchical Dungeon

## Summary
Add Abandoned Mines as a new overworld dungeon location with 4 sub-locations (Mine Entrance, Upper Tunnels, Flooded Level, Boss Chamber), validating that danger-zone hierarchy works for dungeons before adding the more complex depth/floor system.

## Spec

### Abandoned Mines Structure
```
⛏️ Abandoned Mines (DANGER, overworld at 1, 1 - northeast of Cave)
├── Mine Entrance (entry_point, with Old Miner NPC - quest giver)
├── Upper Tunnels (danger zone, with occasional hostile spawns)
├── Flooded Level (danger zone, environmental hazard flavor)
└── Boss Chamber (danger zone, with Mine Foreman boss enemy potential)
```

### Location Fields
- **Abandoned Mines**: `is_overworld=True`, `is_safe_zone=False`, `category="dungeon"`, `sub_locations=["Mine Entrance", "Upper Tunnels", "Flooded Level", "Boss Chamber"]`, `entry_point="Mine Entrance"`, `coordinates=(1, 1)`
- **Sub-locations**: `parent_location="Abandoned Mines"`, `is_safe_zone=False`, `category="dungeon"`, `connections={}`

### Grid Placement
- Cave is at (1, 0)
- Abandoned Mines at (1, 1) - north of Cave
- Creates connection: Cave has north->Abandoned Mines, Abandoned Mines has south->Cave

### NPCs
1. **Old Miner** (Mine Entrance): Quest giver with lore about the mines, not recruitable, not merchant

## Tests

### File: `tests/test_world.py` (add to TestCreateDefaultWorld)

1. **test_default_world_location_count_with_sublocations** - Update from 13 to 17 (4 new)
2. **test_default_world_abandoned_mines_exists** - Mines in world dict
3. **test_default_world_abandoned_mines_is_overworld** - `is_overworld=True`, `is_safe_zone=False`, `sub_locations` length=4, `entry_point="Mine Entrance"`
4. **test_default_world_abandoned_mines_sub_locations_exist** - All 4 sub-locations in world
5. **test_default_world_abandoned_mines_sub_locations_have_parent** - `parent_location="Abandoned Mines"`, `is_safe_zone=False`
6. **test_default_world_abandoned_mines_sub_locations_have_dungeon_category** - `category="dungeon"`
7. **test_default_world_abandoned_mines_sub_locations_no_cardinal_exits** - Empty `connections`
8. **test_default_world_abandoned_mines_connections** - `south->Cave`
9. **test_default_world_cave_has_north_connection** - `north->Abandoned Mines`
10. **test_default_world_old_miner_in_mine_entrance** - Old Miner NPC exists

## Implementation Steps

### Step 1: Write tests first
**File: `tests/test_world.py`**
- Update `test_default_world_location_count_with_sublocations` from 13 to 17
- Add 9 new test methods for Abandoned Mines

### Step 2: Add Abandoned Mines to world.py
**File: `src/cli_rpg/world.py`**

1. Create Abandoned Mines Location (~line 180, after Millbrook):
```python
abandoned_mines = Location(
    name="Abandoned Mines",
    description="A dark entrance yawns in the hillside, wooden beams rotting at the threshold. The clang of pickaxes once echoed here, but now only silence and the occasional rumble from deep below.",
    is_overworld=True,
    is_safe_zone=False,  # Danger zone
    category="dungeon",
    sub_locations=["Mine Entrance", "Upper Tunnels", "Flooded Level", "Boss Chamber"],
    entry_point="Mine Entrance"
)
```

2. Add to grid at (1, 1) - north of Cave (~line 197):
```python
grid.add_location(abandoned_mines, 1, 1)
```

3. Create Old Miner NPC (~line 325, after Blacksmith NPC):
```python
old_miner = NPC(
    name="Old Miner",
    description="A grizzled old man with coal-stained hands and haunted eyes",
    dialogue="These mines... they took everything from us. Something woke up down there.",
    greetings=[
        "These mines... they took everything from us. Something woke up down there.",
        "You're not thinking of going deeper, are you? Foolish...",
        "I was the last one out. I still hear the screams some nights.",
    ]
)
```

4. Create sub-locations (~line 430, after Blacksmith sub-location):
```python
mine_entrance = Location(
    name="Mine Entrance",
    description="The first chamber inside the mines. Abandoned mining equipment rusts in the corners, and old torches hang unlit on the walls. A cold draft blows from deeper within.",
    parent_location="Abandoned Mines",
    is_safe_zone=False,
    category="dungeon",
    connections={}
)
mine_entrance.npcs.append(old_miner)

upper_tunnels = Location(
    name="Upper Tunnels",
    description="Narrow passages carved through solid rock. The ceiling is low, and the walls are marked with old chisel strikes. Occasional cave-ins have blocked some paths.",
    parent_location="Abandoned Mines",
    is_safe_zone=False,
    category="dungeon",
    connections={}
)

flooded_level = Location(
    name="Flooded Level",
    description="The lower tunnels have flooded with dark, stagnant water. Wooden walkways float precariously, and the sound of dripping echoes endlessly. Something moves beneath the surface.",
    parent_location="Abandoned Mines",
    is_safe_zone=False,
    category="dungeon",
    connections={}
)

boss_chamber = Location(
    name="Boss Chamber",
    description="A vast natural cavern at the deepest point of the mines. Ancient crystals embedded in the walls give off an eerie glow. The bones of unlucky miners litter the ground.",
    parent_location="Abandoned Mines",
    is_safe_zone=False,
    category="dungeon",
    connections={}
)
```

5. Add sub-locations to world dict (~line 435):
```python
world["Mine Entrance"] = mine_entrance
world["Upper Tunnels"] = upper_tunnels
world["Flooded Level"] = flooded_level
world["Boss Chamber"] = boss_chamber
```

### Step 3: Run tests
```bash
pytest tests/test_world.py -v
```
