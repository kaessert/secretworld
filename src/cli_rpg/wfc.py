"""Wave Function Collapse (WFC) algorithm for procedural terrain generation.

This module implements the WFC algorithm for generating coherent terrain chunks
that respect adjacency constraints defined in world_tiles.py.
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, Optional, List
import random
import math
from collections import deque

from cli_rpg.world_tiles import TileRegistry, ADJACENCY_RULES


@dataclass
class WFCCell:
    """Represents a single cell in the WFC grid.

    Attributes:
        coords: Cell position as (x, y) tuple
        possible_tiles: Set of terrain types this cell can still become
        collapsed: Whether cell has been resolved to a final tile
        tile: Final tile type (set when collapsed)
    """

    coords: Tuple[int, int]
    possible_tiles: Set[str]
    collapsed: bool = False
    tile: Optional[str] = None


class WFCGenerator:
    """Wave Function Collapse generator for terrain chunks.

    Uses constraint propagation to generate terrain that respects
    adjacency rules defined in ADJACENCY_RULES.
    """

    # Maximum restart attempts before giving up
    MAX_RESTARTS = 100

    def __init__(self, tile_registry: TileRegistry, seed: int):
        """Initialize the WFC generator.

        Args:
            tile_registry: Registry containing tile definitions and weights
            seed: Random seed for deterministic generation
        """
        self.tile_registry = tile_registry
        self.seed = seed
        self._rng = random.Random(seed)

    def generate_chunk(
        self, origin: Tuple[int, int], size: int = 8
    ) -> Dict[Tuple[int, int], str]:
        """Generate a terrain chunk using WFC algorithm.

        Args:
            origin: Top-left corner of the chunk as (x, y)
            size: Width and height of the chunk (default 8x8)

        Returns:
            Dictionary mapping (x, y) coordinates to terrain tile names
        """
        for attempt in range(self.MAX_RESTARTS):
            result = self._try_generate_chunk(origin, size)
            if result is not None:
                return result
            # On failure, advance RNG state to get different results
            self._rng.random()

        # If we somehow exhausted all attempts, return partial result
        # (This shouldn't happen with well-defined adjacency rules)
        raise RuntimeError(
            f"WFC failed to generate chunk after {self.MAX_RESTARTS} attempts"
        )

    def _try_generate_chunk(
        self, origin: Tuple[int, int], size: int
    ) -> Optional[Dict[Tuple[int, int], str]]:
        """Attempt to generate a chunk, returning None on contradiction."""
        all_tiles = self.tile_registry.get_all_tile_names()
        ox, oy = origin

        # Initialize grid with all cells having all possible tiles
        grid: Dict[Tuple[int, int], WFCCell] = {}
        for x in range(ox, ox + size):
            for y in range(oy, oy + size):
                grid[(x, y)] = WFCCell(
                    coords=(x, y), possible_tiles=all_tiles.copy()
                )

        # Main WFC loop
        while True:
            # Find all uncollapsed cells
            uncollapsed = {
                coords: cell for coords, cell in grid.items() if not cell.collapsed
            }

            if not uncollapsed:
                # All cells collapsed - success!
                break

            # Select cell with minimum entropy
            min_cell = self._select_minimum_entropy_cell(uncollapsed)

            # Collapse the cell
            self._collapse_cell(min_cell)

            # Propagate constraints
            if not self._propagate(grid, min_cell.coords):
                # Contradiction detected - restart
                return None

        # Build result dictionary
        return {coords: cell.tile for coords, cell in grid.items()}

    def _calculate_entropy(self, cell: WFCCell) -> float:
        """Calculate Shannon entropy for a cell based on tile weights.

        Entropy = -sum(p * log(p)) where p is the probability of each tile.

        Args:
            cell: The cell to calculate entropy for

        Returns:
            Shannon entropy value (0 if only one option)
        """
        if len(cell.possible_tiles) <= 1:
            return 0.0

        # Calculate total weight
        weights = [
            self.tile_registry.get_weight(tile) for tile in cell.possible_tiles
        ]
        total_weight = sum(weights)

        if total_weight == 0:
            return 0.0

        # Calculate Shannon entropy
        entropy = 0.0
        for weight in weights:
            if weight > 0:
                p = weight / total_weight
                entropy -= p * math.log(p)

        return entropy

    def _select_minimum_entropy_cell(
        self, cells: Dict[Tuple[int, int], WFCCell]
    ) -> WFCCell:
        """Select the uncollapsed cell with minimum entropy.

        Ties are broken using random noise to ensure variety.

        Args:
            cells: Dictionary of uncollapsed cells

        Returns:
            The cell with lowest entropy
        """
        min_entropy = float("inf")
        min_cell = None

        for cell in cells.values():
            # Skip already-collapsed cells
            if cell.collapsed:
                continue

            entropy = self._calculate_entropy(cell)
            # Add small random noise to break ties
            noise = self._rng.random() * 0.0001
            adjusted_entropy = entropy + noise

            if adjusted_entropy < min_entropy:
                min_entropy = adjusted_entropy
                min_cell = cell

        return min_cell

    def _collapse_cell(self, cell: WFCCell) -> str:
        """Collapse a cell to a single tile using weighted random selection.

        Args:
            cell: The cell to collapse

        Returns:
            The selected tile name
        """
        if len(cell.possible_tiles) == 0:
            raise ValueError(f"Cannot collapse cell {cell.coords} with no options")

        # Build weighted list (sorted for deterministic iteration order)
        tiles = sorted(cell.possible_tiles)
        weights = [self.tile_registry.get_weight(tile) for tile in tiles]

        # Weighted random selection
        selected = self._rng.choices(tiles, weights=weights, k=1)[0]

        # Update cell state
        cell.tile = selected
        cell.possible_tiles = {selected}
        cell.collapsed = True

        return selected

    def _propagate(
        self, grid: Dict[Tuple[int, int], WFCCell], collapsed_coords: Tuple[int, int]
    ) -> bool:
        """Propagate constraints from a collapsed cell to its neighbors.

        Uses BFS-based arc consistency to propagate changes through the grid.

        Args:
            grid: The full grid of cells
            collapsed_coords: Coordinates of the just-collapsed cell

        Returns:
            True if propagation succeeded, False if contradiction detected
        """
        # Queue of cells that need their neighbors updated
        queue = deque([collapsed_coords])

        while queue:
            current_coords = queue.popleft()
            current_cell = grid.get(current_coords)

            if current_cell is None:
                continue

            # Get valid tiles that can be adjacent to current cell's options
            valid_neighbor_tiles = set()
            for tile in current_cell.possible_tiles:
                valid_neighbor_tiles.update(ADJACENCY_RULES.get(tile, set()))

            # Check all 4 neighbors
            x, y = current_coords
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_coords = (x + dx, y + dy)
                neighbor = grid.get(neighbor_coords)

                if neighbor is None or neighbor.collapsed:
                    continue

                # Calculate which tiles are valid for the neighbor
                # Must be valid adjacent to current cell AND current cell must be valid adjacent to them
                new_options = set()
                for neighbor_tile in neighbor.possible_tiles:
                    # Check: can this neighbor tile be adjacent to any of current's options?
                    for current_tile in current_cell.possible_tiles:
                        if (
                            neighbor_tile in ADJACENCY_RULES.get(current_tile, set())
                            and current_tile in ADJACENCY_RULES.get(neighbor_tile, set())
                        ):
                            new_options.add(neighbor_tile)
                            break

                # Check if options were reduced
                if new_options != neighbor.possible_tiles:
                    if len(new_options) == 0:
                        # Contradiction - no valid tiles for this cell
                        return False

                    neighbor.possible_tiles = new_options

                    # Add to queue to propagate changes further
                    if neighbor_coords not in queue:
                        queue.append(neighbor_coords)

        return True
