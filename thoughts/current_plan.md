# Implementation Plan: E2E Tests for Dynamic World Expansion

## Overview
Add end-to-end tests that validate dynamic world expansion during gameplay by simulating real player sessions. The world expansion code exists (lines 176-194 in game_state.py) and a unit test (test_game_state_move_triggers_expansion) validates it works. We need comprehensive E2E tests to ensure the feature works seamlessly in realistic scenarios.

## 1. Identify/Create Feature Specification

### Current Behavior (from code analysis)
- **File**: `src/cli_rpg/game_state.py` lines 176-194
- **Mechanism**: When player moves to a direction with a dangling connection (destination not in world):
  - GameState checks if AI service is available
  - Calls `expand_world()` to generate the missing location
  - Updates the world dictionary with new location
  - Creates bidirectional connections between locations
  - Continues move to the newly generated location

### Specification Elements to Test
1. **Dangling Connection Detection**: System detects when destination location doesn't exist in world
2. **AI-Powered Generation**: Calls AI service to generate appropriate location based on theme/context
3. **World State Update**: New location added to world dictionary with proper connections
4. **Bidirectional Connection**: Both source→destination and destination→source connections created
5. **Seamless Continuation**: Player move completes successfully to new location
6. **Graceful Failure**: If generation fails, player receives error message and stays at current location
7. **No-AI Fallback**: Without AI service, move to missing destination fails with clear message

## 2. Develop Tests that Verify the Spec

### Test File
**Location**: `tests/test_e2e_world_expansion.py` (new file)

### Test Scenarios

#### Test 1: Basic Single Expansion
**Purpose**: Verify single location expansion works end-to-end
**Setup**:
- Create GameState with one location (Town Square)
- Add dangling connection: Town Square→north→"Forest" (but Forest doesn't exist)
- Mock AI service to return valid Forest data
**Actions**:
- Execute move("north")
**Assertions**:
- Move succeeds (returns True)
- Current location is "Forest"
- Forest exists in world dictionary
- Town Square has connection north→Forest
- Forest has connection south→Town Square
- AI service was called once with correct parameters (theme, context, source, direction)

#### Test 2: Multi-Step Expansion Chain
**Purpose**: Verify multiple consecutive expansions work
**Setup**:
- Start with Town Square
- Mock AI to generate sequence: Town Square→Forest→Cave→Dungeon
**Actions**:
- move("north") to Forest
- move("east") to Cave
- move("down") to Dungeon
**Assertions**:
- All three moves succeed
- All four locations exist in world
- All connections are bidirectional
- Current location is "Dungeon"
- Each AI call received correct context from previous locations

#### Test 3: Expansion with Existing Location
**Purpose**: Verify expansion doesn't break when destination already exists
**Setup**:
- World has both Town Square and Forest
- Connection exists: Town Square→north→Forest
**Actions**:
- move("north")
**Assertions**:
- Move succeeds without calling AI
- No duplicate locations created
- AI service never called

#### Test 4: Expansion After Movement Through Existing World
**Purpose**: Verify expansion works mid-game after exploring existing areas
**Setup**:
- World: Town Square ↔ Market ↔ Harbor
- Add dangling connection from Harbor: east→"Shipwreck"
**Actions**:
- move to Market
- move to Harbor
- move("east") to trigger expansion
**Assertions**:
- Current location is "Shipwreck"
- Shipwreck has context from all three previous locations
- All existing locations remain unchanged

#### Test 5: Expansion Failure Handling
**Purpose**: Verify graceful handling when AI generation fails
**Setup**:
- GameState with Town Square
- Dangling connection to "Forest"
- Mock AI service to raise AIServiceError
**Actions**:
- Attempt move("north")
**Assertions**:
- Move fails (returns False)
- Error message contains "failed" or "error"
- Current location unchanged (still Town Square)
- World state unchanged (no partial location added)

#### Test 6: No AI Service Fallback
**Purpose**: Verify behavior without AI service
**Setup**:
- GameState with ai_service=None
- Dangling connection exists
**Actions**:
- Attempt move to missing destination
**Assertions**:
- Move fails with clear error message
- Current location unchanged
- No crashes or exceptions

#### Test 7: Theme Consistency in Expansion
**Purpose**: Verify generated locations match theme
**Setup**:
- GameState with theme="cyberpunk"
- Mock AI service to track theme parameter
**Actions**:
- Trigger expansion
**Assertions**:
- AI service called with theme="cyberpunk"
- Generated location description matches theme

#### Test 8: Connection Update After Expansion
**Purpose**: Verify connections from source location are correctly updated
**Setup**:
- Town Square initially has connections: {"north": "Forest"}
- Forest doesn't exist initially
**Actions**:
- move("north") triggers expansion
- Check Town Square's connections after expansion
**Assertions**:
- Town Square's get_connection("north") returns actual generated name
- If generated name differs from "Forest", connection is updated

#### Test 9: Multiple Paths to Same Expansion Point
**Purpose**: Verify expansion works when multiple locations could lead to same missing destination
**Setup**:
- Location A→north→"Missing"
- Location B→east→"Missing"
- Start at Location A
**Actions**:
- move("north") to trigger expansion of "Missing"
- Return to A, go to B
- move("east") from B
**Assertions**:
- Second move succeeds without regenerating "Missing"
- "Missing" has connections to both A and B

#### Test 10: Expansion Preserves Game State
**Purpose**: Verify character state, inventory, etc. preserved during expansion
**Setup**:
- Character with specific HP, level, stats
- Mock encounter tracking
**Actions**:
- Trigger world expansion
**Assertions**:
- Character state unchanged
- Combat state unchanged
- All game state besides world preserved

### Test Infrastructure Needs
1. **Fixtures**:
   - `basic_character`: Character with default stats
   - `mock_ai_service_success`: Returns valid location data
   - `mock_ai_service_failure`: Raises AIServiceError
   - `simple_world`: Single location world
   - `connected_world`: 3-4 interconnected locations
   - `world_with_dangling`: World with missing connections

2. **Helper Functions**:
   - `create_game_state_with_dangling(location_name, direction, missing_name)`: Creates test scenario
   - `verify_bidirectional_connection(world, loc1, direction, loc2)`: Asserts connections exist both ways
   - `verify_world_integrity(world)`: Validates all connections point to existing locations

## 3. Implement Code Until Tests Pass

### Implementation Steps

#### Step 1: Create Test File Structure
**File**: `tests/test_e2e_world_expansion.py`
**Action**: Create file with imports, fixtures, and test class structure
**Verification**: File exists and imports work

#### Step 2: Implement Fixtures
**Action**: Write all fixtures (basic_character, mock services, worlds)
**Verification**: Fixtures can be instantiated without errors

#### Step 3: Implement Helper Functions
**Action**: Write helper functions for test setup and verification
**Verification**: Helpers work in isolation

#### Step 4: Implement Test 1 (Basic Single Expansion)
**Action**: Write complete test with setup, action, assertions
**Run**: `pytest tests/test_e2e_world_expansion.py::test_basic_single_expansion -v`
**Expected**: Pass (code already works based on unit test)

#### Step 5: Implement Test 2 (Multi-Step Expansion Chain)
**Action**: Write test for multiple consecutive expansions
**Run**: `pytest tests/test_e2e_world_expansion.py::test_multi_step_expansion_chain -v`
**Expected**: Pass

#### Step 6: Implement Test 3 (Expansion with Existing Location)
**Action**: Write test verifying no duplicate generation
**Run**: `pytest tests/test_e2e_world_expansion.py::test_expansion_with_existing_location -v`
**Expected**: Pass

#### Step 7: Implement Test 4 (Mid-Game Expansion)
**Action**: Write test for expansion after exploring existing areas
**Run**: `pytest tests/test_e2e_world_expansion.py::test_expansion_after_movement -v`
**Expected**: Pass

#### Step 8: Implement Test 5 (Failure Handling)
**Action**: Write test for AI service failure scenarios
**Run**: `pytest tests/test_e2e_world_expansion.py::test_expansion_failure_handling -v`
**Expected**: Pass or reveals missing error handling (fix if needed)

#### Step 9: Implement Test 6 (No AI Fallback)
**Action**: Write test for missing AI service
**Run**: `pytest tests/test_e2e_world_expansion.py::test_no_ai_service_fallback -v`
**Expected**: Pass

#### Step 10: Implement Test 7 (Theme Consistency)
**Action**: Write test verifying theme propagation
**Run**: `pytest tests/test_e2e_world_expansion.py::test_theme_consistency -v`
**Expected**: Pass

#### Step 11: Implement Test 8 (Connection Updates)
**Action**: Write test for connection updating after expansion
**Run**: `pytest tests/test_e2e_world_expansion.py::test_connection_update_after_expansion -v`
**Expected**: Pass or reveals connection update issue

#### Step 12: Implement Test 9 (Multiple Paths)
**Action**: Write test for multiple routes to same location
**Run**: `pytest tests/test_e2e_world_expansion.py::test_multiple_paths_expansion -v`
**Expected**: Pass

#### Step 13: Implement Test 10 (State Preservation)
**Action**: Write test verifying game state preservation
**Run**: `pytest tests/test_e2e_world_expansion.py::test_expansion_preserves_game_state -v`
**Expected**: Pass

#### Step 14: Run Complete Test Suite
**Action**: Run all E2E world expansion tests
**Command**: `pytest tests/test_e2e_world_expansion.py -v`
**Expected**: All tests pass

#### Step 15: Run Integration with Existing Tests
**Action**: Run all tests to ensure no regressions
**Command**: `pytest tests/ -v`
**Expected**: All tests pass including new E2E tests

#### Step 16: Document Test Coverage
**Action**: Add docstrings explaining what each test validates
**Verification**: Each test has clear documentation

## Code Locations

### Files to Analyze
- `src/cli_rpg/game_state.py`: Lines 176-194 (expansion logic)
- `src/cli_rpg/ai_world.py`: expand_world() function
- `tests/test_game_state_ai_integration.py`: Existing expansion unit test (line 80)

### Files to Create
- `tests/test_e2e_world_expansion.py`: New E2E test file

### Files to Reference
- `src/cli_rpg/models/location.py`: Location class
- `src/cli_rpg/models/character.py`: Character class
- `src/cli_rpg/ai_service.py`: AIService interface

## Success Criteria
1. All 10 E2E tests pass
2. Tests validate spec requirements (expansion detection, generation, updates, connections)
3. Tests cover success and failure scenarios
4. Tests simulate realistic player movement patterns
5. No regressions in existing tests
6. Code coverage for game_state.py expansion logic reaches 100%
