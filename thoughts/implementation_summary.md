# Implementation Summary: Location Hierarchy Fields

## What Was Implemented

Added 5 new hierarchy fields to the `Location` model to enable the overworld/sub-location system:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `is_overworld` | `bool` | `False` | True for overworld landmarks |
| `parent_location` | `Optional[str]` | `None` | Name of parent landmark (for sub-locations) |
| `sub_locations` | `List[str]` | `[]` | Names of child locations (for landmarks) |
| `is_safe_zone` | `bool` | `False` | No random encounters if True |
| `entry_point` | `Optional[str]` | `None` | Default sub-location when entering |

## Files Modified

### `src/cli_rpg/models/location.py`
- Added 5 new fields to the `Location` dataclass (lines 42-47)
- Updated `to_dict()` method to serialize non-default hierarchy fields (lines 283-293)
- Updated `from_dict()` classmethod to parse hierarchy fields with backward-compatible defaults (lines 325-345)

### `tests/test_location.py`
- Added new test class `TestLocationHierarchy` with 22 comprehensive tests covering:
  - Field defaults (6 tests)
  - Field assignment (3 tests)
  - Serialization `to_dict()` (6 tests)
  - Deserialization `from_dict()` (6 tests)
  - Roundtrip serialization (1 test)

## Test Results

- **Location module tests**: 58 passed
- **Full test suite**: 2407 passed
- **No regressions detected**

## Design Decisions

1. **Backward Compatibility**: All new fields have defaults that preserve existing behavior. Old save files without these fields will load correctly.

2. **Sparse Serialization**: Following the existing pattern, hierarchy fields are only serialized when non-default values are set, keeping save files compact.

3. **Default Factory for List**: Using `field(default_factory=list)` for `sub_locations` ensures each Location instance gets its own list (avoiding mutable default argument issues).

## E2E Validation

The following scenarios should work correctly:
- Creating locations with and without hierarchy fields
- Saving and loading games with hierarchy fields set
- Loading old save files (backward compatibility)
- Locations with all hierarchy fields preserve their values through save/load cycles
