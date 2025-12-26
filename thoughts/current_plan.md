# Implementation Plan: WFC Chunks Manager (`wfc_chunks.py`)

## Overview

Create `src/cli_rpg/wfc_chunks.py` with `ChunkManager` class for infinite terrain generation via cached WFC-generated 8x8 chunks with deterministic seeding from world coordinates.

## Spec (from ISSUES.md lines 398-428)

```python
@dataclass
class ChunkManager:
    chunk_size: int = 8  # 8x8 tiles per chunk
    chunks: Dict[Tuple[int, int], Dict] = field(default_factory=dict)
    generator: WFCGenerator = None
    world_seed: int = 0

    def get_or_generate_chunk(self, chunk_x: int, chunk_y: int) -> Dict
    def get_tile_at(self, world_x: int, world_y: int) -> str
    def _apply_boundary_constraints(self, new_chunk, neighbors)
```

Key behaviors:
- Chunk cache stores generated 8x8 terrain chunks by (chunk_x, chunk_y) key
- Deterministic chunk seeding: `hash((world_seed, chunk_x, chunk_y)) & 0xFFFFFFFF`
- World-to-chunk coordinate conversion: `chunk_x = world_x // chunk_size`
- Local-within-chunk coordinates: `local_x = world_x % chunk_size`
- Boundary constraints: Edge cells constrained by adjacent chunk tiles

## Tests First (`tests/test_wfc_chunks.py`)

### Chunk Manager Creation
1. `test_chunk_manager_creation` - Default values (chunk_size=8, empty chunks dict, world_seed=0)
2. `test_chunk_manager_with_custom_seed` - Custom world_seed accepted

### Deterministic Seeding (spec: chunk boundary tests)
3. `test_chunk_seed_deterministic` - Same world_seed + chunk coords = same terrain
4. `test_different_chunks_different_terrain` - Different chunk coords = different terrain
5. `test_different_world_seeds_different_terrain` - Different world_seed = different terrain

### Chunk Caching (spec: chunk caching works correctly)
6. `test_get_or_generate_caches_chunk` - Second call returns cached chunk (no regeneration)
7. `test_cached_chunk_unchanged` - Cached chunk identical to original

### Coordinate Conversion
8. `test_get_tile_at_positive_coords` - World (5, 3) in chunk (0, 0) returns correct tile
9. `test_get_tile_at_negative_coords` - World (-3, -5) maps to correct chunk
10. `test_get_tile_at_chunk_boundary` - World (8, 0) is in chunk (1, 0)
11. `test_world_to_chunk_conversion` - Verify chunk_x/chunk_y calculation

### Boundary Constraints (spec: chunk boundary consistency)
12. `test_adjacent_chunks_share_compatible_edges` - East edge of (0,0) compatible with west edge of (1,0)
13. `test_boundary_constraints_applied` - Internal helper constrains edge cells

### Integration
14. `test_large_area_traversal` - Walk across chunk boundaries, terrain is coherent
15. `test_serialization_to_dict` - ChunkManager.to_dict() serializes world_seed and cached chunks
16. `test_deserialization_from_dict` - ChunkManager.from_dict() restores state

## Implementation Steps

### 1. Create `tests/test_wfc_chunks.py`
- Import fixtures from `test_wfc.py` pattern
- Write all 16 tests above (red phase)

### 2. Create `src/cli_rpg/wfc_chunks.py`
Implement:
```python
@dataclass
class ChunkManager:
    chunk_size: int = 8
    _chunks: Dict[Tuple[int, int], Dict[Tuple[int, int], str]] = field(default_factory=dict)
    world_seed: int = 0
    _tile_registry: TileRegistry = field(default_factory=TileRegistry)

    def get_or_generate_chunk(self, chunk_x: int, chunk_y: int) -> Dict[Tuple[int, int], str]:
        """Get cached chunk or generate new one with deterministic seeding."""
        key = (chunk_x, chunk_y)
        if key not in self._chunks:
            chunk_seed = hash((self.world_seed, chunk_x, chunk_y)) & 0xFFFFFFFF
            generator = WFCGenerator(self._tile_registry, seed=chunk_seed)
            origin = (chunk_x * self.chunk_size, chunk_y * self.chunk_size)
            self._chunks[key] = generator.generate_chunk(origin, self.chunk_size)
        return self._chunks[key]

    def get_tile_at(self, world_x: int, world_y: int) -> str:
        """Get terrain tile at world coordinates."""
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        chunk = self.get_or_generate_chunk(chunk_x, chunk_y)
        return chunk[(world_x, world_y)]

    def to_dict(self) -> dict:
        """Serialize for persistence."""

    @classmethod
    def from_dict(cls, data: dict) -> "ChunkManager":
        """Deserialize from saved state."""
```

### 3. Add boundary constraint handling (enhancement)
- When generating a new chunk adjacent to existing chunks, pre-constrain edge cells
- Modify `get_or_generate_chunk` to check for neighbor chunks first
- Apply edge constraints before WFC generation

### 4. Run tests, iterate until green

## Files to Create/Modify

| File | Action |
|------|--------|
| `tests/test_wfc_chunks.py` | CREATE |
| `src/cli_rpg/wfc_chunks.py` | CREATE |

## Verification

```bash
pytest tests/test_wfc_chunks.py -v
```
