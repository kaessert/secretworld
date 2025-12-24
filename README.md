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

- **Character Creation**: Create custom characters with customizable attributes (strength, dexterity, intelligence)
- **AI-Generated Worlds**: Dynamically generated locations using OpenAI's GPT models (optional)
- **Turn-Based Combat**: Engage enemies with attack, defend, and flee commands
- **Inventory & Equipment**: Collect loot from defeated enemies, equip weapons and armor, use consumables
- **Persistent Saves**: Save and load complete game progress including world state, location, and theme
- **Exploration**: Navigate through interconnected locations
- **Experience System**: Level up by defeating enemies

## Gameplay

### Character Creation
1. Choose a name for your character
2. Choose your stat allocation method (manual or random)
3. Set your three core attributes (1-20 each):
   - **Strength**: Increases attack damage and max HP
   - **Dexterity**: Improves flee chance
   - **Intelligence**: Increases magic attack damage

**Note:** Constitution is automatically derived from your Strength stat and is used to reduce incoming damage during combat.

### Exploration Commands
- `look` - Examine your current location
- `go <direction>` - Move in a direction (north, south, east, west, up, down)
- `status` - View your character's stats
- `inventory` - View your inventory and equipped items
- `equip <item name>` - Equip a weapon or armor from your inventory
- `unequip weapon|armor` - Unequip from the specified slot and return to inventory
- `use <item name>` - Use a consumable item (e.g., health potion)
- `save` - Save complete game state including world, location, and theme (not available during combat)
- `quit` - Exit to main menu

### Combat System
Combat encounters occur randomly as you explore. When in combat:

- `attack` - Attack the enemy (damage based on your strength vs enemy defense)
- `defend` - Take a defensive stance, reducing incoming damage by 50%
- `flee` - Attempt to escape (chance based on dexterity)
- `cast` - Cast a magic attack (damage based on intelligence)
- `status` - View combat status (HP of both combatants)

**Combat Flow:**
1. You attack or defend
2. Enemy attacks (unless you fled successfully)
3. Combat continues until victory, defeat, or successful flee

**Victory**: Gain XP, potentially level up, and may receive loot drops
**Defeat**: Game over (can restore health for testing)
**Flee**: Escape without gaining XP or loot

### Inventory & Equipment

Defeated enemies have a chance to drop loot. Items include:
- **Weapons**: Increase attack damage when equipped
- **Armor**: Reduce incoming damage when equipped
- **Consumables**: Health potions that restore HP when used
- **Misc Items**: Flavor items like gold coins and monster parts

Your inventory has a capacity of 20 items. Use `inventory` to view your items, `equip <item>` to equip weapons/armor, `unequip weapon|armor` to remove equipment, and `use <item>` for consumables. Equipped items apply their bonuses automatically during combat.

### Save System

The game supports automatic and manual saving:

**Autosave**
- Game automatically saves after key events:
  - Moving to a new location
  - Winning combat
  - Successfully fleeing from combat
- Uses a single autosave slot per character (`autosave_{name}.json`)
- Silent operation - never interrupts gameplay

**Manual Saves** (Full Game State)
- Use the `save` command during gameplay
- Saves complete game progress including:
  - Character stats and progress
  - Entire world structure and locations
  - Current location where you left off
  - Theme setting for consistent AI generation
- Resume exactly where you left off with full world intact

**Character-Only Saves** (Legacy)
- Older save format containing only character data
- Fully supported for backward compatibility
- Loading these saves starts a new adventure with the saved character
- Original saves work without any modification needed

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

Run all tests:
```bash
pytest
```

Run specific test suites:
```bash
# AI-related unit and integration tests
pytest tests/test_ai_*.py -v

# Dynamic world expansion E2E tests
pytest tests/test_e2e_world_expansion.py -v

# All tests with coverage
pytest --cov=src/cli_rpg
```

### Project Structure
```
src/cli_rpg/
├── main.py              # Game entry point and main loop
├── game_state.py        # Game state management
├── combat.py            # Combat system
├── character_creation.py # Character creation flow
├── world.py             # Default world generation
├── ai_world.py          # AI-powered world generation
├── ai_service.py        # AI service integration
├── ai_config.py         # AI configuration management
├── autosave.py          # Automatic game saving
├── models/              # Data models
│   ├── character.py
│   ├── location.py
│   ├── enemy.py
│   ├── item.py
│   └── inventory.py
└── persistence.py       # Save/load system (character and full game state)
```

## Documentation

- [AI Features Guide](docs/AI_FEATURES.md) - Detailed AI world generation documentation
- [AI Specification](docs/ai_location_generation_spec.md) - Technical specification for AI features

## License

MIT
