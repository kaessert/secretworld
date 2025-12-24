# AI-Powered Location Generation

## Overview

The CLI RPG now includes AI-powered dynamic location generation using OpenAI's GPT models. This feature allows the game world to expand dynamically as players explore, creating unique locations on-demand.

## Features

### 1. Dynamic World Generation
- Locations are generated dynamically as players explore
- AI creates contextually appropriate locations based on:
  - World theme (fantasy, sci-fi, cyberpunk, etc.)
  - Existing locations
  - Direction of exploration
  - Source location

### 2. Intelligent Caching
- Generated locations are cached to reduce API calls
- Cache expires after 1 hour (configurable)
- Significant cost savings for repeated scenarios

### 3. Graceful Fallbacks
- Game works without API key (uses default world)
- Falls back to default world if AI generation fails
- No crashes or data loss

### 4. Context-Aware Generation
- Locations fit the overall theme
- Connected to existing world structure
- Bidirectional connections maintained
- Validates against game constraints

### 5. Theme Persistence
- Theme setting is saved with game state
- Restored when loading saved games
- Ensures consistent AI generation across sessions
- AI service continues using saved theme for new locations

## Setup

### 1. Get an OpenAI API Key
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Generate an API key

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```bash
OPENAI_API_KEY=your-api-key-here
```

### 3. Optional Configuration
Customize other settings in `.env`:
- `AI_MODEL`: Model to use (default: gpt-3.5-turbo)
- `AI_TEMPERATURE`: Randomness (0.0-2.0, default: 0.7)
- `AI_MAX_TOKENS`: Response length (default: 500)
- `AI_MAX_RETRIES`: Retry attempts (default: 3)
- `AI_ENABLE_CACHING`: Enable caching (default: true)

## Usage

### As a Player
Just play the game normally! When you move to a new direction, the game will:
1. Check if the location exists
2. If not, generate it using AI (if configured)
3. Or use the default world structure

**Saving and Loading:**
- Use the `save` command to save your complete game state, including:
  - All generated locations and world structure
  - Your current location
  - Theme setting for consistent AI generation
- When you load a saved game, you'll resume exactly where you left off
- AI service can continue generating new locations in the saved world
- The game maintains theme consistency across save/load cycles

**Note**: Combat commands (attack, defend, flee) are only available during combat encounters. The save command is not available during combat to maintain game integrity.

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

2. **AIService** (`ai_service.py`)
   - Interfaces with OpenAI API
   - Handles retries and errors
   - Manages caching
   - Validates responses

3. **AI World** (`ai_world.py`)
   - Creates initial AI world
   - Expands world dynamically
   - Manages connections
   - Handles fallbacks

4. **GameState Integration** (`game_state.py`)
   - Detects missing locations
   - Triggers generation
   - Updates connections
   - Maintains consistency

### Error Handling

The system handles various error scenarios:
- **No API Key**: Falls back to default world
- **Invalid API Key**: Shows error, uses default world
- **Network Issues**: Retries with exponential backoff
- **Rate Limiting**: Respects OpenAI limits
- **Malformed Responses**: Validates and retries
- **Timeout**: Handles gracefully

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

All AI features are fully tested with 55 dedicated tests:
- Configuration validation (13 tests)
- AI service functionality (16 tests)
- World generation (15 tests)
- GameState integration (11 tests)

Tests use mocked API calls - no real API calls during testing.

Run tests:
```bash
pytest tests/test_ai_*.py -v
```

## Limitations

### Current Limitations
1. Single LLM provider (OpenAI)
2. In-memory cache only
3. No location categories/types
4. Basic prompt templates

### Future Enhancements
- Multiple LLM providers (Anthropic, local models)
- Persistent cache (database/file)
- NPC generation
- Item generation
- Quest generation
- Advanced world consistency validation

## Troubleshooting

### "API key not found"
- Ensure `.env` file exists
- Check `OPENAI_API_KEY` is set correctly
- Verify no extra spaces or quotes

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
