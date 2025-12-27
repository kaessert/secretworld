# Implementation Plan: LoreContext (Layer 6)

## Summary
Create the `LoreContext` dataclass model for caching lore information (historical events, legendary items, legendary places, prophecies, ancient civilizations, creation myths, deities) following the established pattern from SettlementContext and RegionContext.

---

## Spec

**Model**: `LoreContext` dataclass in `src/cli_rpg/models/lore_context.py`

```python
@dataclass
class LoreContext:
    # Required identifiers
    region_name: str                           # Region this lore belongs to
    coordinates: tuple[int, int]               # Region coordinates
    generated_at: Optional[datetime] = None    # When AI-generated (None if fallback)

    # Historical Events (list of dicts with name, date, description, impact)
    historical_events: list[dict] = field(default_factory=list)

    # Legendary Items (list of dicts with name, description, powers, location_hint)
    legendary_items: list[dict] = field(default_factory=list)

    # Legendary Places (list of dicts with name, description, danger_level, rumored_location)
    legendary_places: list[dict] = field(default_factory=list)

    # Prophecies (list of dicts with name, text, interpretation, fulfilled)
    prophecies: list[dict] = field(default_factory=list)

    # Ancient Civilizations (list of dicts with name, era, achievements, downfall)
    ancient_civilizations: list[dict] = field(default_factory=list)

    # Creation Myths (list of strings - region-specific origin stories)
    creation_myths: list[str] = field(default_factory=list)

    # Deities (list of dicts with name, domain, alignment, worship_status)
    deities: list[dict] = field(default_factory=list)
```

**Methods**:
- `to_dict() -> dict` - Serialize for save/load (datetime→ISO, tuple→list)
- `from_dict(data: dict) -> LoreContext` - Deserialize with backward-compatible defaults
- `default(region_name: str, coordinates: tuple[int, int]) -> LoreContext` - Fallback factory

**Default Constants**:
- `DEFAULT_HISTORICAL_EVENT_TYPES` - ["war", "plague", "discovery", "founding", "cataclysm"]
- `DEFAULT_DEITY_DOMAINS` - ["war", "nature", "death", "knowledge", "trickery", "life"]
- `DEFAULT_DEITY_ALIGNMENTS` - ["good", "neutral", "evil", "forgotten"]

---

## Tests

**File**: `tests/test_lore_context.py`

### TestLoreContextCreation
1. `test_create_with_all_fields` - All fields specified, verify storage
2. `test_create_with_minimal_fields` - Only required, defaults applied
3. `test_create_empty_collections` - Empty lists work correctly

### TestLoreContextSerialization
4. `test_to_dict_with_all_fields` - datetime→ISO, tuple→list conversions
5. `test_to_dict_with_none_generated_at` - Handles None timestamp

### TestLoreContextDeserialization
6. `test_from_dict_with_all_fields` - Restores all data correctly
7. `test_from_dict_backward_compatible` - Old saves load with defaults
8. `test_from_dict_with_null_generated_at` - Handles null timestamp

### TestLoreContextDefaultFactory
9. `test_default_creates_valid_context` - Creates valid instance
10. `test_default_with_different_coordinates` - Works with various coords

### TestLoreContextRoundTrip
11. `test_round_trip_preserves_all_data` - to_dict→from_dict preserves everything
12. `test_round_trip_without_generated_at` - Round-trip with None timestamp

---

## Implementation Steps

1. **Create test file** `tests/test_lore_context.py`
   - Copy structure from `test_settlement_context.py`
   - Update to test LoreContext fields (historical_events, legendary_items, etc.)
   - 12 test cases covering creation, serialization, deserialization, default factory, round-trip

2. **Create model file** `src/cli_rpg/models/lore_context.py`
   - Add module docstring explaining Layer 6 purpose
   - Define `DEFAULT_HISTORICAL_EVENT_TYPES`, `DEFAULT_DEITY_DOMAINS`, `DEFAULT_DEITY_ALIGNMENTS`
   - Create `LoreContext` dataclass with:
     - Required fields: `region_name`, `coordinates`
     - Optional: `generated_at`
     - Lore fields: `historical_events`, `legendary_items`, `legendary_places`, `prophecies`, `ancient_civilizations`, `creation_myths`, `deities`
   - Implement `to_dict()` with datetime→ISO, tuple→list
   - Implement `from_dict()` with backward-compatible `.get()` defaults
   - Implement `default()` factory classmethod

3. **Run tests** - Verify all 12 tests pass with `pytest tests/test_lore_context.py -v`
