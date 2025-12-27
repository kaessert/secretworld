# Issue 2: Expand RegionContext (Layer 2)

## Spec

Add economy, history, and atmosphere fields to `RegionContext` for richer region-specific AI generation:

**Economy Fields:**
- `primary_resources: list[str]` - e.g., ["iron", "timber"]
- `scarce_resources: list[str]` - e.g., ["gold", "spices"]
- `trade_goods: list[str]` - Exported items
- `price_modifier: float` - Regional price adjustment (default 1.0)

**History Fields:**
- `founding_story: str` - Region origin story
- `historical_events: list[str]` - Notable past events
- `ruined_civilizations: list[str]` - Ancient cultures
- `legendary_locations: list[str]` - Mythic places

**Atmosphere Fields:**
- `common_creatures: list[str]` - Typical fauna/monsters
- `weather_tendency: str` - Dominant weather pattern
- `ambient_sounds: list[str]` - Ambient audio cues

## Tests (add to tests/test_region_context.py)

1. `test_create_with_economy_fields` - Create with all economy fields
2. `test_create_with_history_fields` - Create with all history fields
3. `test_create_with_atmosphere_fields` - Create with all atmosphere fields
4. `test_economy_fields_default_to_empty` - Verify defaults (empty lists, 1.0 modifier)
5. `test_to_dict_includes_new_fields` - Serialization includes all 11 new fields
6. `test_from_dict_with_new_fields` - Deserialization restores all 11 new fields
7. `test_from_dict_backward_compatible` - Old saves without new fields load successfully
8. `test_default_factory_sets_empty_values` - `RegionContext.default()` works with new fields
9. `test_round_trip_with_new_fields` - Full round-trip preserves all new data

## Implementation Steps

1. **Add new fields to RegionContext dataclass** (`src/cli_rpg/models/region_context.py`)
   - Add 4 economy fields with `field(default_factory=list)` and `price_modifier: float = 1.0`
   - Add 4 history fields with `field(default_factory=list)` and `founding_story: str = ""`
   - Add 3 atmosphere fields with `field(default_factory=list)` and `weather_tendency: str = ""`

2. **Update `to_dict()` method**
   - Serialize all 11 new fields

3. **Update `from_dict()` method**
   - Deserialize with `.get()` for backward compatibility (empty defaults)

4. **Update `default()` factory method**
   - Ensure new fields are set to sensible empty defaults

5. **Add tests** (`tests/test_region_context.py`)
   - Add 9 new tests covering economy, history, atmosphere fields

6. **Run tests to verify**
   - `pytest tests/test_region_context.py -v`
