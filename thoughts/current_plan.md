# Implementation Plan: Location/World System

## 1. SPECIFICATION

### Location Model Requirements
**File**: `src/cli_rpg/models/location.py`

**Attributes**:
- `name: str` - Location name (2-50 characters, required)
- `description: str` - Location description (1-500 characters, required)
- `connections: dict[str, str]` - Maps direction names to location names
  - Direction keys: "north", "south", "east", "west", "up", "down"
  - Values: location names (strings)
  - Default: empty dict

**Validation Requirements**:
- Name: 2-50 characters, non-empty, stripped
- Description: 1-500 characters, non-empty, stripped
- Connections: valid direction keys only, non-empty location names
- Direction keys must be from allowed set

**Methods**:
- `add_connection(direction: str, location_name: str) -> None` - Add connection
- `remove_connection(direction: str) -> None` - Remove connection
- `get_connection(direction: str) -> Optional[str]` - Get connected location name
- `get_available_directions() -> list[str]` - List all available directions
- `has_connection(direction: str) -> bool` - Check if direction exists
- `to_dict() -> dict` - Serialize to dictionary
- `from_dict(data: dict) -> Location` - Deserialize from dictionary (classmethod)
- `__str__() -> str` - Human-readable representation

**Class Constants**:
- `MIN_NAME_LENGTH: ClassVar[int] = 2`
- `MAX_NAME_LENGTH: ClassVar[int] = 50`
- `MIN_DESCRIPTION_LENGTH: ClassVar[int] = 1`
- `MAX_DESCRIPTION_LENGTH: ClassVar[int] = 500`
- `VALID_DIRECTIONS: ClassVar[set[str]] = {"north", "south", "east", "west", "up", "down"}`

---

## 2. DEVELOP TESTS (TDD)

### Test File: `tests/test_location.py`

#### Test Class 1: TestLocationCreation
Test location instantiation and validation following Character model pattern.

**Tests**:
1. `test_location_creation_valid()` - Create location with valid attributes
   - Verify name, description, empty connections dict
   
2. `test_location_creation_with_connections()` - Create with initial connections
   - Verify connections dict is properly stored
   
3. `test_location_creation_defaults_empty_connections()` - No connections arg
   - Verify connections defaults to empty dict
   
4. `test_location_name_validation_too_short()` - Name < 2 chars
   - Expect ValueError with "at least 2 characters"
   
5. `test_location_name_validation_too_long()` - Name > 50 chars
   - Expect ValueError with "at most 50 characters"
   
6. `test_location_name_validation_empty()` - Empty/whitespace name
   - Expect ValueError with "cannot be empty"
   
7. `test_location_description_validation_empty()` - Empty description
   - Expect ValueError with "cannot be empty"
   
8. `test_location_description_validation_too_long()` - Description > 500 chars
   - Expect ValueError with "at most 500 characters"
   
9. `test_location_connections_validation_invalid_direction()` - Bad direction key
   - Expect ValueError with "Invalid direction"
   
10. `test_location_connections_validation_empty_location_name()` - Empty value
    - Expect ValueError with "cannot be empty"

#### Test Class 2: TestLocationConnectionMethods
Test connection manipulation methods.

**Tests**:
1. `test_add_connection_valid()` - Add valid connection
   - Verify connection exists in dict
   
2. `test_add_connection_invalid_direction()` - Add with bad direction
   - Expect ValueError
   
3. `test_add_connection_empty_location_name()` - Add with empty location
   - Expect ValueError
   
4. `test_add_connection_overwrites_existing()` - Add to existing direction
   - Verify new location replaces old
   
5. `test_remove_connection_existing()` - Remove existing connection
   - Verify connection no longer exists
   
6. `test_remove_connection_nonexistent()` - Remove non-existing
   - Should not raise error (silent)
   
7. `test_get_connection_existing()` - Get existing connection
   - Returns correct location name
   
8. `test_get_connection_nonexistent()` - Get non-existing
   - Returns None
   
9. `test_has_connection_existing()` - Check existing
   - Returns True
   
10. `test_has_connection_nonexistent()` - Check non-existing
    - Returns False
    
11. `test_get_available_directions_multiple()` - Multiple connections
    - Returns sorted list of directions
    
12. `test_get_available_directions_empty()` - No connections
    - Returns empty list

#### Test Class 3: TestLocationSerialization
Test serialization/deserialization following Character pattern.

**Tests**:
1. `test_location_to_dict()` - Serialize to dict
   - Verify all attributes present and correct
   
2. `test_location_to_dict_with_connections()` - Serialize with connections
   - Verify connections dict preserved
   
3. `test_location_from_dict_basic()` - Deserialize basic location
   - Verify attributes match
   
4. `test_location_from_dict_with_connections()` - Deserialize with connections
   - Verify connections restored correctly
   
5. `test_location_from_dict_missing_required_field()` - Missing name/description
   - Expect ValueError or KeyError
   
6. `test_location_roundtrip_serialization()` - to_dict -> from_dict
   - Verify original equals restored
   
7. `test_location_str_representation()` - __str__ output
   - Verify name, description, available directions in output

---

## 3. IMPLEMENTATION

### Step 1: Create Location Model Skeleton
**File**: `src/cli_rpg/models/location.py`

1. Import required modules: `dataclasses`, `typing`
2. Define class constants (MIN/MAX lengths, VALID_DIRECTIONS)
3. Create `@dataclass` with attributes: name, description, connections
4. Set connections default to `field(default_factory=dict)`

### Step 2: Implement __post_init__ Validation
**File**: `src/cli_rpg/models/location.py`

1. Validate name:
   - Check not empty/whitespace
   - Check length >= MIN_NAME_LENGTH
   - Check length <= MAX_NAME_LENGTH
   - Strip whitespace

2. Validate description:
   - Check not empty/whitespace
   - Check length >= MIN_DESCRIPTION_LENGTH
   - Check length <= MAX_DESCRIPTION_LENGTH
   - Strip whitespace

3. Validate connections:
   - Iterate through connections dict
   - Validate each direction key in VALID_DIRECTIONS
   - Validate each location_name is non-empty string
   - Raise ValueError with specific messages

### Step 3: Implement Connection Methods
**File**: `src/cli_rpg/models/location.py`

1. `add_connection(direction, location_name)`:
   - Validate direction in VALID_DIRECTIONS
   - Validate location_name non-empty
   - Add/update connections[direction] = location_name

2. `remove_connection(direction)`:
   - Use dict.pop(direction, None) for silent removal

3. `get_connection(direction)`:
   - Return connections.get(direction)

4. `has_connection(direction)`:
   - Return direction in connections

5. `get_available_directions()`:
   - Return sorted(list(connections.keys()))

### Step 4: Implement Serialization Methods
**File**: `src/cli_rpg/models/location.py`

1. `to_dict()`:
   - Return dict with name, description, connections
   - Ensure connections is shallow copy

2. `from_dict(data)` classmethod:
   - Extract name, description, connections from data
   - Use .get() for connections with default {}
   - Create and return Location instance

3. `__str__()`:
   - Format: "{name}\n{description}\n"
   - If connections: "Exits: {comma-separated directions}"
   - If no connections: "Exits: None"

### Step 5: Update Models __init__.py
**File**: `src/cli_rpg/models/__init__.py`

1. Add import: `from cli_rpg.models.location import Location`
2. Update `__all__` if present

### Step 6: Run Tests and Fix Issues

1. Run: `pytest tests/test_location.py -v`
2. Fix any failing tests by adjusting implementation
3. Ensure 100% test pass rate
4. Verify test coverage with: `pytest tests/test_location.py --cov=src/cli_rpg/models/location`

### Step 7: Validation Testing

1. Run full test suite: `pytest tests/ -v`
2. Verify no regressions in existing tests
3. Verify Location model integrates with existing codebase patterns

---

## VERIFICATION CHECKLIST

- [ ] All tests in TestLocationCreation pass (10 tests)
- [ ] All tests in TestLocationConnectionMethods pass (12 tests)
- [ ] All tests in TestLocationSerialization pass (7 tests)
- [ ] Total: 29 tests passing
- [ ] No regression in existing tests
- [ ] Location model follows Character model patterns
- [ ] Validation matches specification requirements
- [ ] Serialization supports persistence pattern
- [ ] Code follows existing style conventions (dataclass, ClassVar, docstrings)
