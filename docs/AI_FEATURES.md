# AI-Powered Location Generation

## Overview

The CLI RPG includes AI-powered dynamic location generation using OpenAI's GPT models or Anthropic's Claude models. This feature allows the game world to expand dynamically as players explore, creating unique locations on-demand.

## Features

### 1. Dynamic World Generation
- **Area-based expansion**: When exploring new territory, the AI generates clusters of 4-7 connected locations at once, creating thematic areas (mystical forests, ancient ruins, haunted grounds, etc.)
- AI creates contextually appropriate locations based on:
  - World theme (fantasy, sci-fi, cyberpunk, etc.)
  - Existing locations
  - Direction of exploration
  - Source location
  - Sub-theme hints for area variety

### 2. Intelligent Caching
- Generated locations are cached to reduce API calls
- **Persistent file-based cache**: Cache survives game restarts (stored at `~/.cli_rpg/cache/ai_cache.json` by default)
- Cache expires after 1 hour (configurable via `cache_ttl`)
- Expired entries are automatically pruned on load
- Significant cost savings for repeated scenarios and across sessions

### 3. Graceful Fallbacks
- Game works without API key (uses default world)
- Falls back to default world if AI generation fails
- No crashes or data loss

### 4. Context-Aware Generation
- Locations fit the overall theme
- Connected to existing world structure
- Bidirectional connections maintained
- Validates against game constraints
- **Grid-based coordinates**: AI-generated locations are placed on a spatial grid, ensuring geographic consistency (moving north then south returns to the same place)

### 5. Theme Persistence
- Theme setting is saved with game state
- Restored when loading saved games
- Ensures consistent AI generation across sessions
- AI service continues using saved theme for new locations

### 6. AI-Generated NPC Dialogue & Extended Conversations
- NPCs generate contextual dialogue when players talk to them
- Dialogue considers NPC role (merchant, quest-giver, villager), location, and world theme
- Generated greetings are persisted to the NPC's greetings list for consistency
- Up to 3 unique greetings are generated per NPC to provide variety
- **Extended Conversations**: Players can have multi-turn conversations with NPCs
  - After the initial greeting, type messages freely to continue the dialogue
  - The AI maintains conversation context for natural back-and-forth exchanges
  - Conversation history is stored per-NPC and persists across save/load (capped at 10 exchanges)
  - Type `bye`, `leave`, or `exit` to end the conversation
  - Movement is blocked while in conversation mode
- Silent fallback if AI service is unavailable (NPC responds with "nods thoughtfully")

## Setup

### 1. Get an API Key

**Option A: OpenAI**
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Generate an API key

**Option B: Anthropic**
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```bash
# For OpenAI
OPENAI_API_KEY=your-api-key-here

# OR for Anthropic
ANTHROPIC_API_KEY=your-api-key-here
```

### 3. Optional Configuration
Customize other settings in `.env`:
- `AI_PROVIDER`: Explicit provider selection (`openai` or `anthropic`)
- `AI_MODEL`: Model to use (default: `gpt-3.5-turbo` for OpenAI, `claude-3-5-sonnet-latest` for Anthropic)
- `AI_TEMPERATURE`: Randomness (0.0-2.0, default: 0.7)
- `AI_MAX_TOKENS`: Response length (default: 500)
- `AI_MAX_RETRIES`: Retry attempts (default: 3)
- `AI_ENABLE_CACHING`: Enable caching (default: true)
- `AI_CACHE_FILE`: Custom cache file path (default: `~/.cli_rpg/cache/ai_cache.json`)
- `CLI_RPG_REQUIRE_AI`: Strict mode for AI generation (default: true)

### Provider Selection Logic

When both API keys are configured:
1. If `AI_PROVIDER` is explicitly set, that provider is used
2. Otherwise, Anthropic is preferred when both keys are present
3. If only one key is configured, that provider is used automatically

### Strict Mode (CLI_RPG_REQUIRE_AI)

By default, strict mode is enabled. When AI generation fails:
- **Strict mode (default)**: User is prompted with three options:
  1. Retry AI generation
  2. Use default world (explicit fallback)
  3. Return to main menu
- **Non-strict mode** (`CLI_RPG_REQUIRE_AI=false`): Silently falls back to the default world without prompting

This ensures users are always aware when AI generation fails, rather than unknowingly playing with the default world.

## Usage

### As a Player
Just play the game normally! When you move to a new direction, the game will:
1. Check if the location exists
2. If not, generate an entire area (4-7 connected locations) using AI (if configured)
3. Or use the default world structure if AI is unavailable

**Saving and Loading:**
- Use the `save` command to save your complete game state, including:
  - All generated locations and world structure
  - Your current location
  - Theme setting for consistent AI generation
- When you load a saved game, you'll resume exactly where you left off
- AI service can continue generating new locations in the saved world
- The game maintains theme consistency across save/load cycles

**Note**: Combat commands (attack, defend, flee, cast) are only available during combat encounters. The save command is not available during combat to maintain game integrity.

### As a Developer

```python
from cli_rpg.config import load_ai_config
from cli_rpg.ai_service import AIService
from cli_rpg.world import create_world
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.persistence import save_game_state, load_game_state

# Load AI configuration
config = load_ai_config()

# Create AI service
ai_service = AIService(config) if config else None

# Create world with AI
world = create_world(ai_service=ai_service, theme="fantasy")

# Create character
character = Character(name="Hero", strength=15, dexterity=12, intelligence=14)

# Create game state with AI support
game = GameState(
    character=character,
    world=world,
    starting_location="Town Square",
    ai_service=ai_service,
    theme="fantasy"
)

# Move around - locations generated dynamically!
success, message = game.move("north")

# Save complete game state (world, location, character, theme)
filepath = save_game_state(game)

# Later: Load game state and continue from exact same spot
loaded_game = load_game_state(filepath)
# Re-attach AI service for continued world expansion
loaded_game.ai_service = ai_service
```

## Architecture

### Components

1. **AIConfig** (`ai_config.py`)
   - Manages configuration
   - Validates settings
   - Loads from environment
   - Supports both OpenAI and Anthropic providers

2. **AIService** (`ai_service.py`)
   - Interfaces with OpenAI or Anthropic API
   - Handles retries and errors
   - Manages caching (in-memory with file persistence)
   - Persists cache to disk for cross-session reuse
   - Validates responses
   - Auto-detects provider from configuration
   - `generate_area()`: Generates clusters of 4-7 connected locations with thematic consistency

3. **AI World** (`ai_world.py`)
   - Creates initial AI world using grid coordinates
   - `expand_area()`: Places generated area on the grid with proper connections
   - `expand_world()`: Single-location fallback expansion
   - Manages connections via WorldGrid
   - Handles fallbacks gracefully

4. **WorldGrid** (`world_grid.py`)
   - Coordinate-based world storage
   - Automatic bidirectional connections
   - Direction offsets: north=(0,+1), south=(0,-1), east=(+1,0), west=(-1,0)
   - Border validation methods:
     - `find_unreachable_exits()`: Identifies exits pointing to empty coordinates
     - `validate_border_closure()`: Checks if world border is "closed"
     - `get_frontier_locations()`: Returns locations at the expansion frontier
   - Backward-compatible serialization

5. **GameState Integration** (`game_state.py`)
   - Detects missing locations
   - Triggers generation
   - Updates connections
   - Maintains consistency

### Error Handling

The system handles various error scenarios:
- **No API Key**: In strict mode, prompts user with options; in non-strict mode, falls back to default world
- **Invalid API Key**: In strict mode, prompts user with options; in non-strict mode, shows error and uses default world
- **Network Issues**: Retries with exponential backoff
- **Rate Limiting**: Respects API provider limits (OpenAI/Anthropic)
- **Malformed Responses**: Validates and retries
- **Timeout**: Handles gracefully

See [Strict Mode](#strict-mode-cli_rpg_require_ai) above for details on how failures are presented to users.

## Cost Considerations

### Estimated Costs (GPT-3.5-Turbo)
- Per location generation: ~$0.0007-0.001
- Initial world (3 locations): ~$0.002-0.003
- With caching: Significant reduction

### Cost Optimization Tips
1. Enable caching (reduces repeat calls)
2. Use gpt-3.5-turbo instead of gpt-4
3. Set reasonable max_tokens limit
4. Adjust temperature based on needs

## Performance

### Response Times
- Cached locations: <1ms
- API calls: 1-3 seconds
- With retries: Additional delay on errors

### API Call Optimization
- Initial world: 3-5 calls
- Per new location: 1 call
- Cached: 0 calls

## Testing

All AI features are fully tested with comprehensive test coverage:

### Unit and Integration Tests (68 tests)
- Configuration validation (13 tests)
- AI service functionality (16 tests)
- AI cache persistence (13 tests)
- World generation (15 tests)
- GameState integration (11 tests)

### End-to-End Tests (11 tests)
The E2E test suite validates dynamic world expansion in realistic player scenarios:
- Basic single expansion with dangling connection detection
- Multi-step expansion chains
- Mixed navigation through existing and generated locations
- Failure handling and graceful degradation
- Theme consistency and world integrity

Tests use mocked API calls - no real API calls during testing.

Run all AI tests:
```bash
pytest tests/test_ai_*.py tests/test_e2e_world_expansion.py -v
```

Run only E2E tests:
```bash
pytest tests/test_e2e_world_expansion.py -v
```

## Limitations

### Current Limitations
1. No location categories/types
2. Basic prompt templates

### 7. AI-Generated Enemies
- Combat encounters feature AI-generated enemies with unique names and stats
- Enemies include descriptions (appearance text) and attack flavor text
- Attack flavor text appears during combat for immersive combat messages
- Graceful fallback to template-based enemies when AI is unavailable
- Enemy stats are scaled to player level for balanced encounters

### 8. AI-Generated Items
- `AIService.generate_item()` creates contextual items based on theme, location, and player level
- Supports all item types: weapons (damage_bonus), armor (defense_bonus), consumables (heal_amount), misc
- Optional `item_type` parameter constrains generation to specific type
- Returns item properties including name, description, stats, and suggested price
- Validates generated items against game constraints (name length, stat ranges)
- Graceful fallback when AI is unavailable

### 9. AI-Generated Lore
- `AIService.generate_lore()` creates immersive world history and lore snippets
- Parameters: `theme`, `location_name` (optional), `lore_category` (history/legend/secret)
- Generates 50-500 character snippets appropriate to the world context
- Categories:
  - **history**: Past events, kingdoms, wars
  - **legend**: Myths, prophecies, heroes
  - **secret**: Hidden knowledge, mysteries
- Graceful handling of empty location names (uses "the world" as context)

### 10. AI-Generated Quests
- `AIService.generate_quest()` creates dynamic quests appropriate to the world theme
- Parameters: `theme`, `npc_name` (quest giver), `player_level`, `location_name` (optional)
- Returns quest properties:
  - **name**: Quest title (2-30 characters)
  - **description**: Quest narrative (1-200 characters)
  - **objective_type**: One of kill, collect, explore, talk, drop
  - **target**: Target name (enemy type, item name, location, or NPC)
  - **target_count**: Number to complete (≥1)
  - **gold_reward** and **xp_reward**: Quest completion rewards
  - **quest_giver**: Set to the NPC name for tracking
- Validates generated quests against Quest model constraints
- Integrated with caching for performance optimization
- Graceful fallback when AI is unavailable

### Future Enhancements
- Local model support
- Advanced world consistency validation

## Troubleshooting

### "API key not found"
- Ensure `.env` file exists
- Check `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set correctly
- Verify no extra spaces or quotes
- If using `AI_PROVIDER`, ensure the corresponding API key is configured

### "Rate limit exceeded"
- Wait before retrying
- Reduce exploration speed
- Check OpenAI dashboard for limits

### "Generation failed"
- Check internet connection
- Verify API key is valid
- Check OpenAI service status
- Game will fall back to default world

### Slow generation
- First generation takes 1-3 seconds (normal)
- Subsequent visits use cache (<1ms)
- Check network connection

## Support

For issues or questions:
1. Check the logs for error details
2. Verify configuration in `.env`
3. Test with a simple example
4. Check OpenAI service status

## License

Same as main project (MIT)
