# Implementation Summary: location_noise.py

## What Was Implemented

Created `src/cli_rpg/location_noise.py` with two classes:

### SimplexNoise Class
- Pure-Python 2D simplex noise generator (no external dependencies)
- Uses Ken Perlin's simplex noise algorithm
- Seeded permutation tables for deterministic, reproducible noise patterns
- Standard 12-direction gradient vectors on unit circle
- `noise2d(x, y)` returns values in [-1, 1]

### LocationNoiseManager Class
- Multi-octave noise (3 octaves, persistence 0.5, lacunarity 2.0)
- `get_location_density(x, y)` returns density in [0, 1]
- `should_spawn_location(x, y, terrain)` determines if location should spawn
- Integrates with terrain modifiers from `NAMED_LOCATION_CONFIG` in `world_tiles.py`
- Fully deterministic: same world_seed + coordinates = same result

## Files Created/Modified

| File | Action |
|------|--------|
| `src/cli_rpg/location_noise.py` | Created (new module) |
| `tests/test_location_noise.py` | Created (12 tests) |

## Test Results

All 12 tests passing:
- 5 SimplexNoise tests (range, determinism, seed variation, position variation, smoothness)
- 7 LocationNoiseManager tests (density range, determinism, spatial variation, spawn density correlation, terrain modifiers, spawn determinism, clustering)

Full test suite: **5064 passed, 4 skipped** (no regressions)

## Technical Details

### Simplex Noise Algorithm
1. Skew input coordinates to simplex space using F2 = 0.5 * (sqrt(3) - 1)
2. Determine which simplex triangle contains the point
3. Calculate contributions from 3 triangle corners
4. Each corner: dot product of gradient and offset, attenuated by distance^4
5. Sum contributions, scale by 70.0 to normalize to [-1, 1]

### Multi-Octave Combination
```python
for octave in range(3):
    density += noise.noise2d(x * frequency, y * frequency) * amplitude
    amplitude *= 0.5   # persistence
    frequency *= 2.0   # lacunarity
```

### Spawn Probability
```python
spawn_probability = density * BASE_SPAWN_PROBABILITY / terrain_modifier
```
Where `terrain_modifier` comes from `NAMED_LOCATION_CONFIG["terrain_modifiers"]`.

## E2E Validation

To validate the noise-based location spawning works correctly in-game:
1. Run the game with a fixed seed
2. Walk in multiple directions and observe named location spawn patterns
3. Verify locations cluster naturally (not uniform distribution)
4. Verify mountain/swamp terrain has more POIs than plains

## Integration Notes

The module is ready for integration into `game_state.py`. To use:
```python
from cli_rpg.location_noise import LocationNoiseManager

# In GameState.__init__ or similar
self.location_noise = LocationNoiseManager(world_seed)

# Replace should_generate_named_location() call with:
generate_named = self.location_noise.should_spawn_location(x, y, terrain)
```
