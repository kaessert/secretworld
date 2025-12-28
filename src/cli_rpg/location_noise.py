"""Pure-Python simplex noise for deterministic location density calculations.

Implements 2D simplex noise algorithm for natural clustering of named locations
in world generation. No external dependencies (no numpy, no noise libraries).
"""

import math
import random
from typing import Optional


class SimplexNoise:
    """Pure-Python 2D simplex noise generator.

    Uses Ken Perlin's simplex noise algorithm with deterministic seeded
    permutation tables for reproducible noise patterns.
    """

    # Skewing factors for 2D simplex
    F2 = 0.5 * (math.sqrt(3.0) - 1.0)  # Skew factor for 2D
    G2 = (3.0 - math.sqrt(3.0)) / 6.0  # Unskew factor for 2D

    # Standard 2D gradients (12 directions on unit circle)
    GRADIENTS_2D = [
        (1, 1), (-1, 1), (1, -1), (-1, -1),
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (-1, 1), (1, -1), (-1, -1),
    ]

    def __init__(self, seed: int):
        """Initialize simplex noise with a seed.

        Args:
            seed: Random seed for deterministic permutation table.
        """
        self.seed = seed
        self._perm = self._generate_permutation(seed)
        # Double permutation table to avoid index wrapping
        self._perm_mod12 = [p % 12 for p in self._perm]

    def _generate_permutation(self, seed: int) -> list[int]:
        """Generate a seeded permutation table.

        Args:
            seed: Random seed.

        Returns:
            512-element permutation table (256 values repeated).
        """
        rng = random.Random(seed)
        perm = list(range(256))
        rng.shuffle(perm)
        # Double the table to avoid index wrapping
        return perm + perm

    def _dot2(self, g: tuple[int, int], x: float, y: float) -> float:
        """Dot product of gradient and offset vector.

        Args:
            g: Gradient vector (2D).
            x, y: Offset vector components.

        Returns:
            Dot product result.
        """
        return g[0] * x + g[1] * y

    def noise2d(self, x: float, y: float) -> float:
        """Generate 2D simplex noise at coordinates.

        Args:
            x, y: Input coordinates.

        Returns:
            Noise value in range [-1, 1].
        """
        # Skew input space to determine which simplex cell we're in
        s = (x + y) * self.F2
        i = int(math.floor(x + s))
        j = int(math.floor(y + s))

        # Unskew cell origin back to (x, y) space
        t = (i + j) * self.G2
        x0 = x - (i - t)  # Offset from cell origin in (x, y) space
        y0 = y - (j - t)

        # Determine which simplex we're in (upper or lower triangle)
        if x0 > y0:
            i1, j1 = 1, 0  # Lower triangle, XY order
        else:
            i1, j1 = 0, 1  # Upper triangle, YX order

        # Offsets for middle corner in (x, y) unskewed coords
        x1 = x0 - i1 + self.G2
        y1 = y0 - j1 + self.G2

        # Offsets for last corner in (x, y) unskewed coords
        x2 = x0 - 1.0 + 2.0 * self.G2
        y2 = y0 - 1.0 + 2.0 * self.G2

        # Wrap indices to permutation table range
        ii = i & 255
        jj = j & 255

        # Calculate gradient indices
        gi0 = self._perm_mod12[ii + self._perm[jj]]
        gi1 = self._perm_mod12[ii + i1 + self._perm[jj + j1]]
        gi2 = self._perm_mod12[ii + 1 + self._perm[jj + 1]]

        # Calculate contributions from three corners
        n0 = n1 = n2 = 0.0

        # Corner 0
        t0 = 0.5 - x0 * x0 - y0 * y0
        if t0 >= 0:
            t0 *= t0
            n0 = t0 * t0 * self._dot2(self.GRADIENTS_2D[gi0], x0, y0)

        # Corner 1
        t1 = 0.5 - x1 * x1 - y1 * y1
        if t1 >= 0:
            t1 *= t1
            n1 = t1 * t1 * self._dot2(self.GRADIENTS_2D[gi1], x1, y1)

        # Corner 2
        t2 = 0.5 - x2 * x2 - y2 * y2
        if t2 >= 0:
            t2 *= t2
            n2 = t2 * t2 * self._dot2(self.GRADIENTS_2D[gi2], x2, y2)

        # Scale to return value in [-1, 1]
        # The magic number 70.0 is the standard scaling factor for 2D simplex noise
        return 70.0 * (n0 + n1 + n2)


class LocationNoiseManager:
    """Manages noise-based location density for world generation.

    Uses multi-octave simplex noise to create natural clustering patterns
    for named location spawning. Respects terrain modifiers from
    NAMED_LOCATION_CONFIG in world_tiles.py.
    """

    # Multi-octave noise parameters
    OCTAVES = 3
    PERSISTENCE = 0.5  # Amplitude reduction per octave
    LACUNARITY = 2.0   # Frequency increase per octave
    SCALE = 0.05       # Base scale for coordinate input

    # Base spawn probability at density 0.5 (matches current base_interval behavior)
    BASE_SPAWN_PROBABILITY = 0.20  # ~33% more named locations

    def __init__(self, world_seed: int):
        """Initialize location noise manager.

        Args:
            world_seed: World seed for deterministic generation.
        """
        self.world_seed = world_seed
        self._noise = SimplexNoise(seed=world_seed)
        # Create a separate RNG for spawn decisions, seeded deterministically
        self._spawn_rng_base = world_seed

    def get_location_density(self, x: int, y: int) -> float:
        """Get location density at world coordinates.

        Uses multi-octave noise for natural clustering patterns.

        Args:
            x, y: World coordinates (integers).

        Returns:
            Density value in [0, 1] where higher = more likely to spawn.
        """
        density = 0.0
        amplitude = 1.0
        frequency = self.SCALE
        max_amplitude = 0.0

        for _ in range(self.OCTAVES):
            noise_val = self._noise.noise2d(x * frequency, y * frequency)
            density += noise_val * amplitude
            max_amplitude += amplitude
            amplitude *= self.PERSISTENCE
            frequency *= self.LACUNARITY

        # Normalize to [-1, 1] then scale to [0, 1]
        density /= max_amplitude
        density = (density + 1.0) / 2.0

        # Clamp to [0, 1] for safety
        return max(0.0, min(1.0, density))

    def should_spawn_location(
        self,
        x: int,
        y: int,
        terrain: str,
    ) -> bool:
        """Determine if a named location should spawn at coordinates.

        Combines noise-based density with terrain modifiers from
        NAMED_LOCATION_CONFIG.

        Args:
            x, y: World coordinates.
            terrain: Terrain type at the location.

        Returns:
            True if a named location should spawn here.
        """
        # Import terrain modifiers
        from cli_rpg.world_tiles import NAMED_LOCATION_CONFIG

        # Get base density from noise
        density = self.get_location_density(x, y)

        # Get terrain modifier (lower = more likely to spawn)
        terrain_modifier = NAMED_LOCATION_CONFIG["terrain_modifiers"].get(terrain, 1.0)

        # Calculate spawn probability
        # Higher density + lower terrain modifier = higher spawn chance
        # Invert modifier: mountain (0.6) becomes 1.67x more likely
        # plains (1.2) becomes 0.83x less likely
        spawn_probability = density * self.BASE_SPAWN_PROBABILITY / terrain_modifier

        # Clamp probability
        spawn_probability = max(0.0, min(1.0, spawn_probability))

        # Use deterministic RNG based on coordinates
        coord_seed = self._spawn_rng_base + x * 31337 + y * 7919
        rng = random.Random(coord_seed)

        return rng.random() < spawn_probability
