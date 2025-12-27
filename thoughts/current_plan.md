# Implementation Plan: Issue 9 - Mega-Settlements with Districts

## Overview
Expand SubGrid bounds for larger cities and add a district system to support mega-settlements with themed districts (market district, temple district, residential, etc.).

## Spec

### District Model (`src/cli_rpg/models/district.py`)
A District represents a themed sub-area within a large settlement:
- **DistrictType** enum: `MARKET`, `TEMPLE`, `RESIDENTIAL`, `NOBLE`, `SLUMS`, `CRAFTSMEN`, `DOCKS`, `ENTERTAINMENT`, `MILITARY`
- **District** dataclass:
  - `name: str` - Display name (e.g., "The Golden Market")
  - `district_type: DistrictType` - Category from enum
  - `description: str` - Thematic description
  - `bounds: tuple[int, int, int, int]` - (min_x, max_x, min_y, max_y) within parent SubGrid
  - `atmosphere: str` - Mood/feeling (e.g., "bustling", "quiet", "dangerous")
  - `prosperity: str` - Economic level (poor, modest, prosperous, wealthy)
  - `notable_features: list[str]` - Key landmarks within district
  - Serialization: `to_dict()` / `from_dict()` methods

### Settlement Generator (`src/cli_rpg/settlement_generator.py`)
Functions to partition large settlements into districts:
- `MEGA_SETTLEMENT_CATEGORIES` - Categories that get districts: `{"city", "metropolis", "capital"}`
- `MEGA_SETTLEMENT_THRESHOLD` - Minimum size (e.g., 17x17) to qualify
- `generate_districts(bounds, category, settlement_name, rng)` -> `list[District]`
- `get_district_at_coords(districts, x, y)` -> `Optional[District]`
- District layout uses quadrant-based approach for simplicity

### World Grid Updates (`src/cli_rpg/world_grid.py`)
- Add `"metropolis": (-12, 12, -12, 12, 0, 0)` (25x25) to `SUBGRID_BOUNDS`
- Add `"capital": (-16, 16, -16, 16, 0, 0)` (33x33) to `SUBGRID_BOUNDS`
- Add `districts: list[District]` field to `SubGrid` dataclass
- Update `SubGrid.to_dict()` / `from_dict()` for district serialization

---

## Test Plan

### File: `tests/test_district.py`

```python
# Test District dataclass creation and validation
def test_district_creation():
    """District created with name, type, description, bounds."""

def test_district_type_enum():
    """DistrictType has expected values (MARKET, TEMPLE, etc.)."""

def test_district_serialization_roundtrip():
    """to_dict/from_dict preserves all fields."""

def test_district_bounds_validation():
    """Bounds tuple has 4 integers."""
```

### File: `tests/test_settlement_generator.py`

```python
# Test district generation functions
def test_mega_settlement_categories():
    """MEGA_SETTLEMENT_CATEGORIES includes city, metropolis, capital."""

def test_generate_districts_for_city():
    """generate_districts creates 2-4 districts for city-sized settlements."""

def test_generate_districts_returns_covering():
    """Districts cover the settlement bounds without gaps."""

def test_get_district_at_coords():
    """get_district_at_coords returns correct district for given coordinates."""

def test_get_district_at_coords_outside_bounds():
    """get_district_at_coords returns None for coords outside all districts."""

def test_generate_districts_deterministic():
    """Same RNG seed produces same district layout."""
```

### File: `tests/test_subgrid_districts.py`

```python
# Test SubGrid integration with districts
def test_subgrid_has_districts_field():
    """SubGrid has districts field defaulting to empty list."""

def test_subgrid_districts_serialization():
    """SubGrid.to_dict includes districts; from_dict restores them."""

def test_metropolis_bounds():
    """SUBGRID_BOUNDS has metropolis entry with 25x25 size."""

def test_capital_bounds():
    """SUBGRID_BOUNDS has capital entry with 33x33 size."""
```

---

## Implementation Steps

### Step 1: Create District Model
**File**: `src/cli_rpg/models/district.py`
1. Create `DistrictType` enum with 9 district types
2. Create `District` dataclass with fields: name, district_type, description, bounds, atmosphere, prosperity, notable_features
3. Add `to_dict()` and `from_dict()` methods following existing patterns (see `faction.py`)
4. Add module docstring explaining the district system

### Step 2: Create Tests for District Model
**File**: `tests/test_district.py`
1. Test district creation with required fields
2. Test enum values exist
3. Test serialization roundtrip
4. Test backward compatibility defaults in from_dict

### Step 3: Update SubGrid for Districts
**File**: `src/cli_rpg/world_grid.py`
1. Add imports for District at top
2. Add `"metropolis"` and `"capital"` to `SUBGRID_BOUNDS`
3. Add `districts: list["District"] = field(default_factory=list)` to `SubGrid`
4. Update `SubGrid.to_dict()` to include districts serialization
5. Update `SubGrid.from_dict()` to restore districts with backward compatibility

### Step 4: Create Tests for SubGrid Districts
**File**: `tests/test_subgrid_districts.py`
1. Test new bounds entries exist
2. Test districts field defaults to empty
3. Test serialization with districts

### Step 5: Create Settlement Generator
**File**: `src/cli_rpg/settlement_generator.py`
1. Define `MEGA_SETTLEMENT_CATEGORIES` frozenset
2. Define `MEGA_SETTLEMENT_THRESHOLD` constant
3. Implement `generate_districts()` with quadrant-based partitioning
4. Implement `get_district_at_coords()` for coordinate lookup
5. Add default district descriptions/atmospheres per type

### Step 6: Create Tests for Settlement Generator
**File**: `tests/test_settlement_generator.py`
1. Test category constants
2. Test district generation creates appropriate count
3. Test districts cover bounds
4. Test coordinate lookup
5. Test determinism with RNG seed

### Step 7: Run Full Test Suite
```bash
pytest tests/test_district.py tests/test_settlement_generator.py tests/test_subgrid_districts.py -v
pytest --tb=short
```
