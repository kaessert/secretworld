# Implementation Plan: SettlementContext (Layer 5)

## Summary
Create `SettlementContext` dataclass model for character networks, politics, and trade - enabling richer settlement generation with NPC relationships, guilds, political figures, and trade routes.

## Spec
**File**: `src/cli_rpg/models/settlement_context.py`

```python
@dataclass
class SettlementContext:
    # Required identifiers
    settlement_name: str
    location_coordinates: tuple[int, int]
    generated_at: Optional[datetime] = None

    # Character Networks
    notable_families: list[str] = field(default_factory=list)
    npc_relationships: list[dict] = field(default_factory=list)  # [{npc_a, npc_b, type, strength}]

    # Economic Connections
    trade_routes: list[dict] = field(default_factory=list)  # [{origin, destination, goods, status}]
    local_guilds: list[str] = field(default_factory=list)
    market_specialty: str = ""

    # Political Structure
    government_type: str = ""  # council, monarchy, theocracy, etc.
    political_figures: list[dict] = field(default_factory=list)  # [{name, title, faction}]
    current_tensions: list[str] = field(default_factory=list)

    # Social Atmosphere
    population_size: str = ""  # hamlet, village, town, city, metropolis
    prosperity_level: str = ""  # poor, modest, prosperous, wealthy
    social_issues: list[str] = field(default_factory=list)
```

**Required methods** (following WorldContext/RegionContext patterns):
- `to_dict()` - serialize for save/load (datetime as ISO, tuple as list)
- `from_dict()` - deserialize with backward-compatible defaults
- `default()` - factory for fallback when AI unavailable

## Tests
**File**: `tests/test_settlement_context.py`

1. **Creation tests**:
   - `test_create_with_all_fields` - all fields specified
   - `test_create_with_minimal_fields` - only required, defaults applied
   - `test_create_empty_collections` - empty lists/strings work

2. **Serialization tests**:
   - `test_to_dict_with_all_fields` - datetime→ISO, tuple→list
   - `test_to_dict_with_none_generated_at` - handles None timestamp

3. **Deserialization tests**:
   - `test_from_dict_with_all_fields` - restores all data correctly
   - `test_from_dict_backward_compatible` - old saves without new fields load with defaults
   - `test_from_dict_with_null_generated_at` - handles null timestamp

4. **Default factory tests**:
   - `test_default_creates_valid_context` - creates valid instance
   - `test_default_with_different_coordinates` - works with various coords

5. **Round-trip test**:
   - `test_round_trip_preserves_all_data` - to_dict→from_dict preserves everything

## Implementation Steps

1. **Create model file** `src/cli_rpg/models/settlement_context.py`:
   - Module docstring explaining Layer 5 purpose
   - Import dataclass, field, datetime, Optional
   - Add DEFAULT constants for fallback values (government types, population sizes, prosperity levels)
   - Define `SettlementContext` dataclass with all fields
   - Implement `to_dict()` method
   - Implement `from_dict()` classmethod with backward-compatible defaults
   - Implement `default()` classmethod factory

2. **Create test file** `tests/test_settlement_context.py`:
   - Follow test patterns from `test_region_context.py`
   - 11 tests covering creation, serialization, deserialization, default factory, round-trip

3. **Run tests**: `pytest tests/test_settlement_context.py -v`

## Files to Create
- `src/cli_rpg/models/settlement_context.py`
- `tests/test_settlement_context.py`

## Files NOT Modified
No existing files need changes for this task - this is a new model only. Integration with AI service and GameState will be done in Issue 5 (GenerationContext aggregator).
