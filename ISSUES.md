## Active Issues

### Non-interactive mode for AI agent playtesting
**Status**: CRITICAL

Enable automated playtesting via AI agents to validate game mechanics, find bugs, and stress-test content generation. The game currently requires interactive terminal input, making automated testing impossible.

**Requirements**:

1. **Non-interactive input mode**
   - Accept commands from stdin pipe, file, or programmatic API
   - Run without blocking on `input()` calls
   - Support command-line flag (e.g., `--non-interactive` or `--batch`)
   - Graceful handling when input stream ends

2. **Structured output for AI parsing**
   - Machine-readable output format (JSON lines or similar)
   - Clear separation of game state, narrative text, and available actions
   - Emit current valid commands after each action
   - Error messages with codes, not just human text

3. **Comprehensive gameplay logging**
   - Full session transcript with timestamps
   - Log file output (e.g., `--log-file gameplay.log`)
   - Record: commands issued, game responses, state changes, errors
   - Include RNG seeds for reproducibility
   - Log AI-generated content for review

4. **Session state export**
   - Dump full game state as JSON on demand or at intervals
   - Include: player stats, inventory, location, quest progress, world state
   - Enable session replay from logged state

5. **Automation-friendly features**
   - Configurable delays/timeouts
   - Deterministic mode option (fixed RNG seed)
   - Headless operation (no ANSI colors/formatting when piped)
   - Exit codes reflecting game outcomes

**Use cases**:
- AI agent explores the world and reports issues
- Automated regression testing of game mechanics
- Stress testing AI content generation
- Fuzzing command parser for edge cases
- Generating gameplay datasets for analysis

**Implementation notes**:
- Detect `sys.stdin.isatty()` for automatic mode switching
- Consider separate `GameSession` class wrapping `GameState` for programmatic use
- Logging should use Python's `logging` module with configurable levels

### More content
**Status**: ACTIVE

~~Multiple NPCs per location~~ (DONE - locations support multiple NPCs with improved talk command UX), multiple enemies for fights, boss fights

### More content 2
**Status**: ACTIVE

Users requesting ASCII art for things like locations, npcs, monsters in fights and similar

### Meaningful choices and consequences
**Status**: ACTIVE

Player decisions should have lasting impact on the world and story. Currently, choices feel inconsequential.

**Desired features**:
- Dialogue choices that affect NPC relationships and quest outcomes
- Moral dilemmas with no clear "right" answer
- Branching quest paths based on player decisions
- World state changes based on completed quests (e.g., saving a village makes it thrive, ignoring it leads to ruin)
- NPCs remembering past interactions and reacting accordingly

### Character skill and ability system
**Status**: ACTIVE

Combat lacks tactical depth - players just attack repeatedly. Need a skill/ability system.

**Desired features**:
- Learnable skills and abilities (e.g., Power Strike, Fireball, Heal, Stealth)
- Skill trees or progression paths for different playstyles (warrior, mage, rogue)
- Resource management (mana, stamina, cooldowns)
- Passive abilities that modify gameplay
- Skill synergies and combos

### Status effects and combat depth
**Status**: ACTIVE

Combat is too simple - attack until enemy dies.

**Desired features**:
- Status effects: poison, burn, freeze, stun, bleed, buff/debuff
- Elemental strengths and weaknesses
- Defensive options: block, dodge, parry
- Enemy attack patterns and telegraphed special moves
- Critical hits and miss chances based on stats
- Combat stances or modes

### Dynamic world events
**Status**: ACTIVE

The world feels static. Need ambient events and world dynamics.

**Desired features**:
- Random encounters while traveling (bandits, merchants, wandering creatures)
- Weather system affecting gameplay (storms reduce visibility, rain extinguishes fire)
- Day/night cycle with different encounters and NPC availability
- Seasonal events and festivals
- World events triggered by player progress or time (invasions, plagues, celebrations)

### Reputation and faction system
**Status**: ACTIVE

NPCs and towns should react to player's reputation and allegiances.

**Desired features**:
- Reputation levels with different factions (guilds, towns, races)
- Actions affect reputation (helping vs. harming, quest choices)
- Reputation unlocks or blocks content (shops, quests, areas)
- Faction conflicts where siding with one alienates another
- Titles and recognition based on achievements

### Crafting and gathering system
**Status**: ACTIVE

Players should be able to create items, not just buy/find them.

**Desired features**:
- Gatherable resources in locations (herbs, ore, wood)
- Crafting recipes for weapons, armor, potions, and tools
- Crafting skill progression
- Rare recipes as quest rewards or discoveries
- Item enhancement/enchanting system

### Secrets and discovery
**Status**: ACTIVE

Exploration should reward curiosity with hidden content.

**Desired features**:
- Hidden rooms and secret passages (require specific actions to find)
- Lore fragments and collectible journal entries
- Easter eggs and rare encounters
- Riddles and puzzles guarding treasure
- Environmental storytelling (discover what happened through clues)
- Achievements for thorough exploration

### Companion system
**Status**: ACTIVE

Adventuring alone limits roleplay possibilities.

**Desired features**:
- Recruitable NPC companions with personalities
- Companion dialogue and banter during travel
- Companion abilities in combat
- Relationship building with companions
- Companion-specific quests and storylines
- Companions reacting to player choices

### Immersive text presentation
**Status**: ACTIVE

Text output could be more atmospheric and engaging.

**Desired features**:
- Typewriter-style text reveal for dramatic moments
- Color-coding for different types of information (damage, healing, dialogue, narration)
- Sound effects via terminal bell for important events
- Pause and pacing for dramatic tension
- Stylized borders and frames for different UI elements

### Procedural quest generation
**Status**: ACTIVE

Quests should be dynamically generated to keep gameplay fresh.

**Desired features**:
- AI-generated side quests based on current location and world state
- Quest templates with procedural elements (targets, rewards, locations)
- Scaling difficulty based on player level
- Quest chains that build on each other
- Emergent storylines from completed quests

## Resolved Issues

### Invalid "up"/"down" directions shown as movement options
**Status**: RESOLVED

**Description**: The game displayed "up" and "down" as possible movement directions, but the world uses a 2D grid where only cardinal directions (north, south, east, west) make sense. This caused player confusion and potential stuck states where only vertical exits existed.

**Fix**: Removed vertical directions from the 2D world grid:
1. Removed "up" and "down" from `VALID_DIRECTIONS` in `models/location.py`
2. Removed "up" and "down" from `OPPOSITE_DIRECTIONS` in `world_grid.py`
3. Updated AI prompt in `ai_config.py` to only generate cardinal directions

Players using "up" or "down" as a direction now receive an "Invalid direction" error. The AI no longer suggests vertical connections in generated locations.

### Misleading error message when trying to equip an already-equipped item
**Status**: RESOLVED

**Description**: When a user tried to run `equip <item>` on an item that was already equipped, the error message shown was "You don't have '<item>' in your inventory." This was misleading because the item was visible in the inventory display (shown with "[Weapon]" or "[Armor]" prefix).

**Fix**: Added a check in the `equip` command handler to detect if the item is already equipped as weapon or armor before returning the generic "not found" error. The new message clearly indicates the item is already equipped: "{Item Name} is already equipped."

This follows the same pattern as the `use` command fix for equipped items.

### Misleading error message when trying to 'use' an equipped item
**Status**: RESOLVED

**Description**: When a user tried to use the `use` command on an item that was currently equipped (e.g., `use Steel Spear` when Steel Spear was equipped as their weapon), the game showed the error message "You don't have 'steel spear' in your inventory." This was misleading because the user had the item - it was equipped, not missing.

**Fix**: Updated both exploration and combat `use` command handlers to check if the target item is currently equipped before returning the "not found" error. The new messages clearly indicate why the item cannot be used:
- "{Item Name} is currently equipped as your weapon and cannot be used."
- "{Item Name} is currently equipped as your armor and cannot be used."

This matches the pattern already used by `sell` and `drop` commands in the codebase.

### Unclear error message when trying to equip non-equippable items
**Status**: RESOLVED

**Description**: When a user tries to equip a consumable item (like "Life Draught" or "Healing Elixir"), the error message was simply "You can't equip Life Draught." This message didn't explain *why* the item couldn't be equipped.

**Fix**: Enhanced error messages to be more helpful:
- For consumables: "You can only equip weapons or armor. Use 'use <item>' for consumables."
- For misc items: "You can only equip weapons or armor."

This is now consistent with other helpful error messages in the game.

### TALK quest objective type
**Status**: RESOLVED

**Description**: The quest system now tracks when players talk to NPCs for TALK quest objectives.

**Fix**: Added `record_talk(npc_name)` method to `Character` class and integrated it into the `talk` command handler in `main.py`. Quest progress updates automatically when talking to target NPCs. Case-insensitive matching is supported, consistent with other quest types.

### EXPLORE quest objective type
**Status**: RESOLVED

**Description**: The EXPLORE quest objective type now tracks when players visit locations.

**Fix**: Added `record_explore(location_name)` method to `Character` class and integrated it into `GameState.move()`. Quest progress updates automatically when visiting target locations. Case-insensitive matching is supported.

### Combat quit confirmation prompt doesn't consume y/n input
**Status**: RESOLVED

**Root Cause**: The quit confirmation prompt was working correctly, but there were two issues affecting user experience:
1. Stdout buffering could cause the prompt to not display immediately before the blocking `input()` call
2. No feedback was provided when the user chose 'n' to cancel the quit

**Fix**: Added `sys.stdout.flush()` before the input() call to ensure the prompt is visible, and added a "Continuing combat..." message when the user cancels the quit action. The confirmation prompt now properly consumes the y/n input and provides clear feedback.

### `complete` command not recognized
**Status**: RESOLVED

**Root Cause**: The `complete` command was missing from the `known_commands` set in `game_state.py`'s `parse_command()` function. While the command handler existed in `main.py`, the parser was returning `("unknown", [])` because it didn't recognize `complete` as a valid command.

**Fix**: Added `"complete"` to the `known_commands` set in `game_state.py` (line 67). All 27 quest-related tests now pass, including 6 tests specifically for the `complete` command.

### AI-generated content expansion
**Status**: RESOLVED

All AI-generated content features have been implemented:
- ✅ NPC conversations (AI-generated dialogue that persists to NPC greetings)
- ✅ Monsters/enemies (AI-generated with descriptions and attack flavor text)
- ✅ Item catalogue (weapons, armor, consumables) - `AIService.generate_item()` method
- ✅ Lore and world history - `AIService.generate_lore()` method

### Map misaligned and confusing
**Status**: RESOLVED

The map alignment issue with colored markers has been fixed. The player's `@` marker now aligns correctly with column headers and other location markers. Additionally, available exits are now displayed below the map legend (e.g., "Exits: east, north").

### Better Map
**Status**: RESOLVED

Enhanced the map renderer with:
- Expanded 9x9 viewport (sees 4 tiles in each direction instead of 2)
- Decorative box-drawing border using Unicode characters
- Category-based location markers with emoji icons (🏠 town, 🏪 shop, ⚔ dungeon, 🌲 forest, etc.)
- Vertical legend format for better readability
- Increased cell width to accommodate emoji markers


