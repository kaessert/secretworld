# CLI RPG

A CLI-based role-playing game with AI-generated worlds and turn-based combat. The entire game world is generated on-the-fly using AI and persisted, allowing for endless exploration.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run the game
python -m cli_rpg.main
```

## Features

- **Character Creation**: Create custom characters with customizable attributes (strength, dexterity, constitution, intelligence)
- **AI-Generated Worlds**: Dynamically generated locations using OpenAI's GPT models (optional)
- **Turn-Based Combat**: Engage enemies with attack, defend, and flee commands
- **Persistent Saves**: Save and load your game progress
- **Exploration**: Navigate through interconnected locations
- **Experience System**: Level up by defeating enemies

## Gameplay

### Character Creation
1. Choose a name for your character
2. Distribute 30 stat points across four attributes:
   - **Strength**: Increases attack damage
   - **Dexterity**: Improves flee chance
   - **Constitution**: Reduces damage taken
   - **Intelligence**: (Future feature)

### Exploration Commands
- `look` - Examine your current location
- `go <direction>` - Move in a direction (north, south, east, west, up, down)
- `status` - View your character's stats
- `save` - Save your game (not available during combat)
- `quit` - Exit to main menu

### Combat System
Combat encounters occur randomly as you explore. When in combat:

- `attack` - Attack the enemy (damage based on your strength vs enemy defense)
- `defend` - Take a defensive stance, reducing incoming damage by 50%
- `flee` - Attempt to escape (chance based on dexterity)
- `status` - View combat status (HP of both combatants)

**Combat Flow:**
1. You attack or defend
2. Enemy attacks (unless you fled successfully)
3. Combat continues until victory, defeat, or successful flee

**Victory**: Gain XP and potentially level up
**Defeat**: Game over (can restore health for testing)
**Flee**: Escape without gaining XP

### AI World Generation (Optional)

Enable dynamic world generation with AI:

1. Get an OpenAI API key from [platform.openai.com](https://platform.openai.com/)
2. Create a `.env` file:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```
3. Select a theme when creating a new character (fantasy, sci-fi, cyberpunk, etc.)

See [docs/AI_FEATURES.md](docs/AI_FEATURES.md) for detailed AI configuration.

## Development

### Running Tests
```bash
pytest
```

### Project Structure
```
src/cli_rpg/
├── main.py              # Game entry point and main loop
├── game_state.py        # Game state management
├── combat.py            # Combat system
├── character_creation.py # Character creation flow
├── world.py             # World generation
├── ai_service.py        # AI integration (optional)
├── models/              # Data models
│   ├── character.py
│   ├── location.py
│   └── enemy.py
└── persistence.py       # Save/load system
```

## Documentation

- [AI Features Guide](docs/AI_FEATURES.md) - Detailed AI world generation documentation
- [AI Specification](docs/ai_location_generation_spec.md) - Technical specification for AI features

## License

MIT
