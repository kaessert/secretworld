# Implementation Plan: Fix E2E AI Integration Test Mocking

## Problem
The 5 failing E2E tests in `tests/test_e2e_ai_integration.py` incorrectly mock `create_world` to return only `mock_world` instead of the expected tuple `(mock_world, "Town Square")`. The `create_world` function signature returns `tuple[dict[str, Location], str]` as verified in `src/cli_rpg/world.py`.

## Affected Tests (Lines with incorrect mocking)
1. `test_theme_selection_flow_with_ai` - Line 141
2. `test_world_creation_with_ai_service` - Line 186  
3. `test_game_state_initialization_with_ai` - Line 237
4. `test_complete_e2e_flow_with_mocked_ai` - Line 296
5. `test_default_theme_when_ai_unavailable` - Line 380

## Implementation Steps

### 1. Verify Specification
- **File**: `src/cli_rpg/world.py`
- **Action**: Confirm `create_world()` function signature and return type
- **Expected**: Function returns `tuple[dict[str, Location], str]` where first element is world dict and second is starting location name

### 2. Write/Update Test Verification
- **File**: `tests/test_e2e_ai_integration.py`
- **Action**: Review each test to ensure they properly handle the tuple return value
- **Validation**: Tests should destructure or use both elements of the returned tuple

### 3. Fix Test 1: `test_theme_selection_flow_with_ai`
- **File**: `tests/test_e2e_ai_integration.py`
- **Location**: Line 141
- **Change**: 
  - FROM: `mock_create_world.return_value = mock_world`
  - TO: `mock_create_world.return_value = (mock_world, "Town Square")`

### 4. Fix Test 2: `test_world_creation_with_ai_service`
- **File**: `tests/test_e2e_ai_integration.py`
- **Location**: Line 186
- **Change**:
  - FROM: `mock_create_world.return_value = mock_world`
  - TO: `mock_create_world.return_value = (mock_world, "Town Square")`

### 5. Fix Test 3: `test_game_state_initialization_with_ai`
- **File**: `tests/test_e2e_ai_integration.py`
- **Location**: Line 237
- **Change**:
  - FROM: `mock_create_world.return_value = mock_world`
  - TO: `mock_create_world.return_value = (mock_world, "Town Square")`

### 6. Fix Test 4: `test_complete_e2e_flow_with_mocked_ai`
- **File**: `tests/test_e2e_ai_integration.py`
- **Location**: Line 296
- **Change**:
  - FROM: `mock_create_world.return_value = mock_world`
  - TO: `mock_create_world.return_value = (mock_world, "Town Square")`

### 7. Fix Test 5: `test_default_theme_when_ai_unavailable`
- **File**: `tests/test_e2e_ai_integration.py`
- **Location**: Line 380
- **Change**:
  - FROM: `mock_create_world.return_value = mock_world`
  - TO: `mock_create_world.return_value = (mock_world, "Town Square")`

### 8. Run Tests to Verify Fixes
- **Command**: `pytest tests/test_e2e_ai_integration.py -v`
- **Expected**: All 5 previously failing tests should now pass
- **Validation**: 
  - No tuple unpacking errors
  - Tests correctly verify AI integration behavior
  - Mock return values match actual function signature
