# WFC Core Algorithm Implementation Plan

## Objective
Create `src/cli_rpg/wfc.py` with Wave Function Collapse algorithm for procedural terrain generation (Phase 2, Item 1 of ISSUES.md P0 blocker).

## Spec

### `WFCCell` Dataclass
- `coords: Tuple[int, int]` - Cell position
- `possible_tiles: Set[str]` - Starts with ALL terrain types from `TileRegistry`
- `collapsed: bool = False` - Whether cell has been resolved
- `tile: Optional[str] = None` - Final tile (set when collapsed)

### `WFCGenerator` Class
- `__init__(self, tile_registry: TileRegistry, seed: int)` - Uses `world_tiles.TileRegistry`
- `generate_chunk(self, origin: Tuple[int, int], size: int = 8) -> Dict[Tuple[int, int], str]`
  - Initialize cells with all possible tiles
  - Loop until all collapsed:
    1. Find cell with minimum entropy (fewest options, break ties with RNG)
    2. Collapse cell (weighted random by `TileRegistry.get_weight()`)
    3. Propagate constraints to neighbors using `ADJACENCY_RULES`
    4. Handle contradictions (cell with 0 options) - restart or backtrack
  - Return `{(x, y): tile_name}` dict

- `_calculate_entropy(self, cell: WFCCell) -> float` - Shannon entropy formula
- `_collapse_cell(self, cell: WFCCell) -> str` - Weighted random selection
- `_propagate(self, grid: Dict, collapsed_coords: Tuple[int, int]) -> bool` - Arc consistency, returns False on contradiction

---

## Tests First (`tests/test_wfc.py`)

### Basic tests
1. `test_wfc_cell_creation` - WFCCell dataclass exists with correct fields
2. `test_wfc_cell_starts_uncollapsed` - collapsed=False, tile=None by default
3. `test_wfc_generator_creation` - WFCGenerator accepts TileRegistry and seed
4. `test_wfc_generator_deterministic` - Same seed produces same output

### Entropy tests
5. `test_entropy_single_option` - 1 option = 0 entropy
6. `test_entropy_multiple_options` - More options = higher entropy
7. `test_select_minimum_entropy_cell` - Correctly finds lowest entropy cell

### Collapse tests
8. `test_collapse_reduces_to_one` - After collapse, cell has exactly 1 tile
9. `test_collapse_respects_weights` - Higher weight tiles selected more often (statistical)
10. `test_collapse_sets_collapsed_flag` - collapsed=True after collapse

### Propagation tests
11. `test_propagate_reduces_neighbor_options` - Neighbors lose invalid options
12. `test_propagate_chain_reaction` - Reduction cascades through grid
13. `test_propagate_detects_contradiction` - Returns False when cell has 0 options

### Generation tests
14. `test_generate_chunk_all_collapsed` - All cells have tile assigned
15. `test_generate_chunk_respects_adjacency` - All neighbors satisfy ADJACENCY_RULES
16. `test_generate_chunk_correct_size` - 8x8 = 64 cells by default
17. `test_generate_chunk_handles_contradiction` - Restarts on contradiction, eventually succeeds

---

## Implementation Steps

1. **Create `tests/test_wfc.py`** with all tests above (they will fail initially)

2. **Create `src/cli_rpg/wfc.py`**:
   ```python
   from dataclasses import dataclass, field
   from typing import Dict, Set, Tuple, Optional, List
   import random
   import math
   from cli_rpg.world_tiles import TileRegistry, ADJACENCY_RULES
   ```

3. **Implement `WFCCell`** dataclass

4. **Implement `WFCGenerator.__init__`** - store registry and seed RNG

5. **Implement `_calculate_entropy`** - Shannon entropy: `sum(-p*log(p) for p in probs)`

6. **Implement `_collapse_cell`** - weighted random using `registry.get_weight()`

7. **Implement `_propagate`** - BFS/queue-based arc consistency:
   - Add collapsed cell to queue
   - For each neighbor: intersect options with valid adjacencies
   - If any neighbor changed, add to queue
   - Return False if any cell reaches 0 options

8. **Implement `generate_chunk`**:
   - Init grid of WFCCells
   - While uncollapsed cells exist:
     - Find min entropy cell (tie-break with RNG)
     - Collapse it
     - Propagate
     - On contradiction: restart with different RNG state
   - Return tile dict

9. **Run tests** - all should pass

---

## Files
- Create: `src/cli_rpg/wfc.py`
- Create: `tests/test_wfc.py`
- Uses: `src/cli_rpg/world_tiles.py` (already exists with TileRegistry)
