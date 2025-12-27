# AI-Powered Location Generation Specification

## 1. Overview

This specification defines the AI-powered location generation system for the CLI RPG game. The system uses Large Language Models (LLMs) to dynamically generate game locations based on context, theme, and player exploration.

## 2. Goals

- Generate unique, contextually appropriate locations on-demand
- Support configurable LLM providers (OpenAI as primary)
- Maintain consistency with game world theme
- Handle API failures gracefully with fallback mechanisms
- Optimize API usage through caching and smart generation
- Integrate seamlessly with existing game systems

## 3. Core Components

### 3.1 AIConfig

Configuration management for AI services.

**Fields:**
- `api_key: str` - API key for LLM provider (required)
- `model: str` - Model identifier (default: "gpt-3.5-turbo")
- `temperature: float` - Generation randomness (0.0-2.0, default: 0.7)
- `max_tokens: int` - Maximum response length (default: 3000)
- `max_retries: int` - Retry attempts for API failures (default: 3)
- `retry_delay: float` - Delay between retries in seconds (default: 1.0)
- `enable_caching: bool` - Enable response caching (default: True)
- `cache_ttl: int` - Cache time-to-live in seconds (default: 3600)
- `location_generation_prompt: str` - Prompt template for location generation

**Configuration Sources:**
1. Environment variables (primary)
2. Configuration file (.env)
3. Programmatic configuration (dict)

**Environment Variables:**
- `OPENAI_API_KEY` - API key
- `AI_MODEL` - Model selection
- `AI_TEMPERATURE` - Temperature setting
- `AI_MAX_TOKENS` - Token limit
- `AI_MAX_RETRIES` - Retry count
- `AI_ENABLE_CACHING` - Cache toggle

### 3.2 AIService

Core service for interacting with LLM APIs.

**Methods:**

`__init__(config: AIConfig)`
- Initialize service with configuration

`generate_location(theme: str, context_locations: list[str] = [], source_location: Optional[str] = None, direction: Optional[str] = None) -> dict`
- Generate a new location based on context
- Returns: `{"name": str, "description": str, "category": str, "npcs": list[dict]}`
- Note: Does NOT return connections - exits are determined by WFC terrain system
- Raises: `AIGenerationError` on generation failure

**Internal Methods:**

`_build_location_prompt(...) -> str`
- Construct prompt from context parameters

`_call_llm(prompt: str) -> str`
- Execute LLM API call with retry logic
- Handle timeouts, rate limits, and errors

`_parse_location_response(response: str) -> dict`
- Parse and validate LLM response
- Ensure compatibility with Location model

`_get_cached(cache_key: str) -> Optional[dict]`
- Retrieve cached location data

`_set_cached(cache_key: str, data: dict) -> None`
- Store location data in cache

`generate_area(theme: str, sub_theme_hint: str = "", entry_direction: str = "north", context_locations: list[str] = [], size: int = 5) -> list[dict]`
- Generate a cluster of 4-7 connected locations forming a thematic area (monolithic generation)
- Returns list of dicts: `{"name": str, "description": str, "relative_coords": [int, int], "connections": dict[str, str]}`
- Entry location is always at relative coordinates [0, 0]
- Uses sub-theme hints (mystical forest, ancient ruins, haunted grounds, etc.) for variety
- Supports caching for performance
- **Note**: Prefer `generate_area_with_context()` when context objects are available

`generate_area_with_context(theme: str, world_context: WorldContext, region_context: RegionContext, entry_direction: str = "north", size: int = 5) -> list[dict]`
- Generate a cluster of locations using layered generation (Layers 3-4)
- Takes WorldContext (Layer 1) and RegionContext (Layer 2) as inputs for thematic consistency
- Generates area layout coordinates using `_generate_area_layout()`
- Calls `generate_location_with_context()` for each location (Layer 3)
- Calls `generate_npcs_for_location()` for each location (Layer 4)
- Returns list of dicts: `{"name": str, "description": str, "category": str, "npcs": list[dict], "relative_coords": [int, int]}`
- Entry location is always at relative coordinates [0, 0]
- Size is clamped to 4-7 locations (matching `generate_area()` behavior)

`generate_world_context(theme: str) -> WorldContext`
- Generate Layer 1 world context with theme_essence, naming_style, and tone
- Returns `WorldContext` instance
- Raises `AIGenerationError` on generation failure

`generate_region_context(theme: str, world_context: WorldContext, coordinates: Tuple[int, int], terrain_hint: str = "") -> RegionContext`
- Generate Layer 2 region context with name, theme, danger_level, and landmarks
- Uses Layer 1 `WorldContext` for thematic consistency
- Maps LLM danger levels ("low/medium/high/deadly") to model values ("safe/moderate/dangerous/deadly")
- Returns `RegionContext` instance
- Raises `AIGenerationError` on generation failure

`generate_location_with_context(theme: str, world_context: WorldContext, region_context: RegionContext, source_location: Optional[str] = None, direction: Optional[str] = None, terrain_type: Optional[str] = None, neighboring_locations: Optional[list[dict]] = None) -> dict`
- Generate Layer 3 location using minimal prompt with cached context
- Uses `location_prompt_minimal` template from AIConfig
- Returns location dict with empty `npcs` list (NPCs generated separately in Layer 4)
- Accepts optional `world_context` and `region_context` for thematic consistency
- Accepts optional `terrain_type` to ensure generated locations match WFC terrain (e.g., desert oasis on desert tiles)
- Accepts optional `neighboring_locations` list (each dict has `name`, `direction`) for spatial coherence with adjacent locations
- Defaults to "wilderness" when terrain_type is None
- Raises `AIGenerationError` on generation failure

`generate_npcs_for_location(theme: str, location_name: str, location_description: str, location_category: str = "") -> list[dict]`
- Generate Layer 4 NPCs as a separate call
- Uses `npc_prompt_minimal` template from AIConfig
- Returns list of validated NPC dicts with fields: `name`, `description`, `dialogue`, `role`
- Keeps NPC generation isolated for reliable JSON parsing
- **Note**: Only called for named locations (`is_named=True`). Unnamed locations (generic terrain tiles) have empty NPC lists.
- Raises `AIGenerationError` on generation failure

### 3.3 WorldContext

Cached world theme context for layered AI generation (Layer 1 of the hierarchical generation system).

**Class:** `WorldContext` (`models/world_context.py`)

**Core Fields:**
- `theme: str` - Base theme keyword (e.g., "fantasy", "cyberpunk")
- `theme_essence: str` - AI-generated theme summary describing the world's feel
- `naming_style: str` - How to name locations/NPCs in this world
- `tone: str` - Narrative tone (gritty, whimsical, mysterious, etc.)
- `generated_at: Optional[datetime]` - When context was AI-generated (None if using defaults)

**Lore & Faction Fields:**
- `creation_myth: str` - World origin story (theme-specific defaults available)
- `major_conflicts: list[str]` - 2-3 world-defining conflicts
- `legendary_artifacts: list[str]` - World-famous items
- `prophecies: list[str]` - Active prophecies
- `major_factions: list[str]` - 3-5 world powers (theme-specific defaults available)
- `faction_tensions: dict[str, list[str]]` - Faction rivalries (faction → list of rivals)
- `economic_era: str` - One of "stable", "recession", "boom", "war_economy" (theme-specific defaults)

**Methods:**
- `to_dict() -> dict`: Serializes to dictionary with ISO datetime string
- `from_dict(data: dict) -> WorldContext`: Deserializes with backward compatibility for missing fields
- `default(theme: str = "fantasy") -> WorldContext`: Creates fallback context when AI unavailable

**Default Values:**
Pre-configured defaults for 5 theme types:
- `fantasy`: Medieval magic, mythic creatures, epic quests
- `cyberpunk`: Neon-lit dystopia, tech-noir, gritty survival
- `steampunk`: Victorian industrial, brass and steam, adventure
- `horror`: Dark atmosphere, psychological dread, survival tension
- `post-apocalyptic`: Ruined civilization, scavenging, harsh survival

**Usage:**
- Generated once at world creation (Layer 1)
- Cached in GameState for reuse across all location/NPC generation
- Passed to AIService methods to ensure thematic consistency
- Serialized with game state for persistence across save/load

### 3.3.1 RegionContext

Cached region theme context for layered AI generation (Layer 2 of the hierarchical generation system).

**Class:** `RegionContext` (`models/region_context.py`)

**Fields:**
- `name: str` - Region name (1-50 characters, e.g., "The Whispering Woods")
- `theme: str` - Region-specific theme (1-200 characters, e.g., "Ancient forest shrouded in mist")
- `danger_level: str` - One of "safe", "moderate", "dangerous", "deadly"
- `landmarks: list[str]` - 0-5 notable landmarks (each 1-50 characters)
- `coordinates: Tuple[int, int]` - Grid coordinates this context was generated for
- `generated_at: Optional[datetime]` - When context was AI-generated (None if using defaults)

**Methods:**
- `to_dict() -> dict`: Serializes to dictionary (coordinates as list for JSON compatibility)
- `from_dict(data: dict) -> RegionContext`: Deserializes with backward compatibility
- `default(coordinates: Tuple[int, int]) -> RegionContext`: Creates fallback context when AI unavailable

**Default Values:**
Pre-configured defaults for 8 terrain types in `DEFAULT_REGION_THEMES`:
- `plains`, `forest`, `mountain`, `water`, `desert`, `swamp`, `tundra`, `volcanic`, `ruins`

**AIService Integration:**

`generate_region_context(theme: str, world_context: WorldContext, coordinates: Tuple[int, int], terrain_hint: str = "") -> RegionContext`
- Generates region-level context using Layer 1 WorldContext for consistency
- Prompt includes world's theme_essence, naming_style, and tone
- LLM returns JSON with name, theme, danger_level ("low/medium/high/deadly"), and landmarks
- Parser maps danger levels: "low"→"safe", "medium"→"moderate", "high"→"dangerous", "deadly"→"deadly"
- Validates all field constraints (lengths, enum values, landmark count)
- Gracefully filters invalid landmarks instead of failing
- Supports markdown code block extraction and truncated JSON repair

**Usage:**
- Generated when entering new region/area (Layer 2)
- Cached per region coordinates
- Passed to location generation for thematic consistency
- Serialized with game state for persistence across save/load

### 3.4 WorldGrid

Coordinate-based world storage for spatial consistency.

**Class:** `WorldGrid` (`world_grid.py`)

**Key Methods:**
- `add_location(location, x, y)`: Place location at coordinates, auto-create bidirectional connections
- `get_by_coordinates(x, y)`: Coordinate-based lookup
- `get_by_name(name)`: Backward compatible name lookup
- `get_neighbor(x, y, direction)`: Get adjacent location
- `as_dict()`: Returns `dict[str, Location]` for backward compatibility
- `to_dict()` / `from_dict()`: Serialization with coordinates
- `from_legacy_dict()`: Handles old saves without coordinates
- `find_unreachable_exits()`: Returns list of exits pointing to empty coordinates
- `validate_border_closure()`: Returns True if all cardinal exits point to existing locations
- `get_frontier_locations()`: Returns locations with exits to empty coordinates (expansion candidates)

**Direction Offsets:**
- north: (0, +1)
- south: (0, -1)
- east: (+1, 0)
- west: (-1, 0)

**Design Properties:**
- Sparse grid (not all coordinates need locations)
- Origin at (0, 0) for starting location
- Automatic bidirectional connection management
- Location coordinates stored as `Tuple[int, int]`

### 3.5 World Generation Functions

**`create_ai_world(ai_service: AIService, theme: str = "fantasy", starting_location_name: str = "Town Square", initial_size: int = 3) -> dict[str, Location]`**
- Generate initial world on a coordinate grid starting from (0,0)
- Locations are placed using WorldGrid with spatial coordinates
- Validate all connections are bidirectional
- Sets hierarchy fields based on location category:
  - `is_overworld=True` for all AI-generated locations
  - `is_safe_zone=True` for safe categories (town, village, settlement)
  - `is_safe_zone=False` for danger categories (dungeon, wilderness, ruins, cave, forest, mountain)
- Return Location dictionary compatible with GameState (via `WorldGrid.as_dict()`)

**`expand_area(world: dict[str, Location], ai_service: AIService, from_location: str, direction: str, theme: str, target_coords: Tuple[int, int], terrain_type: Optional[str] = None) -> dict[str, Location]`**
- Generate a thematic area (4-7 connected locations) using `AIService.generate_area()`
- Places locations on the grid at calculated absolute coordinates
- Creates bidirectional connections between area locations
- Connects the area entry point back to the source location
- Handles coordinate conflicts and duplicate names gracefully
- Falls back to single-location expansion (`expand_world`) if needed
- Randomly selects sub-theme hints for variety (mystical forest, ancient ruins, haunted grounds, etc.)
- Accepts optional `terrain_type` to pass WFC terrain type to location generation
- Sets hierarchy fields for parent-child relationships:
  - Entry location (rel 0,0): `is_overworld=True`, `sub_locations` populated, `entry_point` set
  - Sub-locations: `is_overworld=False`, `parent_location` set to entry name
  - All locations get `is_safe_zone` based on category
- Return updated world

**`expand_world(world: dict[str, Location], ai_service: AIService, from_location: str, direction: str, theme: str, terrain_type: Optional[str] = None) -> dict[str, Location]`**
- Generate single new location in specified direction (fallback for area generation)
- Calculate coordinates based on source location and direction offset
- Direction offsets: north=(0,+1), south=(0,-1), east=(+1,0), west=(-1,0)
- Add bidirectional connections based on spatial positions
- Guarantee at least one dangling connection for future exploration (prevents dead-ends)
- If AI returns only a back-connection, auto-add a dangling connection (format: "Unexplored {Direction}")
- Sets hierarchy fields: `is_overworld=True`, `is_safe_zone` based on category
- Update world dictionary in-place
- Return updated world
- Accepts optional `world_context` and `region_context` for layered generation
- Accepts optional `terrain_type` to pass WFC terrain type to location generation

**`create_world_with_fallback(ai_service: Optional[AIService] = None, theme: str = "fantasy") -> dict[str, Location]`**
- Attempt AI world generation
- Fall back to default world on failure
- Log warnings about fallback

### 3.6 GameState Context Caching

The GameState class manages context caching for the layered generation system.

**Attributes:**
- `world_context: Optional[WorldContext]` - Cached Layer 1 context (generated once per world)
- `region_contexts: dict[tuple[int, int], RegionContext]` - Cached Layer 2 contexts by coordinates

**Methods:**

`get_or_create_world_context() -> WorldContext`
- Returns cached `world_context` if available
- Generates new WorldContext via `ai_service.generate_world_context()` if AI available
- Falls back to `WorldContext.default(theme)` if AI unavailable
- Caches result for future calls

`get_or_create_region_context(coordinates: Tuple[int, int]) -> RegionContext`
- Returns cached context for coordinates if available
- Generates new RegionContext via `ai_service.generate_region_context()` if AI available
- Falls back to `RegionContext.default(coordinates)` if AI unavailable
- Caches result by coordinate tuple

**Serialization:**
- `to_dict()`: Serializes `world_context` and `region_contexts` with coordinate keys as strings
- `from_dict()`: Deserializes contexts with backward compatibility for saves without context data

## 4. Data Formats

### 4.1 Location Generation Input

```python
{
    "theme": "fantasy",  # Overall world theme
    "context_locations": ["Town Square", "Forest"],  # Existing locations
    "source_location": "Town Square",  # Location to expand from
    "direction": "north"  # Direction of expansion
}
```

### 4.2 Location Generation Output

```python
{
    "name": "Ancient Temple",  # 2-50 characters
    "description": "A weathered temple with...",  # 1-500 characters
    "category": "ruins",  # Location type for gameplay mechanics (optional)
    "npcs": [  # Optional list of NPCs
        {"name": "Temple Guardian", "description": "A robed figure...", "dialogue": "Welcome, traveler.", "role": "guard"}
    ]
}
```

**Note**: Connections/exits are NOT generated by AI. They are determined by the WFC terrain system, ensuring terrain is the single source of truth for spatial structure. AI handles content only (name, description, category, NPCs).

### 4.3 LLM Prompt Template

```
You are a creative game world designer. Generate a new location for a {theme} RPG game.

Context:
- World Theme: {theme}
- Terrain Type: {terrain_type}
- Expanding from: {source_location}
- Direction: {direction}
- Nearby: {neighboring_locations}

Requirements:
1. Create a unique location name (2-50 characters)
2. Write a vivid description (1-500 characters) that matches the terrain type
3. Assign a category (town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village)
4. Ensure the location fits the {theme} theme
5. Make the location interesting and explorable
6. Consider nearby locations for thematic and spatial consistency

Respond with valid JSON in this exact format:
{
  "name": "Location Name",
  "description": "A detailed description...",
  "category": "wilderness"
}
```

**Note**: This is a simplified example. The actual prompts (`DEFAULT_LOCATION_PROMPT_MINIMAL` in `ai_config.py`) include world context, region context, neighboring locations, and request NPCs separately. Connections are NOT requested - they are determined by the WFC terrain system.

## 5. Error Handling

### 5.1 Error Types

**`AIConfigError`**
- Invalid configuration (missing API key, invalid parameters)
- Raised during initialization

**`AIServiceError`**
- API connection failures
- Authentication errors
- Rate limiting

**`AIGenerationError`**
- Malformed LLM responses
- Validation failures
- Parsing errors

**`AITimeoutError`** (subclass of AIServiceError)
- Request timeouts
- Network connectivity issues

### 5.2 Retry Strategy

1. Transient errors (timeout, rate limit): Retry with exponential backoff
2. Authentication errors: Fail immediately
3. Malformed responses: Retry up to max_retries
4. All retries exhausted: Raise AIGenerationError

### 5.3 Fallback Strategy

1. AI generation fails → Use `create_default_world()`
2. Dynamic expansion fails → Show error, don't create connection
3. Cache unavailable → Direct API calls only
4. Invalid API key → Skip AI features, warn user

## 6. Performance Considerations

### 6.1 Caching Strategy

- Cache key: Hash of prompt content
- Cache hit: Return immediately (no API call)
- Cache miss: Generate and cache result
- Cache expiration: Time-based (default: 1 hour)
- Cache storage: In-memory dictionary

### 6.2 Rate Limiting

- Respect OpenAI rate limits
- Exponential backoff on rate limit errors
- Consider batch generation for initial world

### 6.3 Cost Optimization

- Use caching to reduce API calls
- Use gpt-3.5-turbo for cost efficiency
- Keep prompts concise but descriptive
- Limit max_tokens to reasonable values

## 7. Integration Points

### 7.1 GameState Integration

**Modified Methods:**
- `__init__()`: Accept optional `ai_service` and `theme` parameters
- `move()`: Check if destination exists, generate if missing
- `to_dict()`: Include `theme` in serialization
- `from_dict()`: Accept optional `ai_service` parameter

**Dynamic Expansion Behavior:**
1. Player attempts to move in direction
2. Connection exists but destination missing
3. GameState calls `expand_world()` to generate location
4. New location added to world
5. Movement proceeds normally

### 7.2 World Module Integration

**New Function:**
- `create_world(ai_service: Optional[AIService] = None, theme: str = "fantasy") -> dict[str, Location]`
  - Routes to AI or default world creation

### 7.3 Main Integration

**Startup Sequence:**
1. Load AI configuration from environment
2. Initialize AIService if config available
3. Create world (AI or default)
4. Initialize GameState with AI service
5. Start game loop

## 8. Validation Rules

### 8.1 Location Validation

- Name: 2-50 characters (enforced by Location model)
- Description: 1-500 characters (enforced by Location model)
- Category: One of 9 valid types (town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village)
- NPCs: Valid NPC objects with name, description, dialogue, and role

**Note**: Connections are managed by WorldGrid based on WFC terrain, not by AI generation. The AI only generates content (name, description, category, NPCs).

### 8.2 World Validation

- All locations must be reachable from starting location
- Connections should be bidirectional (enforced by generation logic)
- No duplicate location names
- Starting location must exist

## 9. Testing Strategy

### 9.1 Unit Tests

- Mock all API calls
- Test configuration validation
- Test prompt construction
- Test response parsing
- Test error handling
- Test retry logic
- Test caching behavior

### 9.2 Integration Tests

- Test world generation
- Test location expansion
- Test GameState integration
- Test serialization/deserialization
- Test fallback mechanisms

### 9.3 End-to-End Tests

The E2E test suite (`tests/test_e2e_world_expansion.py`) validates dynamic world expansion in realistic gameplay scenarios:

**Test Scenarios:**
- Single location expansion from dangling connection
- Multi-step expansion chains (3+ consecutive expansions)
- Expansion after navigating through existing world
- Expansion when destination already exists (no duplication)
- Failure handling when AI generation fails
- Behavior without AI service (graceful fallback)
- Theme consistency across expansions
- Connection updates after expansion
- Multiple paths to same expansion point
- Game state preservation during expansion
- World integrity after multiple expansions
- Dead-end prevention (locations always have forward exploration options)
- **Area generation tests** (`tests/test_area_generation.py`):
  - Area returns 4-7 connected locations
  - Entry location at origin [0,0]
  - All locations connected and reachable
  - Border closure after expansion
  - Existing world preservation
  - Entry connects to source location
- **Border validation tests** (`tests/test_world_grid.py`):
  - `find_unreachable_exits` detects orphan exits
  - `validate_border_closure` verification
  - `get_frontier_locations` returns correct locations
- **Hierarchy field tests** (`tests/test_ai_world_hierarchy.py`):
  - `_infer_hierarchy_from_category()` helper function
  - `create_ai_world()` sets `is_overworld` and `is_safe_zone` based on category
  - `expand_world()` sets hierarchy fields on expanded locations
  - `expand_area()` sets parent-child relationships for sub-locations
  - Graceful defaults when AI omits hierarchy fields

**Test Infrastructure:**
- Fixtures for different world configurations
- Mock AI service with predictable outputs
- Helper functions for bidirectional connection verification
- World integrity validation utilities

**Coverage:**
- All specification elements validated
- Success and failure paths tested
- State preservation confirmed
- Connection integrity verified

### 9.4 Manual Tests

- Real API integration (with test key)
- Performance testing
- Cost estimation
- User experience testing

## 10. Future Enhancements

- Persistent cache (database or file-based)
- World consistency validation
- Semantic similarity checks for location names
- ~~Support for multiple LLM providers (Anthropic, Cohere, local models)~~ ✓ Implemented (OpenAI, Anthropic, Ollama)
- ~~Graph-based world generation constraints~~ ✓ Implemented via WorldGrid coordinate system
- ~~Location categories/types (town, dungeon, wilderness)~~ ✓ Implemented with 9 category types
- ~~NPC generation~~ ✓ Implemented (AI-generated dialogue and conversations)
- ~~Item generation~~ ✓ Implemented via `AIService.generate_item()`
- ~~Quest generation~~ ✓ Implemented via `AIService.generate_quest()`
