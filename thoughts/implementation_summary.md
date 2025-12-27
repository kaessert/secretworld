# Implementation Summary: Class-Specific Ability Error Message Ordering

## What Was Implemented

Fixed the UX issue where class-specific combat abilities showed "Not in combat" instead of class restriction errors when used outside combat by the wrong class.

### Changes Made

**1. Modified `src/cli_rpg/main.py` (lines 2488-2527)**

Refactored the combat command handling to check class restrictions BEFORE combat state for class-specific abilities:

- `bash` - Now shows "Only Warriors can bash!" for non-Warriors
- `fireball` - Now shows "Only Mages can cast Fireball!" for non-Mages
- `ice_bolt` - Now shows "Only Mages can cast Ice Bolt!" for non-Mages
- `heal` - Now shows "Only Mages can cast Heal!" for non-Mages
- `bless` - Now shows "Only Clerics can bless!" for non-Clerics
- `smite` - Now shows "Only Clerics can smite!" for non-Clerics

Generic combat commands (`attack`, `defend`, `block`, `parry`, `flee`, `rest`, `cast`, `hide`) continue to show "Not in combat." as before.

**2. Updated `tests/test_main_coverage.py` (lines 599-797)**

- Modified 6 existing tests to verify class restriction errors are shown for wrong class
- Added 6 complementary tests to verify "Not in combat" is shown for correct class

## Test Results

All 18 tests in `TestExplorationCombatCommandsOutsideCombat` pass.
Full test suite: 4119 tests pass.

## Verification Command

```bash
pytest tests/test_main_coverage.py::TestExplorationCombatCommandsOutsideCombat -v
```

## Design Decision

The import of `CharacterClass` is done locally within each command handler to match the existing code style in the file (lazy imports for specific functionality).
