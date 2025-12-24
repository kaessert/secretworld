# Implementation Plan: AI-Powered Location Generation

## 1. SPECIFICATION

### 1.1 Feature Spec Document
**File:** `docs/ai_location_generation_spec.md`

Create specification covering:
- AI service interface requirements
- Location generation input/output format
- Configuration management (API keys, models, prompts)
- Error handling and fallback strategies
- Context-aware generation requirements
- Integration points with existing World and GameState systems

### 1.2 Core Requirements
- Generate locations with: name (2-50 chars), description (1-500 chars), suggested connections (valid directions)
- Support configurable LLM provider (OpenAI as primary)
- Accept context parameters: world theme, existing location names, current location info
- Return structured data compatible with Location model
- Handle API failures gracefully with fallback mechanisms
- Support caching to reduce API calls
- Environment-based configuration (API keys via env vars)
- Rate limiting awareness

## 2. TEST DEVELOPMENT

### 2.1 AI Service Unit Tests
**File:** `tests/test_ai_service.py`

Tests to implement (using mocked API calls):
1. `test_ai_service_initialization_with_api_key()` - Verify AIService accepts API key
2. `test_ai_service_initialization_with_env_var()` - Verify reads from environment
3. `test_ai_service_missing_api_key_raises_error()` - Verify raises error without key
4. `test_generate_location_returns_valid_structure()` - Mock API, verify output has name, description, connections
5. `test_generate_location_validates_constraints()` - Verify name/description length limits
6. `test_generate_location_accepts_context_parameters()` - Test theme, existing locations passed
7. `test_generate_location_with_api_error_raises_exception()` - Mock API failure
8. `test_generate_location_with_timeout_raises_exception()` - Mock timeout
9. `test_generate_location_connection_directions_valid()` - Verify only valid directions returned
10. `test_generate_location_caching_enabled()` - Test cache hit/miss scenarios
11. `test_generate_location_prompt_includes_context()` - Verify prompt construction
12. `test_ai_service_configurable_model()` - Test different model selection
13. `test_ai_service_configurable_temperature()` - Test temperature parameter
14. `test_generate_location_retry_on_transient_error()` - Test retry logic
15. `test_generate_location_max_retries_exceeded()` - Test retry limit

### 2.2 AI World Generation Integration Tests
**File:** `tests/test_ai_world_generation.py`

Tests to implement:
1. `test_create_ai_world_generates_location()` - Test single location generation
2. `test_create_ai_world_with_starting_location()` - Test world creation with start point
3. `test_create_ai_world_generates_connected_locations()` - Test connected location generation
4. `test_create_ai_world_expands_from_seed()` - Test expansion from initial location
5. `test_create_ai_world_respects_theme()` - Test theme consistency
6. `test_create_ai_world_with_ai_failure_fallback()` - Test fallback to default world
7. `test_create_ai_world_validates_generated_locations()` - Test Location model validation
8. `test_create_ai_world_handles_duplicate_names()` - Test duplicate prevention
9. `test_expand_world_from_location()` - Test on-demand location generation
10. `test_expand_world_creates_bidirectional_connections()` - Test connection consistency

### 2.3 Configuration Tests
**File:** `tests/test_ai_config.py`

Tests to implement:
1. `test_ai_config_from_environment()` - Test reading config from env vars
2. `test_ai_config_from_dict()` - Test config from dictionary
3. `test_ai_config_defaults()` - Test default values
4. `test_ai_config_validation()` - Test invalid config raises errors
5. `test_ai_config_custom_prompts()` - Test custom prompt templates

### 2.4 GameState Integration Tests
**File:** `tests/test_game_state_ai_integration.py`

Tests to implement:
1. `test_game_state_with_ai_world()` - Test GameState works with AI-generated world
2. `test_game_state_move_triggers_expansion()` - Test moving to non-existent location generates it
3. `test_game_state_ai_generation_failure_handling()` - Test graceful handling of generation failure
4. `test_game_state_ai_world_persistence()` - Test save/load with AI-generated world

## 3. IMPLEMENTATION

### 3.1 Configuration Module
**File:** `src/cli_rpg/ai_config.py`

Implementation order:
1. Create `AIConfig` dataclass with fields:
   - `api_key: str`
   - `model: str = "gpt-3.5-turbo"`
   - `temperature: float = 0.7`
   - `max_tokens: int = 500`
   - `max_retries: int = 3`
   - `retry_delay: float = 1.0`
   - `enable_caching: bool = True`
   - `cache_ttl: int = 3600`
   - `location_generation_prompt: str` (template)

2. Implement `from_env()` class method to read from environment variables:
   - `OPENAI_API_KEY`
   - `AI_MODEL`
   - `AI_TEMPERATURE`
   - etc.

3. Implement validation in `__post_init__()`:
   - Validate API key not empty
   - Validate temperature in [0.0, 2.0]
   - Validate max_tokens > 0
   - Validate max_retries >= 0

4. Implement `to_dict()` and `from_dict()` methods

### 3.2 AI Service Core
**File:** `src/cli_rpg/ai_service.py`

Implementation order:
1. Create `AIService` class with constructor accepting `AIConfig`

2. Implement `_build_location_prompt()` method:
   - Accept parameters: `theme: str`, `context_locations: list[str]`, `source_location: Optional[str]`, `direction: Optional[str]`
   - Build prompt using template from config
   - Include context: theme, existing locations, direction context
   - Return formatted prompt string

3. Implement `_call_llm()` method:
   - Use OpenAI API (or abstraction layer)
   - Pass prompt, model, temperature, max_tokens
   - Implement retry logic with exponential backoff
   - Handle API errors (timeout, rate limit, invalid key, etc.)
   - Return raw response text

4. Implement `_parse_location_response()` method:
   - Parse LLM response (expect JSON format)
   - Extract name, description, connections
   - Validate against Location model constraints
   - Handle parsing errors
   - Return dict with validated data

5. Implement `generate_location()` method:
   - Accept context parameters
   - Build prompt using `_build_location_prompt()`
   - Call LLM using `_call_llm()`
   - Parse response using `_parse_location_response()`
   - Return Location-compatible dict

6. Implement optional caching layer:
   - Create `_LocationCache` inner class
   - Cache key: hash of prompt
   - Cache value: generated location dict + timestamp
   - Implement `_get_cached()` and `_set_cached()` methods
   - Check cache in `generate_location()` before API call

7. Add error handling wrapper:
   - Catch specific exceptions (API errors, parsing errors)
   - Raise custom exceptions: `AIServiceError`, `AIGenerationError`, `AIConfigError`

### 3.3 World Generation Integration
**File:** `src/cli_rpg/ai_world.py`

Implementation order:
1. Create `create_ai_world()` function:
   - Accept parameters: `ai_service: AIService`, `theme: str = "fantasy"`, `starting_location_name: str = "Town Square"`, `initial_size: int = 3`
   - Generate starting location using AI service
   - Generate connected locations based on starting location's suggested connections
   - Build world dict compatible with existing World type
   - Validate all connections are bidirectional
   - Return `dict[str, Location]`

2. Create `expand_world()` function:
   - Accept: `world: dict[str, Location]`, `ai_service: AIService`, `from_location: str`, `direction: str`, `theme: str`
   - Generate new location in specified direction from source
   - Add to world dict
   - Update connections (bidirectional)
   - Return updated world dict

3. Create `create_world_with_fallback()` function:
   - Try to create AI world
   - On failure, fall back to `create_default_world()`
   - Log warning about fallback
   - Return world dict

4. Add validation helper `_validate_world_consistency()`:
   - Check all connections point to existing locations
   - Check bidirectional connections are correct
   - Raise `ValueError` if inconsistent

### 3.4 Update World Module
**File:** `src/cli_rpg/world.py`

Changes:
1. Keep existing `create_default_world()` function (for fallback)

2. Add `create_world()` function:
   - Accept optional `ai_service: Optional[AIService] = None`
   - Accept optional `theme: str = "fantasy"`
   - If ai_service provided, call `create_ai_world()`
   - Else, call `create_default_world()`
   - Return world dict

### 3.5 GameState Dynamic Expansion
**File:** `src/cli_rpg/game_state.py`

Changes:
1. Add optional `ai_service` attribute to `GameState.__init__()`:
   - `ai_service: Optional[AIService] = None`
   - Store as instance attribute

2. Add optional `theme` attribute:
   - `theme: str = "fantasy"`

3. Modify `move()` method:
   - After checking connection exists
   - Before moving, check if destination exists in world
   - If destination missing and ai_service available:
     - Call `expand_world()` to generate location
     - Update `self.world`
   - If destination missing and no ai_service:
     - Return error (connection broken)

4. Update `to_dict()` method:
   - Add `theme` to serialization
   - Do NOT serialize ai_service (config-based, not state)

5. Update `from_dict()` method:
   - Accept optional `ai_service` parameter
   - Read theme from dict
   - Pass ai_service to GameState constructor

### 3.6 Configuration File Support
**File:** `src/cli_rpg/config.py`

Implementation:
1. Create `load_config()` function:
   - Read from `.env` file if exists
   - Use environment variables
   - Return `AIConfig` instance or None if no API key

2. Create example config file:
   - **File:** `.env.example`
   - Document all configuration options

### 3.7 Main Integration
**File:** `src/cli_rpg/main.py`

Changes:
1. Import new modules: `ai_service`, `ai_world`, `config`

2. Modify game initialization:
   - Try to load AI config from environment
   - If config available, create `AIService` instance
   - Pass ai_service to world creation
   - Pass ai_service to GameState

3. Add error handling:
   - Catch AI-related exceptions
   - Show user-friendly messages
   - Fall back gracefully

### 3.8 Dependencies Update
**File:** `pyproject.toml`

Add dependencies:
```toml
dependencies = [
    "openai>=1.0.0",
    "python-dotenv>=1.0.0",
]
```

Add to dev dependencies:
```toml
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.12.0",
    "responses>=0.24.0",  # for HTTP mocking
    "black>=23.0.0",
    "mypy>=1.5.0",
    "ruff>=0.0.291",
]
```

## 4. VERIFICATION

### 4.1 Run Test Suite
```bash
pytest tests/test_ai_service.py -v
pytest tests/test_ai_world_generation.py -v
pytest tests/test_ai_config.py -v
pytest tests/test_game_state_ai_integration.py -v
pytest tests/ -v  # Full suite
```

### 4.2 Manual Integration Test
1. Set `OPENAI_API_KEY` environment variable
2. Run game: `cli-rpg`
3. Create character
4. Verify starting location is AI-generated
5. Move to different locations
6. Verify new locations generated on-demand
7. Save and reload game
8. Verify AI-generated world persists

### 4.3 Error Scenario Testing
1. Test without API key - should fall back to default world
2. Test with invalid API key - should show error and fall back
3. Test with rate limiting - should retry appropriately
4. Test with network timeout - should handle gracefully

## 5. IMPLEMENTATION ORDER SUMMARY

1. **Phase 1: Configuration & Testing Infrastructure**
   - Write spec document
   - Create `ai_config.py` with tests
   - Set up test mocking infrastructure

2. **Phase 2: Core AI Service**
   - Implement `AIService` class in `ai_service.py`
   - Write and pass all unit tests in `test_ai_service.py`
   - Test with mocked OpenAI API responses

3. **Phase 3: World Generation**
   - Implement `ai_world.py` functions
   - Write and pass integration tests in `test_ai_world_generation.py`
   - Ensure Location model compatibility

4. **Phase 4: GameState Integration**
   - Modify `game_state.py` for dynamic expansion
   - Write and pass integration tests
   - Ensure serialization works with AI worlds

5. **Phase 5: Main Integration**
   - Update `world.py` with new creation function
   - Modify `main.py` for AI service initialization
   - Add configuration file support
   - Update dependencies

6. **Phase 6: Full Verification**
   - Run complete test suite
   - Manual end-to-end testing
   - Error scenario testing
   - Performance testing (cache effectiveness)

## NOTES

- All tests use mocked API calls (no real API calls during testing)
- API keys stored only in environment variables (never in code)
- Fallback to default world ensures game is always playable
- Generated locations must pass Location model validation
- Caching reduces API costs and improves performance
- Retry logic handles transient API failures
- Theme parameter ensures world consistency
- Bidirectional connection validation prevents broken navigation
