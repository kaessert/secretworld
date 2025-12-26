# Implementation Plan: Add Hierarchy Fields to Location Model

## Summary
Add 5 new fields to the Location model (`is_overworld`, `parent_location`, `sub_locations`, `is_safe_zone`, `entry_point`) with backward-compatible defaults. This foundational change enables the hierarchical world system without breaking existing functionality.

## Spec

**New Fields for `Location` class:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `is_overworld` | `bool` | `False` | True if this is an overworld landmark |
| `parent_location` | `Optional[str]` | `None` | Name of parent landmark (for sub-locations) |
| `sub_locations` | `List[str]` | `[]` | Names of child locations (for landmarks) |
| `is_safe_zone` | `bool` | `False` | No random encounters if True |
| `entry_point` | `Optional[str]` | `None` | Default sub-location when entering |

**Backward Compatibility:**
- All fields have defaults that preserve existing behavior
- Old save files (without these fields) load without error
- Existing locations behave identically (not overworld, not safe, no hierarchy)

## Test Cases

### 1. Field Defaults (`tests/test_location.py`)
- `test_location_hierarchy_fields_default_values` - All 5 fields have correct defaults
- `test_location_is_overworld_default_false` - `is_overworld` defaults to False
- `test_location_parent_location_default_none` - `parent_location` defaults to None
- `test_location_sub_locations_default_empty_list` - `sub_locations` defaults to `[]`
- `test_location_is_safe_zone_default_false` - `is_safe_zone` defaults to False
- `test_location_entry_point_default_none` - `entry_point` defaults to None

### 2. Field Assignment
- `test_location_creation_with_hierarchy_fields` - Can create location with all 5 new fields
- `test_location_overworld_landmark_creation` - Create a typical overworld landmark
- `test_location_sub_location_creation` - Create a sub-location with parent reference

### 3. Serialization (`to_dict`)
- `test_location_to_dict_excludes_default_hierarchy_fields` - Defaults not serialized (backward compat)
- `test_location_to_dict_includes_is_overworld_when_true` - `is_overworld: true` serialized
- `test_location_to_dict_includes_parent_location_when_set` - `parent_location` serialized when not None
- `test_location_to_dict_includes_sub_locations_when_non_empty` - `sub_locations` serialized when not empty
- `test_location_to_dict_includes_is_safe_zone_when_true` - `is_safe_zone: true` serialized
- `test_location_to_dict_includes_entry_point_when_set` - `entry_point` serialized when not None

### 4. Deserialization (`from_dict`)
- `test_location_from_dict_missing_hierarchy_fields_uses_defaults` - Old saves load fine
- `test_location_from_dict_with_is_overworld` - Deserialize `is_overworld`
- `test_location_from_dict_with_parent_location` - Deserialize `parent_location`
- `test_location_from_dict_with_sub_locations` - Deserialize `sub_locations`
- `test_location_from_dict_with_is_safe_zone` - Deserialize `is_safe_zone`
- `test_location_from_dict_with_entry_point` - Deserialize `entry_point`

### 5. Roundtrip Serialization
- `test_location_hierarchy_roundtrip_serialization` - All fields preserved through to_dict/from_dict

## Implementation Steps

### Step 1: Write tests first
**File**: `tests/test_location.py`
**Action**: Add new test class `TestLocationHierarchy` with all tests from spec above

### Step 2: Add fields to Location dataclass
**File**: `src/cli_rpg/models/location.py`
**Location**: After line 41 (`secrets: Optional[str] = None`)
**Add**:
```python
# Hierarchy fields for overworld/sub-location system
is_overworld: bool = False          # Is this an overworld landmark?
parent_location: Optional[str] = None  # Parent landmark (for sub-locations)
sub_locations: List[str] = field(default_factory=list)  # Child locations
is_safe_zone: bool = False          # No random encounters if True
entry_point: Optional[str] = None   # Default sub-location when entering
```

### Step 3: Update `to_dict()` method
**File**: `src/cli_rpg/models/location.py`
**Location**: After line 276 (secrets serialization)
**Add** (same pattern as other optional fields):
```python
# Only include hierarchy fields if non-default (backward compatibility)
if self.is_overworld:
    data["is_overworld"] = self.is_overworld
if self.parent_location is not None:
    data["parent_location"] = self.parent_location
if self.sub_locations:
    data["sub_locations"] = self.sub_locations.copy()
if self.is_safe_zone:
    data["is_safe_zone"] = self.is_safe_zone
if self.entry_point is not None:
    data["entry_point"] = self.entry_point
```

### Step 4: Update `from_dict()` classmethod
**File**: `src/cli_rpg/models/location.py`
**Location**: In `from_dict()`, before the return statement (around line 307)
**Add**:
```python
# Parse hierarchy fields if present (backward compatibility)
is_overworld = data.get("is_overworld", False)
parent_location = data.get("parent_location")
sub_locations = data.get("sub_locations", [])
is_safe_zone = data.get("is_safe_zone", False)
entry_point = data.get("entry_point")
```
**Update return statement** to include new fields

### Step 5: Run tests
```bash
pytest tests/test_location.py -v
```

### Step 6: Run full test suite
```bash
pytest
```
