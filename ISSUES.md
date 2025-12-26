## Active Issues

---

### AI Location Generation Failures - JSON Parsing & Token Limits
**Status**: HIGH PRIORITY

**Problem**: AI location generation frequently fails with JSON parsing errors:

```
Failed to generate location: Failed to parse response as JSON: Expecting ',' delimiter: line 13 column 7 (char 474)
Failed to generate location: Failed to parse response as JSON: Expecting ',' delimiter: line 13 column 7 (char 502)
```

This causes world generation to fall back to templates, breaking immersion and AI-generated coherence.

**Root Causes to Investigate**:

1. **Token limits too restrictive**: Complex prompts with context may exceed response token budget
2. **Prompts too large**: Single prompts try to generate too much at once (location + NPCs + connections + description)
3. **No JSON validation/repair**: Truncated or malformed JSON crashes instead of recovering

**Proposed Solution: Layered Query Architecture**

Instead of one monolithic prompt, use a hierarchical generation system:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: World Context (cached, reused)                    │
│  ─────────────────────────────────────────────────────────  │
│  • Theme essence: "cyberpunk noir with neon-lit streets"    │
│  • Naming conventions: "Tech-inspired, Japanese influence"  │
│  • Tone: "Gritty, mysterious, morally ambiguous"            │
│  • Generated ONCE at world creation, stored in game state   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: Region Context (per area cluster)                 │
│  ─────────────────────────────────────────────────────────  │
│  • Region theme: "Industrial district, factory smoke"       │
│  • Danger level: "Moderate - gang territory"                │
│  • Key landmarks: ["Rust Tower", "The Vats"]                │
│  • Generated when entering new region, cached per region    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: Location Details (per location, small prompt)     │
│  ─────────────────────────────────────────────────────────  │
│  INPUT: World context + Region context + direction          │
│  OUTPUT: Just { name, description, category, connections }  │
│  • Small, focused prompt = reliable JSON                    │
│  • No NPCs in this query (separate layer)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: NPC Generation (optional, per location)           │
│  ─────────────────────────────────────────────────────────  │
│  INPUT: Location name + description + region context        │
│  OUTPUT: Just { npcs: [{name, description, role}] }         │
│  • Only called for locations that should have NPCs          │
│  • Separate small prompt = reliable JSON                    │
└─────────────────────────────────────────────────────────────┘
```

**Benefits of Layered Approach**:

| Benefit | Description |
|---------|-------------|
| **Smaller prompts** | Each layer generates less = fits in token budget |
| **Better coherence** | World/region context ensures consistency |
| **Faster generation** | Layer 1-2 cached, only Layer 3-4 called per location |
| **Easier debugging** | Know exactly which layer failed |
| **Graceful degradation** | If NPC layer fails, location still works |

**Implementation Steps**:

1. **Audit current prompts** (`ai_config.py`):
   - Measure token counts for each prompt type
   - Identify which prompts are too large
   - Document current `max_tokens` settings vs actual needs

2. **Add JSON repair utilities** (`ai_service.py`):
   - Extract JSON from markdown code blocks
   - Attempt to close truncated arrays/objects
   - Validate against expected schema before use

**Completed (2025-12-26)**:
- ✓ WorldContext and RegionContext models created
- ✓ Split generation prompts (world context, region context, minimal location, NPC)
- ✓ AIService layered generation methods
- ✓ GameState context caching and serialization
- ✓ Increased max_tokens to 3000
- ✓ JSON extraction from markdown code blocks
- ✓ JSON repair for truncated responses
- ✓ Debug logging for parse failures

---

### Map System Bugs (Discovered via Playtesting)
**Status**: ACTIVE
**Date Discovered**: 2025-12-26

Issues discovered through comprehensive map system playtesting in non-interactive mode.

**Note**: Map command issues inside SubGrid locations are resolved.

---

### OVERWORLD & SUB-LOCATION REWORK - Hierarchical World System
**Status**: IN PROGRESS (Core Infrastructure Complete)

**Problem**: The current flat world grid doesn't support meaningful world structure.

**Progress**:
- Location model hierarchy fields implemented
- Town Square, Forest, Millbrook Village, Ironhold City, Abandoned Mines all implemented with sub-locations
- Enter/exit commands working
- AI world generation respects hierarchy
- Safe zone encounters working

**Remaining**:
- Vertical dungeon navigation (`up`/`down` commands) - deferred

---

### Non-interactive mode enhancements
**Status**: ACTIVE

**Future enhancements**:
- Include RNG seeds in logs for reproducibility
- Log AI-generated content for review
- Enable session replay from logged state

---

### Overworld map with cities and sub-locations
**Status**: ACTIVE (Partially Implemented)

Players want a more sophisticated map system with hierarchical locations.

**Implemented**:
- `map` command shows current layer, `worldmap` shows overworld
- Enter/exit commands for city/dungeon navigation
- SubGrid system for interior locations

**Remaining**:
- Fast travel between discovered overworld locations
- Travel time/random encounters on overworld

---

### Unique AI-generated ASCII art per entity
**Status**: ACTIVE

**Implemented**:
- Monster art stored in bestiary by monster name
- First encounter generates and caches art in bestiary
- Subsequent encounters reuse cached art
- `bestiary` command displays discovered monster art

**Remaining**:
- NPC art stored with NPC data in location
- Consistent art for all entity types

---

### Meaningful choices and consequences
**Status**: ACTIVE (Partial)

**Implemented**:
- NPCs reference player's combat flee history ("cautious" reputation if 3+ flees)
- NPCs reference player's combat kill history ("aggressive" reputation if 10+ kills)
- Player choices tracked in `game_state.choices` list

**Remaining**:
- Dialogue choices that affect NPC relationships
- Branching quest paths
- World state changes based on completed quests

---

### Character classes with unique playstyles
**Status**: ACTIVE (Base System Implemented)

**Implemented**:
- 5 classes: Warrior, Mage, Rogue, Ranger, Cleric with stat bonuses
- Class-specific abilities: bash, fireball, ice_bolt, heal, sneak, pick, track, bless, smite

**Remaining (Future)**:
- Heavy armor for Warrior
- Armor restrictions for Mage
- Animal companion for Ranger
- Holy symbols for Cleric

---

### Stealth & sneaking
**Status**: ACTIVE (Partial)

**Implemented**:
- `sneak` command for Rogues (combat stealth, exploration encounter avoidance)
- `hide` command in combat

**Remaining**:
- Enemies with perception stats
- Stealth kills bonus XP

---

### Status effects and combat depth
**Status**: ACTIVE (MVP Complete)

**Implemented**:
- Poison, burn, bleed, stun, freeze status effects
- Buff/debuff system
- Elemental strengths/weaknesses
- Block, parry commands
- Boss telegraphed attacks
- Critical hits and dodge
- Combat stances

---

### Dynamic world events
**Status**: ACTIVE (MVP Complete)

**Implemented**:
- Day/night cycle with NPC availability
- Random travel encounters
- Living world events (caravans, plagues, invasions)
- Weather system with combat interactions
- Seasonal events and festivals

---

### Reputation and faction system
**Status**: ACTIVE (MVP Implemented)

**Implemented**:
- Faction model with reputation levels
- Combat reputation consequences
- Merchant Guild shop price modifiers

**Remaining**:
- Faction-based content unlocks
- Quest-based reputation changes

---

### Crafting and gathering system
**Status**: ACTIVE (MVP Implemented)

**Implemented**:
- `gather` command for resources
- 8 crafting recipes
- Location-specific resources

**Remaining**:
- Crafting skill progression
- Rare recipes as rewards

---

### Secrets and discovery
**Status**: ACTIVE

**Desired features**:
- Hidden rooms and secret passages
- Lore fragments and collectibles
- Riddles and puzzles
- Environmental storytelling

---

### Companion system
**Status**: ACTIVE (MVP Implemented)

**Implemented**:
- Recruitable companions with bond levels
- Companion banter, combat bonuses, reactions
- Companion personal quests

---

### Immersive text presentation
**Status**: ACTIVE (MVP Complete)

**Implemented**:
- Typewriter text effects
- Color-coding for dialogue/narration
- Sound effects via terminal bell
- Dramatic pauses
- Stylized borders/frames

---

### Dream sequences trigger too frequently
**Status**: ACTIVE

**Problem**: Players report dreams happen too often, becoming annoying rather than atmospheric. Current trigger rates:
- 25% chance on `rest` command
- 40% chance during `camp` command

This means players see dreams almost every other rest, which:
- Breaks gameplay flow
- Makes dreams feel mundane instead of special
- Adds unwanted delay when trying to heal quickly

**Proposed Fix**:

1. **Reduce base trigger rates**:
   - `rest`: 25% → 10%
   - `camp`: 40% → 15%

2. **Add cooldown between dreams**:
   - Track `last_dream_time` in GameState
   - Minimum 3-4 rests between dreams
   - Cooldown resets on significant events (level up, quest complete, boss kill)

3. **Make dreams contextual** (only trigger when meaningful):
   - High dread (50%+): Nightmare more likely
   - After major event: Prophetic dream
   - Low activity: Skip dreams entirely

4. **Add player control**:
   - `rest --quick` or `r!` to skip dream check entirely
   - Settings option to disable dreams

---

### Tiredness stat for realistic sleep/rest mechanics
**Status**: PROPOSED
**Date Added**: 2025-12-26

**Problem**: Falling asleep during rest is currently random, which feels arbitrary and unrealistic.

**Proposed Feature**: Add a **Tiredness** stat that determines when the player falls asleep.

#### Tiredness Mechanic Design

**Stat Properties**:
- Range: 0-100 (0 = fully rested, 100 = exhausted)
- Display: Could show in status bar like stamina/dread

**Tiredness Increases From**:
- Traveling between locations (+2-5 per move)
- Combat (+5-10 per fight, more for longer fights)
- Time passing (+1 per game hour)
- Using abilities/spells (+1-3 per use)
- Carrying heavy load (+1 per move if encumbered)

**Tiredness Decreases From**:
- Resting at inn/safe location (-50 to -100)
- Camping (-30 to -50)
- Quick rest command (-10 to -20)
- Consuming food/drink items (-5 to -15)

**Sleep/Dream Connection**:
- Tiredness < 30: Cannot fall asleep, no dreams
- Tiredness 30-60: May fall asleep (low chance), light dreams
- Tiredness 60-80: Will fall asleep, normal dreams
- Tiredness > 80: Deep sleep guaranteed, vivid/prophetic dreams more likely
- Tiredness 100: Forced rest - character collapses, vulnerability period

**Gameplay Effects of High Tiredness**:
- Combat penalties (slower reactions, reduced accuracy)
- Reduced perception (miss secrets, ambushed more easily)
- Dialogue options limited (too tired to negotiate)
- Movement speed reduced

**Implementation**:

```python
# In models/character.py or new models/tiredness.py
@dataclass
class Tiredness:
    current: int = 0  # 0-100

    def increase(self, amount: int) -> Optional[str]:
        """Increase tiredness, return warning if getting exhausted."""
        self.current = min(100, self.current + amount)
        if self.current >= 80:
            return "You're exhausted and need rest soon."
        elif self.current >= 60:
            return "You're feeling tired."
        return None

    def decrease(self, amount: int) -> None:
        self.current = max(0, self.current - amount)

    def can_sleep(self) -> bool:
        return self.current >= 30

    def sleep_quality(self) -> str:
        if self.current >= 80:
            return "deep"  # Vivid dreams, full recovery
        elif self.current >= 60:
            return "normal"
        else:
            return "light"  # Restless, partial recovery
```

**Files to Create/Modify**:
- `src/cli_rpg/models/tiredness.py`: NEW - Tiredness model
- `src/cli_rpg/models/character.py`: Add tiredness field
- `src/cli_rpg/game_state.py`: Track tiredness changes on actions
- `src/cli_rpg/dreams.py`: Use tiredness instead of random chance
- `src/cli_rpg/combat.py`: Apply tiredness penalties
- `src/cli_rpg/main.py`: Display tiredness in status, handle collapse

**Benefits**:
- More realistic and immersive
- Player agency - manage tiredness strategically
- Dreams feel earned, not random
- Adds resource management depth
- Natural pacing mechanism (can't grind indefinitely)

---

### WFC Playtesting Issues (2025-12-26)
**Status**: ACTIVE

Issues discovered during `--wfc` mode playtesting (updated 2025-12-26):

#### HIGH PRIORITY BUGS

1. ~~**Shop price inconsistency**~~ ✅ RESOLVED (2025-12-26)
   - Shop display now shows adjusted prices (CHA, faction, persuade, haggle modifiers)
   - Matches the actual purchase price shown in buy command errors

2. **ASCII art first line loses leading whitespace**
   - First row of ASCII art displays without leading spaces, breaking alignment
   - Example (wrong):
     ```
     /\    /\
        /  \  /  \
       |    ||    |
     ```
   - Expected:
     ```
         /\    /\
        /  \  /  \
       |    ||    |
     ```
   - **Cause**: Likely string stripping or split/join operation removing leading spaces from first line
   - **Files to investigate**: `ai_service.py` (ASCII art parsing), `location_art.py` (fallback templates)

3. **Shop command doesn't work with AI-generated merchants in SubGrid locations**
   - Location shows "NPCs: Tech Merchant" but `shop` command says "There's no merchant here."
   - Reproduction:
     1. Enter a SubGrid location (e.g., `enter Rusty Outpost`)
     2. Navigate to a location with a merchant NPC (e.g., "Silent Bazaar" with "Tech Merchant")
     3. Run `shop` command → "There's no merchant here."
   - **Cause**: Shop command likely checks for:
     - A `Shop` object attached to the location, OR
     - NPC with specific `role="merchant"` attribute
   - AI-generated NPCs with "Merchant" in name may not have proper role/shop setup
   - **Files to investigate**:
     - `src/cli_rpg/main.py`: `shop` command handler
     - `src/cli_rpg/ai_world.py`: NPC generation for SubGrid locations
     - `src/cli_rpg/models/npc.py`: NPC role field

4. ~~**Caravan world event doesn't provide shop access**~~ ✅ RESOLVED (2025-12-26)
    - Fixed: `shop` command now checks for active caravan events at current location
    - When a CARAVAN event is active, provides temporary shop with exotic items:
      - Exotic Spices (50g), Traveler's Map (75g), Foreign Elixir (100g), Rare Gemstone (200g), Antidote (40g)
    - Files modified: `world_events.py` (added `get_caravan_shop()`), `main.py` (shop command handler)

5. **"Can't go that way" even though map shows valid exits**
    - Map displays "Exits: east, south, west" but movement fails with "You can't go that way."
    - Location "Dim Glade North" at (1, 11) shows exits but they don't work
    - **Possible causes**:
      - Location connections don't match displayed exits
      - WFC terrain blocking not reflected in exit list
      - Connection target location doesn't exist or has invalid coordinates
      - Desync between `location.connections` and actual traversability
    - **Files to investigate**:
      - `src/cli_rpg/game_state.py`: `move()` method - what blocks movement
      - `src/cli_rpg/models/location.py`: `get_available_directions()` vs actual connections
      - `src/cli_rpg/map_renderer.py`: How exits are determined for display

#### MEDIUM PRIORITY BUGS

1. **NPCs show as "???" when revisiting locations**
   - After leaving a location and returning, NPC names display as "???" instead of actual names
   - Reproduction: Start at Whispering Woods → Go east → Return west → NPCs now "???, ???, ???"
   - May be related to fog/visibility system being too aggressive

2. **Exits disappear/change when revisiting locations**
   - Available exits change inconsistently when revisiting a location
   - Whispering Woods initially shows "east, north, west", later shows "east, west" (north gone)

3. **Wild Boar ASCII art is a cat**
   - The Wild Boar enemy uses ASCII art that clearly depicts a cat:
   ```
      /\_/\
     ( o.o )
      > ^ <
     /|   |\
    (_|   |_)
   ```
   - The `/\_/\` ears and `( o.o )` face is universal ASCII cat pattern

4. **Inconsistent shop pricing message**
   - Shop display shows one price but error message shows different price
   - Shop displays: "Iron Sword - 100 gold", Error says: "99 gold needed"

5. **Load character screen is overwhelming**
   - Shows 140+ entries including all autosaves with "(saved: unknown)" timestamps
   - Autosave entries flood the list, making manual saves hard to find
   - **Suggestions**:
     - Collapse autosaves into single expandable entry
     - Show only recent 10-20 characters by default
     - Add pagination or search
     - Fix "(saved: unknown)" to show actual timestamps

6. **Can enter any sub-location instead of designated entry point**
   - Currently shows multiple "Enter:" options for all sub-locations in an area
   - Player can enter any sub-location directly (e.g., "Enter: Data Glade, Cyber Grove, Neon Orchard, Quantum Glade")
   - **Problem**: This is unrealistic - you shouldn't be able to teleport into any room
   - **Expected behavior**: Only show the single entry point location (the one with `is_exit_point=True`)
   - Example: "Enter: Data Glade" (the designated entrance), then navigate internally to other rooms
   - **Files to investigate**:
     - `src/cli_rpg/game_state.py`: `get_enterable_locations()` or similar
     - `src/cli_rpg/main.py`: `enter` command handling
     - `src/cli_rpg/models/location.py`: `sub_grid` and entry point logic

#### LOW PRIORITY / UX ISSUES

1. **Combo system unclear**
   - During combat, "COMBO AVAILABLE: Frenzy!" displayed but no obvious trigger command
   - **Suggestion**: Add hint text like "Type 'frenzy' to use combo!" or document in help

2. **Confusing "exit" message when not in sub-location**
   - Using `exit` when not inside sub-location shows "You're not inside a landmark."
   - **Suggestion**: Change to "You're not inside a building or dungeon. Use 'go <direction>' to travel."

3. **"bye" command outside of talk mode is confusing**
   - Typing `bye` when not talking to an NPC shows: "Unknown command 'bye'. Did you mean 'buy'?"
   - Suggests "buy" which is also contextual (shop only)
   - Better: "The 'bye' command ends conversations. Use it while talking to an NPC."

4. **"accept" could auto-accept single quest**
   - When talking to NPC with only one quest, "accept" says "Accept what? Specify a quest name."
   - If only one quest available, could auto-accept it
   - At minimum, show: "Accept what? Available: Quest Name"

5. **Terrain blocking message varies**
   - Water blocked: "The water ahead is impassable."
   - Wall blocked: "You can't go that way."
   - Consistent phrasing would be better UX

#### DESIGN OBSERVATIONS

1. ~~**Shop price shows base, not reputation-adjusted price**~~ ✅ RESOLVED (2025-12-26)
   - Shop now displays fully adjusted prices (CHA, faction, persuade, haggle modifiers)

2. **Rest command output**
   - Shows stamina recovery and dread reduction
   - HP recovery (25% max) not shown in message if health is full
   - Consider showing "HP: X/X (already full)" for clarity

---

### Procedural quest generation
**Status**: ACTIVE

**Desired features**:
- AI-generated side quests
- Quest templates with procedural elements
- Scaling difficulty
- Quest chains

---

### CRITICAL: Quest System World Integration Failures
**Status**: HIGH PRIORITY
**Date Added**: 2025-12-26

**Problem**: Quest generation and world generation are completely decoupled, creating "impossible quests" where targets don't exist in the game world.

#### Root Cause Analysis

Quest generation (`ai_service.py:1639-1689`) receives minimal context:
- Theme, NPC name, player level, location name
- **NO** list of existing locations
- **NO** list of spawnable enemy types
- **NO** list of existing NPCs
- **NO** list of obtainable items

The AI generates arbitrary target strings that may not exist anywhere in the game.

#### Issue 1: EXPLORE Quest Targets Don't Match World Locations

**Severity**: HIGH

```
Quest: "Explore the Obsidian Cathedral"
World: Contains "Town Square", "Dark Forest", "Mountain Pass"
Result: IMPOSSIBLE - "Obsidian Cathedral" doesn't exist
```

**How it fails**:
- AI generates arbitrary location name in `target` field
- Progress checked via string match: `quest.target.lower() == location_name.lower()`
- Player can never visit a location that doesn't exist

**Files**:
- `src/cli_rpg/ai_service.py:1639-1689` - generates arbitrary targets
- `src/cli_rpg/models/character.py:625-630` - string matching only

#### Issue 2: KILL Quest Targets Don't Match Spawnable Enemies

**Severity**: HIGH

```
Quest: "Kill 5 Frost Phoenixes"
Spawnable: Goblin, Skeleton, Orc, Spider, Wolf, Bear (templates)
Result: IMPOSSIBLE - "Frost Phoenix" never spawns
```

**How it fails**:
- AI generates arbitrary enemy name in `target` field
- Enemies spawn from templates (`combat.py:2500+`) or AI generation
- AI-generated enemies use different names than quest targets
- Quest prompt lists suggested enemies but AI ignores them

**Evidence from prompt** (`ai_config.py:172-177`):
```
IMPORTANT for KILL quests - use ONLY these enemy types as targets:
- Wolf, Bear, Wild Boar, Giant Spider (for forest/wilderness)
- Bat, Goblin, Troll, Cave Dweller (for caves)
...
```
But this is guidance only - no validation enforces it.

#### Issue 3: TALK Quest Targets Don't Match World NPCs

**Severity**: HIGH

```
Quest: "Talk to Elder Mage Aldous"
NPCs in World: Merchant, Guard, Hermit, Town Elder
Result: IMPOSSIBLE - "Elder Mage Aldous" doesn't exist
```

**How it fails**:
- AI generates arbitrary NPC name in `target` field
- NPCs created via hardcoded defaults (`world.py`) or AI location generation
- No cross-reference between quest NPCs and world NPCs
- Player can never find NPC that wasn't generated

#### Issue 4: COLLECT Quest Targets Don't Match Obtainable Items

**Severity**: CRITICAL (most common failure)

```
Quest: "Collect 3 Dragon Scales"
Obtainable Items: Health Potion, Iron Sword, Leather Armor (shops + drops)
Result: IMPOSSIBLE - "Dragon Scales" can't be obtained
```

**How it fails**:
- AI generates arbitrary item name in `target` field
- Items only come from: hardcoded shops, template enemy drops
- **No AI item generation exists** in the codebase
- Quest items are pure fiction with no way to obtain them

#### Risk Assessment

| Objective Type | Impossible Quest Risk | Reason |
|----------------|----------------------|--------|
| COLLECT | 70% | Items are hardcoded, no AI item generation |
| KILL | 60% | AI generates exotic enemy names not in templates |
| TALK | 50% | NPCs generated separately from quests |
| EXPLORE | 40% | AI generates unique location names |

#### Proposed Solutions

**Solution 1: Validation-Based (Quick Fix)**

Add validation before accepting quests:

```python
# In main.py when accepting quest
def validate_quest_target(quest: Quest, game_state: GameState) -> bool:
    if quest.objective_type == ObjectiveType.EXPLORE:
        return quest.target.lower() in [loc.lower() for loc in game_state.world.keys()]
    elif quest.objective_type == ObjectiveType.KILL:
        return quest.target.lower() in VALID_ENEMY_TYPES
    elif quest.objective_type == ObjectiveType.TALK:
        return any(quest.target.lower() == npc.name.lower()
                   for loc in game_state.world.values()
                   for npc in loc.npcs)
    elif quest.objective_type == ObjectiveType.COLLECT:
        return quest.target.lower() in OBTAINABLE_ITEMS
    return True
```

**Solution 2: Context-Aware Generation (Better)**

Pass world state to quest generation:

```python
def generate_quest(
    self,
    theme: str,
    npc_name: str,
    player_level: int,
    location_name: str = "",
    # NEW: World context for valid targets
    valid_locations: List[str] = None,
    valid_enemies: List[str] = None,
    valid_npcs: List[str] = None,
    valid_items: List[str] = None,
) -> dict:
```

Update prompt to include:
```
VALID TARGETS (you MUST use one of these):
- Locations: {valid_locations}
- Enemies: {valid_enemies}
- NPCs: {valid_npcs}
- Items: {valid_items}
```

**Solution 3: World-Creating Quests (Best)**

When AI generates a quest target, ensure it gets created:

```python
# After generating KILL quest for "Shadow Drake"
# → Add "Shadow Drake" to enemy spawn table for relevant locations

# After generating EXPLORE quest for "Obsidian Cathedral"
# → Schedule location generation for "Obsidian Cathedral"

# After generating TALK quest for "Elder Mage Aldous"
# → Create NPC "Elder Mage Aldous" in appropriate location

# After generating COLLECT quest for "Dragon Scales"
# → Add "Dragon Scales" to loot table or shop inventory
```

#### Implementation Priority

1. **Immediate**: Add `VALID_ENEMY_TYPES` constant and validate KILL quests (most common type)
2. **Short-term**: Pass obtainable items list to quest generation for COLLECT quests
3. **Medium-term**: Implement context-aware generation with all world state
4. **Long-term**: World-creating quests that guarantee completability

#### Files to Modify

- `src/cli_rpg/ai_service.py`: Accept world state in `generate_quest()`
- `src/cli_rpg/ai_config.py`: Update `DEFAULT_QUEST_GENERATION_PROMPT` with valid targets
- `src/cli_rpg/main.py`: Add quest validation before acceptance
- `src/cli_rpg/combat.py`: Export `VALID_ENEMY_TYPES` constant
- `src/cli_rpg/models/quest.py`: Add `validated: bool` field (optional)

#### Related Issues

- Links to "World Generation Immersion & Coherence Improvements" - same root cause of disconnected systems
- Links to "AI Location Generation Failures" - same pattern of AI generating invalid content

---

### Quest System Improvements for Immersion
**Status**: ACTIVE
**Date Added**: 2025-12-26

**Analysis Summary**: Deep analysis of the quest system revealed functional but basic mechanics that lack depth for immersive gameplay.

#### Current Limitations

| Feature | Current State | Impact |
|---------|---------------|--------|
| Quest context | Minimal (theme, NPC, level only) | Generic, disconnected quests |
| Quest chains | None | No narrative arcs |
| Faction integration | None (system exists unused) | No meaningful choices |
| Time limits | None | No urgency |
| Branching objectives | None | No moral complexity |
| Difficulty indicators | None | Player can't gauge appropriateness |
| Quest memory | None | World doesn't react to outcomes |

#### Proposed Enhancements

**1. Quest Context Integration (HIGH PRIORITY)**

Pass `WorldContext` and `RegionContext` to quest generation:

```python
def generate_quest(
    ...
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None,
    npc_background: str = "",
    recent_player_actions: List[str] = None,
) -> dict:
```

**2. Quest Chains & Prerequisites (HIGH PRIORITY)**

Add chain support to Quest model:

```python
@dataclass
class Quest:
    # ... existing fields ...
    chain_id: Optional[str] = None
    chain_position: int = 0
    prerequisite_quests: List[str] = field(default_factory=list)
    unlocks_quests: List[str] = field(default_factory=list)
```

**3. Faction Integration (HIGH PRIORITY)**

Connect quests to existing faction system:

```python
@dataclass
class Quest:
    # ... existing fields ...
    faction_affiliation: Optional[str] = None
    faction_reward: int = 0
    faction_penalty: Optional[Tuple[str, int]] = None
    required_reputation: int = 0
```

**4. Quest Difficulty (MEDIUM PRIORITY)**

```python
class QuestDifficulty(Enum):
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    CHALLENGING = "challenging"
    HEROIC = "heroic"

@dataclass
class Quest:
    difficulty: QuestDifficulty = QuestDifficulty.NORMAL
    recommended_level: int = 1
```

**5. Time-Sensitive Quests (MEDIUM PRIORITY)**

```python
@dataclass
class Quest:
    time_limit_hours: Optional[int] = None
    accepted_at: Optional[int] = None

    def is_expired(self, current_game_hour: int) -> bool:
        if self.time_limit_hours is None:
            return False
        return (current_game_hour - self.accepted_at) >= self.time_limit_hours
```

**6. Branching Objectives (HIGH PRIORITY)**

```python
@dataclass
class QuestBranch:
    name: str
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    moral_alignment: str = "neutral"  # good/evil/neutral
    faction_effects: Dict[str, int] = field(default_factory=dict)

@dataclass
class Quest:
    alternative_completions: List[QuestBranch] = field(default_factory=list)
```

Example: "Stop the Bandit Leader"
- **Path A**: Kill the Bandit Leader (+Militia rep)
- **Path B**: Convince him to leave (+Outlaw rep)
- **Path C**: Help him raid (+major Outlaw rep, Militia hostile)

**7. Multi-Stage Objectives (MEDIUM PRIORITY)**

```python
@dataclass
class QuestStage:
    description: str
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    current_count: int = 0

@dataclass
class Quest:
    stages: List[QuestStage] = field(default_factory=list)
    current_stage: int = 0
```

**8. Quest Memory & NPC Reactions (MEDIUM PRIORITY)**

```python
@dataclass
class QuestOutcome:
    quest_name: str
    completion_method: str
    timestamp: int
    affected_npcs: List[str]
    world_changes: Dict[str, Any]

# In Character model
completed_quest_outcomes: List[QuestOutcome] = field(default_factory=list)
```

#### Implementation Priority

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| World/Region context in generation | High | Low | **P0** |
| Faction integration | High | Medium | **P0** |
| Quest chains & prerequisites | High | Medium | **P1** |
| Branching objectives/choices | High | High | **P1** |
| Difficulty indicators | Medium | Low | **P2** |
| Time-sensitive quests | Medium | Low | **P2** |
| Multi-stage objectives | Medium | High | **P2** |
| Quest memory/NPC reactions | Medium | Medium | **P3** |

#### Files to Modify

- `src/cli_rpg/models/quest.py`: Add new fields (chain, faction, difficulty, branches)
- `src/cli_rpg/ai_service.py`: Accept context params, generate richer quests
- `src/cli_rpg/ai_config.py`: Enhanced quest generation prompt
- `src/cli_rpg/main.py`: Handle branching completion, faction rewards
- `src/cli_rpg/game_state.py`: Track quest outcomes for memory system

---

### World Generation Immersion & Coherence Improvements
**Status**: ACTIVE
**Date Added**: 2025-12-26

**Analysis Summary**: Deep analysis of the world generation system revealed excellent procedural terrain generation (WFC) and solid spatial management (WorldGrid), but critical disconnects that harm immersion.

#### Current Architecture

| Layer | Component | Status |
|-------|-----------|--------|
| **Terrain** | WFC algorithm + ChunkManager | ✅ Solid, but isolated |
| **Locations** | AI or fallback templates | ⚠️ Works, but generic |
| **Context** | WorldContext + RegionContext | ❌ Models exist, unintegrated |

#### Critical Issues

**1. Terrain ↔ Location Disconnect**

The WFC terrain system (`wfc.py`, `wfc_chunks.py`) generates coherent terrain chunks, but location generation (`ai_world.py`) completely ignores terrain. A "forest clearing" could spawn in a desert chunk.

```
WFC generates: [forest][forest][plains][water]
AI generates:  "Desert Oasis" at coordinates (1,1) ← No connection!
```

**Files involved**:
- `src/cli_rpg/wfc.py` - WFC algorithm (working correctly)
- `src/cli_rpg/wfc_chunks.py` - ChunkManager (working correctly)
- `src/cli_rpg/ai_world.py` - Location generation (doesn't query terrain)

**2. Each Location Generated in Isolation**

The AI prompt for location generation (`ai_config.py`) doesn't include:
- World theme/essence
- Regional theme
- Terrain type at coordinates
- Neighboring location themes

Result: Locations feel random, not part of a cohesive world.

**3. Minimal NPC/Content Generation**

- Only 0-2 NPCs per AI-generated location
- No shop inventories generated
- No quest hooks or faction ties
- Hardcoded merchants feel out of place in AI worlds

#### Implementation Plan

**Phase 1: High Priority (Integrate existing systems)**

1. **Enrich Location Prompts** (Partially Complete)
   - [x] Add `terrain_type` from ChunkManager to prompt ✓ (2025-12-26)
   - [ ] Add `world_theme_essence` from WorldContext to prompt
   - [ ] Add `region_theme` from RegionContext to prompt
   - [ ] Add `neighboring_locations` names/themes for coherence

   **Files to modify**:
   - `src/cli_rpg/ai_config.py`: Expand `DEFAULT_LOCATION_PROMPT_MINIMAL`

**Phase 2: Medium Priority (New features)**

2. **Region Planning System**
   - [ ] Divide world into ~16x16 tile regions
   - [ ] Pre-generate `RegionContext` when player approaches region boundary
   - [ ] All locations in region share theme, danger level, naming style
   - [ ] Add region-based lookup: `get_region_context(x, y)` → `RegionContext`

   **Files to modify**:
   - `src/cli_rpg/game_state.py`: Add region management
   - `src/cli_rpg/ai_world.py`: Use region context during expansion

3. **Enhanced NPC Generation**
   - [ ] Request 3-5 NPCs per location with roles (merchant, quest giver, guard, traveler)
   - [ ] Generate shop inventories for merchants
   - [ ] Generate quest hooks tied to region theme
   - [ ] Add faction affiliations

   **Files to modify**:
   - `src/cli_rpg/ai_service.py`: Enhance NPC generation
   - `src/cli_rpg/ai_config.py`: Update NPC prompt template

4. **Terrain-Biased WFC**
   - [ ] Modify chunk generation to respect region themes
   - [ ] Mountain region → bias WFC toward mountain/foothills/hills
   - [ ] Swamp region → bias toward swamp/water/forest
   - [ ] Creates mega-biomes instead of random terrain salad

   **Files to modify**:
   - `src/cli_rpg/wfc.py`: Add tile weight biasing
   - `src/cli_rpg/wfc_chunks.py`: Accept region bias parameter

**Phase 3: Lower Priority (Polish)**

5. **Strategic World Expansion**
   - [ ] Place frontier exits strategically (toward unexplored regions)
   - [ ] Ensure terrain transitions feel natural (forest → plains → desert, not forest → desert)
   - [ ] Cluster similar locations together

6. **Configurable SubGrid Bounds**
   - [ ] Support linear dungeons (1x10 corridors)
   - [ ] Support large open areas (10x10 plazas)
   - [ ] Multi-level dungeons with z-coordinate

   **Files to modify**:
   - `src/cli_rpg/world_grid.py`: Make SubGrid bounds configurable

#### Suggested Implementation Order

1. **Quick win**: Pass terrain type to location AI prompt (changes to `ai_world.py`, `ai_config.py`)
2. **Core fix**: Generate and cache WorldContext at world creation, include in prompts
3. **Major improvement**: Implement coordinate-based RegionContext lookup
4. **Full system**: Region planning with terrain biasing

#### Strengths to Preserve

- **WFC Algorithm** (`wfc.py:45-120`) - Shannon entropy-based collapse with proper constraint propagation
- **ChunkManager** (`wfc_chunks.py`) - Deterministic seeding, boundary linking, disk persistence
- **WorldGrid** (`world_grid.py`) - Clean coordinate-based placement with automatic bidirectional connections
- **SubGrid Architecture** - Bounded interiors for dungeons/buildings separate from overworld
- **Multi-provider AI** (`ai_service.py`) - Supports OpenAI, Anthropic, Ollama with graceful fallback

