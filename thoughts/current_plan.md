# Implementation Plan: Issue 1 - Expand WorldContext (Layer 1)

## Spec

Add lore and faction fields to WorldContext for richer world generation:

| Field | Type | Purpose |
|-------|------|---------|
| `creation_myth` | `str` | World origin story |
| `major_conflicts` | `list[str]` | 2-3 world-defining conflicts |
| `legendary_artifacts` | `list[str]` | World-famous items |
| `prophecies` | `list[str]` | Active prophecies |
| `major_factions` | `list[str]` | 3-5 world powers |
| `faction_tensions` | `dict[str, list[str]]` | Faction rivalries |
| `economic_era` | `str` | stable, recession, boom, war_economy |

All new fields default to empty values for backward compatibility.

## Tests (add to `tests/test_world_context.py`)

1. **Test new field creation** - Instantiate with all new fields, verify values stored
2. **Test new field defaults** - Minimal instantiation still works, new fields default empty
3. **Test to_dict includes new fields** - Serialization includes all 7 new fields
4. **Test from_dict restores new fields** - Deserialization restores all 7 new fields
5. **Test from_dict backward compatibility** - Old saves without new fields still load
6. **Test default() includes new field defaults** - Factory method provides sensible defaults
7. **Test round-trip with new fields** - All new fields survive serialization cycle

## Implementation Steps

### 1. Add new fields to WorldContext dataclass
**File**: `src/cli_rpg/models/world_context.py`

Add after line 55 (`generated_at` field):
```python
# Lore fields
creation_myth: str = ""
major_conflicts: list[str] = field(default_factory=list)
legendary_artifacts: list[str] = field(default_factory=list)
prophecies: list[str] = field(default_factory=list)
# Faction fields
major_factions: list[str] = field(default_factory=list)
faction_tensions: dict[str, list[str]] = field(default_factory=dict)
# Economy field
economic_era: str = ""
```

Add import: `from dataclasses import dataclass, field`

### 2. Update to_dict() method
**File**: `src/cli_rpg/models/world_context.py` (lines 57-69)

Add to return dict:
```python
"creation_myth": self.creation_myth,
"major_conflicts": self.major_conflicts,
"legendary_artifacts": self.legendary_artifacts,
"prophecies": self.prophecies,
"major_factions": self.major_factions,
"faction_tensions": self.faction_tensions,
"economic_era": self.economic_era,
```

### 3. Update from_dict() method
**File**: `src/cli_rpg/models/world_context.py` (lines 71-91)

Add to return cls():
```python
creation_myth=data.get("creation_myth", ""),
major_conflicts=data.get("major_conflicts", []),
legendary_artifacts=data.get("legendary_artifacts", []),
prophecies=data.get("prophecies", []),
major_factions=data.get("major_factions", []),
faction_tensions=data.get("faction_tensions", {}),
economic_era=data.get("economic_era", ""),
```

### 4. Update default() factory method
**File**: `src/cli_rpg/models/world_context.py` (lines 93-113)

Add DEFAULT_LORE and DEFAULT_FACTIONS dicts at module level, then include in default():
```python
DEFAULT_CREATION_MYTHS = {
    "fantasy": "Forged by ancient gods from primordial chaos",
    "cyberpunk": "Built on the ashes of the old world's collapse",
    ...
}
DEFAULT_MAJOR_FACTIONS = {
    "fantasy": ["The Crown", "The Mage's Circle", "The Merchant League"],
    ...
}
DEFAULT_ECONOMIC_ERAS = {
    "fantasy": "stable",
    "cyberpunk": "boom",
    ...
}
```

### 5. Add tests for new fields
**File**: `tests/test_world_context.py`

Add new test class `TestWorldContextLoreAndFactions` with the 7 tests specified above.

## Verification

```bash
pytest tests/test_world_context.py -v
```

All existing tests must continue to pass (backward compatibility). All 7 new tests must pass.
