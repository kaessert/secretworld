# Plan: Reduce MAX_TILES_WITHOUT_ENTERABLE from 25 to 15

## Task
Complete the "Increase Named Location Density" issue by reducing `MAX_TILES_WITHOUT_ENTERABLE` from 25 to 15 in `world_tiles.py`.

## Change
**File:** `src/cli_rpg/world_tiles.py` (line 924)

```python
# Before
MAX_TILES_WITHOUT_ENTERABLE = 25

# After
MAX_TILES_WITHOUT_ENTERABLE = 15
```

## Tests
Existing tests should continue to pass - this config change affects gameplay density, not test logic.

```bash
pytest tests/test_named_locations_enterable.py -v
pytest tests/test_world_tiles.py -v
```

## Update ISSUES.md
Mark "Reduce Tiles Between Enterables" as complete in the "Increase Named Location Density" issue.
