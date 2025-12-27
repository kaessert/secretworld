# Implementation Summary: Issue 1 - Expand WorldContext (Layer 1)

## What Was Implemented

Added 7 new fields to `WorldContext` dataclass for richer world generation:

### New Fields Added
| Field | Type | Purpose |
|-------|------|---------|
| `creation_myth` | `str` | World origin story |
| `major_conflicts` | `list[str]` | 2-3 world-defining conflicts |
| `legendary_artifacts` | `list[str]` | World-famous items |
| `prophecies` | `list[str]` | Active prophecies |
| `major_factions` | `list[str]` | 3-5 world powers |
| `faction_tensions` | `dict[str, list[str]]` | Faction rivalries |
| `economic_era` | `str` | stable, recession, boom, war_economy |

### Files Modified

1. **`src/cli_rpg/models/world_context.py`**:
   - Added `field` import from dataclasses
   - Added 3 new default dictionaries at module level:
     - `DEFAULT_CREATION_MYTHS` - theme-specific origin stories
     - `DEFAULT_MAJOR_FACTIONS` - theme-specific faction lists
     - `DEFAULT_ECONOMIC_ERAS` - theme-specific economic states
   - Added 7 new fields to the `WorldContext` dataclass with proper defaults
   - Updated `to_dict()` to serialize all new fields
   - Updated `from_dict()` to deserialize new fields with backward-compatible defaults
   - Updated `default()` factory to include sensible defaults for new fields

2. **`tests/test_world_context.py`**:
   - Added new test class `TestWorldContextLoreAndFactions` with 7 tests:
     - `test_new_field_creation` - instantiation with all new fields
     - `test_new_field_defaults` - minimal instantiation preserves defaults
     - `test_to_dict_includes_new_fields` - serialization includes new fields
     - `test_from_dict_restores_new_fields` - deserialization restores new fields
     - `test_from_dict_backward_compatibility` - old saves load correctly
     - `test_default_includes_new_field_defaults` - factory provides defaults
     - `test_round_trip_with_new_fields` - serialization cycle preserves data

## Test Results

- **WorldContext tests**: 17 passed (10 existing + 7 new)
- **Full test suite**: 4192 passed

## Design Decisions

1. **Backward compatibility**: All new fields use `.get()` with empty defaults in `from_dict()` so old save files without these fields continue to work.

2. **List/dict fields use `field(default_factory=...)`**: Per Python dataclass best practices, mutable defaults use factory functions to avoid shared state.

3. **Default factory includes subset of new fields**: The `default()` method populates `creation_myth`, `major_factions`, and `economic_era` with theme-specific defaults. Other fields (`major_conflicts`, `legendary_artifacts`, `prophecies`, `faction_tensions`) are left empty since they're more context-dependent and would be AI-generated.

## E2E Validation

The implementation can be validated by:
1. Creating a new game and checking that `WorldContext.default()` includes the new fields
2. Loading an old save file to verify backward compatibility
3. Verifying new games save/load the new fields correctly
