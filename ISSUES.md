## Active Issues

### Non-interactive mode enhancements
**Status**: ACTIVE

The basic `--non-interactive` mode has been implemented. The following enhancements would improve automated playtesting further:

1. ~~**Structured output for AI parsing**~~ (DONE - see "JSON output mode" in Resolved Issues)

2. ~~**Comprehensive gameplay logging**~~ (DONE - `--log-file` option implemented)
   - ~~Full session transcript with timestamps~~
   - ~~Log file output (e.g., `--log-file gameplay.log`)~~
   - ~~Record: commands issued, game responses, state changes~~
   - Future: Include RNG seeds for reproducibility
   - Future: Log AI-generated content for review

3. ~~**Session state export**~~ (DONE - `dump-state` command implemented)
   - ~~Dump full game state as JSON on demand or at intervals~~
   - ~~Include: player stats, inventory, location, quest progress, world state~~
   - Future: Enable session replay from logged state

4. ~~**Additional automation features**~~ (DONE)
   - ~~Configurable delays/timeouts~~ (DONE - `--delay` option implemented)
   - ~~Deterministic mode option (fixed RNG seed)~~ (DONE - `--seed` option implemented)

### Long-running AI simulation test suite
**Status**: ACTIVE

Once non-interactive mode is fully implemented, set up periodic long-running simulations to catch bugs and evaluate gameplay quality.

**Goals**:
- Discover edge cases and crashes through extended play
- Evaluate AI-generated content quality over time
- Catch gameplay dead-ends or stuck states
- Measure game balance (combat difficulty, economy, progression)
- Build regression test corpus from successful runs

**Implementation**:

1. **AI agent player**
   - Script or agent that plays the game autonomously
   - Makes contextual decisions (explore, fight, shop, quest)
   - Varies playstyles (aggressive, cautious, completionist)

2. **Scheduled runs**
   - CI/cron job running simulations periodically (nightly, weekly)
   - Multiple concurrent sessions with different seeds
   - Configurable session length (commands, time, or milestones)

3. **Reporting and analysis**
   - Aggregate logs from simulation runs
   - Flag anomalies: crashes, infinite loops, stuck states, empty responses
   - Track metrics: locations visited, quests completed, deaths, gold earned
   - Generate summary reports for review

4. **Reproducibility**
   - Save RNG seeds and full command logs
   - Replay failed sessions to debug issues
   - Snapshot game state at intervals for analysis

**Depends on**: Non-interactive mode enhancements (structured output, logging)

### World not truly infinite and NPC persistence issues
**Status**: ACTIVE

Players report the world can be fully explored despite being advertised as infinite. Additionally, NPCs only appear in the starting location.

**Issues**:

1. **World stops expanding**
   - Players can explore all locations and hit a boundary
   - No new locations generate when moving to unexplored exits
   - World feels small and finite rather than infinite

2. **NPCs only in starting location**
   - New locations are generated without NPCs
   - Only the initial "Town Square" or starting area has NPCs
   - Makes exploration feel empty and pointless

3. **NPCs don't persist in locations**
   - NPCs should be permanent fixtures of their locations
   - Revisiting a location should show the same NPCs
   - Exception: special quest NPCs may move or disappear after quest completion

**Expected behavior**:
- Every unexplored exit should generate a new location on demand
- AI-generated locations should include contextually appropriate NPCs (merchants in towns, guards in dungeons, hermits in wilderness)
- NPCs should persist in their locations across visits and save/load
- World should truly be infinite - always have at least one unexplored direction available

**Fix areas**:
- `world.py` / `world_grid.py`: Ensure location generation triggers on unexplored exits
- `ai_service.py`: Include NPC generation in location creation prompts
- `persistence.py`: Verify NPC data is saved/loaded with locations

### Blocked location markers on map
**Status**: ACTIVE

Map lacks visual feedback for inaccessible areas.

**Issues**:

1. **No indication of blocked/inaccessible locations**
   - Players can't see which adjacent cells are impassable
   - Should mark cells with no valid path (walls, barriers, unexplorable)

**Fix**:
- Add distinct marker for blocked/wall cells (e.g., `█` or `#`)
- Consider using ASCII fallback markers (D for dungeon, T for town, etc.) with a `--ascii` flag

### More content
**Status**: ACTIVE

~~Multiple NPCs per location~~ (DONE - locations support multiple NPCs with improved talk command UX), ~~multiple enemies for fights~~ (DONE - combat now spawns 1-3 enemies with target-based attacks), boss fights

### More content 2
**Status**: ACTIVE

Users requesting ASCII art for things like ~~locations~~ (DONE - locations now display ASCII art when entering or looking, with AI-generated or fallback template art) and NPCs. ~~Monsters in combat~~ (DONE - enemies now display ASCII art when combat starts, with AI-generated or fallback template art)

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

### Map emoji alignment
**Status**: RESOLVED

**Description**: Emoji markers (🏠, ⚔, 🌲, etc.) in the map display were causing column misalignment because they have display width 2 but Python's string formatting treated them as width 1.

**Fix**: Used the `wcwidth` library to calculate actual display widths and pad markers correctly. Added `pad_marker()` helper function in `map_renderer.py` that:
- Calculates actual display width using `wcswidth()`
- Adds appropriate left-padding to achieve target visual width (4 columns per cell)
- Each cell now displays correctly regardless of marker type (ASCII or emoji)

The `wcwidth>=0.2.0` dependency was added to `pyproject.toml`.

### Tab auto-completion
**Status**: RESOLVED

**Description**: Added tab auto-completion for commands and contextual arguments using readline integration.

**Features implemented**:
- Command name completion: `ta<tab>` → `talk`
- Contextual argument completion based on game state:
  - `go <tab>` → shows available exit directions from current location
  - `talk <tab>` → shows NPCs at current location
  - `equip <tab>` → shows only WEAPON/ARMOR items in inventory
  - `use <tab>` → shows only CONSUMABLE items in inventory
  - `buy <tab>` → shows shop items (when in shop)
- Cycle through multiple matches with repeated tab
- Graceful fallback if readline unavailable (Windows without pyreadline3)

**Implementation**: New `completer.py` module with `CommandCompleter` class integrated into `input_handler.py`.

### Command history with arrow keys
**Status**: RESOLVED

**Description**: Added readline integration for command history navigation using up/down arrow keys.

**Features implemented**:
- Up arrow scrolls back through previous commands
- Down arrow scrolls forward through history
- History persists across sessions (saved to `~/.cli_rpg_history`)
- Configurable history size (500 commands)
- Fallback to basic input if readline unavailable (e.g., Windows without pyreadline3)
- Input editing with left/right arrow, backspace, delete, home/end keys

**Implementation**: New `input_handler.py` module with `init_readline()` and `get_input()` functions.

### Ultra-short movement commands
**Status**: RESOLVED

**Description**: Navigation was too verbose. Players wanted quick movement shortcuts.

**Fix**: Added ultra-short movement shortcuts to `parse_command()` in `game_state.py`:
- `n`, `gn` → go north
- `w`, `gw` → go west
- `gs` → go south
- `ge` → go east

Note: `s` remains mapped to `status` and `e` remains mapped to `equip` to avoid conflicts with existing commands.

### Dead-end navigation bug [RESOLVED]
**Status**: RESOLVED

**Description**: Players could encounter locations with no valid exits, becoming permanently stuck with no way to continue the game.

**Fix**: Fixed in commit 8d7f56f by ensuring AI-generated locations always include at least one valid exit connection. Additional safeguards were added in fa915b9 to prevent dead-ends in initial world generation.

### Non-interactive mode for AI agent playtesting (basic)
**Status**: RESOLVED

**Description**: Implemented basic non-interactive mode to enable automated playtesting via stdin.

**Features implemented**:
- `--non-interactive` CLI flag
- Reads commands from stdin line-by-line
- Graceful exit (code 0) when stdin is exhausted (EOF)
- ANSI colors automatically disabled for machine-readable output
- Creates default character ("Agent") with balanced stats (10/10/10)
- No AI service (deterministic behavior)

**Usage**:
```bash
# Single command
echo "look" | cli-rpg --non-interactive

# Multiple commands
echo -e "look\nstatus\ninventory" | cli-rpg --non-interactive

# From file
cli-rpg --non-interactive < commands.txt
```

See "Non-interactive mode enhancements" in Active Issues for future improvements.

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

### JSON output mode for structured AI parsing
**Status**: RESOLVED

**Description**: Added a `--json` flag for machine-readable output, enabling AI agents and automation tools to parse game output.

**Features implemented**:
- `--json` CLI flag (implies `--non-interactive`)
- JSON Lines output format (one JSON object per line)
- Message types: `state`, `narrative`, `actions`, `error`, `combat`
- Structured error codes for programmatic handling (e.g., `INVALID_DIRECTION`, `UNKNOWN_COMMAND`)
- ANSI colors automatically disabled for clean output

**Usage**:
```bash
echo -e "look\ngo north\nstatus" | cli-rpg --json
```

**Output example**:
```json
{"type": "state", "location": "Town Square", "health": 150, "max_health": 150, "gold": 0, "level": 1}
{"type": "narrative", "text": "=== Town Square ===\nA bustling town square..."}
{"type": "actions", "exits": ["north", "east"], "npcs": ["Town Merchant"], "commands": ["look", "go", ...]}
```


