## Active Issues

### VISION: Transformative Features for a Mesmerizing Experience
**Status**: ACTIVE (VISION)

These features would elevate the game from "good CLI RPG" to "unforgettable experience":

---

#### 1. THE WHISPER SYSTEM - Ambient Narrative Layer
**Impact**: Creates atmosphere and wonder
**Status**: MVP IMPLEMENTED

The world *speaks* to observant players through subtle environmental cues:

```
You enter the Forgotten Chapel...

    ╔═══════════════════════════════════╗
    ║  The candles flicker as you enter ║
    ║  ...almost as if greeting you     ║
    ╚═══════════════════════════════════╝

[Whisper]: "The stones here remember a prayer never finished..."
```

**MVP Implemented**:
- ✅ **Ambient whispers** appear randomly (30% chance) when entering locations
- ✅ **Category-based whispers**: Themed text based on location type (town, dungeon, wilderness, ruins, cave, forest)
- ✅ **Player-specific**: Whispers reference player history (high gold, high level, low health, many kills)
- ✅ No whispers during combat

**Future Enhancements**:
- **Hidden lore fragments** revealed to players who `look` multiple times or `wait`
- **Foreshadowing**: Whispers hint at dangers ahead, secrets nearby, or story beats
- **AI-generated whispers**: Dynamic whisper content via AI service (stub implemented)

---

#### 2. ECHO CHOICES - Decisions That Haunt You
**Impact**: Emotional weight, replayability
**Status**: MVP IMPLEMENTED

Every significant choice creates an "echo" that reverberates through the game:

```
The wounded bandit begs for mercy...

  [1] Spare him     - "Perhaps redemption exists for all"
  [2] Execute him   - "Justice must be swift"
  [3] Recruit him   - "Every sword has its use"

Your choice will echo...
```

**MVP Implemented**:
- ✅ **Reputation tracking**: Player choices (like fleeing combat) are tracked in `game_state.choices`
- ✅ **NPC reputation awareness**: NPCs reference player's "cautious" reputation if they've fled 3+ times
- ✅ Reputation-aware greetings with 3 variants for "cautious" players

**Future Enhancements**:
- Spare the bandit → He becomes an informant, or betrays you later, or saves you in Act 3
- A town you helped prospers; one you ignored falls to ruin (visible on return)
- NPCs reference your reputation: "You're the one who burned the witch... or was it saved her?"
- **Companion memories**: "I still remember what you did in Thornwood. I've never forgotten."

---

#### 3. THE DARKNESS METER - Psychological Horror Element
**Impact**: Tension, resource management, atmosphere

Exploring dangerous areas builds **Dread**:

```
═══════════════════════════════════════
  DREAD: ████████░░░░░░░░ 53%

  The shadows seem to lean toward you...
  You hear footsteps that aren't your own.
═══════════════════════════════════════
```

- **Dread builds** in dark places, after combat, when alone, at night
- **High dread effects**: Hallucinations (fake enemies), paranoid whispers, stat penalties
- **At 100%**: Something terrible happens (shadow creature attack, madness event)
- **Reduce dread**: Rest at campfires, talk to companions, visit towns, use light sources
- **Brave players rewarded**: High-dread areas contain the best secrets

---

#### 4. LIVING WORLD EVENTS - The World Moves Without You
**Impact**: Immersion, urgency, emergent stories

The world has a heartbeat. Events happen whether you're there or not:

```
╔════════════════════════════════════════════╗
║  WORLD EVENT: The Crimson Plague spreads   ║
║                                            ║
║  Millbrook Village is infected.            ║
║  Estimated time until collapse: 3 days     ║
║                                            ║
║  [Rumor]: An herbalist in Shadowfen knows  ║
║           of a cure...                     ║
╚════════════════════════════════════════════╝
```

- **Spreading events**: Plagues, wars, monster migrations, seasons changing
- **Timed quests**: Some opportunities expire ("The caravan leaves at dawn")
- **Consequences of inaction**: Towns can fall, NPCs can die, regions can become corrupted
- **Cascading effects**: Saved village → thriving trade → better shop inventory
- **Rival adventurers**: NPCs who complete quests you ignore, becoming allies or enemies

---

#### 5. DREAM SEQUENCES - Surreal Narrative Moments
**Impact**: Storytelling, foreshadowing, emotional depth

When you rest, sometimes you dream:

```
You drift into an uneasy sleep...

    ═══════════════════════════════════

    You stand in a field of white flowers.
    A child's voice asks: "Why did you
    choose the sword over the words?"

    A mountain crumbles in the distance.
    You recognize it as a place you've
    never been...

    ═══════════════════════════════════

You wake with a strange sense of purpose.
[Gained insight: "The Mountain's Secret"]
```

- **Prophetic dreams** hint at future locations, enemies, or choices
- **Memory dreams** replay key moments with new perspective
- **Character dreams** reveal companion backstories
- **Nightmare sequences** if Dread is high (interactive horror)
- **Dream items** that manifest in reality

---

#### 6. COMBO COMBAT SYSTEM - Fluid, Strategic Fighting
**Impact**: Combat depth, mastery satisfaction

Chain attacks for devastating effects:

```
Combat Round 3:

  Your last 2 actions: [ATTACK] → [DEFEND]

  COMBO AVAILABLE: "Counter Strike"
    → On next attack, deal 2x damage if enemy attacked you

  What will you do?
  > [A]ttack (triggers Counter Strike!)
  > [D]efend (breaks combo)
  > [C]ast   (chains to "Arcane Counter")
```

- **Combo chains**: Attack→Attack→Attack = "Frenzy" (3x hit, exhausted next turn)
- **Defensive combos**: Defend→Defend→Attack = "Revenge" (damage = damage taken)
- **Magic weaving**: Cast→Cast→Cast = "Arcane Storm" (hits all enemies)
- **Hybrid moves**: Defend→Cast→Attack = "Calculated Strike" (guaranteed crit)
- **Enemy patterns**: Bosses telegraph moves, allowing counter-play

---

#### 7. THE BOND SYSTEM - Companions Who Matter
**Impact**: Emotional investment, tactical depth

Companions aren't just stat bonuses—they're people:

```
KIRA THE SCOUT
  ════════════════════════════════════
  Bond Level: ████████░░ Trusted

  "I've been watching you. You fight like
   someone who's lost things. I know that
   feeling."

  [Memory]: She opened up about her sister
  [Memory]: You chose mercy when she wanted blood
  [Memory]: She saved you in the Shadow Caves
  ════════════════════════════════════

  Bond Ability: "Flanking Strike" (unlocked at Trust)
  Next unlock at "Devoted": "Last Stand"
```

- **Bond levels** through choices, gifts, and shared experiences
- **Companion quests** that explore their past and resolve their arc
- **Combat synergies** unlock at higher bond levels
- **Companions react** to your choices (approval/disapproval affects bond)
- **Permadeath option**: Companions can die, with devastating consequences
- **Betrayal possibility**: Wrong choices can turn companions against you

---

#### 8. ENVIRONMENTAL STORYTELLING - The World as Narrator
**Impact**: Discovery, atmosphere, lore depth
**Status**: MVP IMPLEMENTED

Locations tell stories through details:

```
You enter the Abandoned Manor...

Upon closer inspection, you notice:
  - Claw marks on the walls, going upward
  - A child's toy near the cold fireplace
  - A journal, its last entry unfinished
  - The dining table set for guests who never arrived

[Examine journal?] > yes

  "Day 12 - The scratching in the walls has stopped.
   I tell myself this is good news, but Martha
   won't come out of the cellar. She says she
   saw something in the mirror that wasn't he"

   The entry ends mid-word. The pen is still here.
```

- **Multi-layered examination**: Look once = surface. Look again = details. Look three times = secrets ✅ IMPLEMENTED
- **Collectible lore**: Journals, letters, inscriptions that piece together larger stories
- **Environmental puzzles**: "The painting's eyes follow the candlestick..."
- **Tragic histories**: Every ruin was once alive. Find out what happened.
- **Hidden messages**: Some text only appears under certain conditions (night, high INT, specific items)

---

#### 9. THE WEIGHT OF GOLD - Meaningful Economy
**Impact**: Strategic decisions, world immersion

Money matters because scarcity creates drama:

```
Your pouch: 47 gold

The merchant eyes your equipment...
  "That sword you carry—fine craftsmanship.
   I'd give you 200 gold for it. Enough to
   buy passage on the ship leaving tonight."

But without the sword, how will you fight?

The ship leaves in 2 hours. The dungeon
with the cure is 3 hours away on foot.

What do you do?
```

- **Meaningful prices**: Good equipment is expensive. Choices feel real.
- **Multiple currencies**: Gold for common goods, ancient coins for artifacts, favors for services
- **Economic consequences**: Spend lavishly → prices rise. Flood market → crash.
- **Bribery and corruption**: Some problems can be solved with gold. At a cost.
- **Gambling**: High-risk games of chance in taverns
- **Investment**: Fund a merchant and get returns later

---

#### 10. TEMPORAL ECHOES - Time-Based Secrets
**Impact**: Replayability, discovery, world depth
**Status**: MVP IMPLEMENTED

The world changes based on time:

```
You return to the Old Well at midnight...

Unlike during the day, the well glows faintly.
A voice rises from the depths:

  "You came at the hour. Few do.
   Ask your question, and I shall answer.
   But truth always has a price..."

[Ask about the Forgotten King]
[Ask about your father's fate]
[Ask about the coming darkness]
[Leave - some truths are too heavy]
```

**MVP Implemented**:
- ✅ **Day/night cycle**: Time tracked as hour (0-23), advances on movement (+1hr) and rest (+4hrs)
- ✅ **Night whispers**: Eerie atmospheric whispers appear at night (40% chance)
- ✅ **NPC availability**: NPCs can be marked as unavailable at night (shops close)
- ✅ **Status display**: Current time shown in status command (e.g., "14:00 (Day)")
- ✅ **Persistence**: Time saved/loaded with game state (backward compatible)

**Future Enhancements**:
- **Moon phases** affect magic power and unlock hidden areas
- **Seasonal events**: Winter festivals, harvest celebrations, summer dangers
- **Anniversary triggers**: Return to a location one "year" later for special events
- **Time-locked content**: Some doors only open at specific times

---

#### 11. THE LEGACY SYSTEM - Death Has Meaning
**Impact**: Tension, long-term investment, emergent stories

When you die, the story continues:

```
Your vision fades... but this is not the end.

╔══════════════════════════════════════════════╗
║         LEGACY CONTINUES                     ║
║                                              ║
║  20 years later, a new adventurer finds      ║
║  your journal in the ruins of Thornkeep...   ║
║                                              ║
║  INHERITED:                                  ║
║    - Your map (partial)                      ║
║    - Knowledge: "Beware the third chamber"   ║
║    - Reputation: "Child of the Fallen Hero"  ║
║    - Your unfinished quest                   ║
║                                              ║
║  The world remembers. Will you succeed       ║
║  where your predecessor failed?              ║
╚══════════════════════════════════════════════╝
```

- **Death is a chapter break**, not game over
- **Inheritors** start with partial knowledge of the world
- **Your grave** becomes a location in the world (can be found, looted, honored)
- **Legend grows**: Die heroically → NPCs speak of you. Die shamefully → your name is cursed.
- **Unfinished business**: Your ghost might appear to your successor
- **Cumulative progress**: Each generation can contribute to a greater goal

---

#### IMPLEMENTATION PRIORITY

**Phase 1 - Atmosphere** (Transform the feel):
1. Whisper System - Adds soul to every location
2. Environmental Storytelling - Makes exploration magical
3. Temporal Echoes - Adds depth and mystery

**Phase 2 - Consequence** (Make choices matter):
4. Echo Choices - Every decision resonates
5. Living World Events - Urgency and stakes
6. The Weight of Gold - Meaningful economy

**Phase 3 - Depth** (Mastery and investment):
7. Combo Combat - Satisfying combat loop
8. Bond System - Emotional investment
9. Darkness Meter - Psychological tension

**Phase 4 - Transcendence** (Truly unique):
10. Dream Sequences - Surreal storytelling
11. Legacy System - Death becomes narrative

---

### Non-interactive mode bugs
**Status**: ACTIVE

Issues discovered while playtesting `--non-interactive` mode:

1. ~~**Character creation broken in non-interactive mode**~~ (RESOLVED)
   - Fixed: Added `create_character_non_interactive()` function that reads character creation inputs from stdin
   - New `--skip-character-creation` flag to use default "Agent" character (backward compatible)
   - Validates all inputs immediately and returns errors for invalid input
   - Supports manual stat allocation (name, method "1", str, dex, int, confirmation) and random stats (name, method "2", confirmation)

2. ~~**Shop command requires prior NPC interaction**~~ (RESOLVED)
   - Fixed: `shop` command now auto-detects merchant NPCs in the current location
   - No need to `talk Merchant` first - just use `shop` when a merchant is present
   - If multiple merchants exist, uses the first one found

3. ~~**NPC conversation responses are generic**~~ (RESOLVED with AI service)
   - When AI is enabled, NPCs respond intelligently to player input
   - Without AI, NPCs fall back to "nods thoughtfully" responses

4. ~~**Enemy attack text duplicates name**~~ (RESOLVED)
   - AI-generated attack flavor text included enemy name, but combat code also prefixed it
   - Result was: "Frostbite Yeti The Frostbite Yeti unleashes a chilling roar..."
   - Fixed: Added `strip_leading_name()` helper in `combat.py` that removes redundant name prefix from attack flavor text

5. **Non-interactive mode skipped AI initialization** (RESOLVED)
   - `run_non_interactive()` and `run_json_mode()` hardcoded `ai_service=None`
   - Fixed: Now loads AI config from environment variables like interactive mode

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
**Status**: ACTIVE (Partial)

Player decisions should have lasting impact on the world and story.

**Implemented**:
- ✅ NPCs reference player's combat flee history ("cautious" reputation if 3+ flees)
- ✅ Player choices tracked in `game_state.choices` list

**Remaining features**:
- Dialogue choices that affect NPC relationships and quest outcomes
- Moral dilemmas with no clear "right" answer
- Branching quest paths based on player decisions
- World state changes based on completed quests (e.g., saving a village makes it thrive, ignoring it leads to ruin)
- Additional reputation types beyond "cautious" (e.g., aggressive, heroic, wealthy)

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
**Status**: ACTIVE (Partial)

Combat is too simple - attack until enemy dies. Core status effect system has been implemented with poison, burn, bleed, stun, and freeze.

**Implemented**:
- ✅ Basic poison status effect (DOT damage over time)
- ✅ Poison-capable enemies (spiders, snakes, serpents, vipers with 20% poison chance)
- ✅ Burn status effect (DOT damage over time, 2 turns)
- ✅ Burn-capable enemies (fire elementals, dragons, flame creatures with 20% burn chance)
- ✅ Bleed status effect (DOT damage over time, 3 damage per turn, 4 turns)
- ✅ Bleed-capable enemies (wolves, bears, lions, claw/fang-based creatures with 20% bleed chance)
- ✅ Stun status effect (player skips next action)
- ✅ Stun-capable enemies (trolls, golems, giants, hammer-wielders with 15% stun chance)
- ✅ Freeze status effect (reduces attack damage by 50% while frozen)
- ✅ Freeze-capable enemies (yetis, ice-themed creatures with 20% freeze chance, 2 turns)
- ✅ Freeze can be applied to both players and enemies
- ✅ Status effect display in combat status
- ✅ Status effects cleared on combat end
- ✅ Full persistence/serialization support
- ✅ Buff/debuff status effects (buff_attack, buff_defense, debuff_attack, debuff_defense)
- ✅ Buff/debuff modifies attack power and defense by percentage (stat_modifier field)
- ✅ Multiple buffs/debuffs stack additively
- ✅ Buff/debuff serialization with backward compatibility

**Remaining features**:
- Elemental strengths and weaknesses
- Defensive options: block, dodge, parry
- Enemy attack patterns and telegraphed special moves
- Critical hits and miss chances based on stats
- Combat stances or modes

### Dynamic world events
**Status**: ACTIVE (Partial)

The world feels static. Need ambient events and world dynamics.

**Implemented**:
- ✅ Day/night cycle with NPC availability (time advances on movement/rest, night whispers, NPCs can be unavailable at night)

**Remaining features**:
- Random encounters while traveling (bandits, merchants, wandering creatures)
- Weather system affecting gameplay (storms reduce visibility, rain extinguishes fire)
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

### Silent fallback masks AI generation failures
**Status**: RESOLVED

**Description**: When AI area generation failed, the code silently fell back to template-based generation without informing the player. Players had no way to know they weren't getting AI-generated content.

**Fix**: Added user notification when AI fallback occurs. The game now displays a yellow warning message: "[AI world generation temporarily unavailable. Using template generation.]" when AI generation fails but fallback succeeds. The `colors.warning()` helper function was added to style the message. Test added: `test_move_informs_player_when_ai_fails` in `tests/test_game_state.py`.

### JSON truncation during AI area generation
**Status**: RESOLVED

**Description**: AI area generation was failing with JSON truncation errors (`Failed to parse response as JSON: Unterminated string starting at...`) because the default `max_tokens` value (500) was too low for generating 5-7 locations with NPCs, which can require 1500-2000+ tokens.

**Fix**: Increased `max_tokens` default from 500 to 2000 in `ai_config.py`. Updated in dataclass default, `from_env()` fallback, `from_dict()` fallback, and docstring. Users can still override via `AI_MAX_TOKENS` environment variable.

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

