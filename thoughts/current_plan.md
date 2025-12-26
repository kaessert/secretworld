# Plan: Create RegionContext Model

**Task**: Implement `RegionContext` model for Layer 2 of the layered query architecture (per ISSUES.md step 4).

## Spec

RegionContext caches region-level theme information for consistent AI generation within a geographic area. This is Layer 2 in the hierarchy (WorldContext → RegionContext → Location → NPCs).

```python
@dataclass
class RegionContext:
    """Stores cached region theme information for consistent AI generation."""
    name: str                      # Region identifier (e.g., "Industrial District")
    theme: str                     # Sub-theme (e.g., "factory smoke, rust, labor")
    danger_level: str              # safe/moderate/dangerous/deadly
    landmarks: list[str]           # Key POIs (e.g., ["Rust Tower", "The Vats"])
    coordinates: tuple[int, int]   # Center coordinates of the region
    generated_at: Optional[datetime] = None  # When context was AI-generated
```

**Required methods** (following WorldContext pattern):
- `to_dict()` / `from_dict()` for serialization
- `default(name, coordinates)` factory for fallback when AI unavailable

## Implementation Steps

### 1. Create tests first (`tests/test_region_context.py`)
- Test creation with all fields
- Test creation with minimal fields (defaults)
- Test `to_dict()` serialization
- Test `from_dict()` deserialization
- Test `from_dict()` with missing fields (backward compatibility)
- Test `default()` factory method
- Test serialization round-trip

### 2. Create model (`src/cli_rpg/models/region_context.py`)
- Import from `dataclasses`, `datetime`, `typing`
- Define `DEFAULT_REGION_THEMES` dict for fallback themes
- Define `RegionContext` dataclass with fields from spec
- Implement `to_dict()` method
- Implement `from_dict()` classmethod
- Implement `default()` classmethod

### 3. Export from models package (`src/cli_rpg/models/__init__.py`)
- Add import for `RegionContext`
- Add to `__all__` list

## Files to Create/Modify
- `tests/test_region_context.py` (NEW)
- `src/cli_rpg/models/region_context.py` (NEW)
- `src/cli_rpg/models/__init__.py` (ADD export)
