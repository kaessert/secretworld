# Implementation Plan: location_noise.py with Pure-Python Simplex Noise

## Spec

Create `src/cli_rpg/location_noise.py` implementing pure-Python simplex noise for deterministic, seeded location density calculations with natural clustering. This replaces the current linear probability curve in `should_generate_named_location()` with noise-based density.

### Requirements
1. **Pure Python**: No external dependencies (no numpy, no noise libraries)
2. **2D Simplex Noise**: Standard algorithm with gradient tables and permutation
3. **Deterministic**: Same world seed produces identical location patterns
4. **Multi-octave**: Support layered noise for natural clustering patterns
5. **Location Density API**: Transform noise values to spawn probabilities

### Public Interface
```python
class SimplexNoise:
    """Pure-Python 2D simplex noise generator."""
    def __init__(self, seed: int): ...
    def noise2d(self, x: float, y: float) -> float: ...  # Returns [-1, 1]

class LocationNoiseManager:
    """Manages noise-based location density for world generation."""
    def __init__(self, world_seed: int): ...
    def get_location_density(self, x: int, y: int) -> float: ...  # Returns [0, 1]
    def should_spawn_location(self, x: int, y: int, terrain: str) -> bool: ...
```

### Integration Points
- Called by `game_state.py` during movement instead of `should_generate_named_location()`
- Uses terrain modifiers from `NAMED_LOCATION_CONFIG` in `world_tiles.py`
- Respects existing `tiles_since_named` counter for minimum spacing

---

## Tests First (TDD)

Create `tests/test_location_noise.py`:

### SimplexNoise Tests
1. `test_simplex_returns_float_in_range` - noise2d returns value in [-1, 1]
2. `test_simplex_deterministic_same_seed` - same seed + coords = same value
3. `test_simplex_different_seeds_differ` - different seeds produce different values
4. `test_simplex_varies_with_position` - adjacent coords produce different values
5. `test_simplex_gradient_smoothness` - nearby coords have similar values (continuity)

### LocationNoiseManager Tests
6. `test_density_returns_float_in_range` - get_location_density returns [0, 1]
7. `test_density_deterministic_same_seed` - same seed = same density map
8. `test_density_varies_spatially` - different coords produce different densities
9. `test_should_spawn_respects_density` - high density = higher spawn chance
10. `test_should_spawn_terrain_modifiers` - mountain terrain increases spawn chance
11. `test_should_spawn_deterministic` - same inputs = same result
12. `test_clustering_nearby_coords_similar` - adjacent tiles have similar density (clustering)

---

## Implementation Steps

### Step 1: Create test file
- File: `tests/test_location_noise.py`
- Import from `cli_rpg.location_noise`
- Write all 12 tests (expect failures initially)

### Step 2: Implement SimplexNoise class
- File: `src/cli_rpg/location_noise.py`
- Implement permutation table generation from seed
- Implement gradient vectors (12 standard 2D gradients)
- Implement `noise2d()` using simplex lattice algorithm
- Run tests 1-5, verify passing

### Step 3: Implement LocationNoiseManager class
- File: `src/cli_rpg/location_noise.py` (same file)
- Multi-octave noise combining 3 layers (detail, medium, large-scale)
- `get_location_density()` normalizes to [0, 1]
- `should_spawn_location()` applies terrain modifiers from `NAMED_LOCATION_CONFIG`
- Run tests 6-12, verify passing

### Step 4: Run full test suite
- `pytest tests/test_location_noise.py -v`
- `pytest` (ensure no regressions in 5052 tests)

---

## Algorithm Reference

### Simplex Noise 2D (Ken Perlin's improved algorithm)
1. Skew input coords to simplex space: `F2 = 0.5 * (sqrt(3) - 1)`
2. Determine simplex triangle containing point
3. Calculate contributions from 3 corners
4. Each corner: dot product of gradient and offset, attenuated by distance
5. Sum contributions, scale to [-1, 1]

### Multi-octave Combination
```python
density = 0
amplitude = 1.0
frequency = 1.0
for _ in range(octaves):
    density += noise.noise2d(x * frequency, y * frequency) * amplitude
    amplitude *= persistence  # 0.5 typical
    frequency *= lacunarity   # 2.0 typical
density = (density + 1) / 2  # Normalize to [0, 1]
```
