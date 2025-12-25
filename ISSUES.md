## Active Issues

### AI area generation fails with JSON truncation - NEVER use fallback
**Status**: ACTIVE (CRITICAL)

**Problem**: AI area generation fails with error: `Failed to parse response as JSON: Unterminated string starting at: line 50 column 21 (char 1854)`. When this happens, the code silently falls back to template-based generation, which should NEVER happen.

**Root Causes**:

1. **Insufficient max_tokens**: Default `max_tokens: 500` in `ai_config.py` is too low for area generation (5-7 locations with NPCs can require 1500-2000+ tokens). The LLM response gets truncated mid-JSON.

2. **Silent fallback in game_state.py**: Lines 320-343 catch AI exceptions and fall back to `generate_fallback_location()`. This masks failures instead of surfacing them.

3. **Invalid connections**: Fallback locations add dangling "Unexplored X" connections pointing to non-existent locations, creating inconsistent world state.

**Required Fixes**:

1. **Increase max_tokens**:
   - Change default from 500 to 2000 in `ai_config.py` (line 284)
   - Update docstring (line 270) and env var default (line 406)

2. **Remove silent fallback in game_state.py**:
   - Lines 320-343: When `expand_area` fails, do NOT call `generate_fallback_location`
   - Instead, re-raise the exception or return an error message to the player
   - The player should be informed AI generation failed

3. **Add JSON repair logic in ai_service.py** (optional enhancement):
   - Extract JSON from markdown code blocks (AI sometimes wraps in ```json)
   - Attempt to repair truncated arrays by closing brackets

**Files to modify**:
- `src/cli_rpg/ai_config.py`: Increase max_tokens default
- `src/cli_rpg/game_state.py`: Remove fallback, propagate errors
- `src/cli_rpg/ai_service.py`: Add JSON extraction/repair logic (optional)

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

### Distance-based enemy difficulty scaling
**Status**: RESOLVED

**Description**: Enemies now scale in difficulty based on Manhattan distance from the origin (0,0). The further players travel from the starting area, the more challenging encounters become.

**Implementation**: Enemy stats (HP, attack, defense) and XP rewards scale using the formula `base_stat * (1 + distance * 0.15)`. Distance tiers:
- Near (0-3): Easy encounters (multiplier 1.0-1.45)
- Mid (4-7): Moderate encounters (multiplier 1.6-2.05)
- Far (8-12): Challenging encounters (multiplier 2.2-2.8)
- Deep (13+): Dangerous encounters (multiplier 2.95+)

### Shop context persists after switching to non-merchant NPC
**Status**: RESOLVED

**Description**: When a player talked to a Merchant NPC and opened their shop, then talked to a different non-merchant NPC (like a Guard), the shop context from the Merchant remained active. This allowed the player to execute `shop`, `buy`, and `sell` commands while appearing to be in conversation with the non-merchant NPC.

**Fix**: Added `else` clause in `talk` command handler to clear `game_state.current_shop = None` when NPC is not a merchant. Test added: `test_talk_to_non_merchant_clears_shop_context` in `tests/test_shop_commands.py`.

### Connection system movement bug
**Status**: RESOLVED

**Description**: Players could move in ANY direction, even when no connection/exit existed. The game generated new locations on-the-fly for any direction, completely bypassing the exit system defined in `connections` dict.

**Fix**: Added connection check in `game_state.py` move() function that blocks movement if no connection exists in that direction:
```python
if not current.has_connection(direction):
    return (False, "You can't go that way.")
```
This check occurs before any coordinate-based movement or new location generation, ensuring players can only move in directions with valid exits. Test added: `test_move_blocked_when_no_connection_coordinate_mode` in `tests/test_game_state.py`.

### Dead-end navigation bug [RESOLVED]
**Status**: RESOLVED

**Description**: Players could get stuck in locations with no exits, unable to continue exploring.

**Fix**: Fixed world generation to ensure all locations have at least one valid exit. Commit: 8d7f56f.

