# FeatureCoverage Tracker Implementation Plan

## Summary
Implement `scripts/validation/coverage.py` - a tracker for which game features are exercised during playtesting, enabling coverage gap identification.

## Spec

### FeatureCategory Enum
Categories matching ISSUES.md "Features to Cover":
- CHARACTER_CREATION (all 5 classes)
- MOVEMENT (overworld, subgrid, vertical z-levels)
- COMBAT (attack, abilities, flee, stealth, companions)
- NPC_INTERACTION (dialogue, shops, quests, arc progression)
- INVENTORY (equip, unequip, use, drop, restrictions)
- QUESTS (accept, track, complete, world effects, chains)
- CRAFTING (gather, craft, skill progression, recipes)
- EXPLORATION (map, secrets, puzzles, treasures)
- REST_CAMPING (rest, camp, forage, hunt, dreams)
- ECONOMY (buy, sell, price modifiers, supply/demand)
- ENVIRONMENTAL (hazards, interior events)
- RANGER_COMPANION (tame, summon, feed, combat)
- SOCIAL_SKILLS (persuade, intimidate, bribe)
- PERSISTENCE (save, load)

### FeatureEvent Dataclass
```python
@dataclass
class FeatureEvent:
    feature: str           # Feature identifier (e.g., "combat.attack")
    category: FeatureCategory
    timestamp: float       # time.time()
    command: str           # Command that triggered this
    context: dict          # Optional metadata
```

### FeatureCoverage Class
```python
class FeatureCoverage:
    def __init__(self):
        self.events: list[FeatureEvent]
        self._feature_definitions: dict[FeatureCategory, set[str]]

    def record(self, feature: str, category: FeatureCategory, command: str, context: dict = None)
    def get_coverage_by_category(self) -> dict[FeatureCategory, CoverageStats]
    def get_uncovered_features(self) -> dict[FeatureCategory, set[str]]
    def get_coverage_percentage(self) -> float
    def to_dict(self) -> dict
    @classmethod
    def from_dict(cls, data: dict) -> "FeatureCoverage"
```

### CoverageStats Dataclass
```python
@dataclass
class CoverageStats:
    total: int        # Total features in category
    covered: int      # Features exercised
    events: int       # Total events recorded
    features: set[str]  # Which features were hit
```

### FEATURE_DEFINITIONS
Constant mapping each category to its required features:
```python
FEATURE_DEFINITIONS = {
    FeatureCategory.COMBAT: {
        "combat.attack", "combat.ability", "combat.flee",
        "combat.stealth_kill", "combat.companion_attack"
    },
    FeatureCategory.MOVEMENT: {
        "movement.overworld", "movement.subgrid_entry",
        "movement.subgrid_exit", "movement.vertical"
    },
    # ... etc
}
```

## Tests (tests/test_validation_coverage.py)

1. **test_feature_category_has_all_categories** - 14 categories defined
2. **test_feature_event_creation** - All fields populated
3. **test_feature_event_serialization** - to_dict/from_dict roundtrip
4. **test_coverage_record_event** - Recording adds to events list
5. **test_coverage_record_multiple_same_feature** - Multiple events same feature
6. **test_coverage_by_category** - Stats per category
7. **test_uncovered_features** - Returns unexercised features
8. **test_coverage_percentage** - Total percentage calculation
9. **test_coverage_empty** - 0% coverage when no events
10. **test_coverage_serialization** - to_dict/from_dict roundtrip
11. **test_feature_definitions_complete** - All categories have definitions

## Implementation Steps

1. Create `scripts/validation/coverage.py`:
   - FeatureCategory enum (14 categories)
   - FEATURE_DEFINITIONS constant
   - FeatureEvent dataclass with serialization
   - CoverageStats dataclass
   - FeatureCoverage class with all methods

2. Create `tests/test_validation_coverage.py`:
   - 11 tests covering spec

3. Update `scripts/validation/__init__.py`:
   - Export FeatureCategory, FeatureEvent, FeatureCoverage, CoverageStats

4. Run tests: `pytest tests/test_validation_coverage.py -v`
