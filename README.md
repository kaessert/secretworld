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
- **AI-Generated Worlds**: Dynamically generated locations using OpenAI or Anthropic Claude models (optional)
- **Turn-Based Combat**: Engage enemies with attack, defend, and flee commands
- **Inventory & Equipment**: Collect loot from defeated enemies, equip weapons and armor, use consumables
- **NPC Shops**: Interact with merchants, buy equipment, and sell items for gold
- **AI-Generated Dialogue**: NPCs feature contextual AI-generated conversations that persist across sessions
- **Gold Economy**: Earn gold from combat victories, spend it at shops
- **Persistent Saves**: Save and load complete game progress including world state, location, and theme
- **Grid-Based World**: Navigate a spatially consistent world where directions are reliable (going north then south returns you to the same place)
- **Experience System**: Level up by defeating enemies
- **Colorized Output**: Color-coded terminal output for improved readability (enemies in red, locations in cyan, items in green, etc.)

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
- `look` (l) - Examine your current location
- `go <direction>` (g) - Move in a direction (north/n, south/s, east/e, west/w)
- `map` (m) - Display an ASCII map of explored locations with available exits
- `status` (s) - View your character's stats, gold, and XP progress
- `inventory` (i) - View your inventory and equipped items
- `equip <item name>` (e) - Equip a weapon or armor from your inventory
- `unequip weapon|armor` - Unequip from the specified slot and return to inventory
- `use <item name>` (u) - Use a consumable item (e.g., health potion)
- `talk <npc>` (t) - Talk to an NPC (opens shop if merchant, shows quests if quest-giver, or enter extended conversation)
- `accept <quest>` - Accept a quest from the NPC you're talking to
- `shop` - View the current merchant's inventory and prices
- `buy <item>` - Purchase an item from the current shop
- `sell <item>` - Sell an item from your inventory for gold
- `drop <item>` (dr) - Drop an item from your inventory (cannot drop equipped items)
- `quests` (q) - View your quest journal with all active and completed quests
- `quest <name>` - View details of a specific quest (supports partial matching)
- `complete <quest>` - Turn in a completed quest to the NPC you're talking to
- `abandon <quest>` - Abandon an active quest from your journal
- `lore` - Discover AI-generated lore snippets about your current location
- `rest` (r) - Rest to recover health (restores 25% of max HP, not available during combat)
- `save` - Save complete game state including world, location, and theme (not available during combat)
- `help` (h) - Display the full command reference
- `quit` - Exit to main menu

### Combat System
Combat encounters occur randomly as you explore. When in combat:

- `attack` (a) - Attack the enemy (damage based on your strength vs enemy defense)
- `defend` (d) - Take a defensive stance, reducing incoming damage by 50%
- `flee` (f) - Attempt to escape (chance based on dexterity)
- `cast` (c) - Cast a magic attack (damage based on intelligence)
- `use <item>` (u) - Use a consumable item (e.g., health potion) - counts as your turn
- `status` (s) - View combat status (HP of both combatants)
- `help` (h) - Display the full command reference
- `quit` - Exit to main menu (no save during combat - combat progress will be lost)

**Combat Flow:**
1. You attack or defend
2. Enemy attacks (unless you fled successfully)
3. Combat continues until victory, defeat, or successful flee

**Victory**: Gain XP and gold, potentially level up, and may receive loot drops
**Defeat**: Game over (can restore health for testing)
**Flee**: Escape without gaining XP, gold, or loot

### Inventory & Equipment

Defeated enemies have a chance to drop loot. Items include:
- **Weapons**: Increase attack damage when equipped
- **Armor**: Reduce incoming damage when equipped
- **Consumables**: Health potions that restore HP when used
- **Misc Items**: Flavor items like gold coins and monster parts

Your inventory has a capacity of 20 items. Use `inventory` to view your items, `equip <item>` to equip weapons/armor, `unequip weapon|armor` to remove equipment, and `use <item>` for consumables. Equipped items apply their bonuses automatically during combat.

### NPC Shops

Merchants can be found throughout the world. Interact with them to buy and sell items:

1. Use `look` to see NPCs in your location
2. Use `talk <npc>` to interact with a merchant and open their shop
3. Use `shop` to view available items and prices
4. Use `buy <item>` to purchase items (requires sufficient gold)
5. Use `sell <item>` to sell items from your inventory for gold

**Earning Gold**: Defeat enemies in combat to earn gold (5-15 × enemy level per victory).

### NPC Quests

Quest-giver NPCs can be found throughout the world. Interact with them to receive quests:

1. Use `look` to see NPCs in your location
2. Use `talk <npc>` to interact with a quest-giver and see available quests
3. Use `accept <quest>` to accept a quest (partial matching supported)
4. Use `quests` to view your quest journal (shows active, ready to turn in, and completed quests)

**Quest Progress**: Quests automatically track your progress:
- **Kill quests**: Progress updates when you defeat matching enemies in combat
- **Collect quests**: Progress updates when you acquire matching items (from combat loot or shop purchases)
- **Drop quests**: Progress updates when you defeat a specific enemy AND it drops a specific item (e.g., "Collect 3 Wolf Pelts from Wolves")
- **Explore quests**: Progress updates when you visit matching locations
- **Talk quests**: Progress updates when you talk to matching NPCs
- **Use quests**: Progress updates when you use matching consumable items (e.g., "Use a Health Potion")

You'll see progress messages after each relevant action.

**Turning In Quests**: When quest objectives are complete, you must return to the quest giver:
1. Travel back to the NPC who gave you the quest
2. Use `talk <npc>` to interact with them (shows quests ready to turn in)
3. Use `complete <quest>` to claim your rewards

**Quest Rewards**: Rewards are granted when you turn in a quest:
- **Gold**: Added directly to your gold total
- **XP**: Grants experience points (may trigger level-ups)
- **Items**: Quest reward items are added to your inventory

**Note**: You must talk to an NPC before accepting or completing their quests. Quest names are matched case-insensitively.

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

Enable dynamic world generation with AI using either OpenAI or Anthropic:

**Option 1: OpenAI**
1. Get an API key from [platform.openai.com](https://platform.openai.com/)
2. Create a `.env` file:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

**Option 2: Anthropic**
1. Get an API key from [console.anthropic.com](https://console.anthropic.com/)
2. Create a `.env` file:
   ```bash
   ANTHROPIC_API_KEY=your-api-key-here
   ```

**Both keys configured?** Anthropic is used by default. Set `AI_PROVIDER=openai` to use OpenAI instead.

3. Select a theme when creating a new character (fantasy, sci-fi, cyberpunk, etc.)

**Strict Mode (Default)**: If AI generation fails, you'll be prompted with options to retry, use the default world, or return to the main menu. To enable silent fallback (no prompts), set `CLI_RPG_REQUIRE_AI=false` in your `.env` file.

See [docs/AI_FEATURES.md](docs/AI_FEATURES.md) for detailed AI configuration.

### Disabling Colors

Colors are enabled by default for terminals that support ANSI escape codes. To disable colorized output:

```bash
CLI_RPG_NO_COLOR=true cli-rpg
```

Or add to your `.env` file:
```bash
CLI_RPG_NO_COLOR=true
```

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
├── world_grid.py        # Grid-based world coordinate system
├── ai_world.py          # AI-powered world generation
├── ai_service.py        # AI service integration
├── ai_config.py         # AI configuration management
├── autosave.py          # Automatic game saving
├── models/              # Data models
│   ├── character.py
│   ├── location.py
│   ├── enemy.py
│   ├── item.py
│   ├── inventory.py
│   ├── npc.py
│   ├── quest.py
│   └── shop.py
└── persistence.py       # Save/load system (character and full game state)
```

## Documentation

- [AI Features Guide](docs/AI_FEATURES.md) - Detailed AI world generation documentation
- [AI Specification](docs/ai_location_generation_spec.md) - Technical specification for AI features

## License

MIT
