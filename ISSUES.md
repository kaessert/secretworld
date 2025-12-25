## Active Issues

### Shop context persists after switching to non-merchant NPC
**Status**: ACTIVE

**Description**: When a player talks to a Merchant NPC and opens their shop, then talks to a different non-merchant NPC (like a Guard), the shop context from the Merchant remains active. This allows the player to execute `shop`, `buy`, and `sell` commands while appearing to be in conversation with the non-merchant NPC.

**Steps to reproduce**:
1. Go to Town Square (or any location with a Merchant and another NPC)
2. `talk Merchant` - opens shop dialogue
3. `shop` - shows Merchant's items (working correctly)
4. `talk Guard` - switches to Guard conversation
5. `shop` - still shows Merchant's items (BUG)
6. `buy <item>` - attempts to purchase from Merchant (BUG)

**Expected behavior**:
- After `talk Guard`, the shop context should be cleared
- `shop` command should return "You're not at a shop. Talk to a merchant first."
- `buy` command should return "You're not at a shop. Talk to a merchant first."

**Actual behavior**:
- Shop context remains active from the previous Merchant interaction
- `shop` shows the Merchant's inventory despite talking to Guard
- `buy` attempts the purchase (only fails if insufficient gold)

**User impact**: Confusing UX where users may not realize they're still transacting with the Merchant while the dialogue suggests they're talking to a different NPC.

**Suggested fix**: Clear the shop context (`current_shop`) when starting a conversation with a non-merchant NPC in the `talk` command handler.

### Constrained movement with guaranteed exploration frontier
**Status**: ACTIVE

Players should NOT be able to move in any direction - only specific exits should exist. However, the world must always have at least one unexplored exit to ensure infinite exploration.

**Current problem**:
- All 4 cardinal directions are always open (or should be)
- Makes the world feel like an open grid rather than a structured map
- No sense of geography, corridors, or natural barriers

**Desired behavior**:

1. **Limited exits per location**
   - Each location has 1-4 exits, not always all 4
   - AI generates appropriate connections based on location type
   - Dungeons: corridors, not open plazas
   - Forests: winding paths, not open grids
   - Mountains: limited passable routes

2. **Guaranteed exploration frontier**
   - World must always have at least one unexplored exit somewhere
   - When generating new locations, ensure at least one exit leads to unexplored territory
   - "Dead ends" are OK for individual locations, but world as a whole must remain explorable

3. **Blocked directions**
   - Invalid directions return "You can't go that way" (not generate new area)
   - Map shows blocked adjacent cells (already implemented with `█`)
   - Creates natural boundaries and structure

**Implementation**:
- Track "frontier exits" globally (exits that lead to unexplored locations)
- When generating a location, if it would close all frontiers, force an additional unexplored exit
- AI prompt should specify that not all directions need exits

### Distance-based enemy difficulty scaling
**Status**: ACTIVE

Enemies should get harder the further the player explores from the starting location.

**Current problem**:
- Enemy difficulty is flat or only based on player level
- No incentive to stay near town early game
- No sense of danger when venturing into the unknown

**Desired behavior**:

1. **Distance-based scaling**
   - Calculate distance from starting location (Manhattan or path distance)
   - Enemy stats scale with distance: HP, damage, defense
   - Enemies at distance 10+ should be significantly harder than starting area

2. **Zone difficulty tiers**
   - Near spawn (0-3): Easy enemies, safe for new players
   - Mid-range (4-7): Moderate difficulty, appropriate for leveled players
   - Far reaches (8-12): Challenging encounters
   - Deep wilderness (13+): Dangerous, high-risk high-reward

3. **Rewards scale with difficulty**
   - Harder enemies drop more gold
   - Better loot tables at higher distances
   - More XP from distant encounters

4. **Visual/narrative hints**
   - Location descriptions hint at danger level
   - "The air grows thick with menace" as player ventures far
   - NPCs warn about dangerous regions

**Implementation**:
- Store origin coordinates (0,0) as reference point
- Pass distance to enemy generation in `ai_service.py`
- Scale enemy stats: `base_stat * (1 + distance * 0.15)` or similar
- Update AI prompts to generate appropriately threatening enemies

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

### Overworld map with cities and sub-locations
**Status**: ACTIVE

Players want a more sophisticated map system with hierarchical locations - an overworld containing cities, dungeons, and other points of interest that can be entered to explore sub-locations.

**Desired structure**:

1. **Overworld layer**
   - Large-scale map showing major landmarks (cities, forests, mountains, dungeons)
   - Travel between landmarks (possibly with travel time or random encounters)
   - Each landmark is an entry point to a sub-location

2. **Sub-location layer**
   - Cities contain: market district, tavern, castle, slums, etc.
   - Dungeons contain: multiple floors/rooms to explore
   - Forests contain: clearings, caves, ruins
   - Each sub-location has its own local map

3. **Navigation**
   - `enter <location>` to go into a city/dungeon
   - `exit` or `leave` to return to overworld
   - Local movement within sub-locations (current n/s/e/w system)
   - Fast travel between discovered overworld locations

4. **Map display**
   - Overworld map showing discovered landmarks
   - Local map when inside a sub-location
   - `map` command shows current layer, `worldmap` shows overworld

**Benefits**:
- More organized world structure
- Logical grouping of related areas
- Clearer sense of scale and progression
- Natural quest hubs (cities) vs adventure zones (dungeons/wilderness)

### Unique AI-generated ASCII art per entity
**Status**: ACTIVE

ASCII art should be unique and AI-generated for each distinct monster type, NPC, and location - not reused templates.

**Current problem**:
- Fallback template art is used when AI generation fails
- Same monster type (e.g., "Goblin") may get different art each encounter
- Art is not persisted, regenerated each time

**Requirements**:

1. **Unique per entity type**
   - Each monster kind gets ONE consistent ASCII art (all Goblins look the same)
   - Each NPC gets unique art matching their description
   - Each location gets unique art matching its theme

2. **AI-generated, not templates**
   - All art should be AI-generated based on entity name/description
   - Fallback templates only as last resort (API failure)
   - Art should reflect entity characteristics (menacing monsters, friendly merchants, etc.)

3. **Persistence**
   - Generated art stored with entity data
   - Art saved/loaded with game state
   - Monster art stored in a bestiary/cache by monster name
   - NPC art stored with NPC data in location

4. **Art cache/bestiary**
   - Global cache of monster art by monster name
   - First encounter generates and caches art
   - Subsequent encounters reuse cached art
   - `bestiary` command to view discovered monster art?

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

### World not truly infinite
**Status**: RESOLVED

**Description**: Players could fully explore the world and hit boundaries despite it being advertised as infinite. Moving in a valid cardinal direction without an existing connection returned "You can't go that way" instead of generating new locations.

**Fix**:
1. Added `generate_fallback_location()` in `world.py` with 5 fallback location templates (wilderness, rocky, misty, grassy, dense thicket) for when AI is unavailable
2. Updated `move()` in `game_state.py` to remove the exit-required check for coordinate-based movement
3. Movement in any valid cardinal direction now always succeeds - either moves to an existing location or generates a new one (AI if available, fallback templates otherwise)
4. Generated locations always include a back connection to the source and 1-2 frontier exits for future expansion

The world is now truly infinite - players can explore in any cardinal direction indefinitely.

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

### ASCII art for entities
**Status**: RESOLVED

Users requesting ASCII art for things like locations, NPCs, and monsters in combat.

**Implementation**:
- **Locations**: Display ASCII art when entering or looking (3-10 lines, max 50 chars wide). AI-generated via `generate_location_ascii_art()` with fallback templates in `location_art.py`
- **NPCs**: Display ASCII art when talking to them (5-7 lines, max 40 chars wide). AI-generated via `generate_npc_ascii_art()` with fallback templates in `npc_art.py`
- **Enemies**: Display ASCII art when combat starts (5-7 lines, max 40 chars wide). AI-generated via `generate_ascii_art()` with fallback templates by category

All ASCII art is persisted with entity data and survives save/load cycles.

### Blocked location markers on map
**Status**: RESOLVED

**Description**: Map lacked visual feedback for inaccessible/blocked areas adjacent to explored locations.

**Fix**: Added visual markers (`█`) for blocked/impassable cells in the map display:
- Cells adjacent to explored locations that have no connection (walls/barriers) now display `█`
- Added `BLOCKED_MARKER = "█"` constant and `DIRECTION_DELTAS` dictionary to `map_renderer.py`
- Legend updated to include `█ = Blocked/Wall`
- Uses width-aware padding via `pad_marker()` for proper alignment

Players can now see which adjacent cells are impassable, improving map readability and navigation.

### NPC persistence issues
**Status**: RESOLVED

**Description**: NPCs were suspected of not persisting when saving/loading game state.

**Investigation**: Code review confirmed that NPC persistence was already correctly implemented:
- `Location.to_dict()` serializes NPCs: `"npcs": [npc.to_dict() for npc in self.npcs]`
- `Location.from_dict()` deserializes NPCs: `npcs = [NPC.from_dict(npc_data) for npc_data in data.get("npcs", [])]`
- `NPC.to_dict()/from_dict()` handle all fields including `conversation_history`, `shop`, and `offered_quests`

**Fix**: Added explicit test `test_load_game_state_preserves_npcs` in `tests/test_persistence_game_state.py` to verify NPC persistence through save/load cycles, confirming all NPC fields are preserved.

### More content
**Status**: RESOLVED

All "more content" features have been implemented:
- ~~Multiple NPCs per location~~ (DONE - locations support multiple NPCs with improved talk command UX)
- ~~Multiple enemies for fights~~ (DONE - combat now spawns 1-3 enemies with target-based attacks)
- ~~Boss fights~~ (DONE - bosses spawn with 2x stats, 4x XP, guaranteed legendary loot drops, unique ASCII art)

### AI generation failure exposes raw errors to player
**Status**: RESOLVED

**Description**: When AI location generation failed (JSON parse errors, API failures, etc.), raw technical errors like "Failed to parse response as JSON: Expecting value: line 52 column 19" were exposed to players, breaking immersion.

**Fix**: Implemented graceful fallback handling in the `move()` method in `game_state.py`:
1. Catches all AI errors silently and falls back to `generate_fallback_location()`
2. Shows friendly "The path is blocked by an impassable barrier." message when even fallback fails
3. Errors are logged at warning level for debugging without being exposed to players
4. Added 5 new tests in `tests/test_ai_failure_fallback.py` to verify graceful fallback behavior

### `quit` command crashes in non-interactive mode
**Status**: RESOLVED

**Description**: When using the `quit` command in non-interactive mode (`--non-interactive` or `--json`), the game crashed with an `EOFError` because it attempted to prompt the user "Save before quitting? (y/n):" using `input()`, but stdin was already exhausted.

**Fix**: Updated `handle_exploration_command()` and `handle_combat_command()` in `main.py` to accept a `non_interactive` parameter. When `non_interactive=True`, quit handlers now return immediately with `(False, "\nExiting game...")` without calling `input()`. This prevents the `EOFError` crash while maintaining clean exit behavior.

Both `run_non_interactive()` and `run_json_mode()` now pass `non_interactive=True` to the command handlers. Added tests in `tests/test_non_interactive.py` to verify quit exits cleanly in both modes.
