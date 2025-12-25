## Active Issues

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

### Shop context persists after switching to non-merchant NPC
**Status**: RESOLVED

**Description**: When a player talked to a Merchant NPC and opened their shop, then talked to a different non-merchant NPC (like a Guard), the shop context from the Merchant remained active. This allowed the player to execute `shop`, `buy`, and `sell` commands while appearing to be in conversation with the non-merchant NPC.

**Fix**: Added `else` clause in `talk` command handler to clear `game_state.current_shop = None` when NPC is not a merchant. Test added: `test_talk_to_non_merchant_clears_shop_context` in `tests/test_shop_commands.py`.

