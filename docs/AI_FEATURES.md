# AI-Powered Location Generation

## Overview

The CLI RPG includes AI-powered dynamic location generation using OpenAI's GPT models, Anthropic's Claude models, or local Ollama models. This feature allows the game world to expand dynamically as players explore, creating unique locations on-demand.

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

### 2a. Layered Context System
The AI generation uses a 4-layer hierarchical architecture for consistent, efficient world building:

- **Layer 1 (WorldContext)**: Theme essence, naming style, and narrative tone - generated once at world creation and cached in GameState
- **Layer 2 (RegionContext)**: Region name, theme, danger level, and landmarks - generated per-area and cached by coordinates
- **Layer 3 (Location)**: Individual location details using minimal prompts that reference cached context
- **Layer 4 (NPCs)**: NPC generation as a separate call, keeping each prompt focused and reliable

This architecture reduces API calls and token usage by caching context at higher layers and using minimal prompts at lower layers.

### 3. Graceful Fallbacks
- Game works without API key (uses fallback location templates)
- Falls back to template-based location generation if AI fails
- Fallback locations include 5 terrain themes (wilderness, rocky, misty, grassy, dense thicket)
- The world is truly infinite even without AI - fallback locations always have frontier exits
- No crashes or data loss

### 4. Context-Aware Generation
- Locations fit the overall theme
- Connected to existing world structure
- Bidirectional connections maintained
- Validates against game constraints
- **Grid-based coordinates**: AI-generated locations are placed on a spatial grid, ensuring geographic consistency (moving north then south returns to the same place)
- **Location categories**: AI assigns a category to each location (town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village) which influences enemy spawning during combat encounters
- **NPC population**: AI-generated locations include thematically appropriate NPCs (merchants, quest-givers, villagers) with contextual names and dialogue

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

### 1. Choose Your AI Provider

**Option A: OpenAI (Cloud)**
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Generate an API key

**Option B: Anthropic (Cloud)**
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key

**Option C: Ollama (Local - Free, No API Key Required)**
1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a model: `ollama pull llama3.2`
3. Start the Ollama server: `ollama serve`

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and configure your provider:

**For OpenAI:**
```bash
OPENAI_API_KEY=your-api-key-here
```

**For Anthropic:**
```bash
ANTHROPIC_API_KEY=your-api-key-here
```

**For Ollama (Local AI):**
```bash
AI_PROVIDER=ollama
# Optional: customize the endpoint and model
# OLLAMA_BASE_URL=http://localhost:11434/v1
# OLLAMA_MODEL=llama3.2
```

### 3. Optional Configuration
Customize other settings in `.env`:
- `AI_PROVIDER`: Explicit provider selection (`openai`, `anthropic`, or `ollama`)
- `AI_MODEL`: Model to use (default varies by provider)
  - OpenAI: `gpt-3.5-turbo`
  - Anthropic: `claude-3-5-sonnet-latest`
  - Ollama: `llama3.2`
- `AI_TEMPERATURE`: Randomness (0.0-2.0, default: 0.7)
- `AI_MAX_TOKENS`: Response length (default: 3000)
- `AI_MAX_RETRIES`: API-level retry attempts (default: 3)
- `AI_GENERATION_MAX_RETRIES`: Generation/parsing retry attempts before fallback (default: 2)
- `AI_ENABLE_CACHING`: Enable caching (default: true)
- `AI_CACHE_FILE`: Custom cache file path (default: `~/.cli_rpg/cache/ai_cache.json`)
- `CLI_RPG_REQUIRE_AI`: Strict mode for AI generation (default: true)

**Ollama-specific settings:**
- `OLLAMA_BASE_URL`: Custom Ollama endpoint (default: `http://localhost:11434/v1`)
- `OLLAMA_MODEL`: Model to use (default: `llama3.2`)

### Provider Selection Logic

When both API keys are configured:
1. If `AI_PROVIDER` is explicitly set, that provider is used
2. Otherwise, Anthropic is preferred when both keys are present
3. If only one key is configured, that provider is used automatically

**Note:** Ollama requires `AI_PROVIDER=ollama` to be explicitly set since it doesn't use API keys.

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
   - Supports OpenAI, Anthropic, and Ollama providers

2. **AIService** (`ai_service.py`)
   - Interfaces with OpenAI, Anthropic, or Ollama API
   - Handles retries and errors
   - Manages caching (in-memory with file persistence)
   - Persists cache to disk for cross-session reuse
   - Validates responses
   - Auto-detects provider from configuration
   - Ollama uses OpenAI-compatible API with custom base URL
   - `generate_area()`: Generates clusters of 4-7 connected locations with thematic consistency

3. **AI World** (`ai_world.py`)
   - Creates initial AI world using grid coordinates
   - `expand_area()`: Places generated area on the grid with proper connections
   - `expand_world()`: Single-location fallback expansion
   - Manages connections via WorldGrid
   - Handles fallbacks gracefully
   - **Hierarchy support**: Sets `is_overworld`, `is_safe_zone`, `parent_location`, `sub_locations`, and `entry_point` fields based on location category
   - Safe zone categories (town, village, settlement) get `is_safe_zone=True`; danger zones (dungeon, wilderness, ruins, cave, forest, mountain) get `is_safe_zone=False`

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
1. Basic prompt templates

### 7. AI-Generated Enemies
- Combat encounters feature AI-generated enemies with unique names and stats
- Enemies include descriptions (appearance text) and attack flavor text
- Attack flavor text appears during combat for immersive combat messages
- **ASCII art display**: Enemies show ASCII art when combat begins (5-7 lines, max 40 chars wide)
- AI generates unique ASCII art for each enemy type via `generate_ascii_art()`
- Fallback templates for common enemy categories (beasts, undead, humanoids, creepy crawlies)
- Graceful fallback to template-based enemies when AI is unavailable
- Enemy stats are scaled to player level for balanced encounters
- **Distance-based scaling**: Enemy stats scale with Manhattan distance from origin (0,0) using formula `base_stat * (1 + distance * 0.15)`, making exploration progressively more challenging

### 7a. AI-Generated Location ASCII Art
- Locations display ASCII art when players enter or look at them (3-10 lines, max 50 chars wide)
- AI generates unique ASCII art for each location via `generate_location_ascii_art()`
- Art reflects the location category and theme (forest, dungeon, town, etc.)
- Fallback templates in `location_art.py` for common location categories:
  - Town/city, village, forest, dungeon, cave, ruins, mountain, wilderness, settlement
- Name-based matching: locations named "Dark Forest" use forest templates even without explicit category
- Backward compatible: existing saves without ASCII art load correctly (empty string default)
- ASCII art is persisted with location data and survives save/load cycles

### 7b. AI-Generated NPC ASCII Art
- NPCs display ASCII art when players talk to them (5-7 lines, max 40 chars wide)
- AI generates unique ASCII art for each NPC via `generate_npc_ascii_art()`
- Art reflects the NPC's role and name (merchant, quest_giver, guard, etc.)
- Fallback templates in `npc_art.py` for common NPC roles:
  - Merchant, quest_giver, villager, guard, elder, blacksmith, innkeeper
- Role-based and name-based detection: NPCs named "Town Merchant" use merchant templates
- ASCII art appears above the greeting dialogue when talking
- Backward compatible: existing saves without ASCII art load correctly (empty string default)
- ASCII art is persisted with NPC data and survives save/load cycles

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

### 11. AI-Generated Dreams
- `AIService.generate_dream()` creates personalized dream sequences when players rest
- Triggered with 25% chance when using the `rest` command
- Parameters: `theme`, `dread_percent`, `choices` (flee/kill counts), `location_name`, `is_nightmare`
- Context-aware generation based on:
  - **World theme**: Dreams fit the game's theme (fantasy, sci-fi, etc.)
  - **Dread level**: Higher dread (50%+) triggers nightmare sequences
  - **Player choices**: Dreams reflect combat behavior (fleeing vs. killing)
  - **Current location**: Location name adds context to dream content
- Validates response length (20-300 characters)
- Graceful fallback to template dreams when AI is unavailable or generation fails
- Dreams display with decorative borders and typewriter effect

### 12. AI-Generated Whispers
- `AIService.generate_whisper()` creates atmospheric ambient whispers as players explore
- Triggered with 30% chance when entering new locations
- Parameters: `theme` (world theme), `location_category` (dungeon, forest, town, etc.)
- Context-aware generation based on:
  - **World theme**: Whispers fit the game's theme (fantasy, sci-fi, etc.)
  - **Location category**: Whispers reflect the type of area (eerie for dungeons, peaceful for towns)
- Validates response length (10-100 characters, single sentence)
- Graceful fallback to template whispers when AI is unavailable or generation fails
- Whispers display with typewriter effect for atmospheric presentation

### Future Enhancements
- Advanced world consistency validation
- Additional local model providers

## Troubleshooting

### "API key not found"
- Ensure `.env` file exists
- Check `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set correctly
- Verify no extra spaces or quotes
- If using `AI_PROVIDER`, ensure the corresponding API key is configured
- For Ollama, set `AI_PROVIDER=ollama` (no API key needed)

### "Failed to connect to Ollama"
- Ensure Ollama is installed and running (`ollama serve`)
- Check that the model is pulled (`ollama pull llama3.2`)
- Verify `OLLAMA_BASE_URL` if using a custom endpoint
- Default URL is `http://localhost:11434/v1`

### "Rate limit exceeded"
- Wait before retrying
- Reduce exploration speed
- Check OpenAI/Anthropic dashboard for limits
- Consider switching to Ollama for unlimited local generation

### "Generation failed"
- Check internet connection (for cloud providers)
- Verify API key is valid
- Check OpenAI/Anthropic service status
- For Ollama, ensure the model is loaded
- Game will fall back to default world

### Slow generation
- First generation takes 1-3 seconds (normal for cloud providers)
- Ollama speed depends on your hardware (faster with GPU)
- Subsequent visits use cache (<1ms)
- Check network connection (for cloud providers)

## Support

For issues or questions:
1. Check the logs for error details
2. Verify configuration in `.env`
3. Test with a simple example
4. Check OpenAI service status

## License

Same as main project (MIT)
