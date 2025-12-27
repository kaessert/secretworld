# Implementation Plan: Verify and Document Shop Pricing Fix

## Summary
The "Inconsistent shop pricing message" bug (ISSUES.md line 805) is **already fixed**. The shop display and buy error message both show the same adjusted price. This plan adds a regression test and marks the issue as resolved.

## Problem Statement
Per ISSUES.md: "Shop displays: 'Iron Sword - 100 gold', Error says: '99 gold needed'"

## Analysis Findings

### Code Review
Both shop display (main.py:1384-1396) and buy command (main.py:1425-1437) use **identical price calculation logic**:
1. Apply CHA modifier via `get_cha_price_modifier()`
2. Apply faction modifier if present
3. Apply persuade discount (20%) if NPC was persuaded
4. Apply haggle bonus if active

### Manual Verification
```python
# Test with CHA 11 (0.99 modifier), 100g base price, 50g in pocket
# Shop display: "Iron Sword - 99 gold"
# Buy error: "You can't afford Iron Sword (99 gold)."
```

Prices match! The issue was fixed as part of the "Shop price inconsistency" fix on 2025-12-26.

## Implementation Steps

### 1. Add regression test
**File**: `tests/test_shop_price_consistency.py`

```python
def test_shop_display_matches_buy_error_with_cha_modifier():
    """Shop display price matches buy error message price when CHA modifier applies.

    Regression test for ISSUES.md bug: "Shop displays: 'Iron Sword - 100 gold',
    Error says: '99 gold needed'"
    """
    # Create shop with 100g item
    # Create character with CHA 11 (0.99 modifier), insufficient gold
    # Verify shop shows 99g
    # Verify buy error shows 99g
```

### 2. Mark issue as resolved in ISSUES.md
**Location**: Line 805

**Change**:
```markdown
3. **Inconsistent shop pricing message**
```

**To**:
```markdown
3. ~~**Inconsistent shop pricing message**~~ ✅ RESOLVED (2025-12-27)
   - Already fixed as part of shop price consistency fix on 2025-12-26
   - Regression test added in `tests/test_shop_price_consistency.py`
```

## Files to Modify

| File | Changes |
|------|---------|
| `tests/test_shop_price_consistency.py` | New file with regression test |
| `ISSUES.md` | Mark issue #3 as resolved (lines 805-807) |

## Success Criteria

1. New test passes verifying shop display price == buy error price
2. All 3657+ tests continue to pass
3. Issue marked resolved in ISSUES.md
