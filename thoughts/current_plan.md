# Implementation Plan: Fix WFC Chunk Boundary Adjacency Bug

## Problem
The `test_large_area_traversal` test in `test_wfc_chunks.py` is flaky - it sometimes fails with invalid adjacencies at chunk boundaries (e.g., `swamp -> desert`, `forest -> beach`).

## Root Cause
**Non-deterministic set iteration** causes WFC to generate different terrain each run, even with the same seed:

1. `_collapse_cell()` in both `wfc.py` (line 196) and `wfc_chunks.py` (line 333) converts `cell.possible_tiles` (a `Set[str]`) to a list via `list(cell.possible_tiles)`
2. Python's hash randomization causes set iteration order to vary between runs
3. This causes `random.choices()` to associate different weights with different tiles, producing different results

When incompatible tiles are randomly generated at chunk boundaries, there's no mechanism to correct them.

## Fix Strategy
Sort all sets before iteration to ensure deterministic order. This makes WFC generation reproducible with a given seed.

## Files to Modify
| File | Lines | Change |
|------|-------|--------|
| `src/cli_rpg/wfc.py` | 196 | `list(cell.possible_tiles)` → `sorted(cell.possible_tiles)` |
| `src/cli_rpg/wfc_chunks.py` | 333 | `list(cell.possible_tiles)` → `sorted(cell.possible_tiles)` |

## Implementation Steps

### 1. Fix `wfc.py:_collapse_cell()`
```python
# Line 196: Change
tiles = list(cell.possible_tiles)
# To:
tiles = sorted(cell.possible_tiles)
```

### 2. Fix `wfc_chunks.py:_collapse_cell()`
```python
# Line 333: Change
tiles = list(cell.possible_tiles)
# To:
tiles = sorted(cell.possible_tiles)
```

## Tests
The existing test `test_large_area_traversal` should pass consistently after the fix. Verify with multiple runs:

```bash
# Run the specific test multiple times to verify no flakiness
for i in {1..20}; do pytest tests/test_wfc_chunks.py::test_large_area_traversal -v; done
```

Also run the full WFC test suite:
```bash
pytest tests/test_wfc_chunks.py tests/test_wfc.py -v
```
