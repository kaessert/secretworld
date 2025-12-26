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

3. **Create WorldContext model** (`models/world_context.py`):
   ```python
   @dataclass
   class WorldContext:
       theme: str
       theme_essence: str  # AI-generated theme summary
       naming_style: str   # How to name things
       tone: str           # Narrative tone
       generated_at: datetime
   ```

4. **Create RegionContext model** (`models/region_context.py`):
   ```python
   @dataclass
   class RegionContext:
       name: str
       theme: str          # Sub-theme for this region
       danger_level: str   # safe/moderate/dangerous
       landmarks: list[str]
       parent_world: str
   ```

5. **Split generation prompts** (`ai_config.py`):
   - `WORLD_CONTEXT_PROMPT`: Generate theme essence (once)
   - `REGION_CONTEXT_PROMPT`: Generate region details (per area)
   - `LOCATION_PROMPT_MINIMAL`: Just name/desc/category (per location)
   - `NPC_PROMPT_MINIMAL`: Just NPC list (optional per location)

6. **Update AIService** (`ai_service.py`):
   - Add `generate_world_context()` method
   - Add `generate_region_context()` method
   - Refactor `generate_location()` to use layered contexts
   - Add `generate_npcs_for_location()` as separate call

7. **Cache contexts in GameState**:
   - Store WorldContext at game creation
   - Store RegionContexts as player explores
   - Pass relevant context to generation calls

**Files to modify**:
- `src/cli_rpg/ai_config.py`: Split prompts, adjust token limits
- `src/cli_rpg/ai_service.py`: Add layered generation methods, JSON repair
- `src/cli_rpg/models/world_context.py`: NEW - WorldContext model
- `src/cli_rpg/models/region_context.py`: NEW - RegionContext model
- `src/cli_rpg/game_state.py`: Cache contexts, pass to generation
- `src/cli_rpg/ai_world.py`: Use layered generation

**Quick Wins (do first)**:
1. Increase `max_tokens` for location generation (current: 2000, try: 3000)
2. Add JSON extraction from markdown code blocks
3. Add try/except with JSON repair for truncated responses
4. Log full AI responses on parse failure for debugging

---

### AI Area Generation - Coordinates Outside SubGrid Bounds
**Status**: HIGH PRIORITY

**Problem**: AI area generation fails when generated locations have coordinates outside SubGrid bounds:

```
AI area generation failed: Coordinates (0, 4) outside bounds (-3, 3, -3, 3)
```

The SubGrid has bounds of (-3, 3, -3, 3) = 7x7 grid, but AI is generating locations at y=4 which is outside.

**Root Cause**:

In `ai_world.py:expand_area()`, the AI generates relative coordinates for sub-locations, but:
1. The prompt doesn't specify coordinate bounds to the AI
2. SubGrid enforces bounds strictly, causing placement to fail
3. One failed placement crashes the entire area generation

**Current Code** (`ai_world.py`):
```python
sub_grid.bounds = (-3, 3, -3, 3)  # 7x7 grid

for loc_data in area_data:
    rel_x, rel_y = loc_data["relative_coords"]
    # AI might return (0, 4) which is outside bounds!
    sub_grid.add_location(interior_loc, rel_x, rel_y)  # CRASH
```

**Fix Options**:

1. **Clamp coordinates to bounds** (quick fix):
   ```python
   min_x, max_x, min_y, max_y = sub_grid.bounds
   rel_x = max(min_x, min(max_x, rel_x))  # Clamp to bounds
   rel_y = max(min_y, min(max_y, rel_y))
   ```

2. **Expand bounds dynamically** (flexible):
   ```python
   # Auto-expand bounds to fit all locations
   sub_grid.expand_bounds_to_fit(rel_x, rel_y)
   ```

3. **Skip out-of-bounds locations** (graceful degradation):
   ```python
   if not sub_grid.is_within_bounds(rel_x, rel_y):
       logger.warning(f"Skipping {loc_data['name']}: coords ({rel_x}, {rel_y}) outside bounds")
       continue
   ```

4. **Update AI prompt** (proper fix):
   - Tell AI the coordinate bounds in the prompt
   - Request coordinates within (-3, 3) range
   - Add to `DEFAULT_AREA_GENERATION_PROMPT` in `ai_config.py`

**Recommended Approach**: Combine options 3 and 4:
- Update prompt to specify bounds (reduces failures)
- Skip out-of-bounds as fallback (handles edge cases)
- Log warnings for debugging

**Files to modify**:
- `src/cli_rpg/ai_world.py`: Add bounds checking/clamping in `expand_area()`
- `src/cli_rpg/ai_config.py`: Update area generation prompt with coordinate constraints

---

### Map System Bugs (Discovered via Playtesting)
**Status**: ACTIVE
**Date Discovered**: 2025-12-26

Issues discovered through comprehensive map system playtesting in non-interactive mode:

1. **CRITICAL: Map command fails inside SubGrid locations**
   - **File**: `src/cli_rpg/main.py`, line 1639
   - **Problem**: `render_map()` is called WITHOUT the `sub_grid` parameter, even when player is inside a sub-location
   - **Current code**:
     ```python
     elif command == "map":
         map_output = render_map(game_state.world, game_state.current_location)
         return (True, f"\n{map_output}")
     ```
   - **Impact**: When player enters a dungeon/building interior, running `map` shows "No map available - current location does not have coordinates" instead of the interior map
   - **Root cause**: Sub-locations are stored in `SubGrid`, not in `game_state.world`. The `render_map()` function HAS correct SubGrid rendering (via `_render_sub_grid_map()`), but main.py never passes the `sub_grid` parameter
   - **Fix**: Pass `game_state.current_sub_grid` as third argument:
     ```python
     map_output = render_map(game_state.world, game_state.current_location, game_state.current_sub_grid)
     ```
   - **Priority**: P1 - Core feature completely broken for dungeons/interiors

2. **MEDIUM: Worldmap command fails inside SubGrid locations**
   - **File**: `src/cli_rpg/main.py`, line 1643
   - **Problem**: `render_worldmap()` looks up current location in `world` dict, but SubGrid locations aren't stored there
   - **Current behavior**: Returns "No overworld map available - current location not found."
   - **Expected behavior**: Show overworld map centered on parent location with message "(You are inside [Parent Location])"
   - **Fix in main.py** (preferred):
     ```python
     elif command == "worldmap":
         worldmap_location = game_state.current_location
         if game_state.in_sub_location:
             current_loc = game_state.get_current_location()
             if current_loc.parent_location:
                 worldmap_location = current_loc.parent_location
         worldmap_output = render_worldmap(game_state.world, worldmap_location)
         return (True, f"\n{worldmap_output}")
     ```
   - **Priority**: P2 - Inconvenient but workaround exists (use `exit` first)

**Note**: The `render_map()` function in `map_renderer.py` already has full SubGrid rendering support (`_render_sub_grid_map()` with 13 passing tests). The infrastructure is complete - only the main.py integration is missing.

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

### Non-interactive mode bugs
**Status**: ACTIVE

Issues discovered while playtesting `--non-interactive` mode:

1. ~~**Character creation broken in non-interactive mode**~~ (RESOLVED)
2. ~~**Shop command requires prior NPC interaction**~~ (RESOLVED)
3. ~~**NPC conversation responses are generic**~~ (RESOLVED with AI service)
4. ~~**Enemy attack text duplicates name**~~ (RESOLVED)
5. ~~**Non-interactive mode skipped AI initialization**~~ (RESOLVED)

---

### Non-interactive mode enhancements
**Status**: ACTIVE (Mostly Complete)

The basic `--non-interactive` mode has been implemented. The following enhancements would improve automated playtesting further:

1. ~~**Structured output for AI parsing**~~ (DONE - JSON output mode)
2. ~~**Comprehensive gameplay logging**~~ (DONE - `--log-file` option)
3. ~~**Session state export**~~ (DONE - `dump-state` command)
4. ~~**Additional automation features**~~ (DONE - `--delay`, `--seed` options)

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

### Procedural quest generation
**Status**: ACTIVE

**Desired features**:
- AI-generated side quests
- Quest templates with procedural elements
- Scaling difficulty
- Quest chains

