# Implementation Summary

## Task: Documentation Cleanup - Clarify Named Location Enterability Issue

### What Was Done

Updated `ISSUES.md` to mark the "All Named Locations Should Be Enterable" issue (lines 41-68) as **COMPLETED (Clarified as Working as Designed)**.

### Changes Made

**File Modified**: `ISSUES.md`

1. Changed status from `OPEN` to `COMPLETED ✓ (Clarified as Working as Designed)`
2. Added `Completed: 2025-12-28` date
3. Replaced the "Problem" section with a "Resolution" section explaining:
   - Category-based enterability is intentional by design
   - Named locations with enterable categories (18 types) CAN be entered
   - Named locations with non-enterable categories (forest, wilderness, etc.) CANNOT be entered because they're open terrain
4. Added "What Was Actually Fixed" section referencing the related bug fix at lines 1444-1467
5. Added "Verification" section with the existing test code showing this is tested behavior
6. Updated "Related Files" to reference the actual bug fix issue

### Rationale

The analysis in `thoughts/current_plan.md` correctly identified that:

1. The current behavior is intentional - not all named locations should be enterable
2. Some named locations represent open terrain (forests, passes, clearings) that have no interior
3. The actual bug (missing categories in validation) was already fixed in a separate issue
4. Making ALL named locations enterable would be confusing ("You enter the open grassland... into a corridor?")

### Test Verification

No new tests needed - this is documentation cleanup only. The existing test at `tests/test_enterable_sublocations.py:485-510` (`test_enter_fails_for_non_enterable`) already verifies the intended behavior.

### E2E Validation

N/A - documentation change only.
