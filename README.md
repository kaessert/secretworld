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
- **AI-Generated Worlds**: Dynamically generated locations using OpenAI, Anthropic, or Ollama local models (optional)
- **Turn-Based Combat**: Engage enemies with attack, defend, and flee commands
- **Inventory & Equipment**: Collect loot from defeated enemies, equip weapons and armor, use consumables
- **NPC Shops**: Interact with merchants, buy equipment, and sell items for gold
- **AI-Generated Dialogue**: NPCs feature contextual AI-generated conversations that persist across sessions
- **Gold Economy**: Earn gold from combat victories, spend it at shops
- **Persistent Saves**: Save and load complete game progress including world state, location, and theme
- **Day/Night Cycle**: Time advances as you explore (movement: +1 hour, rest: +4 hours). Night brings eerie whispers and some NPCs/shops may be unavailable
- **Weather System**: Dynamic weather (clear, rain, storm, fog) affects gameplay with dread modifiers and storm travel delays. Underground locations are sheltered from weather.
- **Dread System**: Psychological horror element that tracks your fear level (0-100%). Dangerous areas build dread; high dread causes paranoid whispers and combat penalties. Reduce dread by resting, visiting towns, or talking to NPCs.
- **Grid-Based World**: Navigate a spatially consistent world where directions are reliable (going north then south returns you to the same place)
- **Experience System**: Level up by defeating enemies
- **Colorized Output**: Color-coded terminal output for improved readability (enemies in red, locations in cyan, items in green, etc.)
- **Tab Completion**: Auto-complete commands and contextual arguments (directions, NPCs, items) with Tab key
- **Command History**: Navigate previous commands with up/down arrow keys (persists across sessions)

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
- `look` (l) - Examine your current location (use multiple times to reveal environmental details and hidden secrets)
- `go <direction>` (g) - Move in a direction (north/n, south/s, east/e, west/w)
  - Quick shortcuts: `n`, `gn` (north), `w`, `gw` (west), `gs` (south), `ge` (east)
- `map` (m) - Display an ASCII map of explored locations with available exits
- `status` (s, stats) - View your character's stats, gold, XP progress, current time, and weather
- `inventory` (i) - View your inventory and equipped items
- `equip <item name>` (e) - Equip a weapon or armor from your inventory
- `unequip weapon|armor` - Unequip from the specified slot and return to inventory
- `use <item name>` (u) - Use a consumable item (e.g., health potion)
- `talk [npc]` (t) - Talk to an NPC (opens shop if merchant, shows quests if quest-giver, or enter extended conversation). If only one NPC is present, starts conversation automatically. If multiple NPCs are present, lists available NPCs.
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
- `bestiary` (b) - View all defeated enemies with kill counts and stats
- `dump-state` - Export complete game state as JSON for programmatic inspection
- `rest` (r) - Rest to recover health (restores 25% of max HP, advances time by 4 hours, reduces dread, may trigger dreams; not available during combat)
- `events` - View active world events and their status
- `save` - Save complete game state including world, location, and theme (not available during combat)
- `help` (h) - Display the full command reference
- `quit` - Exit to main menu

### World Events
The world is alive with timed events that progress with in-game time:

- **Caravans**: Trading caravans pass through locations, offering opportunities for commerce
- **Plagues**: Disease outbreaks spread through affected areas, creating urgency
- **Invasions**: Hostile forces threaten locations, requiring player intervention

Events have limited duration and consequences if not resolved. Use the `events` command to view active events and their time remaining. When entering a location affected by an event, you'll receive a warning. Events persist across save/load.

### Random Travel Encounters
When moving between locations, you have a 15% chance to trigger a random encounter:
- **Hostile Encounters** (60%): Wandering enemies ambush you, immediately starting combat
- **Merchant Encounters** (25%): A traveling merchant appears with 2-3 items for sale (use `talk` to shop)
- **Wanderer Encounters** (15%): A mysterious traveler offers lore and atmosphere (use `talk` to converse)

Merchants and wanderers are added to your current location and can be interacted with normally.

### Combat System
Combat encounters occur randomly as you explore. You may face multiple enemies at once (1-2 enemies at lower levels, up to 3 at level 4+). Enemies display ASCII art when combat begins.

**Distance-Based Difficulty**: Enemy difficulty scales based on how far you've traveled from the starting location (0,0). The further you explore, the stronger the enemies:
- Near spawn (0-3 tiles): Easy encounters for new players
- Mid-range (4-7 tiles): Moderate difficulty
- Far reaches (8-12 tiles): Challenging encounters
- Deep wilderness (13+ tiles): Dangerous, high-risk high-reward

Enemy stats (HP, attack, defense) and XP rewards all scale with distance, encouraging strategic exploration and progression.

**Boss Fights**: Occasionally, you'll encounter powerful boss enemies with enhanced stats (2x health, attack, and defense) and 4x XP rewards. Bosses are guaranteed to drop legendary loot with enhanced stats upon defeat. Boss types vary by location category (Lich Lords in dungeons, Ancient Guardians in ruins, Cave Troll Kings in caves, etc.).

**Status Effects**: Some enemies can inflict status effects during combat:
- **Poison**: Certain creatures (spiders, snakes, serpents, vipers) have a chance to poison you on attack. Poison deals damage each turn and wears off after a set duration.
- **Burn**: Fire-based enemies (fire elementals, dragons, flame creatures) can inflict burn, dealing damage over time for 2 turns.
- **Bleed**: Slashing enemies (wolves, bears, lions, claw/fang-based creatures) can cause bleeding wounds, dealing 3 damage per turn for 4 turns.
- **Stun**: Heavy-hitting enemies (trolls, golems, giants, hammer-wielders) can stun you, causing you to skip your next action.
- **Freeze**: Ice-themed enemies (yetis, frost creatures) can freeze you or themselves, reducing attack damage by 50% while frozen.

Status effects are cleared when combat ends.

**Combat Commands:**
- `attack [target]` (a) - Attack an enemy (damage based on your strength vs enemy defense). Specify a target name when facing multiple enemies, or attacks the first living enemy.
- `defend` (d) - Take a defensive stance, reducing incoming damage by 50% from all enemies
- `flee` (f) - Attempt to escape (chance based on dexterity)
- `cast [target]` (c) - Cast a magic attack at an enemy (damage based on intelligence). Targeting works like `attack`.
- `use <item>` (u) - Use a consumable item (e.g., health potion) - counts as your turn
- `status` (s, stats) - View combat status (HP of you and all enemies, action history, pending combos)
- `help` (h) - Display the full command reference
- `quit` - Exit to main menu (no save during combat - combat progress will be lost)

**Combo System**: Chain specific action sequences to unlock powerful combo attacks:
- **Frenzy** (Attack → Attack → Attack): Triple hit dealing ~1.5x total damage
- **Revenge** (Defend → Defend → Attack): Counter-attack dealing damage equal to damage taken while defending
- **Arcane Burst** (Cast → Cast → Cast): Empowered spell dealing 2x magic damage

The combat status shows your last actions (e.g., "Last actions: [Attack] → [Defend]"). When a combo pattern is complete, you'll see "COMBO AVAILABLE: Frenzy!" - perform the matching action to trigger the combo. Fleeing clears your action history.

**Targeting:** When facing multiple enemies, you can target specific enemies by name (e.g., `attack goblin` or `cast orc`). Partial, case-insensitive matching is supported. If no target is specified, attacks hit the first living enemy.

**Combat Flow:**
1. You attack, defend, or cast
2. All living enemies attack (unless you fled successfully)
3. Combat continues until all enemies are defeated, you are defeated, or you successfully flee

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
2. Use `shop` to view available items and prices (auto-detects merchant in location)
3. Use `buy <item>` to purchase items (requires sufficient gold)
4. Use `sell <item>` to sell items from your inventory for gold
5. Optionally use `talk <npc>` to chat with a merchant before shopping

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

Enable dynamic world generation with AI using OpenAI, Anthropic, or Ollama (local):

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

**Option 3: Ollama (Local - Free, No API Key)**
1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a model: `ollama pull llama3.2`
3. Start the server: `ollama serve`
4. Create a `.env` file:
   ```bash
   AI_PROVIDER=ollama
   ```

**Multiple providers configured?** Anthropic is used by default. Set `AI_PROVIDER=openai` or `AI_PROVIDER=ollama` to override.

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

### Non-Interactive Mode

For automated testing and AI agent playtesting, use the `--non-interactive` flag to read commands from stdin:

```bash
# Single command
echo "look" | cli-rpg --non-interactive

# Multiple commands
echo -e "look\nstatus\ninventory" | cli-rpg --non-interactive

# From file
cli-rpg --non-interactive < commands.txt

# Reproducible runs with fixed seed
cli-rpg --non-interactive --seed 42 < commands.txt

# With delay between commands (500ms)
cli-rpg --non-interactive --delay 500 < commands.txt

# Skip character creation and use default "Agent" character
cli-rpg --non-interactive --skip-character-creation < commands.txt
```

**Features:**
- Reads commands from stdin line-by-line
- Exits with code 0 when stdin is exhausted (EOF)
- ANSI colors automatically disabled for machine-readable output
- Runs without AI service for deterministic behavior
- `--seed <int>` option for reproducible random outcomes (combat, loot, etc.)
- `--delay <ms>` option for pacing between commands (0-60000ms, default 0)

**Character Creation:**
- By default, reads character creation inputs from stdin (name, stat method, stats, confirmation)
- Use `--skip-character-creation` to use a default character ("Agent") with balanced stats (10/10/10)
- Manual stats: provide name, "1", str, dex, int, "yes" (one per line)
- Random stats: provide name, "2", "yes" (one per line)
- Invalid inputs return error messages and exit with code 1

### Gameplay Logging

For comprehensive session logging, use the `--log-file` option to record all gameplay activity:

```bash
# Log session to file
cli-rpg --non-interactive --log-file session.log < commands.txt

# Combined with JSON mode (log file separate from stdout)
cli-rpg --json --log-file transcript.log < commands.txt

# With delay for observable pacing (useful for demos/recordings)
cli-rpg --json --delay 200 < commands.txt
```

**Log format** (JSON Lines, one entry per line):
```json
{"timestamp": "2025-01-15T12:00:00.000000+00:00", "type": "session_start", "character": "Agent", "location": "Town Square", "theme": "fantasy"}
{"timestamp": "2025-01-15T12:00:01.000000+00:00", "type": "command", "input": "look"}
{"timestamp": "2025-01-15T12:00:01.100000+00:00", "type": "response", "text": "=== Town Square ===\n..."}
{"timestamp": "2025-01-15T12:00:01.100000+00:00", "type": "state", "location": "Town Square", "health": 100, "max_health": 100, "gold": 50, "level": 1}
{"timestamp": "2025-01-15T12:00:02.000000+00:00", "type": "session_end", "reason": "eof"}
```

**Entry types:**
- `session_start` - Session initialization with character, location, and theme
- `command` - Player input commands
- `response` - Game output text
- `state` - Game state snapshots (location, health, gold, level)
- `session_end` - Session termination with reason (eof/quit/death)

### JSON Output Mode

For programmatic consumption and AI agent integration, use the `--json` flag to output structured JSON Lines:

```bash
echo -e "look\ngo north\nstatus" | cli-rpg --json
```

**Output format** (one JSON object per line):
```json
{"type": "state", "location": "Town Square", "health": 150, "max_health": 150, "gold": 0, "level": 1}
{"type": "narrative", "text": "=== Town Square ===\nA bustling town square..."}
{"type": "actions", "exits": ["north", "east"], "npcs": ["Town Merchant"], "commands": ["look", "go", ...]}
```

**Message types:**
- `state` - Current game state (location, health, gold, level)
- `narrative` - Human-readable text (descriptions, action results)
- `actions` - Available exits, NPCs, and valid commands
- `error` - Machine-readable error code + human message
- `combat` - Combat state (enemy name, enemy health, player health)

**Error codes** for programmatic handling:
- `INVALID_DIRECTION` - Moving in invalid direction
- `NOT_IN_SHOP` - Shop command when not at shop
- `ITEM_NOT_FOUND` - Item not in inventory
- `UNKNOWN_COMMAND` - Unrecognized command
- `NOT_IN_COMBAT` - Combat command outside combat
- `IN_CONVERSATION` - Movement blocked by conversation
- `NO_NPC` - Talk command with no NPCs
- `INVENTORY_FULL` - Inventory capacity reached
- `INSUFFICIENT_GOLD` - Can't afford purchase

**Features:**
- Implies non-interactive mode (reads from stdin)
- ANSI colors automatically disabled
- Each line is a valid JSON object
- Suitable for AI agents, testing frameworks, and automation tools

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
├── location_art.py      # Fallback ASCII art for locations
├── npc_art.py           # Fallback ASCII art for NPCs
├── autosave.py          # Automatic game saving
├── dreams.py            # Dream sequences triggered on rest
├── models/              # Data models
│   ├── character.py
│   ├── location.py
│   ├── enemy.py
│   ├── item.py
│   ├── inventory.py
│   ├── npc.py
│   ├── quest.py
│   ├── shop.py
│   └── status_effect.py
└── persistence.py       # Save/load system (character and full game state)
```

## Documentation

- [AI Features Guide](docs/AI_FEATURES.md) - Detailed AI world generation documentation
- [AI Specification](docs/ai_location_generation_spec.md) - Technical specification for AI features

## License

MIT
