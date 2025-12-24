## Active Issues

_No active issues at this time._

---

## Resolved Issues

### Grid-based map structure
**Status**: RESOLVED

**Original Problem**: Map should be more logically laid out instead of connecting random locations to each other. There should be a logical representation of the map under the hood like a matrix.

**Solution Implemented**:
- Created `WorldGrid` class (`src/cli_rpg/world_grid.py`) with coordinate-based storage
- Locations now have optional `coordinates: Tuple[int, int]` field
- Direction offsets ensure spatial consistency: north=(0,+1), south=(0,-1), east=(+1,0), west=(-1,0)
- Moving north then south returns to the same location (geographic consistency)
- Bidirectional connections are automatically created based on coordinates
- Backward compatible with existing saves via `from_legacy_dict()`

**Test Coverage**: 38 new tests verify grid functionality:
- 20 WorldGrid unit tests
- 8 Location coordinate tests
- 10 Integration tests for movement roundtrips and save/load
