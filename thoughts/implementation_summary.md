# Implementation Summary: CellularAutomataGenerator for Caves and Mines

## What Was Implemented

### New Class: `CellularAutomataGenerator`

A procedural layout generator using cellular automata algorithm for organic, cave-like interior layouts. Located in `src/cli_rpg/procedural_interiors.py`.

**Key Features:**
- **Cellular Automata Algorithm**: Uses the 4-5 rule (cell becomes solid if ≥5 neighbors are solid) to generate organic cave shapes
- **Initial Noise**: Starts with 45% solid fill, then applies automata rules for 4 iterations
- **Flood Fill Connectivity**: Ensures all traversable cells connect to entry point
- **3D Support**: Handles multi-level caves with z-axis navigation (up/down stairs)
- **Room Type Assignment**: ENTRY at top level, BOSS_ROOM at deepest level, TREASURE/PUZZLE at dead ends
- **Deterministic**: Same seed produces identical layouts
- **Bounds-Aware**: Respects 6-tuple bounds `(min_x, max_x, min_y, max_y, min_z, max_z)`

**Public Interface:**
```python
class CellularAutomataGenerator:
    INITIAL_FILL_PROBABILITY = 0.45
    AUTOMATA_ITERATIONS = 4
    BIRTH_THRESHOLD = 5
    DEATH_THRESHOLD = 4

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int): ...
    def generate(self) -> list[RoomTemplate]: ...
```

### Updated Factory Function

The `generate_interior_layout()` factory now uses `CellularAutomataGenerator` for "cave" and "mine" categories:

```python
if generator_type == "CellularAutomataGenerator":
    generator = CellularAutomataGenerator(bounds=bounds, seed=seed)
    return generator.generate()
```

### Helper Constants Added

Added to `procedural_interiors.py`:
- `DIRECTION_OFFSETS`: Maps direction strings to 3D coordinate offsets
- `OPPOSITE_DIRECTION`: Maps directions to their opposites

## Files Modified

1. **`src/cli_rpg/procedural_interiors.py`**
   - Added `CellularAutomataGenerator` class (~310 lines)
   - Added `DIRECTION_OFFSETS` and `OPPOSITE_DIRECTION` constants
   - Updated `generate_interior_layout()` to use new generator

2. **`tests/test_cellular_automata_generator.py`** (NEW)
   - 21 tests covering core algorithm, cave layouts, multi-level support, room types, and integration

## Test Results

- **New Tests**: 21 tests in `test_cellular_automata_generator.py` - All passing
- **Related Tests**: 55 tests in procedural modules - All passing
- **Full Suite**: 5102 tests passed, 4 skipped, no regressions

## Algorithm Details

1. **Grid Initialization**: Create 2D grid with random noise (45% solid), borders always solid
2. **Cellular Automata Smoothing**: 4 iterations of the 4-5 rule (8-neighbor count)
3. **Flood Fill**: Find largest connected region starting from center
4. **Room Creation**: Convert connected cells to RoomTemplates with world coordinates
5. **Connection Building**: Add cardinal direction connections based on adjacency
6. **Level Linking**: Add up/down stair connections between z-levels
7. **Room Type Assignment**: Entry at center of max_z, Boss at min_z, Treasure/Puzzle at dead ends

## E2E Validation

The implementation should be validated with the following scenarios:
- Entering a cave location generates an organic layout
- Entering a mine location generates similar organic layout
- Multi-level caves have stair connections between levels
- All rooms are reachable from the entry point
- Cave layouts are visibly irregular (not rectangular grids)
