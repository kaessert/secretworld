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

3. ~~**Create WorldContext model** (`models/world_context.py`)~~ ✓ Completed (2025-12-26):
   - Created `WorldContext` dataclass with fields: `theme`, `theme_essence`, `naming_style`, `tone`, `generated_at`
   - Added `to_dict()`/`from_dict()` serialization with backward compatibility
   - Added `default(theme)` factory for fallback contexts when AI unavailable
   - Default values for 5 theme types: fantasy, cyberpunk, steampunk, horror, post-apocalyptic
   - Full test coverage (10 tests) in `tests/test_world_context.py`

4. ~~**Create RegionContext model** (`models/region_context.py`)~~ ✓ Completed (2025-12-26):
   - Created `RegionContext` dataclass with fields: `name`, `theme`, `danger_level`, `landmarks`, `coordinates`, `generated_at`
   - Added `to_dict()`/`from_dict()` serialization (coordinates as tuple internally, list for JSON)
   - Added `default(coordinates)` factory for fallback contexts when AI unavailable
   - Default values for 8 terrain types in `DEFAULT_REGION_THEMES`
   - Full test coverage (12 tests) in `tests/test_region_context.py`

5. ~~**Split generation prompts** (`ai_config.py`)~~ ✓ Completed (2025-12-26):
   - Added `DEFAULT_WORLD_CONTEXT_PROMPT`: Generate theme essence (Layer 1, once per world)
   - Added `DEFAULT_REGION_CONTEXT_PROMPT`: Generate region details (Layer 2, per area)
   - Added `DEFAULT_LOCATION_PROMPT_MINIMAL`: Just name/desc/category (Layer 3, per location)
   - Added `DEFAULT_NPC_PROMPT_MINIMAL`: Just NPC list (Layer 4, optional per location)
   - Added 4 new AIConfig fields with serialization support
   - Full test coverage (5 new tests) in `tests/test_ai_config.py`

6. ~~**Update AIService** (`ai_service.py`)~~ ✓ Partially Completed (2025-12-26):
   - ~~Add `generate_world_context()` method~~ ✓ Completed - generates WorldContext with theme_essence, naming_style, and tone
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
1. ~~Increase `max_tokens` for location generation (current: 2000, try: 3000)~~ ✓ Completed (2025-12-26) - Default increased to 3000
2. ~~Add JSON extraction from markdown code blocks~~ ✓ Completed (2025-12-26) - Added `_extract_json_from_response()` to extract JSON from ```json...``` or ```...``` blocks in all 5 parse methods
3. ~~Add try/except with JSON repair for truncated responses~~ ✓ Completed (2025-12-26) - Added `_repair_truncated_json()` method that closes unclosed strings/brackets; integrated into all 5 parse methods
4. ~~Log full AI responses on parse failure for debugging~~ ✓ Completed (2025-12-26) - Added `_log_parse_failure()` helper that logs full response text with DEBUG level; integrated into all 5 parse methods (location, area, enemy, item, quest)

---

### ~~AI Area Generation - Coordinates Outside SubGrid Bounds~~
**Status**: RESOLVED (2025-12-26)

**Problem**: AI area generation was failing when generated locations had coordinates outside SubGrid bounds:

```
AI area generation failed: Coordinates (0, 4) outside bounds (-3, 3, -3, 3)
```

**Solution Implemented**: Combined defense-in-depth approach:
1. **Prompt guidance** (`ai_service.py`): Updated area generation prompt to inform AI about coordinate bounds (-3 to 3 for both x and y)
2. **Runtime bounds checking** (`ai_world.py`): Added `is_within_bounds()` check before adding locations - out-of-bounds locations are skipped with a warning log instead of crashing
3. **Test coverage** (`test_ai_world_subgrid.py`): Added test `test_expand_area_skips_out_of_bounds_locations` to verify graceful degradation

---

### Map System Bugs (Discovered via Playtesting)
**Status**: ACTIVE
**Date Discovered**: 2025-12-26

Issues discovered through comprehensive map system playtesting in non-interactive mode:

1. ~~**CRITICAL: Map command fails inside SubGrid locations**~~ (RESOLVED 2025-12-26)
   - Fixed in `src/cli_rpg/main.py` - now passes `game_state.current_sub_grid` to `render_map()`
   - Test added: `test_map_command_inside_subgrid_shows_interior_map`

2. ~~**MEDIUM: Worldmap command fails inside SubGrid locations**~~ (RESOLVED 2025-12-26)
   - Fixed in `src/cli_rpg/main.py` - now detects `in_sub_location` and uses `parent_location` to center the worldmap
   - Test added: `test_worldmap_command_inside_subgrid_uses_parent_location`

**Note**: Both map issues are now resolved. The `render_map()` and `render_worldmap()` functions fully support SubGrid locations.

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

**Files to modify**:
- `src/cli_rpg/dreams.py`: Add cooldown logic, reduce rates
- `src/cli_rpg/game_state.py`: Track `last_dream_time`
- `src/cli_rpg/camping.py`: Reduce dream rate during camp

---

### ~~Class-specific combat abilities show "Unknown command" outside combat~~
**Status**: RESOLVED (2025-12-26)

**Problem**: When a player used class-specific combat abilities (fireball, ice_bolt, heal, bash, bless, smite, hide) outside of combat, they received "Unknown command. Type 'help' for a list of commands." instead of the clearer "Not in combat." message that basic combat commands give.

**Solution Implemented**:
- Extended the combat command check in `handle_exploration_command()` to include class-specific abilities
- Added `fireball`, `ice_bolt`, `heal`, `bash`, `bless`, `smite`, `hide` to the combat commands list
- All now correctly return "Not in combat." when used outside combat
- Added comprehensive test coverage in `test_main_coverage.py`

---

### Talk command fails in SubGrid sublocations
**Status**: ACTIVE
**Date Discovered**: 2025-12-26

**Problem**: The `talk` command does not find NPCs when inside SubGrid sublocations. Despite `look` showing NPCs present (e.g., "NPCs: Merchant"), the `talk` command returns "There are no NPCs here to talk to."

**Root Cause**: In `src/cli_rpg/main.py` line 1154, the talk command uses:
```python
location = game_state.world.get(game_state.current_location)
```

This looks up the location from the main `world` dictionary, but SubGrid sublocations are stored in `game_state.current_sub_grid`, not in `world`. So for sublocations, `world.get()` returns `None`.

**Steps to Reproduce**:
1. Start new game without AI (to use default world with sublocations)
2. At Town Square, use `enter Market` to enter Market District sublocation
3. Use `look` - shows "NPCs: Merchant"
4. Use `talk Merchant` - returns "There are no NPCs here to talk to."

**Fix**: Replace:
```python
location = game_state.world.get(game_state.current_location)
```

With:
```python
location = game_state.get_current_location()
```

The `get_current_location()` method properly handles both overworld locations (in `world`) and sublocations (in `current_sub_grid`).

**Files to modify**:
- `src/cli_rpg/main.py`: Line 1154 in the `talk` command handler

---

### Procedural quest generation
**Status**: ACTIVE

**Desired features**:
- AI-generated side quests
- Quest templates with procedural elements
- Scaling difficulty
- Quest chains

