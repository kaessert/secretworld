# Implementation Plan: Integrate WFC ChunkManager with GameState Movement

## Spec Summary
Wire the existing WFC ChunkManager into GameState's movement system so terrain tiles are generated as players explore. Opt-in via `--wfc` flag.

## Files to Modify/Create
| File | Action |
|------|--------|
| `src/cli_rpg/game_state.py` | MODIFY - Add `chunk_manager` attribute, use WFC terrain in `move()` |
| `src/cli_rpg/world.py` | MODIFY - Add terrain parameter to `generate_fallback_location()` |
| `src/cli_rpg/main.py` | MODIFY - Add `--wfc` CLI flag |
| `tests/test_wfc_integration.py` | CREATE - Integration tests |

## Tests First (`tests/test_wfc_integration.py`)

### GameState with WFC
1. `test_gamestate_with_chunk_manager` - GameState accepts optional `chunk_manager` parameter
2. `test_gamestate_without_chunk_manager` - Backward compatibility: works without chunk_manager
3. `test_move_triggers_chunk_generation` - Moving to unexplored coords generates terrain
4. `test_terrain_stored_on_location` - Generated Location has `terrain` field from WFC
5. `test_move_blocks_impassable_terrain` - Cannot move onto water tiles

### Terrain-Aware Location Generation
6. `test_fallback_uses_terrain_type` - `generate_fallback_location()` accepts terrain param
7. `test_location_category_from_terrain` - Category matches terrain (forest→forest)

### Persistence
8. `test_save_includes_chunk_manager` - `to_dict()` includes chunk_manager when present
9. `test_load_restores_chunk_manager` - `from_dict()` restores chunk_manager
10. `test_load_without_chunk_manager` - Old saves load successfully

## Implementation Steps

### 1. Add terrain field to Location model
```python
# models/location.py - add field
terrain: Optional[str] = None  # WFC terrain type
```

### 2. Modify `GameState.__init__()` and serialization
```python
# game_state.py
def __init__(self, ..., chunk_manager: Optional[ChunkManager] = None):
    self.chunk_manager = chunk_manager

def to_dict(self):
    data = {...}
    if self.chunk_manager:
        data["chunk_manager"] = self.chunk_manager.to_dict()
    return data

@classmethod
def from_dict(cls, data, ...):
    chunk_manager = None
    if "chunk_manager" in data:
        chunk_manager = ChunkManager.from_dict(data["chunk_manager"], DEFAULT_TILE_REGISTRY)
    gs = cls(..., chunk_manager=chunk_manager)
```

### 3. Modify `move()` to use WFC terrain
In coordinate-based movement (line ~500):
```python
if target_location is None and self.chunk_manager:
    terrain = self.chunk_manager.get_tile_at(*target_coords)
    if not TERRAIN_PASSABLE.get(terrain, True):
        return (False, f"The {terrain} ahead is impassable.")
    new_location = generate_fallback_location(..., terrain=terrain)
```

### 4. Modify `generate_fallback_location()` in world.py
```python
def generate_fallback_location(..., terrain: Optional[str] = None):
    if terrain:
        category = TERRAIN_TO_CATEGORY.get(terrain, "wilderness")
        template = TERRAIN_TEMPLATES.get(terrain, ...)
    else:
        template = random.choice(FALLBACK_LOCATION_TEMPLATES)
    ...
```

### 5. Add terrain templates to world.py
```python
TERRAIN_TEMPLATES = {
    "forest": {"name_patterns": [...], "descriptions": [...]},
    "plains": {...},
    ...
}
```

### 6. Add `--wfc` flag to main.py
```python
parser.add_argument("--wfc", action="store_true")
if args.wfc:
    chunk_manager = ChunkManager(tile_registry=DEFAULT_TILE_REGISTRY, world_seed=random.randint(0, 2**32-1))
```

## Verification
```bash
pytest tests/test_wfc_integration.py -v
```
