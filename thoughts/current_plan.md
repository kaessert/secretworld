# Fix README Direction Shortcut Documentation

## Task
Update README.md to clarify that `s` and `e` are NOT direction shortcuts (they're hijacked by `status` and `equip` commands). Only `gs` and `ge` work for south and east.

## Implementation

**File**: `README.md` (lines 57-58)

**Current text**:
```markdown
- `go <direction>` (g) - Move in a direction (north/n, south/s, east/e, west/w)
  - Quick shortcuts: `n`, `gn` (north), `w`, `gw` (west), `gs` (south), `ge` (east)
```

**Updated text**:
```markdown
- `go <direction>` (g) - Move in a direction (north, south, east, west)
  - Quick shortcuts: `n`, `gn` (north), `w`, `gw` (west), `gs` (south), `ge` (east)
  - Note: `s` runs `status` and `e` runs `equip`, so use `gs`/`ge` for south/east
```

## Verification
1. Read the updated README section to confirm clarity
2. Ensure the note accurately reflects the behavior described in ISSUES.md

## ISSUES.md Update
Mark issue as resolved by moving from Active to Resolved section.
