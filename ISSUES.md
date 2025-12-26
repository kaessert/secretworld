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
- ✅ **AI-generated whispers**: Dynamic whisper content via AI service - MVP IMPLEMENTED (context-aware whispers generated using world theme and location category; graceful fallback to template whispers on error)

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
- ✅ **Reputation tracking**: Player choices (fleeing combat, killing enemies) are tracked in `game_state.choices`
- ✅ **NPC reputation awareness**: NPCs reference player's "cautious" reputation (3+ flees) or "aggressive" reputation (10+ kills)
- ✅ Reputation-aware greetings with 3 variants each for "cautious" and "aggressive" players

**Future Enhancements**:
- Spare the bandit → He becomes an informant, or betrays you later, or saves you in Act 3
- A town you helped prospers; one you ignored falls to ruin (visible on return)
- NPCs reference your reputation: "You're the one who burned the witch... or was it saved her?"
- **Companion memories**: "I still remember what you did in Thornwood. I've never forgotten."

---

#### 3. THE DARKNESS METER - Psychological Horror Element
**Impact**: Tension, resource management, atmosphere
**Status**: MVP IMPLEMENTED

Exploring dangerous areas builds **Dread**:

```
═══════════════════════════════════════
  DREAD: ████████░░░░░░░░ 53%

  The shadows seem to lean toward you...
  You hear footsteps that aren't your own.
═══════════════════════════════════════
```

**MVP Implemented**:
- ✅ **DreadMeter model** with 0-100% tracking and visual bar display
- ✅ **Dread triggers**: Dungeons (+15), caves (+12), ruins (+10), wilderness (+5), forest (+3), night movement (+5 bonus), low health (+5), combat (+10)
- ✅ **Dread reduction**: Towns (-15), resting (-20), talking to NPCs (-5)
- ✅ **Milestone messages**: At 25%, 50%, 75%, and 100% thresholds
- ✅ **High dread effects**: Paranoid whispers at 50%+, -10% attack penalty at 75%+
- ✅ **Status display**: Dread meter shown in `status` command
- ✅ **Persistence**: Dread saved/loaded with game state (backward compatible)

**Future Enhancements**:
- ✅ **At 100%**: Shadow creature attacks - MVP IMPLEMENTED (Shadow of Dread manifests and attacks; defeating it reduces dread by 50%)
- ✅ **Hallucinations**: Fake enemies at high dread - MVP IMPLEMENTED (At 75-99% dread, 30% chance per move to encounter spectral enemies that dissipate when attacked, reducing dread by 5 with no XP/loot rewards)
- ✅ **Light sources**: Items that reduce dread buildup - MVP IMPLEMENTED (Torches reduce dread buildup by 50%, negate night bonus, consumable with limited duration)
- ✅ **Brave player rewards**: Best secrets in high-dread areas - MVP IMPLEMENTED (Dread Treasures: 30% chance to discover powerful items when looking at 75%+ dread; includes Shadow Essence, Veil of Courage, Dread Blade, Darklight Torch)

---

#### 4. LIVING WORLD EVENTS - The World Moves Without You
**Impact**: Immersion, urgency, emergent stories
**Status**: MVP IMPLEMENTED

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

**MVP Implemented**:
- ✅ **WorldEvent model** with event types, affected locations, duration, and time tracking
- ✅ **Event types**: Caravan, plague, and invasion events with unique consequences
- ✅ **Timed events**: Events have duration and expire after a set number of game hours
- ✅ **Event spawn**: 5% chance to spawn a new event on each move (max 3 active)
- ✅ **Consequences**: Expired events apply negative effects (health loss, gold loss, dread increase)
- ✅ **Location warnings**: Players warned when entering affected locations
- ✅ **`events` command**: View all active events with time remaining
- ✅ **Persistence**: Events saved/loaded with game state

**Future Enhancements**:
- **Spreading events**: Plagues, wars, monster migrations, seasons changing
- **Cascading effects**: Saved village → thriving trade → better shop inventory
- **Rival adventurers**: NPCs who complete quests you ignore, becoming allies or enemies
- ✅ **Event resolution**: Player actions to resolve events before they expire - MVP IMPLEMENTED (`resolve` command for plagues/invasions, auto-resolution for caravans on purchase; cure items drop from loot)

---

#### 5. DREAM SEQUENCES - Surreal Narrative Moments
**Impact**: Storytelling, foreshadowing, emotional depth
**Status**: MVP IMPLEMENTED

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

**MVP Implemented**:
- ✅ **25% trigger rate** on rest command
- ✅ **Prophetic dreams** hint at future events and locations
- ✅ **Atmospheric dreams** with surreal mood-setting content
- ✅ **Nightmare sequences** at 50%+ dread (psychological horror)
- ✅ **Choice-based personalization**: Dreams reflect player behavior (3+ flees → flee-themed, 10+ kills → combat-themed)
- ✅ **Formatted output** with decorative borders and intro/outro text

**Future Enhancements**:
- **Memory dreams** replay key moments with new perspective
- **Character dreams** reveal companion backstories
- **Dream items** that manifest in reality
- ✅ **AI-generated dreams** for dynamic content - MVP IMPLEMENTED (AI generates context-aware dreams based on theme, dread level, player choices, and location; graceful fallback to template dreams on error)

---

#### 6. COMBO COMBAT SYSTEM - Fluid, Strategic Fighting
**Impact**: Combat depth, mastery satisfaction
**Status**: MVP IMPLEMENTED

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

**MVP Implemented**:
- ✅ **Action history tracking**: Last 3 player actions tracked and displayed in combat status
- ✅ **Frenzy combo** (Attack→Attack→Attack): Triple hit dealing ~1.5x total damage
- ✅ **Revenge combo** (Defend→Defend→Attack): Counter-attack dealing damage equal to damage taken while defending
- ✅ **Arcane Burst combo** (Cast→Cast→Cast): Empowered spell dealing 2x magic damage
- ✅ **Combo notifications**: "COMBO AVAILABLE" message when pattern is ready
- ✅ **Flee breaks chain**: Attempting to flee clears action history

**Future Enhancements**:
- **Hybrid moves**: Defend→Cast→Attack = "Calculated Strike" (guaranteed crit)
- **Enemy patterns**: Bosses telegraph moves, allowing counter-play
- **More combos**: Additional combo patterns for variety

---

#### 7. THE BOND SYSTEM - Companions Who Matter
**Impact**: Emotional investment, tactical depth
**Status**: MVP IMPLEMENTED

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

**MVP Implemented**:
- ✅ **Companion model** with name, description, recruitment location, and bond points (0-100)
- ✅ **BondLevel enum**: STRANGER (0-24), ACQUAINTANCE (25-49), TRUSTED (50-74), DEVOTED (75-100)
- ✅ **Bond tracking**: `add_bond(amount)` adds points (capped at 100), returns level-up message if threshold crossed
- ✅ **Visual bond display**: Unicode bar (█░) with color-coded levels (green=DEVOTED, yellow=TRUSTED/ACQUAINTANCE)
- ✅ **`companions` command**: View party members with bond levels and descriptions
- ✅ **`recruit <npc>` command**: Recruit NPCs marked as `is_recruitable=True` to your party
- ✅ **NPC recruitability**: Added `is_recruitable` field to NPC model
- ✅ **Persistence**: Companions saved/loaded with game state (backward compatible)

**Future Enhancements**:
- **Bond levels** through choices, gifts, and shared experiences
- **Companion quests** that explore their past and resolve their arc
- ✅ **Combat synergies** unlock at higher bond levels - MVP IMPLEMENTED (passive attack damage bonuses: STRANGER 0%, ACQUAINTANCE +3%, TRUSTED +5%, DEVOTED +10%)
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
- ✅ **Seasonal events**: Winter festivals, harvest celebrations, summer dangers - MVP IMPLEMENTED (see `seasons.py`)
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
5. ~~Living World Events~~ ✅ MVP IMPLEMENTED - Urgency and stakes
6. The Weight of Gold - Meaningful economy

**Phase 3 - Depth** (Mastery and investment):
7. ~~Combo Combat~~ ✅ MVP IMPLEMENTED - Satisfying combat loop
8. Bond System - Emotional investment
9. ~~Darkness Meter~~ ✅ MVP IMPLEMENTED - Psychological tension

**Phase 4 - Transcendence** (Truly unique):
10. ~~Dream Sequences~~ ✅ MVP IMPLEMENTED - Surreal storytelling
11. Legacy System - Death becomes narrative

---

### OVERWORLD & SUB-LOCATION REWORK - Hierarchical World System
**Status**: IN PROGRESS (Core Infrastructure Complete, Dungeon Hierarchy Validated)

**Problem**: The current flat world grid doesn't support meaningful world structure. Players wander an endless grid with random combat everywhere. There's no sense of safe havens, no cities to explore internally, no dungeons with depth.

**Progress**:
- ✅ **Location model fields** (IMPLEMENTED): Added 5 hierarchy fields to `Location` dataclass
  - `is_overworld: bool` - True for overworld landmarks
  - `parent_location: Optional[str]` - Parent landmark for sub-locations
  - `sub_locations: List[str]` - Child locations for landmarks
  - `is_safe_zone: bool` - No random encounters if True
  - `entry_point: Optional[str]` - Default sub-location when entering
- ✅ Serialization: `to_dict()` and `from_dict()` updated with backward compatibility
- ✅ Tests: 22 comprehensive tests for hierarchy fields
- ✅ **Town Square hierarchical structure** (IMPLEMENTED): Default world now includes:
  - Town Square as overworld landmark with `is_overworld=True`, `is_safe_zone=True`
  - 3 sub-locations: Market District (with Merchant), Guard Post (with Guard), Town Well
  - All sub-locations have `parent_location="Town Square"` and `is_safe_zone=True`
  - `enter`/`exit` commands work with actual content
- ✅ **Forest hierarchical structure** (IMPLEMENTED): Forest expanded to overworld landmark:
  - Forest as overworld landmark with `is_overworld=True`, `is_safe_zone=False` (danger zone)
  - 3 sub-locations: Forest Edge, Deep Woods, Ancient Grove
  - All sub-locations have `parent_location="Forest"`, `is_safe_zone=False`, `category="forest"`
  - Hermit NPC in Ancient Grove (`is_recruitable=True`)
- ✅ **Abandoned Mines dungeon** (IMPLEMENTED): First dungeon with hierarchical sub-locations:
  - Abandoned Mines at (1, 1) with `is_overworld=True`, `is_safe_zone=False`, `category="dungeon"`
  - 4 sub-locations: Mine Entrance (entry point), Upper Tunnels, Flooded Level, Boss Chamber
  - All sub-locations have `parent_location="Abandoned Mines"`, `is_safe_zone=False`, `category="dungeon"`
  - Old Miner NPC in Mine Entrance (quest giver)
  - Connected south to Cave, west to Forest via grid system

**🚧 FUTURE ENHANCEMENTS**:

1. ~~**BLOCKER: AI World Generation Ignores Hierarchy (CRITICAL)**~~ ✅ RESOLVED
   - **File**: `src/cli_rpg/ai_world.py`
   - **Resolution**: Updated `create_ai_world()`, `expand_world()`, and `expand_area()` to set hierarchy fields based on location category
   - **Implementation**:
     - Added `SAFE_ZONE_CATEGORIES` constant defining safe location categories (town, village, settlement)
     - Added `_infer_hierarchy_from_category()` helper function that maps categories to hierarchy fields
     - All AI-generated locations now get `is_overworld=True` and appropriate `is_safe_zone` based on category
     - `expand_area()` properly sets parent-child relationships for sub-locations
   - **Tests**: 26 tests in `tests/test_ai_world_hierarchy.py`

2. **ENHANCEMENT: Vertical Dungeon Navigation (DESIGN GAP)**
   - **Problem**: No `up`/`down` commands for multi-floor vertical dungeons
   - **Current state**: Dungeons work with horizontal sub-location hierarchy (Abandoned Mines implemented with 4 sub-locations using `enter`/`exit`)
   - **Future enhancement**: Add `depth` field to Location, implement `up`/`down` navigation for vertical dungeons
   - **Effort**: 8-12 hours (future milestone)
   - **Status**: Deferred - horizontal hierarchy sufficient for current content

**Remaining Architecture**:

```
OVERWORLD (macro map)
  │
  ├── ✅ 🏠 Town Square (SAFE) - IMPLEMENTED
  │     ├── Market District (with Merchant)
  │     ├── Guard Post (with Guard)
  │     └── Town Well
  │
  ├── ✅ 🌲 Forest (DANGEROUS) - IMPLEMENTED
  │     ├── Forest Edge
  │     ├── Deep Woods
  │     └── Ancient Grove (with Hermit)
  │
  ├── ✅ 🏠 Millbrook Village (SAFE) - IMPLEMENTED
  │     ├── Village Square (with Elder NPC)
  │     ├── Inn (with Innkeeper NPC, recruitable)
  │     └── Blacksmith (with Blacksmith NPC, merchant)
  │
  ├── ✅ 🏰 Ironhold City (SAFE) - IMPLEMENTED
  │     ├── Ironhold Market (with Wealthy Merchant)
  │     ├── Castle Ward (with Captain of the Guard)
  │     ├── Slums (with Beggar, recruitable)
  │     └── Temple Quarter (with Priest)
  │
  └── ✅ ⛏️ Abandoned Mines (DUNGEON) - IMPLEMENTED
        ├── Mine Entrance (with Old Miner NPC)
        ├── Upper Tunnels
        ├── Flooded Level
        └── Boss Chamber
```

**Core Concepts**:

1. **Overworld**: Large-scale map of landmarks (cities, dungeons, forests, mountains)
   - Travel between landmarks (possibly with travel time/random encounters)
   - Each landmark is an entry point to a sub-location
   - ✅ `worldmap` command shows overworld - IMPLEMENTED

2. **Sub-locations**: Internal areas within each landmark
   - Cities contain: districts, shops, taverns, castles
   - Dungeons contain: floors, rooms, boss chambers
   - Forests contain: clearings, caves, ruins
   - Each has its own local grid/map
   - `map` command shows current sub-location

3. **Safety Zones** (NO random encounters):
   - Towns and cities = SAFE
   - Villages = SAFE
   - Inns/taverns = SAFE
   - Shops = SAFE
   - Temple interiors = SAFE

4. **Danger Zones** (random encounters enabled):
   - Wilderness areas
   - Dungeons
   - Caves
   - Ruins
   - Roads between landmarks (overworld travel)

5. **Navigation**:
   - ✅ `enter <landmark>` - Enter a city/dungeon from overworld - IMPLEMENTED
   - ✅ `exit` / `leave` - Return to overworld - IMPLEMENTED
   - `n/s/e/w` - Move within current sub-location
   - `travel <landmark>` - Fast travel on overworld (if discovered)

**Location Model Changes**: ✅ IMPLEMENTED (see Progress section above)

**Enter/Exit Commands**: ✅ IMPLEMENTED
- `enter <location>` supports partial, case-insensitive matching for sub-location names
- Uses `entry_point` as default when no argument provided
- Both commands blocked during NPC conversation
- 11 comprehensive tests in `tests/test_game_state.py`

**Backwards Compatibility**: Implemented with full backward compatibility - old saves load correctly with default values.

**Benefits**:
- Logical world organization
- Safe towns for shopping/questing without combat interruption
- Dungeons feel like dungeons (contained, dangerous)
- Cities feel like cities (explorable, safe, populated)
- Clear distinction between travel and exploration
- Natural quest hubs vs adventure zones

**Files to modify**:
- ✅ `src/cli_rpg/models/location.py`: Add hierarchy fields - DONE
- ✅ `src/cli_rpg/random_encounters.py`: Check `is_safe_zone` before triggering encounters - DONE
- ✅ `src/cli_rpg/game_state.py`: Enter/exit commands - DONE
- ✅ `src/cli_rpg/world.py`: Default hierarchical world structure - DONE
- ✅ `src/cli_rpg/map_renderer.py`: Separate overworld and local map rendering - DONE
- ✅ `src/cli_rpg/ai_world.py`: AI generates landmarks with sub-locations - DONE
- ✅ `src/cli_rpg/game_state.py`: trigger_encounter() safe zone check - DONE

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
**Status**: ✅ RESOLVED

AI agent player and simulation framework have been implemented.

**Implemented Components** (in `scripts/` directory):

1. **`scripts/state_parser.py`** - JSON output parsing utilities
   - `AgentState` dataclass for tracking game state (location, health, gold, inventory, dread, quests, combat status)
   - Parses all JSON message types: `state`, `combat`, `actions`, `dump_state`

2. **`scripts/ai_agent.py`** - Heuristic-based agent implementation
   - `SessionStats` dataclass for collecting simulation statistics
   - `Agent` class with priority-based decision engine:
     - Combat: Flee at <25% HP, use potion at <50% HP, attack otherwise
     - Exploration: Rest if HP <50% or dread >60%, buy potions, complete quests, explore exits
   - `GameSession` class for subprocess management with threaded I/O

3. **`scripts/run_simulation.py`** - CLI entry point
   - Args: `--seed`, `--max-commands`, `--timeout`, `--output`, `--verbose`
   - Outputs summary statistics and optional JSON report

4. **`tests/test_ai_agent.py`** - Comprehensive test suite (31 tests)
   - Unit tests for state parsing and agent decisions
   - Integration tests running 50-100 commands

**Usage**:
```bash
# Run simulation with default settings (1000 commands)
python -m scripts.run_simulation

# Run with specific seed and command limit
python -m scripts.run_simulation --seed=42 --max-commands=100 --verbose

# Save JSON report
python -m scripts.run_simulation --output=report.json
```

**Future Enhancements** (moved to backlog):
- Scheduled CI/cron runs for periodic testing
- LLM-based agent variant for more dynamic playstyles
- Regression test corpus from successful runs

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
   - ✅ `map` command shows current layer, `worldmap` shows overworld - IMPLEMENTED

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
   - ✅ Monster art stored in bestiary by monster name - IMPLEMENTED
   - NPC art stored with NPC data in location

4. **Art cache/bestiary**
   - ✅ First encounter generates and caches art in bestiary - IMPLEMENTED
   - ✅ Subsequent encounters reuse cached art - IMPLEMENTED
   - ✅ `bestiary` command displays discovered monster art - IMPLEMENTED

### Meaningful choices and consequences
**Status**: ACTIVE (Partial)

Player decisions should have lasting impact on the world and story.

**Implemented**:
- ✅ NPCs reference player's combat flee history ("cautious" reputation if 3+ flees)
- ✅ NPCs reference player's combat kill history ("aggressive" reputation if 10+ kills)
- ✅ Player choices tracked in `game_state.choices` list

**Remaining features**:
- Dialogue choices that affect NPC relationships and quest outcomes
- Moral dilemmas with no clear "right" answer
- Branching quest paths based on player decisions
- World state changes based on completed quests (e.g., saving a village makes it thrive, ignoring it leads to ruin)
- Additional reputation types (e.g., heroic, wealthy)

### Character classes with unique playstyles
**Status**: ACTIVE (Base System Implemented)

**Implemented**:
- ✅ CharacterClass enum with 5 classes: Warrior, Mage, Rogue, Ranger, Cleric
- ✅ Class selection during character creation (by number or name)
- ✅ Stat bonuses per class:
  - **Warrior**: +3 STR, +1 DEX
  - **Mage**: +3 INT, +1 DEX
  - **Rogue**: +3 DEX, +1 STR
  - **Ranger**: +2 DEX, +1 STR, +1 INT
  - **Cleric**: +2 INT, +1 STR
- ✅ Class displayed in character status
- ✅ Class persistence in save/load (backward compatible)

**Future enhancements** (class-specific abilities):
- **Warrior**: ✅ `bash` command MVP IMPLEMENTED (shield bash costs 15 stamina, deals 0.75x damage, stuns target for 1 turn); Future: unlocks heavy armor
- **Mage**: ✅ `fireball` command MVP IMPLEMENTED (costs 20 mana, INT × 2.5 damage ignores defense, 25% Burn chance); ✅ `ice_bolt` command MVP IMPLEMENTED (costs 15 mana, INT × 2.0 damage ignores defense, 30% Freeze chance); ✅ `heal` command MVP IMPLEMENTED (costs 25 mana, restores INT × 2 HP); Future: weak armor restrictions
- **Rogue**: ✅ `sneak` command MVP IMPLEMENTED (stealth mode in combat, 1.5x backstab damage, DEX-based dodge while stealthed); ✅ `sneak` exploration MVP IMPLEMENTED (avoid random encounters, costs 10 stamina, success based on DEX/armor/light); ✅ `pick` command MVP IMPLEMENTED (lockpicking for treasure chests)
- **Ranger**: ✅ `track` command MVP IMPLEMENTED (costs 10 stamina, detects enemies in adjacent locations, success rate 50% + 3% per PER); ✅ wilderness damage bonus MVP IMPLEMENTED (+15% attack damage in forest/wilderness locations); Future: animal companion
- **Cleric**: ✅ `bless` command MVP IMPLEMENTED (costs 20 mana, +25% attack buff for 3 turns to player and companions); ✅ `smite` command MVP IMPLEMENTED (costs 15 mana, INT×2.5 damage ignores defense, INT×5.0 vs undead, 30% stun chance on undead); Future: holy symbols

### Charisma stat & social skills
**Status**: ✅ RESOLVED

**Implemented**:
- ✅ **Charisma (CHA) stat** added to Character model (1-20 range, default 10)
- ✅ **Class bonuses**: Cleric +2 CHA, Rogue +1 CHA
- ✅ **CHA price modifiers**: ±1% per CHA from 10 on buy/sell prices
- ✅ **`persuade` command**: 30% + (CHA × 3%) success, grants 20% shop discount
- ✅ **`intimidate` command**: 20% + (CHA × 2%) + (kills × 5%) success, affected by NPC willpower
- ✅ **`bribe <amount>` command**: Threshold 50 - (CHA × 2) gold, min 10 gold
- ✅ **NPC social attributes**: willpower (1-10), bribeable (bool), persuaded (bool)
- ✅ **Persistence**: All stats save/load with backward compatibility
- ✅ **Level up**: CHA +1 on level up like other stats

**Future Enhancements** (moved to backlog):
- High CHA unlocks special dialogue options marked with [CHA]
- Some quests can be resolved through talking instead of fighting

### Stealth & sneaking
**Status**: ACTIVE (Partial)

Let players avoid combat through cunning.

**Implemented**:
- ✅ `sneak` command for Rogues to enter stealth mode in combat (costs 10 stamina, 1.5x backstab damage, DEX-based dodge)
- ✅ `hide` command in combat to become untargetable for 1 turn (costs 10 stamina, available to all classes)
- ✅ `sneak` command for exploration (Rogue only, costs 10 stamina): Chance to avoid random encounters on next move. Success formula: 50% + (DEX × 2%) - (armor defense × 5%) - (15% if lit), capped 10-90%. Effect consumed on move.

**Remaining features**:
- Enemies have perception stats - some are blind, some have keen senses
- Stealth kills grant bonus XP ("clean kill" bonus)

### Perception & secret discovery
**Status**: ✅ RESOLVED

Reward observant players with hidden content.

**Implemented**:
- ✅ **Perception (PER) stat** added to Character model (1-20 range, default 10)
- ✅ **Class bonuses**: Rogue +2 PER, Ranger +1 PER
- ✅ **`search` command** (alias: `sr`) for active searching with +5 PER bonus (+2 with light source)
- ✅ **Hidden secrets on locations**: `hidden_secrets` field with type, description, threshold, discovered status
- ✅ **Secret types**: HIDDEN_DOOR, HIDDEN_TREASURE, TRAP, LORE_HINT
- ✅ **Passive detection**: Auto-detect secrets when PER >= threshold
- ✅ **Active search**: Manual search for harder-to-find secrets
- ✅ **Persistence**: All stats save/load with backward compatibility
- ✅ **Level up**: PER +1 on level up like other stats

**Future Enhancements** (moved to backlog):
- Traps can be spotted before triggering (PER check)
- Some NPC lies can be detected ("You sense they're not being truthful...")
- Secret passages between locations (shortcuts)

### Haggling at shops
**Status**: ✅ RESOLVED

Make shopping more interactive.

**Implemented**:
- ✅ `haggle` command negotiates better buy/sell prices at shops
- ✅ **Success formula**: 25% base + (CHA × 2%) + 15% if NPC is persuaded, max 85%
- ✅ **Success**: 15% discount on next buy OR 15% bonus on next sell
- ✅ **Critical success** (roll ≤ 10% of success chance): 25% discount + merchant hints at rare item
- ✅ **Failure**: No effect, can try again
- ✅ **Critical failure** (roll ≥ 95): Merchant refuses to trade for 3 turns (cooldown)
- ✅ **NPC attributes**: `haggleable: bool = True`, `haggle_cooldown: int = 0`
- ✅ **GameState tracking**: `haggle_bonus: float = 0.0` (reset after one transaction)
- ✅ Cooldown decrements on each exploration command
- ✅ Haggle bonus applied to both buy and sell prices
- ✅ Persistence: All fields save/load with backward compatibility

**Future Enhancements** (moved to backlog):
- Reputation affects starting prices (hero = discount, villain = markup)

### Luck stat affecting outcomes
**Status**: ✅ RESOLVED

**Implemented**:
- ✅ **Luck (LCK) stat** added to Character model (1-20 range, default 10)
- ✅ **Class bonuses**: Rogue +2 LCK, Ranger +1 LCK
- ✅ **Crit chance modifier**: ±0.5% per LCK point from baseline 10
- ✅ **Loot drop rate**: Base 50% ± 2% per LCK point from 10
- ✅ **Loot quality**: Weapon/armor bonuses gain +1 per 5 LCK above 10
- ✅ **Gold rewards**: ±5% per LCK point from 10
- ✅ **Level up**: LCK +1 on level up like other stats
- ✅ **Persistence**: Full save/load support with backward compatibility

**Future Enhancements** (moved to backlog):
- `pray` at temples to temporarily boost luck
- Cursed items reduce luck, blessed items increase it
- Some events are pure luck checks ("The bridge looks unstable...")

### Camping & wilderness survival
**Status**: ✅ RESOLVED

**Implemented**:
- ✅ `camp` command in wilderness to set up camp (uses Camping Supplies item)
- ✅ Camping heals 50% HP, reduces dread by 30 (40 with campfire), advances time 8 hours
- ✅ Campfire cooks Raw Meat → Cooked Meat automatically (40 HP vs 30 HP)
- ✅ 20% chance of friendly visitor spawn with campfire
- ✅ 40% chance of dream sequence during camp (uses dream system)
- ✅ `forage` command to find herbs/berries in forest/wilderness (PER-based, 1-hour cooldown)
- ✅ `hunt` command to track and kill game (DEX/PER-based, 2-hour cooldown, yields Raw Meat and Animal Pelt)
- ✅ Location restrictions: camping only in forest/wilderness/cave/ruins; foraging/hunting only in forest/wilderness
- ✅ Safe zone handling: camp redirects to rest in towns
- ✅ Cooldowns persist through save/load
- ✅ Camping Supplies available at Market District (40g) and Millbrook Village Inn (30g)

**Future Enhancements** (moved to backlog):
- Hunger system (optional hardcore mode) - starving = stat penalties
- Keep watch to avoid ambush
- Repair gear at camp

### Mana/stamina resource system
**Status**: ✅ RESOLVED

Special abilities should cost resources, not be free.

**Mana System - Implemented**:
- ✅ **Mana pool**: Mages get `50 + INT * 5`, other classes get `20 + INT * 2`
- ✅ **Cast costs mana**: Normal cast costs 10 mana, Arcane Burst combo costs 25 mana
- ✅ **Mana potions**: Items with `mana_restore` field restore mana when used
- ✅ **Level up**: Max mana recalculates based on new INT, mana fully restored
- ✅ **Status display**: Mana bar shown with color coding (like health)
- ✅ **Persistence**: Full serialization with backward compatibility for old saves

**Stamina System - Implemented**:
- ✅ **Stamina pool**: Warriors/Rangers get `50 + STR * 5`, other classes get `20 + STR * 2`
- ✅ **Sneak costs stamina**: Rogue sneak ability costs 10 stamina
- ✅ **Stamina regeneration**: 1 stamina per combat turn (in enemy_turn), 25% max stamina restored on rest
- ✅ **Stamina potions**: Items with `stamina_restore` field restore stamina when used (Stamina Potion: 30 gold, 25 stamina restore)
- ✅ **Status display**: Stamina bar shown with color coding (like health/mana)
- ✅ **Persistence**: Full serialization with backward compatibility for old saves

**Future Enhancements** (moved to backlog):
- Powerful abilities cost more: `fireball` = 20 mana, `power strike` = 15 stamina
- Running out = can only use basic attack
- Some enemies drain mana/stamina with attacks

### Weapon proficiencies & fighting styles
**Status**: ✅ RESOLVED

Not all weapons should feel the same.

- ✅ **Weapon types**: Sword, Axe, Dagger, Mace, Bow, Staff (plus UNKNOWN for unrecognized)
- ✅ **Proficiency system**: Using a weapon type increases skill with it (1 XP per attack)
- ✅ **Proficiency levels**: Novice (0 XP) → Apprentice (25 XP) → Journeyman (50 XP) → Expert (75 XP) → Master (100 XP)
- ✅ **Damage bonuses**: Novice +0%, Apprentice +5%, Journeyman +10%, Expert +15%, Master +20%
- ✅ **`proficiency` command** (alias: `prof`): View weapon proficiency levels with progress bars and damage bonuses
- ✅ **Combat integration**: Proficiency damage bonus applied to attacks, level-up messages displayed
- ✅ **Loot generation**: Weapon loot automatically gets weapon_type assigned via `infer_weapon_type()`
- ✅ **Persistence**: Weapon proficiencies save/load correctly, backward compatible with old saves
- ✅ **Fighting stances** (choose one active via `stance` command):
  - Balanced (default): +5% crit chance
  - Aggressive: +20% damage, -10% defense
  - Defensive: -10% damage, +20% defense
  - Berserker: Damage scales with missing HP (up to +50% at low health)
- ✅ Stance modifiers apply to all attacks (physical, spells, abilities)
- ✅ Stance persists through save/load with backward compatibility

**Future Enhancements** (moved to backlog):
- Special moves unlocked at Journeyman and Master levels
- Faster attacks at higher proficiency

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
- ✅ Defensive options: `block` command - MVP IMPLEMENTED (costs 5 stamina, 75% damage reduction vs defend's 50%)
- Defensive options: parry (not yet implemented)
- Enemy attack patterns and telegraphed special moves
- ✅ Critical hits and miss chances based on stats - MVP IMPLEMENTED (Player crits: 5% + 1% per DEX/INT capped at 20%, 1.5x damage; Player dodge: 5% + 0.5% per DEX capped at 15%; Enemy crits: flat 5%, 1.5x damage)
- ✅ Combat stances or modes - MVP IMPLEMENTED (see "Weapon proficiencies & fighting styles" section above; `stance` command with Balanced/Aggressive/Defensive/Berserker options)

### Dynamic world events
**Status**: ACTIVE (Partial)

The world feels static. Need ambient events and world dynamics.

**Implemented**:
- ✅ Day/night cycle with NPC availability (time advances on movement/rest, night whispers, NPCs can be unavailable at night)
- ✅ Random travel encounters (15% chance per move: hostile enemies 60%, wandering merchants 25%, mysterious wanderers 15%)
- ✅ Living world events (5% spawn chance per move: caravans, plagues, invasions with timed consequences)

**Remaining features**:
- ✅ Weather system affecting gameplay (clear, rain, storm, fog with dread modifiers and storm travel delays) - MVP IMPLEMENTED
- ✅ Weather visibility effects (storms reduce visibility/truncate descriptions/hide details, fog obscures exits and NPC names, caves unaffected) - MVP IMPLEMENTED
- ✅ Weather interactions (rain extinguishes burn 40% per turn, storm extends freeze +1 turn on apply) - MVP IMPLEMENTED
- ✅ Seasonal events and festivals - MVP IMPLEMENTED (4 seasons with dread modifiers, 4 festival types with gameplay bonuses)

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
**Status**: ACTIVE (MVP Implemented)

Adventuring alone limits roleplay possibilities.

**Implemented**:
- ✅ Recruitable NPC companions (NPCs with `is_recruitable=True`)
- ✅ Bond system with 4 levels (STRANGER → ACQUAINTANCE → TRUSTED → DEVOTED)
- ✅ `companions` command to view party members
- ✅ `recruit <npc>` command to recruit willing NPCs
- ✅ `dismiss <name>` command to remove companions from party
- ✅ Persistence with backward compatibility

**Remaining features**:
- ✅ Companion dialogue and banter during travel - MVP IMPLEMENTED (25% trigger chance per move, context-aware comments based on location, weather, time, dread, and bond level)
- ✅ Companion combat bonuses - MVP IMPLEMENTED (passive attack damage bonus based on bond level: STRANGER 0%, ACQUAINTANCE +3%, TRUSTED +5%, DEVOTED +10%; bonuses stack with multiple companions)
- ✅ Companion reactions to player choices - MVP IMPLEMENTED (companions react to combat choices based on personality: warrior approves kills/disapproves fleeing, pacifist approves fleeing/disapproves kills, pragmatic is neutral; bond adjusts ±3 points)
- ✅ Companion-specific quests and storylines - MVP IMPLEMENTED (companions can have personal quests that unlock at TRUSTED bond level; completing a companion's quest grants +15 bond bonus)

### Immersive text presentation
**Status**: ACTIVE (Partial)

Text output could be more atmospheric and engaging.

**Implemented**:
- ✅ Typewriter-style text reveal module (`text_effects.py`) with configurable delay, ANSI code handling, and Ctrl+C graceful fallback
- ✅ Effects follow color settings (disabled when colors are disabled, or when `--non-interactive`/`--json` mode)
- ✅ Typewriter effect integrated into `dreams.py` for dream sequences
- ✅ Typewriter effect integrated into `whisper.py` for ambient whispers
- ✅ Typewriter effect integrated into `combat.py` for dramatic combat moments (display functions: `display_combat_start()`, `display_combo()`, `display_combat_end()`)
- ✅ Effects disabled in `--non-interactive` and `--json` modes via `set_effects_enabled(False)` in `main.py`

**Remaining features**:
- ✅ Color-coding for dialogue and narration - MVP IMPLEMENTED (semantic `dialogue()` and `narration()` helpers in `colors.py`; NPC dialogue displays with blue text, narration uses default terminal color)
- ✅ Sound effects via terminal bell for important events - MVP IMPLEMENTED (terminal bell `\a` plays on combat victory, level up, player death, and quest completion; disabled in `--non-interactive` and `--json` modes)
- ✅ Pause and pacing for dramatic tension - MVP IMPLEMENTED (dramatic pause functions in `text_effects.py` with short/medium/long durations; integrated into combat start/combo/end and dream sequences; respects effects toggle)
- ✅ Stylized borders and frames for different UI elements - MVP IMPLEMENTED (`frames.py` with DOUBLE/SINGLE/SIMPLE frame styles; `frame_text()` for custom framing, `frame_announcement()` for world events, `frame_dream()` for dreams, `frame_combat_intro()` for boss/shadow combat; integrated into `dreams.py`, `world_events.py`, `shadow_creature.py`)

### AI-generated quest objectives don't match spawned enemies
**Status**: ✅ RESOLVED

**Description**: When AI generates kill quests (e.g., "Kill 5 goblins"), the specified enemy types don't actually spawn in the game. Random encounters spawn different enemy types (Wild Boar, Mountain Lion, Giant Spider, Wolf, etc.) that don't count toward quest objectives.

**Resolution**: Updated `DEFAULT_QUEST_GENERATION_PROMPT` in `ai_config.py` to include the valid enemy types from `combat.py`'s `enemy_templates` dictionary. The AI is now instructed to ONLY use these enemy types for kill quests:
- Forest/wilderness: Wolf, Bear, Wild Boar, Giant Spider
- Caves: Bat, Goblin, Troll, Cave Dweller
- Dungeons/ruins: Skeleton, Zombie, Ghost, Dark Knight
- Mountains: Eagle, Goat, Mountain Lion, Yeti
- Towns/villages: Bandit, Thief, Ruffian, Outlaw

**Note**: Players must be in the correct location type to encounter matching enemies. A quest for "Wolf" (forest enemy) won't progress while fighting in mountains (which spawn Eagle, Mountain Lion, Yeti). Players should explore forest areas to find wolves.

### Default world has no hidden secrets for search command
**Status**: ✅ RESOLVED

**Description**: The `search` command is documented in the README as a major feature ("Secret Discovery: PER-based check with +5 bonus; light sources provide additional +2") and the Perception & secret discovery system is marked as RESOLVED in ISSUES.md. However, no locations in the default world actually have any hidden secrets defined.

**Resolution**: Added `hidden_secrets` to 14 default world locations in `src/cli_rpg/world.py`:

| Location | Secret Type | Threshold | Description |
|----------|------------|-----------|-------------|
| Town Well | hidden_treasure | 10 | Loose stone with coins |
| Guard Post | lore_hint | 12 | Monster sighting tallies |
| Forest Edge | trap | 12 | Concealed snare trap |
| Deep Woods | hidden_door | 14 | Overgrown path to clearing |
| Ancient Grove | lore_hint | 15 | Ancient runes about guardian |
| Cave | hidden_treasure | 13 | Gemstone in crack |
| Village Square | lore_hint | 10 | Well inscription |
| Blacksmith | hidden_treasure | 12 | Coins in forge ashes |
| Upper Tunnels | trap | 14 | Unstable ceiling section |
| Flooded Level | hidden_treasure | 16 | Submerged payroll cache |
| Boss Chamber | lore_hint | 18 | Crystal warning inscription |
| Castle Ward | lore_hint | 16 | Coded noble's letter |
| Slums | hidden_door | 14 | Thieves' underground passage |
| Temple Quarter | hidden_treasure | 11 | Forgotten offering box |

Secrets are distributed by difficulty:
- Easy (threshold ≤12): Town areas, Millbrook Village
- Medium (threshold 13-14): Forest, Cave, Slums
- Hard (threshold ≥15): Abandoned Mines, Ironhold City

Tests added in `tests/test_perception.py` (TestDefaultWorldSecrets class).

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

### Lockpicking & treasure chests
**Status**: RESOLVED

Rogues can now pick locked treasure chests found throughout the world.

**Implemented**:
- `pick <chest>` command (alias: `lp`) for Rogue-only lockpicking attempts
- DEX-based success formula: 20% base + (DEX × 2%), capped at 80%
- Difficulty modifiers (levels 1-5): +20%/+10%/0%/-10%/-20%
- Lockpick consumable item (always consumed on attempt, success or fail)
- `open <chest>` command (alias: `o`) for anyone to open unlocked chests
- One-time loot: Chests contain items, can only be opened once
- Tab completion for chest names
- Chest state persists through save/load
- Non-Rogues get "Only Rogues can pick locks" message
- Lockpicks available at Market District shop (30 gold)
- Two treasure chests in default world: Mossy Chest (Ancient Grove), Rusted Strongbox (Mine Entrance)

**Future Enhancements** (moved to backlog):
- Failure consequences: trigger traps, alert enemies, jam lock permanently
- Key-based locks (already reserved in data structure with `requires_key` field)
- Locked doors that unlock shortcuts or secret areas
- More chest locations and loot variety

### `cast` command gives wrong error message outside combat
**Status**: RESOLVED

**Description**: When a player used the `cast` command (or its `c` shortcut) outside of combat, the game displayed "Unknown command" instead of "Not in combat" like all other combat commands (`attack`/`a`, `defend`/`d`, `flee`/`f`).

**Fix**: Added "cast" to the list of combat commands in `main.py` (line 1300) that show "Not in combat." when used outside combat. Changed `["attack", "defend", "flee", "rest"]` to `["attack", "defend", "flee", "rest", "cast"]`. Test added: `test_cast_command_outside_combat` in `tests/test_main_coverage.py`.

### `companion-quest` command missing from help output
**Status**: RESOLVED

**Description**: The `companion-quest <name>` command was documented in README.md under "Companion Personal Quests" but was not listed in the in-game `help` command output.

**Fix**: Added `companion-quest <name> - Accept a companion's personal quest` to the exploration commands section in `get_command_reference()` in `main.py`. Test added: `test_help_includes_companion_quest` in `tests/test_main_help_command.py`.

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

### ASCII art first line alignment off
**Status**: RESOLVED

**Description**: ASCII art for locations, enemies, and NPCs had the first line misaligned (missing leading spaces), breaking the visual presentation.

**Cause**: In `src/cli_rpg/ai_service.py`, three parsing functions used `art = response_text.strip()` which removed ALL leading whitespace, including the critical indentation on the first line that makes ASCII art align properly.

**Fix**: Changed from `art = response_text.strip()` to:
```python
# Strip only trailing whitespace, preserve first line's leading spaces
art = response_text.rstrip()
# Remove leading empty lines
while art.startswith("\n"):
    art = art[1:]
```

This preserves the first line's indentation while still removing trailing whitespace and leading empty lines (common in LLM responses).

**Files modified**:
- `src/cli_rpg/ai_service.py` - Fixed 3 methods: `_parse_ascii_art_response`, `_parse_location_ascii_art_response`, `_parse_npc_ascii_art_response`

**Tests added**: 5 new tests in `tests/test_ascii_art.py` class `TestAsciiArtFirstLineAlignment`

### Sub-locations not shown in look command output
**Status**: RESOLVED

**Description**: When a player uses the `look` command at a location with sub-locations (like Town Square), the output only shows directional exits (e.g., "Exits: east, north, west") but does NOT show available sub-locations that can be entered.

**Fix**: Updated `Location.get_layered_description()` and `Location.__str__()` methods in `src/cli_rpg/models/location.py` to display an "Enter:" line after the exits line, showing available sub-locations. The line uses color formatting consistent with location names and is shown regardless of visibility level (weather doesn't hide buildings/areas you can enter).

### Map locations all use same symbol - impossible to distinguish
**Status**: RESOLVED

**Description**: The map command showed all locations with the same bullet point symbol (`•`), making it impossible to tell which location was which when 5+ locations all shared the same symbol.

**Fix**: Each non-current location is now assigned a unique letter symbol (A-Z, then a-z for 27+ locations) in alphabetical order by name. The legend shows the letter with the category icon (if applicable), e.g., `A = 🌲 Forest`. The current player location still uses the `@` symbol. Implementation in `src/cli_rpg/map_renderer.py`.

### README direction shortcut documentation is inconsistent
**Status**: RESOLVED

**Description**: The README documentation for direction shortcuts was misleading. It implied that single-letter shortcuts like `s` and `e` worked for south and east, when in reality:
- `s` is handled by `status` command (NOT south)
- `e` is handled by `equip` command (NOT east)

**Fix**: Updated README.md to clarify that:
1. Removed `/n, /s, /e, /w` from the `go <direction>` description since those aren't actually shortcuts within the go command
2. Added an explicit note explaining that `s` runs `status` and `e` runs `equip`, so players should use `gs`/`ge` for south/east navigation

