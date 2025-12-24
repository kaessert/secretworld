# Implementation Plan: Grid-Based Map Structure

## Objective
Refactor the world representation from a flat `dict[str, Location]` with arbitrary connections to a grid/matrix-based system where locations have spatial coordinates, ensuring geographic consistency (going "north" then "south" returns to the same place).

## Specification

### Core Requirements
1. **Coordinate System**: Each location has (x, y) coordinates (optionally z for up/down)
2. **Directional Consistency**: Moving north increases y, south decreases y, east increases x, west decreases x
3. **Bidirectional Guarantee**: If A connects north to B, B must connect south to A
4. **Backward Compatibility**: Existing `dict[str, Location]` interface must still work for serialization/persistence

### Data Model Changes

**New `WorldGrid` class** (`src/cli_rpg/world_grid.py`):
- Internal storage: `dict[tuple[int, int], Location]` for coordinate-based lookup
- Maintains `dict[str, Location]` view for backward compatibility
- Validates spatial consistency on all mutations

**Updated `Location` model**:
- Add optional `coordinates: tuple[int, int] | None` field
- Connections remain as-is (direction -> name mapping) for compatibility
- `to_dict()`/`from_dict()` extended to include coordinates

### Key Design Decisions
- Grid is sparse (not all coordinates filled) to allow natural terrain
- Coordinate (0, 0) is the default starting location
- `up`/`down` use z-axis or special handling (portals/stairs)
- AI world generation will place locations on grid instead of random connections

## Test Plan

### Phase 1: Unit Tests for WorldGrid (`tests/test_world_grid.py`)

```python
# Test coordinate-based location storage
def test_add_location_with_coordinates()
def test_get_location_by_coordinates()
def test_get_location_by_name()  # backward compat

# Test directional consistency
def test_moving_north_increases_y()
def test_moving_south_decreases_y()
def test_moving_east_increases_x()
def test_moving_west_decreases_x()

# Test bidirectional connections
def test_add_location_creates_bidirectional_connections()
def test_north_south_roundtrip_returns_to_same_location()
def test_east_west_roundtrip_returns_to_same_location()

# Test spatial validation
def test_cannot_add_location_at_occupied_coordinates()
def test_cannot_create_inconsistent_connection()

# Test backward compatibility
def test_world_grid_as_dict_returns_location_dict()
def test_serialization_roundtrip()
```

### Phase 2: Updated Location Tests (`tests/test_location.py`)

```python
def test_location_with_coordinates()
def test_location_coordinates_in_to_dict()
def test_location_coordinates_from_dict()
def test_location_without_coordinates_defaults_to_none()
```

### Phase 3: Integration Tests (`tests/test_world_grid_integration.py`)

```python
def test_game_state_with_world_grid()
def test_default_world_uses_grid_layout()
def test_ai_world_generation_uses_grid()
def test_movement_returns_to_start_after_north_south()
```

## Implementation Steps

### Step 1: Add coordinates to Location model
**File**: `src/cli_rpg/models/location.py`
- Add `coordinates: tuple[int, int] | None = None` field
- Update `to_dict()` to include coordinates (when present)
- Update `from_dict()` to parse coordinates (optional)
- Run existing tests to ensure backward compatibility

### Step 2: Create WorldGrid class
**File**: `src/cli_rpg/world_grid.py` (new file)

```python
@dataclass
class WorldGrid:
    """Grid-based world representation with spatial consistency."""

    _grid: dict[tuple[int, int], Location]  # (x, y) -> Location
    _by_name: dict[str, Location]           # name -> Location (for compat)

    def add_location(self, location: Location, x: int, y: int) -> None
    def get_by_coordinates(self, x: int, y: int) -> Location | None
    def get_by_name(self, name: str) -> Location | None
    def get_neighbor(self, x: int, y: int, direction: str) -> Location | None
    def as_dict(self) -> dict[str, Location]  # backward compat
    def to_dict(self) -> dict  # serialization
    @classmethod
    def from_dict(cls, data: dict) -> "WorldGrid"
```

Direction offsets:
- north: (0, +1)
- south: (0, -1)
- east: (+1, 0)
- west: (-1, 0)

### Step 3: Update create_default_world()
**File**: `src/cli_rpg/world.py`
- Refactor to use WorldGrid internally
- Place Town Square at (0, 0)
- Place Forest at (0, 1) - north
- Place Cave at (1, 0) - east
- Return `world_grid.as_dict()` for backward compatibility initially

### Step 4: Update GameState to use WorldGrid
**File**: `src/cli_rpg/game_state.py`
- Accept either `dict[str, Location]` or `WorldGrid` in constructor
- Internal logic uses WorldGrid if available
- Ensure `move()` leverages grid coordinates when present

### Step 5: Update AI world generation
**File**: `src/cli_rpg/ai_world.py`
- `create_ai_world()`: Generate locations on grid starting from (0, 0)
- `expand_world()`: Place new locations at appropriate grid coordinates
- Ensure bidirectional connections are automatically created based on coordinates

### Step 6: Update persistence
**File**: `src/cli_rpg/persistence.py`
- `save_game_state()`: Include grid coordinates in world data
- `load_game_state()`: Reconstruct WorldGrid from saved coordinates
- Maintain backward compatibility with saves that lack coordinates

## File Change Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/models/location.py` | Add `coordinates` field |
| `src/cli_rpg/world_grid.py` | **NEW** - WorldGrid class |
| `src/cli_rpg/world.py` | Use WorldGrid in `create_default_world()` |
| `src/cli_rpg/game_state.py` | Support WorldGrid, coordinate-based movement |
| `src/cli_rpg/ai_world.py` | Grid-based AI generation |
| `src/cli_rpg/persistence.py` | Serialize/deserialize coordinates |
| `tests/test_world_grid.py` | **NEW** - WorldGrid unit tests |
| `tests/test_location.py` | Add coordinate tests |
| `tests/test_world_grid_integration.py` | **NEW** - Integration tests |

## Migration Strategy
1. All changes maintain backward compatibility with existing saves
2. Locations without coordinates treated as "legacy" (no grid validation)
3. New worlds/locations get coordinates automatically
4. Existing tests must continue to pass throughout
