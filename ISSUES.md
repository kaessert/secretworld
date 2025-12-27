## Active Issues

---

### ✅ RESOLVED: Separate Terrain Generation from Content Generation
**Status**: RESOLVED
**Date Added**: 2025-12-26
**Date Resolved**: 2025-12-26

**Resolution**: Investigation revealed this was **already implemented correctly** in the codebase. The AI service already generates content only (name, description, category, NPCs) without connections. Only 5 obsolete tests in `tests/test_ai_world_generation.py` needed updating to reflect the current correct behavior.

**Architecture (Already Correct)**:
- `ai_config.py`: Both `DEFAULT_LOCATION_PROMPT` and `DEFAULT_LOCATION_PROMPT_MINIMAL` have no references to `connections`
- `ai_service.py`: `_parse_location_response()` returns only `{name, description, category, npcs}` - no connections
- `ai_world.py`: Uses grid-based expansion with all cardinal directions queued from each location

**Tests Updated**:
- `test_expand_world_preserves_ai_suggested_dangling_connections` → `test_expand_world_adds_dangling_connections`
- `test_create_ai_world_queues_suggested_connections` → `test_create_ai_world_queues_cardinal_directions`
- `test_expand_world_adds_bidirectional_connection_to_existing_target` → `test_expand_world_adds_bidirectional_connection`
- `test_expand_world_preserves_existing_reverse_connection` → `test_expand_world_preserves_source_existing_connections`
- `test_create_ai_world_skips_suggested_name_already_in_grid` → `test_create_ai_world_skips_occupied_positions`

**Verification**: All 3573 tests pass, including 11 terrain content separation tests and 54 AI world generation tests.

---

### ✅ RESOLVED: Connections Inferred from Terrain Passability
**Status**: RESOLVED
**Date Added**: 2025-12-26
**Date Resolved**: 2025-12-27

**Resolution**: All `Location.connections` field references have been removed from the codebase. Movement is now determined by coordinate adjacency and terrain passability via the WFC ChunkManager. All 3573 tests pass.

**Problem**: Location connections are currently stored explicitly and managed separately from terrain. Connections should be INFERRED at runtime from terrain passability - if two adjacent tiles are both passable, the player can move between them. Period.

**Current (Wrong)**:
```python
# Connections stored on Location objects
location.connections = {"north": "Forest Path", "east": "Mountain Base"}

# Movement checks connection dict
if direction in current_location.connections:
    move_to(connections[direction])
```

**Target (Correct)**:
```python
# Terrain determines passability
PASSABLE_TERRAIN = {"plains", "forest", "road", "village", "hills", "swamp", "desert", "cave_entrance"}
IMPASSABLE_TERRAIN = {"water", "mountain", "wall", "void"}

# Movement checks adjacent terrain
def can_move(from_coords, direction):
    to_coords = from_coords + DIRECTION_OFFSETS[direction]
    terrain = chunk_manager.get_tile(*to_coords)
    return terrain in PASSABLE_TERRAIN
```

**Key Principles**:

1. **No explicit connections** - Remove `connections` dict from Location model
2. **Terrain is truth** - `ChunkManager.get_tile(x, y)` determines what's at each coordinate
3. **Passability is binary** - Each terrain type is either passable or impassable
4. **Movement is implicit** - Player can always move to adjacent passable terrain

**Terrain Classification**:

| Passable | Impassable |
|----------|------------|
| plains | water |
| forest | mountain (peaks) |
| road | wall |
| village | void |
| hills | cliff |
| swamp | |
| desert | |
| cave_entrance | |
| ruins | |

**Implementation**:

```python
# In world_tiles.py
PASSABLE_TERRAIN: frozenset[str] = frozenset({
    "plains", "forest", "road", "village", "hills",
    "swamp", "desert", "cave_entrance", "ruins"
})

def is_passable(terrain: str) -> bool:
    return terrain in PASSABLE_TERRAIN

def get_valid_moves(chunk_manager: ChunkManager, x: int, y: int) -> list[str]:
    """Return list of valid directions from current position."""
    valid = []
    for direction, (dx, dy) in DIRECTION_OFFSETS.items():
        terrain = chunk_manager.get_tile(x + dx, y + dy)
        if is_passable(terrain):
            valid.append(direction)
    return valid
```

**Required Changes**:

1. **Remove `connections` from Location model**
   - Delete `connections: dict[str, str]` field
   - Remove all connection management code
   - Remove bidirectional connection logic

2. ~~**Add passability to world_tiles.py**~~ ✅ COMPLETE (2025-12-26)
   - ✅ `PASSABLE_TERRAIN` frozenset (8 types: forest, plains, hills, desert, swamp, beach, foothills, mountain)
   - ✅ `IMPASSABLE_TERRAIN` frozenset (water)
   - ✅ `DIRECTION_OFFSETS` dict (north, south, east, west)
   - ✅ `is_passable(terrain)` function with safe default for unknown terrain
   - ✅ `get_valid_moves(chunk_manager, x, y)` function returning sorted valid directions
   - ✅ 18 tests in `tests/test_terrain_passability.py`

3. **Update movement in game_state.py / main.py**
   - Replace connection lookup with terrain passability check
   - Use coordinates + direction offset to find target
   - Query ChunkManager for target terrain

4. **Update map rendering**
   - Show passable directions based on terrain, not connections
   - Impassable terrain shown differently (e.g., `~` for water, `^` for mountains)

**Files to Modify**:
- `src/cli_rpg/models/location.py`: Remove `connections` field
- `src/cli_rpg/world_tiles.py`: Add passability sets and functions
- `src/cli_rpg/game_state.py`: Use terrain for movement validation
- `src/cli_rpg/main.py`: Update `go` command to use terrain
- `src/cli_rpg/map_renderer.py`: Derive exits from terrain
- `src/cli_rpg/world.py`: Remove connection generation logic

**Success Criteria**:
- [x] `Location.connections` field removed entirely ✅
- [x] `PASSABLE_TERRAIN` and `IMPASSABLE_TERRAIN` defined in world_tiles.py ✅
- [x] `is_passable()` and `get_valid_moves()` functions implemented ✅
- [x] `go <direction>` checks terrain passability, not connection dict ✅ (2025-12-26 - Step 3 complete)
- [x] Map shows valid exits based on adjacent terrain types ✅ (resolved per WFC exit display fix)
- [x] No code references "connections" for movement logic ✅

---

### ✅ RESOLVED: AI Location Generation Failures - JSON Parsing & Token Limits
**Status**: RESOLVED
**Date Resolved**: 2025-12-27

**Resolution**: The layered context architecture is fully implemented and integrated. The `move()` method in `game_state.py` now correctly passes both `world_context` and `region_context` to `expand_area()` for AI-generated locations. All 66 related tests pass.

**Original Problem**: AI location generation frequently failed with JSON parsing errors:

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

**Completed (2025-12-27)**:
- ✓ Full integration verified: `move()` passes `world_context` and `region_context` to `expand_area()`
- ✓ 4 integration tests in `tests/test_layered_context_integration.py` confirm context passing
- ✓ All 66 related tests pass

---

### WFC World Generation Overhaul
**Status**: ✅ CORE COMPLETE (All 4 items done)
**Priority**: CRITICAL - BLOCKS IMMERSION

Transform the world generation system to match traditional RPG map design: **vast stretches of traversable terrain with occasional points of interest**.

#### The Problem: Every Tile is a "Location"

**Current behavior breaks immersion.** Walking one tile in any direction spawns a new AI-generated named location with unique NPCs. This creates a world where:

- Every single step is a "destination" - nothing feels like travel
- The world feels cluttered and artificial
- AI generation costs explode (every tile = API call)
- No sense of scale or distance between meaningful places

**Compare to classic RPGs:**

| Game | Overworld Design |
|------|------------------|
| **Zelda/Final Fantasy** | Large overworld map, towns/dungeons are sub-areas you enter |
| **Skyrim** | Vast wilderness, cities/caves are distinct enterable locations |
| **Baldur's Gate** | Region maps with named areas as clickable destinations |
| **Our current system** | ❌ Every tile is a named location with NPCs |

#### Target Architecture: Sparse Overworld + Dense Sub-locations

```
┌─────────────────────────────────────────────────────────────────┐
│  OVERWORLD (95% of tiles)                                       │
│  ─────────────────────────────────────────────────────────────  │
│  • Generic terrain: "Dense Forest", "Rolling Plains", "Rocky    │
│    Hillside" - NO unique names, NO NPCs, NO AI generation       │
│  • Template-based: instant generation, zero API cost            │
│  • Purpose: create sense of travel, scale, and journey          │
│  • Player moves freely through passable terrain                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  NAMED LOCATIONS (5% of tiles) - Enterable Sub-areas            │
│  ─────────────────────────────────────────────────────────────  │
│  • Villages: 5-15 interior rooms (inn, shop, houses, square)    │
│  • Cities: 20-50 interior rooms (districts, guilds, palace)     │
│  • Dungeons: 10-30 rooms (corridors, chambers, boss room)       │
│  • Landmarks: 3-5 rooms (shrine, ruins, cave)                   │
│  • Full AI generation: unique names, NPCs, quests, shops        │
│  • Player uses `enter` command to access interior SubGrid       │
└─────────────────────────────────────────────────────────────────┘
```

**Visual comparison:**

```
CURRENT (bad):                    TARGET (good):
┌─────────────────────┐          ┌─────────────────────┐
│ Town │Cave │Temple │          │  .  .  .  .  .  .   │
├──────┼─────┼───────┤          │  .  .  ⌂  .  .  .   │  ⌂ = Village (enter)
│Ruins │Inn  │Shrine │          │  .  .  .  .  .  .   │
├──────┼─────┼───────┤          │  .  ▲  .  .  .  ☠   │  ▲ = Mountain, ☠ = Dungeon
│Grove │Mill │Tower  │          │  .  .  .  .  .  .   │
└─────────────────────┘          └─────────────────────┘
Every tile = named location      Mostly terrain, rare POIs
```

#### Goals

1. ~~**WFC as Default**~~ ✅ COMPLETE (2025-12-26) - Infinite procedural terrain is now the standard experience
2. **Named vs Unnamed Locations** - Most tiles are generic terrain (forest, road, plains), only key POIs get full AI generation
3. **Variable SubGrid Sizes** - Cities with 20+ rooms, dungeons with 50+ chambers, houses with 3 rooms
4. **Layered AI Integration** - WorldContext → RegionContext → Named Location → NPCs

#### 1. Make WFC Default ✅ COMPLETE

**Completed 2025-12-26:**
- ✅ Replaced `--wfc` flag with `--no-wfc` flag (WFC enabled by default)
- ✅ `start_game()` defaults to `use_wfc=True`
- ✅ Wired WFC ChunkManager to `run_json_mode()`
- ✅ Wired WFC ChunkManager to `run_non_interactive()`
- ✅ Extracted `parse_args()` for testability
- ✅ All 47 WFC tests passing

**Usage:**
- `cli-rpg` - Starts with WFC terrain (default)
- `cli-rpg --no-wfc` - Disables WFC, uses fixed world

#### 2. Named vs Unnamed Location System ✅ COMPLETE

**Completed 2025-12-26:**
- ✅ Added `is_named: bool = False` field to Location model with serialization support
- ✅ Added `UNNAMED_LOCATION_TEMPLATES` in `world_tiles.py` with templates for all 9 terrain types
- ✅ Added `get_unnamed_location_template(terrain)` function with fallback to plains
- ✅ Added `NAMED_LOCATION_CONFIG` with base interval (15 tiles) and terrain modifiers
- ✅ Added `should_generate_named_location(tiles_since_named, terrain, rng)` trigger function
- ✅ Updated `generate_fallback_location()` to set `is_named=False`
- ✅ 21 new tests passing (12 in `test_named_locations.py`, 9 in `test_unnamed_templates.py`)

**Concept:**
- **Unnamed locations**: Generic terrain tiles (forest, plains, road, hills) - cheap/instant generation via templates
- **Named locations**: Story-important POIs (towns, dungeons, temples) - full AI generation with context

**Ratio Target:** ~1 named location per 10-20 unnamed tiles (achieved via linear probability curve)

**✅ INTEGRATION COMPLETE (2025-12-27):**

The named location trigger system is now fully wired up and operational.

| Task | Status | Impact |
|------|--------|--------|
| Wire `should_generate_named_location()` into world expansion | ✅ DONE | Sparse world works |
| Track `tiles_since_named` counter in GameState | ✅ DONE | Persists through save/load |
| Use `get_unnamed_location_template()` for unnamed tiles | ✅ DONE | Most tiles use templates |
| Skip NPC generation for unnamed locations | ✅ DONE | NPCs only in named sub-locations |
| Make named locations enterable SubGrids (not overworld tiles) | ❌ NOT DONE | Future enhancement |

**How it works:**
1. When player moves to unexplored tile → `should_generate_named_location()` is called
2. If FALSE → uses template (`is_named=False`), no AI call, no NPCs, generic terrain description
3. If TRUE → generates named location with AI or fallback (`is_named=True`)
4. `tiles_since_named` counter persists across save/load cycles

#### 3. Variable SubGrid Sizes ✅ COMPLETE

**Completed 2025-12-27:**
- ✅ Added `SUBGRID_BOUNDS` config mapping categories to bounds tuples
- ✅ Added `get_subgrid_bounds(category)` helper with case-insensitive lookup and default fallback
- ✅ Updated `expand_area()` to use dynamic bounds based on entry location category
- ✅ 15 new tests in `tests/test_variable_subgrid_sizes.py`

**Size Categories:**

| Category | Bounds | Grid Size |
|----------|--------|-----------|
| house, shop, cave | `(-1, 1, -1, 1)` | 3x3 (tiny) |
| tavern, ruins, settlement | `(-2, 2, -2, 2)` | 5x5 (small) |
| dungeon, forest, temple, wilderness | `(-3, 3, -3, 3)` | 7x7 (medium) |
| town, village | `(-5, 5, -5, 5)` | 11x11 (large) |
| city | `(-8, 8, -8, 8)` | 17x17 (huge) |
| default (fallback) | `(-2, 2, -2, 2)` | 5x5 (small) |

#### 4. Layered AI Integration ✅ COMPLETE

| Generation Event | Layers Used | Cost |
|------------------|-------------|------|
| Unnamed location | None | Free (template) |
| Named location (single) | 1, 2, 3, 4 | 2 AI calls |
| Named area (SubGrid) | 1, 2, 3+, 4+ | 3+ AI calls |

**Completed 2025-12-27:**
- ✅ Added `generate_area_with_context()` method to AIService
- ✅ Updated `expand_area()` to use layered generation when contexts provided
- ✅ 9 new tests in `tests/test_generate_area_with_context.py`

**How it works:**
1. `generate_area_with_context()` takes WorldContext (Layer 1) and RegionContext (Layer 2) as inputs
2. Generates area layout coordinates using `_generate_area_layout()`
3. Calls `generate_location_with_context()` for each location (Layer 3)
4. Calls `generate_npcs_for_location()` for each location (Layer 4)
5. Returns list of location dicts with `relative_coords`, `name`, `description`, `category`, `npcs`

#### Files to Modify

| File | Changes |
|------|---------|
| `main.py` | Flip WFC default, wire to all modes |
| `models/location.py` | Add `is_named`, `terrain_type` fields |
| `world_tiles.py` | Add unnamed location templates |
| `ai_config.py` | Add SubGrid size config, area prompt |
| `ai_service.py` | Add `generate_area_with_context()` |
| `ai_world.py` | Use dynamic bounds, layered generation |
| `game_state.py` | Check `is_named` before AI calls |

---

### Map System Bugs (Discovered via Playtesting)
**Status**: ACTIVE
**Date Discovered**: 2025-12-26

Issues discovered through comprehensive map system playtesting in non-interactive mode.

**Note**: Map command issues inside SubGrid locations are resolved.

---

### ✅ RESOLVED: OVERWORLD & SUB-LOCATION REWORK - Hierarchical World System
**Status**: RESOLVED
**Date Resolved**: 2025-12-27

**Problem**: The current flat world grid doesn't support meaningful world structure.

**Resolution**: All features fully implemented:
- Location model hierarchy fields implemented
- Town Square, Forest, Millbrook Village, Ironhold City, Abandoned Mines all implemented with sub-locations
- Enter/exit commands working
- AI world generation respects hierarchy
- Safe zone encounters working
- **Vertical dungeon navigation**: `up`/`down` commands now work in SubGrid locations with z-coordinate support
  - Dungeons extend downward (z<0), towers extend upward (z>0)
  - 6-tuple bounds format: `(min_x, max_x, min_y, max_y, min_z, max_z)`
  - 37 new tests in `tests/test_vertical_navigation.py`

---

### Non-interactive mode enhancements
**Status**: ACTIVE

**Completed**:
- ✅ RNG seeds included in logs for reproducibility (2025-12-27)
  - `session_info` JSON output includes seed
  - Log files include seed in `session_start` entries
  - `--seed` flag for reproducible runs

**Future enhancements**:
- Log AI-generated content for review
- Enable session replay from logged state

---

### ✅ RESOLVED: Overworld map with cities and sub-locations
**Status**: RESOLVED
**Date Resolved**: 2025-12-27

Players want a more sophisticated map system with hierarchical locations.

**Implemented**:
- `map` command shows current layer, `worldmap` shows overworld
- Enter/exit commands for city/dungeon navigation
- SubGrid system for interior locations
- Fast travel between discovered overworld locations (`travel` command)
- Travel time/random encounters on overworld (Manhattan distance ÷ 4 hours, 15% encounter chance/hour)

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
- Quest-based reputation changes (faction-affiliated quests reward/penalize reputation on completion)
- Reputation requirements for quest acceptance
- Faction-gated content: NPCs and locations can require minimum reputation to access (`faction_content.py`)

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
**Status**: ACTIVE (Partial)

**Implemented**:
- Secret discovery via `search` command (PER-based checks)
- Reward system for discovered secrets:
  - Hidden treasure: awards gold and items
  - Traps: DEX-based disarm (10 XP) or damage
  - Lore hints: 5 XP reward
  - Hidden doors: reveals new exits via `temporary_exits`

**Remaining**:
- Hidden rooms and secret passages (full SubGrid integration)
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

### ✅ RESOLVED: Sleep sequence borders too wide
**Status**: RESOLVED
**Date Added**: 2025-12-27
**Date Resolved**: 2025-12-27

**Problem**: Dream sequence decorative borders (`══`) were excessively wide, spanning 200+ characters and breaking terminal display.

**Resolution**: Added `MAX_FRAME_WIDTH = 80` constant to `frames.py` and modified `frame_text()` to cap width at 80 characters. All frame borders and content now stay within 80 characters.

**Files Modified**:
- `src/cli_rpg/frames.py`: Added `MAX_FRAME_WIDTH = 80`, capped width in `frame_text()`
- `tests/test_frames.py`: Added `TestFrameWidthCapping` class with 4 tests
- `tests/test_dreams.py`: Updated 4 tests to use substring matching for wrapped content

---

### ✅ RESOLVED: Dream sequences trigger too frequently
**Status**: RESOLVED
**Date Added**: 2025-12-27
**Date Resolved**: 2025-12-27

**Problem**: Players reported dreams happened too often, becoming annoying rather than atmospheric.

**Resolution**: Implemented the following fixes:

1. **Reduced base trigger rates**:
   - `rest`: 25% → 10% (`DREAM_CHANCE` constant)
   - `camp`: 40% → 15% (`CAMP_DREAM_CHANCE` constant)

2. **Added cooldown between dreams**:
   - Added `DREAM_COOLDOWN_HOURS = 12` constant
   - Dreams are blocked if less than 12 game hours have passed since the last dream
   - `last_dream_hour` tracked in GameState and persists across save/load

3. **Added player control**:
   - `rest --quick` or `rest -q` flag skips dream check entirely

**Files Modified**:
- `src/cli_rpg/dreams.py`: Constants and cooldown logic
- `src/cli_rpg/game_state.py`: `last_dream_hour` attribute and serialization
- `src/cli_rpg/main.py`: `rest --quick` flag, cooldown params
- `src/cli_rpg/camping.py`: Uses shared `CAMP_DREAM_CHANCE`, cooldown params

**Tests Added**: 16 new dream tests, 3 new camping tests (all 3635 tests pass)

---

### ✅ RESOLVED: Tiredness stat for realistic sleep/rest mechanics
**Status**: RESOLVED
**Date Added**: 2025-12-26
**Date Resolved**: 2025-12-27

**Problem**: Falling asleep during rest was random, which felt arbitrary and unrealistic.

**Resolution**: The Tiredness stat system is now fully implemented. Tiredness (0-100) tracks player fatigue and determines when the player can fall asleep.

**Implementation Summary**:
- ✅ Tiredness model (`src/cli_rpg/models/tiredness.py`) with range 0-100, threshold warnings, sleep quality calculation
- ✅ Character integration: `tiredness` attribute, attack/perception penalties at 80+
- ✅ GameState integration: movement increases tiredness by 3 per move
- ✅ Combat integration: tiredness increases by 5 base + 1 per combat turn on victory
- ✅ Rest/Camp integration: reduces tiredness based on sleep quality (light: 25, normal: 50, deep: 80)
- ✅ Dream integration: dreams blocked when tiredness < 30, dream chance modified by tiredness level
- ✅ Full serialization support with backward compatibility
- ✅ 31 tests covering all tiredness functionality

**Tiredness Effects**:
- **Movement**: +3 tiredness per move
- **Combat**: +5 base + 1 per turn on victory
- **Warnings**: "Feeling tired" at 60, "Exhausted" at 80, "Completely exhausted" at 100
- **Sleep Availability**: Cannot sleep when tiredness < 30
- **Sleep Quality**: Light (<60), Normal (60-79), Deep (80+)
- **Attack Penalty**: -10% damage at 80+ tiredness
- **Perception Penalty**: -10% perception at 80+ tiredness

---

### WFC Playtesting Issues (2025-12-26)
**Status**: ACTIVE

Issues discovered during WFC mode playtesting (WFC is now enabled by default; updated 2025-12-26):

#### HIGH PRIORITY BUGS

1. ~~**Shop price inconsistency**~~ ✅ RESOLVED (2025-12-26)
   - Shop display now shows adjusted prices (CHA, faction, persuade, haggle modifiers)
   - Matches the actual purchase price shown in buy command errors

2. ~~**ASCII art first line loses leading whitespace**~~ ✅ RESOLVED (2025-12-26)
   - Fixed: Changed `.strip()` to `.rstrip()` in 5 locations to preserve leading spaces
   - Files modified: `location.py` (2), `combat.py` (2), `main.py` (1)
   - Tests added: `tests/test_ascii_art.py` - `TestAsciiArtDisplayPreservesIndentation` (5 tests)

3. ~~**Shop command doesn't work with AI-generated merchants in SubGrid locations**~~ ✅ RESOLVED (2025-12-26)
   - Fixed: AI-generated NPCs with merchant-related names now work correctly with `shop` command
   - **Solution implemented**:
     - Added `MERCHANT_KEYWORDS` set (merchant, trader, vendor, shopkeeper, seller, dealer)
     - NPCs with matching keywords in their name are auto-assigned `role="merchant"`
     - Merchants automatically receive a terrain-aware default shop with thematically appropriate items (e.g., Mountain Supplies with climbing gear, Swamp Wares with antidotes, etc.)
   - Files modified: `src/cli_rpg/ai_world.py` (added `_create_default_merchant_shop()`, `TERRAIN_SHOP_ITEMS`, `TERRAIN_SHOP_NAMES`, `MERCHANT_KEYWORDS`, updated `_create_npcs_from_data()`)

4. ~~**Caravan world event doesn't provide shop access**~~ ✅ RESOLVED (2025-12-26)
    - Fixed: `shop` command now checks for active caravan events at current location
    - When a CARAVAN event is active, provides temporary shop with exotic items:
      - Exotic Spices (50g), Traveler's Map (75g), Foreign Elixir (100g), Rare Gemstone (200g), Antidote (40g)
    - Files modified: `world_events.py` (added `get_caravan_shop()`), `main.py` (shop command handler)

5. ~~**"Can't go that way" even though map shows valid exits**~~ ✅ RESOLVED (2025-12-26)
    - Fixed: Exit display now filters by WFC terrain passability at display time
    - Added `get_filtered_directions(chunk_manager)` method to Location model
    - Updated `look`, `map`, and fallback location generation to use filtered directions
    - Files modified: `location.py`, `game_state.py`, `map_renderer.py`, `world.py`, `main.py`
    - 8 new tests in `tests/test_wfc_exit_display.py`

#### MEDIUM PRIORITY BUGS

1. ~~**Exits disappear/change when revisiting locations**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: `get_filtered_directions()` now uses terrain-based exits for overworld (via WFC `get_valid_moves()`)
   - SubGrid interiors continue to use location-based logic since they have predefined bounded layouts
   - 3 new tests added in `tests/test_wfc_exit_display.py`

2. ~~**Wild Boar ASCII art is a cat**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Added boar-specific ASCII art with pig snout (`(  oo  )`) and hooves in `combat.py`
   - `get_fallback_ascii_art()` now checks for "boar" before falling through to generic beast matching
   - Files modified: `src/cli_rpg/combat.py`, `tests/test_ascii_art.py`

3. ~~**Inconsistent shop pricing message**~~ ✅ RESOLVED (2025-12-27)
   - Already fixed as part of shop price consistency fix on 2025-12-26
   - Shop display and buy command now use identical price calculation logic
   - Regression test added in `tests/test_shop_price_consistency.py`

4. ~~**Load character screen is overwhelming**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Load screen now groups autosaves into a single collapsed entry
   - Fixed: Manual saves limited to 15 most recent with "... and X older saves" hint
   - Fixed: "(saved: unknown)" replaced with human-readable timestamps via file mtime fallback
   - Fixed: `autosave_` prefix stripped from display names for cleaner presentation
   - **Files modified**: `persistence.py` (timestamp formatting, mtime fallback), `main.py` (display logic)

5. ~~**Can enter any sub-location instead of designated entry point**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Location descriptions now show only the entry point (location with `is_exit_point=True`)
   - Fixed: `enter` command validates that only entry point locations can be entered directly
   - Non-entry-point rooms are now blocked with a helpful error message directing players to the entry point
   - **Files modified**:
     - `src/cli_rpg/models/location.py`: `get_layered_description()` and `__str__()` show only entry point
     - `src/cli_rpg/game_state.py`: `enter()` validates entry point access
   - 9 new tests in `tests/test_enter_entry_point.py`

#### LOW PRIORITY / UX ISSUES

1. ~~**Combo system unclear**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Combo notifications now include usage hint (e.g., "COMBO AVAILABLE: Frenzy! (Type 'frenzy' to use)")
   - File modified: `src/cli_rpg/combat.py`

2. ~~**Confusing "exit" message when not in sub-location**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Changed message from "You're not inside a landmark." to "You're not inside a building or dungeon. Use 'go <direction>' to travel."
   - Files modified: `src/cli_rpg/game_state.py`, `tests/test_game_state.py`

3. ~~**"bye" command outside of talk mode is confusing**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Now shows "The 'bye' command ends conversations. Use it while talking to an NPC."
   - No longer incorrectly suggests "buy" command
   - Files modified: `src/cli_rpg/main.py`, `tests/test_main.py`

4. ~~**"accept" could auto-accept single quest**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Bare `accept` command now auto-accepts when NPC has exactly one available quest
   - When 0 quests available: Shows "X doesn't offer any quests."
   - When 2+ quests available: Shows "Accept what? Available: Quest1, Quest2, ..."
   - Files modified: `src/cli_rpg/main.py` (lines 1595-1615)
   - Tests added: 4 new tests in `tests/test_npc_quests.py`

5. ~~**Terrain blocking message varies**~~ ✅ PARTIALLY RESOLVED (2025-12-27)
   - SubGrid messages now consistent:
     - Bounds exceeded: "You can't go that way - you've reached the edge of this area."
     - Wall/empty cell: "The path is blocked by a wall."
   - Overworld impassable terrain: "The {terrain} ahead is impassable."
   - Error/fallback: "The path is blocked by an impassable barrier."

#### DESIGN OBSERVATIONS

1. ~~**Shop price shows base, not reputation-adjusted price**~~ ✅ RESOLVED (2025-12-26)
   - Shop now displays fully adjusted prices (CHA, faction, persuade, haggle modifiers)

2. ~~**Rest command output**~~ ✅ RESOLVED (2025-12-27)
   - Fixed: Rest now shows explicit status for both HP and stamina when already full
   - Example: "HP: 100/100 (already full)" instead of silently omitting the stat

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
**Status**: ✅ CORE VALIDATION COMPLETE (TALK, KILL, COLLECT, EXPLORE all validated)
**Date Added**: 2025-12-26

**Problem**: Quest generation and world generation were completely decoupled, creating "impossible quests" where targets didn't exist in the game world.

**Resolution**: All four major quest objective types now have validation:
- KILL quests: Validated against `VALID_ENEMY_TYPES` in `combat.py`
- COLLECT quests: Validated against `OBTAINABLE_ITEMS` in `ai_service.py`
- EXPLORE quests: Validated against `valid_locations` from world keys
- TALK quests: Validated against `valid_npcs` from world NPCs

Invalid targets raise `AIGenerationError`, forcing quest regeneration until a valid target is used.

#### Root Cause Analysis

Quest generation (`ai_service.py:1639-1689`) receives minimal context:
- Theme, NPC name, player level, location name
- **NO** list of existing locations
- **NO** list of spawnable enemy types
- **NO** list of existing NPCs
- **NO** list of obtainable items

The AI generates arbitrary target strings that may not exist anywhere in the game.

#### Issue 1: EXPLORE Quest Targets Don't Match World Locations

**Severity**: ✅ RESOLVED (2025-12-26)

**Solution Implemented**:
- Added `valid_locations: Optional[set[str]]` parameter to `generate_quest()` and `_parse_quest_response()` in `ai_service.py`
- When `objective_type == "explore"` and `valid_locations` is provided, validates that `target.lower()` exists in the set
- Invalid targets raise `AIGenerationError`, forcing quest regeneration with a valid location
- `main.py` passes `valid_locations` (from `game_state.world.keys()`) when generating quests via the talk command
- Case-insensitive matching maintains consistency with KILL quest validation
- 7 new tests in `tests/test_explore_quest_validation.py` verify the validation

**Original Problem**:
```
Quest: "Explore the Obsidian Cathedral"
World: Contains "Town Square", "Dark Forest", "Mountain Pass"
Result: IMPOSSIBLE - "Obsidian Cathedral" doesn't exist
```

#### Issue 2: KILL Quest Targets Don't Match Spawnable Enemies

**Severity**: ✅ RESOLVED (2025-12-26)

**Solution Implemented**:
- Added `VALID_ENEMY_TYPES` frozenset in `combat.py` containing all spawnable enemy names
- Added validation in `ai_service.py:_parse_quest_response()` that rejects KILL quests with invalid targets
- When target is invalid, raises `AIGenerationError` forcing quest regeneration with valid target
- 15 new tests in `tests/test_quest_validation.py` verify the validation

**Valid enemy types** (case-insensitive):
- Forest: Wolf, Bear, Wild Boar, Giant Spider
- Cave: Bat, Goblin, Troll, Cave Dweller
- Dungeon: Skeleton, Zombie, Ghost, Dark Knight
- Mountain: Eagle, Goat, Mountain Lion, Yeti
- Village: Bandit, Thief, Ruffian, Outlaw
- Default: Monster, Creature, Beast, Fiend

#### Issue 3: TALK Quest Targets Don't Match World NPCs

**Severity**: ✅ RESOLVED (2025-12-26)

**Solution Implemented**:
- Added `valid_npcs: Optional[set[str]]` parameter to `generate_quest()` and `_parse_quest_response()` in `ai_service.py`
- When `objective_type == "talk"` and `valid_npcs` is provided, validates that `target.lower()` exists in the set
- Invalid targets raise `AIGenerationError`, forcing quest regeneration with a valid NPC
- `main.py` collects valid NPC names from all locations when generating quests via the talk command
- Case-insensitive matching maintains consistency with other quest validations
- 8 new tests in `tests/test_talk_quest_validation.py` verify the validation

**Original Problem**:
```
Quest: "Talk to Elder Mage Aldous"
NPCs in World: Merchant, Guard, Hermit, Town Elder
Result: IMPOSSIBLE - "Elder Mage Aldous" doesn't exist
```

#### Issue 4: COLLECT Quest Targets Don't Match Obtainable Items

**Severity**: ✅ RESOLVED (2025-12-26)

**Solution Implemented**:
- Added `OBTAINABLE_ITEMS` frozenset in `ai_service.py` containing 100+ obtainable item names from shops, loot drops, foraging, hunting, gathering, and crafting
- Added validation in `ai_service.py:_parse_quest_response()` that rejects COLLECT quests with invalid targets
- When target is invalid, raises `AIGenerationError` forcing quest regeneration with valid target
- Case-insensitive matching (lowercases target before checking)
- 16 new tests in `tests/test_collect_quest_validation.py`

**Original Problem**:
```
Quest: "Collect 3 Dragon Scales"
Obtainable Items: Health Potion, Iron Sword, Leather Armor (shops + drops)
Result: IMPOSSIBLE - "Dragon Scales" can't be obtained
```

#### Risk Assessment

| Objective Type | Impossible Quest Risk | Reason |
|----------------|----------------------|--------|
| COLLECT | ✅ 0% | Validated against `OBTAINABLE_ITEMS` (fixed 2025-12-26) |
| KILL | ✅ 0% | Validated against `VALID_ENEMY_TYPES` (fixed 2025-12-26) |
| TALK | ✅ 0% | Validated against `valid_npcs` from world (fixed 2025-12-26) |
| EXPLORE | ✅ 0% | Validated against known locations (fixed 2025-12-26) |

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

1. ~~**Immediate**: Add `VALID_ENEMY_TYPES` constant and validate KILL quests (most common type)~~ ✅ DONE (2025-12-26)
2. ~~**Immediate**: Validate EXPLORE quests against known location names~~ ✅ DONE (2025-12-26)
3. ~~**Short-term**: Pass obtainable items list to quest generation for COLLECT quests~~ ✅ DONE (2025-12-26) - Validation via `OBTAINABLE_ITEMS` frozenset
4. ~~**Short-term**: Validate TALK quests against existing NPC names~~ ✅ DONE (2025-12-26) - Validation via `valid_npcs` parameter
5. **Medium-term**: Implement context-aware generation with all world state
6. **Long-term**: World-creating quests that guarantee completability

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

**1. Quest Context Integration ✅ COMPLETE (2025-12-27)**

WorldContext and RegionContext are now passed to quest generation:
- `generate_quest()` accepts optional `world_context` and `region_context` parameters
- Quest prompts include theme essence, tone, region theme, and danger level
- Quests now match world/region context for thematic consistency
- All 7 new integration tests pass

**2. Quest Chains & Prerequisites ✅ COMPLETE (2025-12-27)**

Quest chain and prerequisite support is now implemented:

```python
@dataclass
class Quest:
    # ... existing fields ...
    chain_id: Optional[str] = None  # Groups related quests (e.g., "goblin_war")
    chain_position: int = 0  # Order in chain (0 = standalone, 1 = first, etc.)
    prerequisite_quests: List[str] = field(default_factory=list)  # Must be COMPLETED first
    unlocks_quests: List[str] = field(default_factory=list)  # Unlocked on completion
```

**Features implemented:**
- `prerequisites_met(completed_quests)` method validates completion requirements (case-insensitive)
- Quest acceptance blocks with helpful message if prerequisites not met
- `quest` command shows chain info ("Chain: X (Part N)") and prerequisites when present
- Full serialization support with backward compatibility for existing saves

**3. Faction Integration ✅ COMPLETE (2025-12-27)**

Quest-faction integration is now fully implemented:
- `faction_affiliation: Optional[str]` - The faction this quest is associated with
- `faction_reward: int` - Reputation gained with affiliated faction on completion
- `faction_penalty: int` - Reputation lost with rival faction on completion
- `required_reputation: Optional[int]` - Minimum reputation with faction required to accept quest

Completing faction-affiliated quests now properly adjusts reputation with both the affiliated faction and its rival (using `FACTION_RIVALRIES` mapping). NPCs refuse to give quests if player reputation is below the required threshold.

**4. Quest Difficulty ✅ COMPLETE (2025-12-27)**

Fully implemented:
- `QuestDifficulty` enum: TRIVIAL, EASY, NORMAL, HARD, DEADLY
- `difficulty` and `recommended_level` fields on Quest dataclass
- Validation: recommended_level must be ≥1
- Full serialization with backward compatibility
- Quest journal shows difficulty icons (., -, ~, !, !!)
- Quest details show "Difficulty: X (Recommended: Lv.Y)"
- NPC quest offers show difficulty in brackets
- AI quest generation includes difficulty based on region danger level
- AI response parsing with backward-compatible defaults
- 11 model tests + 14 UI/AI integration tests

**5. Time-Sensitive Quests ✅ COMPLETE (2025-12-27)**

Implemented time-limited quests that expire after a set number of game hours:

```python
@dataclass
class Quest:
    time_limit_hours: Optional[int] = None  # Hours until quest expires (None = no limit)
    accepted_at: Optional[int] = None  # Game hour when quest was accepted

    def is_expired(self, current_game_hour: int) -> bool:
        if self.time_limit_hours is None:
            return False
        return (current_game_hour - self.accepted_at) >= self.time_limit_hours

    def get_time_remaining(self, current_game_hour: int) -> Optional[int]:
        # Returns hours remaining, or None if no time limit
```

**Features implemented:**
- Quest model fields: `time_limit_hours`, `accepted_at`
- `is_expired()` and `get_time_remaining()` methods
- Expired quests auto-fail when time advances (via `check_expired_quests()` in `move()`)
- Journal shows countdown: "(Xh left)" or "(EXPIRED!)"
- Quest details show: "Time Remaining: X hours" or "EXPIRED!"
- 29 tests covering all time limit functionality

**6. Branching Objectives ✅ COMPLETE (2025-12-27)**

Implemented alternative completion paths for quests, enabling moral complexity and player choice.

```python
@dataclass
class QuestBranch:
    id: str
    name: str
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    current_count: int = 0
    description: str = ""
    faction_effects: Dict[str, int] = field(default_factory=dict)
    gold_modifier: float = 1.0
    xp_modifier: float = 1.0
```

**Features implemented:**
- `QuestBranch` dataclass with progress tracking and reward modifiers
- `alternative_branches: List[QuestBranch]` field on Quest
- `completed_branch_id: Optional[str]` tracks which branch was used
- `get_branches_display()` method for UI presentation
- Branch-aware progress in `record_kill()` and `record_talk()`
- Branch-specific rewards applied in `claim_quest_rewards()`
- Full serialization support for save/load
- 17 new tests (all passing)

Example: "Stop the Bandit Leader"
- **Path A**: Kill the Bandit Leader (+Militia rep)
- **Path B**: Convince him to leave (+Outlaw rep)
- **Path C**: Help him raid (+major Outlaw rep, Militia hostile)

**7. Multi-Stage Objectives ✅ COMPLETE (2025-12-27)**

Implemented `QuestStage` dataclass for multi-stage quest support:

```python
@dataclass
class QuestStage:
    name: str  # Stage title (e.g., "Find the Witness")
    description: str  # Stage-specific flavor text
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    current_count: int = 0
```

**Quest class extensions:**
- `stages: List[QuestStage]` - Ordered list of stages
- `current_stage: int` - Index of active stage (0-based)
- `get_active_stage()` - Returns current stage or None
- `advance_stage()` - Moves to next stage, returns True if quest complete
- `get_active_objective()` - Returns active objective (stage or root quest)

**Character integration:**
- All `record_*` methods check stage progress before branch/main objectives
- Stage completion triggers advancement to next stage
- Final stage completion marks quest as READY_TO_TURN_IN

**Tests:** 50 new tests in `tests/test_quest_stages.py`

**8. Quest Memory & NPC Reactions ✅ COMPLETE (2025-12-27)**

NPCs now remember and react to how you completed their quests.

**Implementation:**
- `QuestOutcome` model (`src/cli_rpg/models/quest_outcome.py`) tracks quest completions with:
  - Quest name, giver, completion method (success/branch/failed/abandoned)
  - Timestamp, affected NPCs, faction changes
- GameState stores `quest_outcomes` list with `record_quest_outcome()` and `get_quest_outcomes_for_npc()` methods
- NPC greetings check quest history and respond appropriately:
  - Quest givers react to how you completed their quests (success, branch, failed, abandoned)
  - Affected NPCs react positively or negatively based on quest outcomes
- Full serialization support with backward compatibility
- 30 tests in `tests/test_quest_outcomes.py`

#### Implementation Priority

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| World/Region context in generation | High | Low | ✅ **DONE** |
| Faction integration | High | Medium | ✅ **DONE** |
| Quest chains & prerequisites | High | Medium | ✅ **DONE** |
| Branching objectives/choices | High | High | ✅ **DONE** |
| Difficulty indicators | Medium | Low | ✅ **DONE** |
| Time-sensitive quests | Medium | Low | ✅ **DONE** |
| Multi-stage objectives | Medium | High | ✅ **DONE** |
| Quest memory/NPC reactions | Medium | Medium | ✅ **DONE** |

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

**⚠️ Related to: WFC World Generation Overhaul** - Both issues stem from the same root cause: we generate AI content for every tile instead of treating the overworld as traversable terrain with sparse named sub-locations.

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

**3. NPCs Scattered Across Overworld ✅ RESOLVED (2025-12-27)**

~~Current: Every overworld tile can have 0-2 NPCs spawned on it.~~
~~Target: NPCs should **only exist inside named sub-locations** (villages, dungeons, etc.).~~

**Resolution**: Unnamed locations (`is_named=False`) now skip NPC generation entirely. Both `expand_world()` and `expand_area()` in `ai_world.py` check the `is_named` field before generating NPCs.

- ✅ Overworld tiles = wilderness, no NPCs, just terrain and random encounters
- ✅ Named locations = towns, dungeons, etc. with rich NPC populations
- ✅ Matches RPG conventions: you don't find shopkeepers standing in random forests

**Remaining:**
- ~~No shop inventories generated~~ ✅ RESOLVED (2025-12-27) - AI-generated shop inventories with item stats
- ~~No quest hooks or faction ties~~ ✅ RESOLVED (2025-12-27) - Quest hooks for quest_givers, default factions by role
- ~~Hardcoded merchants feel out of place in AI worlds~~ ✅ RESOLVED (2025-12-27) - Terrain-aware default merchant shops now provide thematically appropriate inventory based on terrain type (mountain supplies, swamp remedies, desert provisions, etc.)

#### Implementation Plan

**Phase 1: High Priority (Integrate existing systems)**

1. **Enrich Location Prompts** (Complete)
   - [x] Add `terrain_type` from ChunkManager to prompt ✓ (2025-12-26)
   - [x] Add `world_theme_essence` from WorldContext to prompt ✓ (2025-12-27)
   - [x] Add `region_theme` from RegionContext to prompt ✓ (2025-12-27)
   - [x] Add `neighboring_locations` names/themes for coherence ✓ (2025-12-27)

   **Files to modify**:
   - `src/cli_rpg/ai_config.py`: Expand `DEFAULT_LOCATION_PROMPT_MINIMAL`

**Phase 2: Medium Priority (New features)**

2. **Region Planning System** ✅ COMPLETE (2025-12-27)
   - [x] Divide world into ~16x16 tile regions (`REGION_SIZE = 16` in `world_tiles.py`)
   - [x] Pre-generate `RegionContext` when player approaches region boundary (`_pregenerate_adjacent_regions()` in `game_state.py`)
   - [x] All locations in region share theme, danger level, naming style (via `get_or_create_region_context()`)
   - [x] Add region-based lookup: `get_region_coords(x, y)` → region coordinates in `world_tiles.py`
   - [x] Boundary proximity detection: `check_region_boundary_proximity()` detects when player is within 2 tiles of region boundaries

   **Files modified**:
   - `src/cli_rpg/world_tiles.py`: Added `REGION_SIZE`, `REGION_BOUNDARY_PROXIMITY`, `get_region_coords()`, `check_region_boundary_proximity()`
   - `src/cli_rpg/game_state.py`: Refactored `get_or_create_region_context()` to use region coords, added `_pregenerate_adjacent_regions()`, added pre-generation trigger in `move()`
   - `tests/test_region_planning.py`: NEW - 12 tests for region planning system

3. **Enhanced NPC Generation** ✅ COMPLETE (2025-12-27)
   - [x] Request 3-5 NPCs per location with roles (merchant, quest giver, guard, traveler) ✓ (was already implemented in Phase 1)
   - [x] Generate shop inventories for merchants ✓ (AI generates items with types and stats)
   - [x] Generate quest hooks tied to region theme ✓ (`_generate_quest_for_npc()` uses region context)
   - [x] Add faction affiliations ✓ (role-based defaults: merchant→Merchant Guild, guard→Town Watch, quest_giver→Adventurer's Guild)

   **Files modified**:
   - `src/cli_rpg/ai_world.py`: `_create_shop_from_ai_inventory()`, `_generate_quest_for_npc()`, `_create_npcs_from_data()` with faction defaults
   - `src/cli_rpg/ai_config.py`: Updated NPC prompt with item stats instructions

4. **Terrain-Biased WFC** ✅ COMPLETE (2025-12-27)
   - [x] Modify chunk generation to respect region themes
   - [x] Mountain region → bias WFC toward mountain/foothills/hills
   - [x] Swamp region → bias toward swamp/water/forest
   - [x] Creates mega-biomes instead of random terrain salad

   **Files modified**:
   - `src/cli_rpg/world_tiles.py`: Added `REGION_TERRAIN_BIASES` and `get_biased_weights()` function
   - `src/cli_rpg/wfc.py`: Added `weight_overrides` parameter and `_get_weight()` helper
   - `src/cli_rpg/wfc_chunks.py`: Added region context support and biased weight passing
   - `src/cli_rpg/game_state.py`: Updated `move()` to set region context before terrain lookup
   - 9 new tests in `tests/test_terrain_biased_wfc.py`

**Phase 3: Lower Priority (Polish)**

5. **Strategic World Expansion**
   - [x] Place frontier exits strategically (toward unexplored regions)
     - ✅ Added `get_unexplored_region_directions()` in `world_tiles.py`
     - ✅ Added `get_prioritized_frontier_exits()` in `WorldGrid`
     - ✅ Added `get_explored_regions()` in `GameState`
     - ✅ Added `FRONTIER_DESCRIPTION_HINTS` in `ai_config.py`
   - [ ] Ensure terrain transitions feel natural (forest → plains → desert, not forest → desert)
   - [ ] Cluster similar locations together

6. **Configurable SubGrid Bounds** ✅ COMPLETE (2025-12-27)
   - [x] Support linear dungeons (1x10 corridors)
   - [x] Support large open areas (10x10 plazas)
   - [x] Multi-level dungeons with z-coordinate

   **Implemented**:
   - 6-tuple bounds: `(min_x, max_x, min_y, max_y, min_z, max_z)`
   - Category-specific bounds in `SUBGRID_BOUNDS` config
   - Dungeons go down (z<0), towers go up (z>0)
   - `up`/`down` commands for vertical navigation

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

---

### Playtest Report: Quest Target Spawn Mismatch (2025-12-26)
**Status**: ✅ RESOLVED (2025-12-26)
**Reproducible**: Yes (seed 999)
**Related To**: "CRITICAL: Quest System World Integration Failures" (above)

#### Resolution Summary

This issue has been fixed. KILL quest targets are now validated against the `VALID_ENEMY_TYPES` set in `combat.py`. Invalid targets cause `AIGenerationError`, forcing quest regeneration until a valid enemy type is used.

#### Original Problem

AI-generated quests could specify enemy targets that **never spawn** in the game world, making quests uncompletable.

**Test Case**: Seed 999
```
Quest: "Whispering Willow Woes"
Description: "Clear out the Giant Spiders infesting Whispering Willow Grove"
Target: Giant Spider x3
```

**Result**: Zero Giant Spiders could spawn because only certain enemy types appear in each location category.

#### Fix Applied

1. Moved `enemy_templates` dict from inside `spawn_enemy()` to module level as `ENEMY_TEMPLATES`
2. Added `VALID_ENEMY_TYPES: frozenset[str]` containing all 24 spawnable enemy names (lowercase)
3. Added validation in `ai_service.py:_parse_quest_response()`:
   - When `objective_type == "kill"`, validates `target.lower()` is in `VALID_ENEMY_TYPES`
   - Raises `AIGenerationError` with descriptive message for invalid targets
4. Added 15 tests in `tests/test_quest_validation.py`

#### Features Confirmed Working

| Feature | Status |
|---------|--------|
| Quest acceptance | Working |
| Quest progress tracking | Working |
| Combat system | Working |
| Ranger Track ability | Working |
| Random encounters | Working |
| KILL quest validation | ✅ **NEW** |

---

### ✅ RESOLVED: Default Character Has No Class (--skip-character-creation)
**Status**: RESOLVED
**Date Added**: 2025-12-27
**Date Resolved**: 2025-12-27

**Problem**: When using `--skip-character-creation` flag, the default "Agent" character was created without a class, making class-specific abilities unavailable for automated testing and AI agent playtesting.

**Resolution**: The default "Agent" character is now assigned `CharacterClass.WARRIOR` class, enabling Warrior abilities (bash) during automated testing.

**Files Modified**:
- `src/cli_rpg/main.py`: Added `character_class=CharacterClass.WARRIOR` to Character creation in both `run_json_mode()` and `run_non_interactive()`
- `tests/test_non_interactive_character_creation.py`: Added test `test_skip_character_creation_assigns_warrior_class()`

**Verification**: All 14 tests in `tests/test_non_interactive_character_creation.py` pass

---

### ✅ RESOLVED: `travel` command crashes with UnboundLocalError when destinations exist
**Status**: RESOLVED
**Date Added**: 2025-12-27
**Date Resolved**: 2025-12-27

**Problem**: The `travel` command crashed with an `UnboundLocalError` when there were fast travel destinations to display. The error occurred because the `colors` module was not imported in the `handle_exploration_command()` function.

**Resolution**: Added missing `from cli_rpg import colors` import at line 1049 in `src/cli_rpg/main.py`, immediately after the function docstring. This follows the existing pattern in the codebase where functions use local imports.

**Files Modified**:
- `src/cli_rpg/main.py`: Added `from cli_rpg import colors` import to `handle_exploration_command()`

**Verification**: All 22 tests in `tests/test_fast_travel.py` pass.

