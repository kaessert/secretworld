# Fix "up/down" Documentation Inconsistency

**Task**: Remove "up, down" from README.md since the grid system uses 2D coordinates only.

## Change

**File**: `README.md`, line 41

**Current**:
```
- `go <direction>` - Move in a direction (north, south, east, west, up, down)
```

**Updated**:
```
- `go <direction>` - Move in a direction (north, south, east, west)
```

## Verification

- Confirm the in-game help matches (north, south, east, west only)
- Mark issue as RESOLVED in ISSUES.md
