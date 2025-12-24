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
- `max_tokens: int` - Maximum response length (default: 500)
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
- Returns: `{"name": str, "description": str, "connections": dict[str, str]}`
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

### 3.3 World Generation Functions

**`create_ai_world(ai_service: AIService, theme: str = "fantasy", starting_location_name: str = "Town Square", initial_size: int = 3) -> dict[str, Location]`**
- Generate initial world with connected locations
- Validate all connections are bidirectional
- Return Location dictionary compatible with GameState

**`expand_world(world: dict[str, Location], ai_service: AIService, from_location: str, direction: str, theme: str) -> dict[str, Location]`**
- Generate new location in specified direction
- Add bidirectional connections
- Update world dictionary in-place
- Return updated world

**`create_world_with_fallback(ai_service: Optional[AIService] = None, theme: str = "fantasy") -> dict[str, Location]`**
- Attempt AI world generation
- Fall back to default world on failure
- Log warnings about fallback

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
    "connections": {  # Suggested connections
        "south": "Town Square",  # Back to source
        "east": "Sacred Grove",  # Potential new location
        "west": "Ruins"
    }
}
```

### 4.3 LLM Prompt Template

```
You are a creative game world designer. Generate a new location for a {theme} RPG game.

Context:
- World Theme: {theme}
- Existing Locations: {location_list}
- Expanding from: {source_location}
- Direction: {direction}

Requirements:
1. Create a unique location name (2-50 characters)
2. Write a vivid description (1-500 characters)
3. Suggest 1-4 connections to other locations
4. Include a connection back to {source_location} via the opposite direction of {direction}
5. Ensure the location fits the {theme} theme
6. Make the location interesting and explorable

Respond with valid JSON in this exact format:
{
  "name": "Location Name",
  "description": "A detailed description...",
  "connections": {
    "direction": "location_name"
  }
}
```

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
- Connections: Only valid directions (north, south, east, west, up, down)
- No self-connections
- All connection targets must exist in world

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

### 9.3 Manual Tests

- Real API integration (with test key)
- Performance testing
- Cost estimation
- User experience testing

## 10. Future Enhancements

- Support for multiple LLM providers (Anthropic, Cohere, local models)
- Persistent cache (database or file-based)
- Location categories/types (town, dungeon, wilderness)
- NPC generation
- Item generation
- Quest generation
- World consistency validation
- Semantic similarity checks for location names
- Graph-based world generation constraints
