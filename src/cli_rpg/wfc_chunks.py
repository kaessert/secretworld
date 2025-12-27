"""ChunkManager for infinite terrain generation via cached WFC-generated chunks.

This module provides a ChunkManager class that generates and caches 8x8 terrain chunks
using the Wave Function Collapse algorithm, with deterministic seeding based on
world coordinates.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List, Set, TYPE_CHECKING
import random
from collections import deque

from cli_rpg.wfc import WFCGenerator, WFCCell
from cli_rpg.world_tiles import TileRegistry, ADJACENCY_RULES, get_biased_weights

if TYPE_CHECKING:
    from cli_rpg.models.location import Location
    from cli_rpg.models.region_context import RegionContext


@dataclass
class ChunkManager:
    """Manages infinite terrain generation via cached WFC-generated chunks.

    Attributes:
        tile_registry: Registry containing tile definitions and weights
        chunk_size: Size of each chunk (default 8x8)
        world_seed: Seed for deterministic world generation
        _chunks: Cache of generated chunks keyed by (chunk_x, chunk_y)
        _region_context: Current region context for biased terrain generation
    """

    tile_registry: TileRegistry
    chunk_size: int = 8
    world_seed: int = 0
    _chunks: Dict[Tuple[int, int], Dict[Tuple[int, int], str]] = field(
        default_factory=dict
    )
    _region_context: Optional["RegionContext"] = None
    _current_weight_overrides: Optional[Dict[str, float]] = None

    def _get_weight(self, tile_name: str) -> float:
        """Get weight for a tile, using current weight override if available.

        Args:
            tile_name: Name of the terrain tile

        Returns:
            Weight from current overrides if present, otherwise from tile_registry
        """
        if self._current_weight_overrides and tile_name in self._current_weight_overrides:
            return self._current_weight_overrides[tile_name]
        return self.tile_registry.get_weight(tile_name)

    def set_region_context(self, region_context: "RegionContext") -> None:
        """Set the current region context for biased terrain generation.

        When set, new chunks will be generated with terrain weights biased
        toward the region's theme (e.g., mountains regions favor mountain terrain).

        Args:
            region_context: RegionContext with theme information for biasing
        """
        self._region_context = region_context

    def get_or_generate_chunk(
        self, chunk_x: int, chunk_y: int
    ) -> Dict[Tuple[int, int], str]:
        """Get cached chunk or generate new one with deterministic seeding.

        Args:
            chunk_x: X coordinate of the chunk
            chunk_y: Y coordinate of the chunk

        Returns:
            Dictionary mapping (world_x, world_y) coordinates to terrain tile names
        """
        key = (chunk_x, chunk_y)
        if key not in self._chunks:
            self._chunks[key] = self._generate_chunk(chunk_x, chunk_y)
        return self._chunks[key]

    def _generate_chunk(
        self, chunk_x: int, chunk_y: int
    ) -> Dict[Tuple[int, int], str]:
        """Generate a new chunk with boundary constraints from neighbors.

        Args:
            chunk_x: X coordinate of the chunk
            chunk_y: Y coordinate of the chunk

        Returns:
            Dictionary mapping (world_x, world_y) coordinates to terrain tile names
        """
        # Deterministic chunk seed
        chunk_seed = hash((self.world_seed, chunk_x, chunk_y)) & 0xFFFFFFFF

        # Get boundary constraints from existing neighbors
        boundary_constraints = self._get_boundary_constraints(chunk_x, chunk_y)

        # Compute biased weights from region context if available
        weight_overrides = None
        if self._region_context is not None:
            weight_overrides = get_biased_weights(self._region_context.theme)

        # Generate chunk with constraints
        origin = (chunk_x * self.chunk_size, chunk_y * self.chunk_size)

        if boundary_constraints:
            return self._generate_with_constraints(
                chunk_seed, origin, boundary_constraints, weight_overrides
            )
        else:
            generator = WFCGenerator(
                self.tile_registry, seed=chunk_seed, weight_overrides=weight_overrides
            )
            return generator.generate_chunk(origin, self.chunk_size)

    def _get_boundary_constraints(
        self, chunk_x: int, chunk_y: int
    ) -> Dict[Tuple[int, int], str]:
        """Get boundary tile constraints from adjacent chunks.

        Returns a dictionary mapping world coordinates to required tiles
        for boundary cells that need to match existing chunks.

        Args:
            chunk_x: X coordinate of the chunk to be generated
            chunk_y: Y coordinate of the chunk to be generated

        Returns:
            Dictionary of (world_x, world_y) -> tile_name for boundary constraints
        """
        constraints: Dict[Tuple[int, int], str] = {}

        # Calculate world coordinate origin for this chunk
        ox = chunk_x * self.chunk_size
        oy = chunk_y * self.chunk_size

        # Check west neighbor (chunk_x - 1, chunk_y)
        west_key = (chunk_x - 1, chunk_y)
        if west_key in self._chunks:
            west_chunk = self._chunks[west_key]
            # East edge of west chunk constrains west edge of new chunk
            west_edge_x = ox - 1
            for y in range(oy, oy + self.chunk_size):
                if (west_edge_x, y) in west_chunk:
                    constraints[(ox, y)] = west_chunk[(west_edge_x, y)]

        # Check east neighbor (chunk_x + 1, chunk_y)
        east_key = (chunk_x + 1, chunk_y)
        if east_key in self._chunks:
            east_chunk = self._chunks[east_key]
            # West edge of east chunk constrains east edge of new chunk
            east_edge_x = ox + self.chunk_size
            for y in range(oy, oy + self.chunk_size):
                if (east_edge_x, y) in east_chunk:
                    constraints[(ox + self.chunk_size - 1, y)] = east_chunk[(east_edge_x, y)]

        # Check south neighbor (chunk_x, chunk_y - 1)
        south_key = (chunk_x, chunk_y - 1)
        if south_key in self._chunks:
            south_chunk = self._chunks[south_key]
            # North edge of south chunk constrains south edge of new chunk
            south_edge_y = oy - 1
            for x in range(ox, ox + self.chunk_size):
                if (x, south_edge_y) in south_chunk:
                    constraints[(x, oy)] = south_chunk[(x, south_edge_y)]

        # Check north neighbor (chunk_x, chunk_y + 1)
        north_key = (chunk_x, chunk_y + 1)
        if north_key in self._chunks:
            north_chunk = self._chunks[north_key]
            # South edge of north chunk constrains north edge of new chunk
            north_edge_y = oy + self.chunk_size
            for x in range(ox, ox + self.chunk_size):
                if (x, north_edge_y) in north_chunk:
                    constraints[(x, oy + self.chunk_size - 1)] = north_chunk[(x, north_edge_y)]

        return constraints

    def _generate_with_constraints(
        self,
        chunk_seed: int,
        origin: Tuple[int, int],
        boundary_constraints: Dict[Tuple[int, int], str],
        weight_overrides: Optional[Dict[str, float]] = None,
    ) -> Dict[Tuple[int, int], str]:
        """Generate chunk with pre-applied boundary constraints using WFC.

        This method creates a WFC grid with edge cells pre-constrained to be
        compatible with existing neighbor chunks, then runs WFC to fill in
        the rest.

        Args:
            chunk_seed: Seed for deterministic generation
            origin: Top-left corner of the chunk (world coordinates)
            boundary_constraints: Mapping of edge coords to required neighbor tiles
            weight_overrides: Optional terrain weight overrides for biased generation

        Returns:
            Dictionary mapping coordinates to terrain tiles
        """
        max_restarts = 100
        rng = random.Random(chunk_seed)

        for restart in range(max_restarts):
            result = self._try_generate_with_constraints(
                rng, origin, boundary_constraints, weight_overrides
            )
            if result is not None:
                return result
            # Advance RNG state for next attempt
            rng.random()

        # Fallback: generate without constraints (shouldn't happen)
        generator = WFCGenerator(
            self.tile_registry, seed=chunk_seed, weight_overrides=weight_overrides
        )
        return generator.generate_chunk(origin, self.chunk_size)

    def _try_generate_with_constraints(
        self,
        rng: random.Random,
        origin: Tuple[int, int],
        boundary_constraints: Dict[Tuple[int, int], str],
        weight_overrides: Optional[Dict[str, float]] = None,
    ) -> Optional[Dict[Tuple[int, int], str]]:
        """Attempt to generate a constrained chunk.

        Args:
            rng: Random number generator
            origin: Top-left corner of the chunk
            boundary_constraints: Required neighbor tiles at boundary positions
            weight_overrides: Optional terrain weight overrides for biased generation

        Returns:
            Generated chunk if successful, None if contradiction detected
        """
        # Store weight overrides for use in helper methods
        self._current_weight_overrides = weight_overrides
        ox, oy = origin
        all_tiles = self.tile_registry.get_all_tile_names()

        # Initialize grid with all cells having all possible tiles
        grid: Dict[Tuple[int, int], WFCCell] = {}
        for x in range(ox, ox + self.chunk_size):
            for y in range(oy, oy + self.chunk_size):
                grid[(x, y)] = WFCCell(
                    coords=(x, y), possible_tiles=all_tiles.copy()
                )

        # Apply boundary constraints: restrict edge cells to be compatible with neighbors
        for edge_coord, neighbor_tile in boundary_constraints.items():
            if edge_coord not in grid:
                continue

            cell = grid[edge_coord]
            # Restrict to tiles that are valid neighbors of the constraint tile
            valid_tiles = ADJACENCY_RULES.get(neighbor_tile, set())
            # Also must be mutually adjacent
            restricted = set()
            for tile in cell.possible_tiles:
                if tile in valid_tiles and neighbor_tile in ADJACENCY_RULES.get(tile, set()):
                    restricted.add(tile)

            if not restricted:
                # Contradiction - no valid tiles
                return None

            cell.possible_tiles = restricted

        # Propagate initial constraints
        for edge_coord in boundary_constraints:
            if edge_coord in grid:
                if not self._propagate(grid, edge_coord):
                    return None

        # Run WFC algorithm on the constrained grid
        while True:
            # Find all uncollapsed cells
            uncollapsed = {
                coords: cell for coords, cell in grid.items() if not cell.collapsed
            }

            if not uncollapsed:
                # All cells collapsed - success!
                break

            # Select cell with minimum entropy
            min_cell = self._select_minimum_entropy_cell(uncollapsed, rng)
            if min_cell is None:
                return None

            # Collapse the cell (pass grid for distance penalty calculations)
            self._collapse_cell(min_cell, rng, grid)

            # Propagate constraints
            if not self._propagate(grid, min_cell.coords):
                # Contradiction detected
                return None

        # Build result dictionary
        return {coords: cell.tile for coords, cell in grid.items()}

    def _select_minimum_entropy_cell(
        self, cells: Dict[Tuple[int, int], WFCCell], rng: random.Random
    ) -> Optional[WFCCell]:
        """Select the uncollapsed cell with minimum entropy.

        Args:
            cells: Dictionary of uncollapsed cells
            rng: Random number generator for tie-breaking

        Returns:
            The cell with lowest entropy, or None if all collapsed
        """
        min_entropy = float("inf")
        min_cell = None

        for cell in cells.values():
            if cell.collapsed:
                continue

            entropy = self._calculate_entropy(cell)
            # Add small random noise to break ties
            noise = rng.random() * 0.0001
            adjusted_entropy = entropy + noise

            if adjusted_entropy < min_entropy:
                min_entropy = adjusted_entropy
                min_cell = cell

        return min_cell

    def _calculate_entropy(self, cell: WFCCell) -> float:
        """Calculate Shannon entropy for a cell based on tile weights.

        Args:
            cell: The cell to calculate entropy for

        Returns:
            Shannon entropy value (0 if only one option)
        """
        import math

        if len(cell.possible_tiles) <= 1:
            return 0.0

        # Use _get_weight to respect current weight overrides
        weights = [self._get_weight(tile) for tile in cell.possible_tiles]
        total_weight = sum(weights)

        if total_weight == 0:
            return 0.0

        entropy = 0.0
        for weight in weights:
            if weight > 0:
                p = weight / total_weight
                entropy -= p * math.log(p)

        return entropy

    def _get_nearby_collapsed_tiles(
        self,
        grid: Dict[Tuple[int, int], WFCCell],
        x: int,
        y: int,
        radius: int = 2,
    ) -> Set[str]:
        """Get terrain types of collapsed tiles within radius.

        Used for biome distance penalty calculations during WFC collapse.

        Args:
            grid: Current WFC grid
            x, y: Center coordinates
            radius: Search radius (default 2)

        Returns:
            Set of terrain types from collapsed cells within radius
        """
        nearby: Set[str] = set()
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                cell = grid.get((x + dx, y + dy))
                if cell and cell.collapsed and cell.tile:
                    nearby.add(cell.tile)
        return nearby

    def _collapse_cell(
        self,
        cell: WFCCell,
        rng: random.Random,
        grid: Optional[Dict[Tuple[int, int], WFCCell]] = None,
    ) -> str:
        """Collapse a cell to a single tile using weighted random selection.

        Applies distance penalties when incompatible biomes are nearby.

        Args:
            cell: The cell to collapse
            rng: Random number generator
            grid: Optional WFC grid for distance penalty calculations

        Returns:
            The selected tile name
        """
        if len(cell.possible_tiles) == 0:
            raise ValueError(f"Cannot collapse cell {cell.coords} with no options")

        tiles = sorted(cell.possible_tiles)
        # Use _get_weight to respect current weight overrides
        weights = [self._get_weight(tile) for tile in tiles]

        # Apply distance penalties if grid provided
        if grid is not None:
            from cli_rpg.world_tiles import get_distance_penalty

            nearby = self._get_nearby_collapsed_tiles(grid, cell.coords[0], cell.coords[1])
            weights = [w * get_distance_penalty(t, nearby) for w, t in zip(weights, tiles)]

        selected = rng.choices(tiles, weights=weights, k=1)[0]

        cell.tile = selected
        cell.possible_tiles = {selected}
        cell.collapsed = True

        return selected

    def _propagate(
        self, grid: Dict[Tuple[int, int], WFCCell], start_coords: Tuple[int, int]
    ) -> bool:
        """Propagate constraints from a cell to its neighbors.

        Args:
            grid: The full grid of cells
            start_coords: Coordinates to start propagation from

        Returns:
            True if propagation succeeded, False if contradiction detected
        """
        queue = deque([start_coords])

        while queue:
            current_coords = queue.popleft()
            current_cell = grid.get(current_coords)

            if current_cell is None:
                continue

            # Get valid tiles that can be adjacent to current cell's options
            x, y = current_coords
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_coords = (x + dx, y + dy)
                neighbor = grid.get(neighbor_coords)

                if neighbor is None or neighbor.collapsed:
                    continue

                # Calculate which tiles are valid for the neighbor
                new_options: Set[str] = set()
                for neighbor_tile in neighbor.possible_tiles:
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
                        # Contradiction
                        return False

                    neighbor.possible_tiles = new_options

                    if neighbor_coords not in queue:
                        queue.append(neighbor_coords)

        return True

    def get_tile_at(self, world_x: int, world_y: int) -> str:
        """Get terrain tile at world coordinates.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            Terrain tile name at the given coordinates
        """
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        chunk = self.get_or_generate_chunk(chunk_x, chunk_y)
        return chunk[(world_x, world_y)]

    def set_tile_at(self, world_x: int, world_y: int, terrain: str) -> None:
        """Set terrain tile at world coordinates.

        This is used to sync WFC terrain with existing locations.
        When a location exists at coordinates, its terrain should be
        set in the chunk to ensure passability checks are consistent.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            terrain: Terrain tile name to set (e.g., "plains", "forest")
        """
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        chunk = self.get_or_generate_chunk(chunk_x, chunk_y)
        chunk[(world_x, world_y)] = terrain

    def sync_with_locations(
        self, world: Dict[str, "Location"], default_terrain: str = "plains"
    ) -> None:
        """Sync WFC terrain with existing location coordinates.

        For each location in the world that has coordinates, ensures the
        WFC terrain at those coordinates is passable. Uses the location's
        terrain field if set, otherwise uses the default terrain.

        This should be called after world creation to ensure the WFC terrain
        matches where locations actually exist.

        Args:
            world: Dictionary mapping location names to Location objects
            default_terrain: Fallback terrain if location has no terrain set
        """
        from cli_rpg.models.location import Location

        for location in world.values():
            if location.coordinates is None:
                continue

            x, y = location.coordinates
            # Use location's terrain if set, otherwise default to passable terrain
            terrain = location.terrain if location.terrain else default_terrain
            self.set_tile_at(x, y, terrain)

    def to_dict(self) -> dict:
        """Serialize ChunkManager state for persistence.

        Returns:
            Dictionary containing world_seed, chunk_size, and cached chunks
        """
        # Serialize chunks with string keys for JSON compatibility
        serialized_chunks = {}
        for (cx, cy), chunk in self._chunks.items():
            chunk_key = f"{cx},{cy}"
            serialized_chunk = {}
            for (wx, wy), tile in chunk.items():
                coord_key = f"{wx},{wy}"
                serialized_chunk[coord_key] = tile
            serialized_chunks[chunk_key] = serialized_chunk

        return {
            "world_seed": self.world_seed,
            "chunk_size": self.chunk_size,
            "chunks": serialized_chunks,
        }

    @classmethod
    def from_dict(cls, data: dict, tile_registry: TileRegistry) -> "ChunkManager":
        """Deserialize ChunkManager from saved state.

        Args:
            data: Serialized state from to_dict()
            tile_registry: TileRegistry to use for generation

        Returns:
            Restored ChunkManager instance
        """
        # Deserialize chunks from string keys
        chunks: Dict[Tuple[int, int], Dict[Tuple[int, int], str]] = {}
        for chunk_key, serialized_chunk in data.get("chunks", {}).items():
            cx, cy = map(int, chunk_key.split(","))
            chunk: Dict[Tuple[int, int], str] = {}
            for coord_key, tile in serialized_chunk.items():
                wx, wy = map(int, coord_key.split(","))
                chunk[(wx, wy)] = tile
            chunks[(cx, cy)] = chunk

        manager = cls(
            tile_registry=tile_registry,
            chunk_size=data.get("chunk_size", 8),
            world_seed=data.get("world_seed", 0),
        )
        manager._chunks = chunks
        return manager
