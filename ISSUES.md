## Active Issues

---

### No Enterable Sublocations on Overworld
**Status**: ✅ COMPLETE (2025-12-27)
**Priority**: CRITICAL - BLOCKER
**Date Added**: 2025-12-27

Named locations on the overworld (dungeons, caves, towns, ruins, etc.) can now be entered via on-demand SubGrid generation.

#### Implementation Complete

**Features Added**:
1. **ENTERABLE_CATEGORIES constant** (`world_tiles.py`): Defines which location categories should be enterable:
   - Adventure locations: `dungeon`, `cave`, `ruins`, `temple`
   - Settlements: `town`, `village`, `city`, `settlement`
   - Commercial buildings: `tavern`, `shop`, `inn`

2. **is_enterable_category() helper** (`world_tiles.py`): Case-insensitive check if a category is enterable.

3. **generate_subgrid_for_location()** (`ai_world.py`): On-demand SubGrid generation function that:
   - Gets appropriate bounds from `get_subgrid_bounds(category)`
   - Attempts AI generation via `generate_area_with_context()` or `generate_area()`
   - Falls back to `_generate_fallback_interior()` for template-based interiors
   - Places bosses in furthest room for dungeon-type categories
   - Marks first location as `is_exit_point=True` for exit navigation

4. **_generate_fallback_interior()** (`ai_world.py`): Template-based interior generation for:
   - Dungeons/caves/ruins: Entrance → Dark Corridor → Ancient Chamber
   - Towns/villages/cities: Gate → Town Square → Marketplace
   - Temples: Entrance → Prayer Hall → Inner Sanctum
   - Generic buildings: Interior → Back Room

5. **GameState.enter() modification** (`game_state.py`): After checking `is_overworld`, now:
   - Checks if location is enterable category but has no sub_grid
   - Generates SubGrid on-demand using `generate_subgrid_for_location()`
   - Sets `entry_point` from first `is_exit_point` location

6. **Location.get_layered_description() update** (`models/location.py`): Shows `Enter: <location_name>` for enterable categories even when `sub_grid` is None.

**Files Modified**:
- `src/cli_rpg/world_tiles.py` - Added `ENTERABLE_CATEGORIES` and `is_enterable_category()`
- `src/cli_rpg/ai_world.py` - Added `generate_subgrid_for_location()` and `_generate_fallback_interior()`
- `src/cli_rpg/game_state.py` - Modified `enter()` for on-demand SubGrid generation
- `src/cli_rpg/models/location.py` - Updated `get_layered_description()` to show Enter prompt

**Files Created**:
- `tests/test_enterable_sublocations.py` - 40 tests covering all functionality

**Test Results**: 40 new tests PASSED, 4284 total tests PASSED (no regressions)

---

### Rest Command Tiredness Threshold Mismatch
**Status**: ACTIVE - Documentation/Implementation Discrepancy
**Priority**: LOW
**Date Added**: 2025-12-27

#### Description
The README documentation states "Sleep is only available when tiredness reaches 30+" but the actual implementation allows rest at any tiredness level above 0%.

#### Steps to Reproduce
1. Start a new game: `cli-rpg --non-interactive --skip-character-creation --no-wfc --seed 9999`
2. Move north once: `go north` (tiredness increases to ~3%)
3. Run `rest` command
4. **Expected**: Rest should fail with message about needing 30%+ tiredness
5. **Actual**: Rest succeeds with message "HP: 165/165 (already full) Stamina: 115/115 (already full) The peaceful rest eases your mind (Dread -5%). Tiredness -3% (light rest)."

#### Evidence from Testing
- At 0% tiredness + 0% dread + full HP/stamina: Rest is blocked ("You're already at full health, stamina, and feeling calm and rested!")
- At 3% tiredness: Rest works (reduces dread and tiredness)
- At 12% tiredness: Rest works
- At 30% tiredness: Rest works

#### Resolution Options
**Option A - Fix Documentation**: Update README.md to accurately describe rest behavior:
- "Rest is available when health/stamina need recovery, dread needs reducing, or tiredness is above 0%"

**Option B - Fix Implementation**: Enforce the documented 30% threshold in `game_state.py`:
- Only allow rest when tiredness >= 30 (or other conditions like low HP/stamina/dread)

#### Related Files
- `README.md` - Line 109: Claims "Sleep is only available when tiredness reaches 30+"
- `src/cli_rpg/game_state.py` - Contains `rest()` method implementation

---

### Map Visibility Radius
**Status**: ✅ COMPLETE (2025-12-27)
**Priority**: CRITICAL - BLOCKER
**Date Added**: 2025-12-27

The map command now automatically reveals nearby terrain within the player's visibility radius, not just tiles physically visited.

#### Implementation Complete

**Files Modified**:
- `src/cli_rpg/world_tiles.py` - Added `VISIBILITY_RADIUS` dict, `MOUNTAIN_VISIBILITY_BONUS`, `get_visibility_radius()`
- `src/cli_rpg/world_grid.py` - Added `get_tiles_in_radius()` helper function
- `src/cli_rpg/game_state.py` - Added `seen_tiles`, `calculate_visibility_radius()`, `update_visibility()`, persistence
- `src/cli_rpg/map_renderer.py` - Added `seen_tiles` parameter, display terrain for seen-not-visited tiles
- `tests/test_visibility_radius.py` - NEW - 24 comprehensive tests

**Visibility by Terrain Type**:
- Plains: 3 tiles (open terrain, far view)
- Hills/Beach/Desert/Water: 2 tiles (moderate obstacles)
- Forest/Swamp/Foothills: 1 tile (blocked view)
- Mountain: 0 tiles (only current tile - but standing ON mountains grants +2 bonus)

**Bonuses**:
- Mountain standing bonus: +2 visibility when on a mountain tile
- Perception bonus: +1 visibility per 5 PER above 10

**Persistence**: `seen_tiles` saved/loaded with game state (backward compatible with old saves)

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
| Make named locations enterable SubGrids (not overworld tiles) | ✅ DONE | On-demand SubGrid generation |

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
**Status**: ACTIVE (Core Complete)

**Implemented**:
- AI-generated secrets for dungeon, cave, ruins, temple, and forest locations (1-2 secrets per location)
- Passive secret detection when entering new areas (PER-based, "You notice: [description]" messages)
- Active secret discovery via `search` command (PER-based checks with +5 bonus)
- Secret thresholds scale with distance from entry (deeper locations = harder secrets)
- Reward system for discovered secrets:
  - Hidden treasure: awards gold and items
  - Traps: DEX-based disarm (10 XP) or damage
  - Lore hints: 5 XP reward
  - Hidden doors: reveals new exits via `temporary_exits` (overworld) or creates navigable hidden rooms (SubGrid locations)
- Hidden rooms in SubGrid locations (dungeons, caves, temples, forests):
  - Generated via `generate_hidden_room()` when hidden door secrets are discovered
  - Themed room templates based on parent location category (e.g., Crystal Grotto in caves, Hidden Shrine in temples)
  - 50% chance to contain additional treasure secrets
  - Navigable via standard `go <direction>` command
  - 12 tests in `tests/test_hidden_rooms.py`
- 10 tests in `tests/test_ai_secrets.py` for secret generation

**Remaining**:
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

---

### Pre-generated Test World
**Status**: PLANNED
**Date Added**: 2025-12-27

Create a pre-generated world with AI content (locations, NPCs, quests, items) that can be loaded for testing without requiring live AI service.

#### The Problem

Currently, meaningful playtesting requires the AI service:
- Quests are only generated when AI is available
- NPCs have empty `offered_quests` lists without AI
- Shop inventories and NPC dialogue rely on AI generation
- This makes automated testing and rapid iteration difficult

#### Proposed Solution

Pre-generate a "test world seed" with full AI content, then serialize it for replay:

1. **Generation Script**: `scripts/generate_test_world.py`
   - Run with AI service enabled
   - Generate a rich world with multiple regions
   - Populate NPCs with quests, shops with inventories
   - Create quest chains and faction conflicts
   - Save entire world state to JSON/pickle

2. **Loading Mechanism**: `--load-world <path>` flag
   - Load pre-generated world state
   - Skip all AI calls, use cached content
   - Deterministic gameplay for testing

3. **Test World Contents** (minimum):
   - 3-5 regions with distinct themes
   - 10+ named locations with NPCs
   - 20+ quests (kill, collect, talk, explore types)
   - Quest chains with prerequisites
   - Faction-affiliated content
   - Shop inventories with varied items
   - Hidden secrets and lore

#### Benefits

- **Automated testing**: Run test suites without AI costs
- **Reproducible bugs**: Same world state for debugging
- **Rapid iteration**: No waiting for AI generation
- **Demo mode**: Showcase game without API keys
- **CI/CD**: Run full integration tests in pipelines

#### Implementation

**Files to Create**:
- `scripts/generate_test_world.py` - Generation script
- `data/test_worlds/default.json` - Pre-generated world

**Files to Modify**:
- `src/cli_rpg/main.py` - Add `--load-world` flag
- `src/cli_rpg/game_state.py` - Add world loading from file
- `src/cli_rpg/persistence.py` - Extend to save/load full world state

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

5. **Strategic World Expansion** ✅ COMPLETE (2025-12-27)
   - [x] Place frontier exits strategically (toward unexplored regions)
     - ✅ Added `get_unexplored_region_directions()` in `world_tiles.py`
     - ✅ Added `get_prioritized_frontier_exits()` in `WorldGrid`
     - ✅ Added `get_explored_regions()` in `GameState`
     - ✅ Added `FRONTIER_DESCRIPTION_HINTS` in `ai_config.py`
   - [x] Ensure terrain transitions feel natural (forest → plains → desert, not forest → desert)
     - ✅ Implemented via `TerrainTransitions` in `world_tiles.py` with `get_transition_weights()`
     - ✅ Comprehensive test suite in `tests/test_terrain_transitions.py`
   - [x] Cluster similar locations together
     - ✅ Added `LOCATION_CLUSTER_GROUPS` mapping categories to cluster groups (settlements, dungeons, wilderness_pois, sacred, commerce)
     - ✅ Added `get_cluster_category_bias()` helper in `world_tiles.py`
     - ✅ Integrated clustering into `move()` via `category_hint` parameter
     - ✅ 16 new tests in `tests/test_location_clustering.py`

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

### AI Content Generation Enhancement
**Status**: PLANNED
**Date Added**: 2025-12-27

Transform the AI content generation system to create bigger, more coherent, and more immersive content through expanded layer system, progress feedback, and content scale improvements.

#### Current Architecture (4 Layers)
- Layer 1: WorldContext (theme_essence, naming_style, tone)
- Layer 2: RegionContext (theme, danger_level, landmarks)
- Layer 3: Location generation
- Layer 4: NPC generation

#### Target Architecture (6 Layers + Unified Context)

---

### Issue 1: Expand WorldContext (Layer 1)
**Status**: ✅ COMPLETE (2025-12-27)
**Priority**: HIGH

Added lore and faction fields to WorldContext for richer world generation.

**New Fields**:
- `creation_myth: str` - World origin story
- `major_conflicts: list[str]` - 2-3 world-defining conflicts
- `legendary_artifacts: list[str]` - World-famous items
- `prophecies: list[str]` - Active prophecies
- `major_factions: list[str]` - 3-5 world powers
- `faction_tensions: dict[str, list[str]]` - Faction rivalries
- `economic_era: str` - stable, recession, boom, war_economy

**Files Modified**:
- `src/cli_rpg/models/world_context.py` - Added 7 new fields with defaults
- `tests/test_world_context.py` - Added 7 new tests for lore/faction fields

**Implementation Details**:
- All new fields use `field(default_factory=...)` for mutable defaults
- Backward compatible: `from_dict()` uses `.get()` with empty defaults
- `default()` factory includes theme-specific creation myths, factions, and economic eras
- 17 tests passing (10 existing + 7 new)

---

### Issue 2: Expand RegionContext (Layer 2)
**Status**: ✅ COMPLETE (2025-12-27)
**Priority**: HIGH

Added economy, history, and atmosphere fields to RegionContext for richer region-specific AI generation.

**New Fields (11 total)**:

*Economy Fields (4)*:
- `primary_resources: list[str]` - Resources abundant in the region (e.g., ["iron", "timber"])
- `scarce_resources: list[str]` - Resources rare in the region (e.g., ["gold", "spices"])
- `trade_goods: list[str]` - Items commonly exported from the region
- `price_modifier: float` - Regional price adjustment factor (default 1.0)

*History Fields (4)*:
- `founding_story: str` - Region origin story
- `historical_events: list[str]` - Notable past events in the region
- `ruined_civilizations: list[str]` - Ancient cultures that once inhabited the region
- `legendary_locations: list[str]` - Mythic places in the region

*Atmosphere Fields (3)*:
- `common_creatures: list[str]` - Typical fauna/monsters found in the region
- `weather_tendency: str` - Dominant weather pattern in the region
- `ambient_sounds: list[str]` - Ambient audio cues for atmosphere

**Files Modified**:
- `src/cli_rpg/models/region_context.py` - Added 11 new fields with defaults, updated to_dict/from_dict
- `tests/test_region_context.py` - Added 9 new tests (23 total passing)

---

### Issue 3: SettlementContext (Layer 5)
**Status**: ✅ COMPLETE (2025-12-27)
**Priority**: HIGH

Created SettlementContext dataclass model for caching settlement-level information including character networks, politics, and trade.

**Model** (implemented in `src/cli_rpg/models/settlement_context.py`):
```python
@dataclass
class SettlementContext:
    settlement_name: str
    location_coordinates: tuple[int, int]
    generated_at: Optional[datetime]
    # Character Networks
    notable_families: list[str]
    npc_relationships: list[dict]
    # Economic Connections
    trade_routes: list[dict]
    local_guilds: list[str]
    market_specialty: Optional[str]
    # Political Structure
    government_type: str  # council, monarchy, theocracy
    political_figures: list[dict]
    current_tensions: list[str]
    # Social Atmosphere
    population_size: str
    prosperity_level: str
    social_issues: list[str]
```

**Implementation Details**:
- `to_dict()` method for serialization (datetime→ISO, tuple→list)
- `from_dict()` classmethod for deserialization with backward-compatible defaults
- `default()` classmethod for fallback when AI unavailable
- Default constants: `DEFAULT_GOVERNMENT_TYPES`, `DEFAULT_POPULATION_SIZES`, `DEFAULT_PROSPERITY_LEVELS`
- 12 tests in `tests/test_settlement_context.py` covering creation, serialization, deserialization, and defaults

**Files Created**:
- `src/cli_rpg/models/settlement_context.py`
- `tests/test_settlement_context.py`

---

### Issue 4: LoreContext (Layer 6)
**Status**: ✅ COMPLETE (2025-12-27)
**Priority**: HIGH

Created LoreContext dataclass for historical events, legendary items, and ancient civilizations.

**Model** (implemented in `src/cli_rpg/models/lore_context.py`):
```python
@dataclass
class LoreContext:
    region_name: str
    coordinates: tuple[int, int]
    generated_at: Optional[datetime]
    # Lore fields (all list types)
    historical_events: list[dict]  # name, date, description, impact
    legendary_items: list[dict]    # name, description, powers, location_hint
    legendary_places: list[dict]   # name, description, danger_level, rumored_location
    prophecies: list[dict]         # name, text, interpretation, fulfilled
    ancient_civilizations: list[dict]  # name, era, achievements, downfall
    creation_myths: list[str]
    deities: list[dict]  # name, domain, alignment, worship_status
```

**Implementation Details**:
- `to_dict()` method for serialization (datetime→ISO, tuple→list)
- `from_dict()` classmethod for deserialization with backward-compatible defaults
- `default()` classmethod for fallback when AI unavailable
- Default constants: `DEFAULT_HISTORICAL_EVENT_TYPES`, `DEFAULT_DEITY_DOMAINS`, `DEFAULT_DEITY_ALIGNMENTS`
- 12 tests in `tests/test_lore_context.py` covering creation, serialization, deserialization, and defaults

**Files Created**:
- `src/cli_rpg/models/lore_context.py`
- `tests/test_lore_context.py`

**Note**: Model complete; integration with GenerationContext aggregator pending (Issue 5).

---

### Issue 5: Unified GenerationContext
**Status**: PENDING
**Priority**: HIGH

Create GenerationContext aggregator that combines all layers for prompt generation.

**Model**:
```python
@dataclass
class GenerationContext:
    world: WorldContext           # Layer 1
    region: Optional[RegionContext]  # Layer 2
    settlement: Optional[SettlementContext]  # Layer 5
    world_lore: Optional[LoreContext]  # Layer 6
    region_lore: Optional[LoreContext]

    def to_prompt_context(self) -> dict:
        """Convert all layers to prompt-ready dict."""
```

**AI Service Integration**:
- `generate_enemy_with_context(context, location, level)` - Use region creatures
- `generate_item_with_context(context, location, level)` - Use region resources
- `generate_quest` - Validate difficulty against `danger_level`
- `generate_settlement_context()` - Layer 5 generation
- `generate_lore_context()` - Layer 6 generation

**Files to Create**:
- `src/cli_rpg/models/generation_context.py`

**Files to Modify**:
- `src/cli_rpg/ai_service.py`
- `src/cli_rpg/game_state.py` - Add `get_generation_context()`

---

### Issue 6: Progress Feedback System
**Status**: PENDING
**Priority**: MEDIUM

Add visual progress bars and thematic loading messages during AI generation.

**ProgressManager**:
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

class ProgressManager:
    _instance = None
    console: Console
    stats: list[GenerationStats]
    _enabled: bool = True

@contextmanager
def generation_progress(description, terrain=None, show_bar=False):
    """Context manager for progress display."""
```

**Thematic Loading Messages**:
```python
LOADING_MESSAGES = {
    "forest": ["The ancient trees part to reveal...", "Pushing through dense undergrowth..."],
    "mountain": ["Scaling the rocky heights...", "The mists clear above the peaks..."],
    "swamp": ["Wading through murky waters...", "The fog slowly lifts..."],
    "default": ["Exploring uncharted territory...", "The path unfolds before you..."],
}
```

**Dependencies**:
```toml
dependencies = [
    "rich>=13.0.0",  # Progress bars and console formatting
]
```

**Files to Create**:
- `src/cli_rpg/progress.py`

**Files to Modify**:
- `pyproject.toml` - Add rich dependency

---

### Issue 7: LLM Streaming Support
**Status**: PENDING
**Priority**: MEDIUM

Add streaming support to AIService for live text display during generation.

**Implementation**:
```python
def _call_llm_streaming(self, prompt: str) -> Generator[str, None, None]:
    """Yield text chunks as they arrive from API."""

def generate_location_streaming(self, on_chunk: Callable[[str], None]) -> dict:
    """Generate with live text streaming."""
```

**Files to Modify**:
- `src/cli_rpg/ai_service.py`

---

### Issue 8: Background Generation Queue
**Status**: PENDING
**Priority**: MEDIUM

Pre-generate adjacent regions in background to eliminate blocking during movement.

**BackgroundGenerator**:
```python
class BackgroundGenerator:
    queue: PriorityQueue[GenerationTask]
    _cache: dict[tuple[int, int], Any]

    def enqueue_adjacent_regions(self, coords, terrain_hints):
        """Queue generation of adjacent regions with priority."""

    def _worker(self):
        """Background thread processing queue."""
```

**Integration**:
```python
# In game_state.py move method:
with generation_progress("Generating area...", terrain=terrain, show_bar=True) as update:
    update(10)  # Starting
    world_ctx = self.get_or_create_world_context()
    update(30)
    region_ctx = self.get_or_create_region_context(coords, terrain)
    update(50)
    expand_area(...)
    update(100)

# Queue adjacent regions for background generation
bg_gen.enqueue_adjacent_regions(target_coords, terrain_hints)
```

**Files to Create**:
- `src/cli_rpg/background_gen.py`

**Files to Modify**:
- `src/cli_rpg/game_state.py`
- `src/cli_rpg/main.py` - Initialize background system

---

### Issue 9: Mega-Settlements with Districts
**Status**: PENDING
**Priority**: HIGH

Expand SubGrid bounds for larger cities and add district system.

**Expanded Bounds**:
```python
SUBGRID_BOUNDS = {
    "city": (-12, 12, -12, 12, 0, 0),      # 25x25 = 625 tiles
    "metropolis": (-20, 20, -20, 20, 0, 0), # 41x41 tiles
}
```

**District Model**:
```python
class DistrictType(Enum):
    MARKET = "market"
    RESIDENTIAL = "residential"
    NOBLE = "noble"
    TEMPLE = "temple"
    SLUMS = "slums"
    DOCKS = "docks"

@dataclass
class District:
    name: str
    district_type: DistrictType
    coordinates_min: tuple[int, int]
    coordinates_max: tuple[int, int]
    prosperity_level: int  # 1-5
    dominant_faction: Optional[str]
    services: list[str]
```

**Batch Generation Strategy**:
1. Single AI call for settlement skeleton (districts, theme)
2. One AI call per district for room layouts
3. Batch NPC generation per district

**Files to Create**:
- `src/cli_rpg/models/district.py`
- `src/cli_rpg/settlement_generator.py`

**Files to Modify**:
- `src/cli_rpg/world_grid.py` - Expand bounds

---

### Issue 10: NPC Relationship Networks
**Status**: PENDING
**Priority**: HIGH

Create relationship system for interconnected NPCs.

**Relationship Model**:
```python
class RelationshipType(Enum):
    SPOUSE, PARENT, CHILD, SIBLING  # Family
    MASTER, APPRENTICE, EMPLOYER    # Professional
    RIVAL, FRIEND, ENEMY            # Social
    ROMANTIC_INTEREST               # Romance

@dataclass
class NPCRelationship:
    npc_a_id: str
    npc_b_id: str
    relationship_type: RelationshipType
    strength: int  # 1-100
    is_secret: bool
```

**Enhanced NPC Fields**:
- `npc_id: str` - Unique identifier
- `relationships: list[str]` - Relationship IDs
- `trust_level: int` - Player trust (1-100)
- `memory: list[dict]` - Interaction history
- `backstory: Optional[str]`
- `secrets: list[str]`

**Files to Create**:
- `src/cli_rpg/models/npc_relationship.py`

**Files to Modify**:
- `src/cli_rpg/models/npc.py`

---

### Issue 11: NPC Network Manager
**Status**: PENDING
**Priority**: MEDIUM

Create manager for NPC networks and family generation.

**NPCNetwork**:
```python
@dataclass
class NPCNetwork:
    npcs: dict[str, NPC]
    relationships: list[NPCRelationship]
    family_trees: dict[str, list[str]]

    def get_npc_relationships(self, npc_id) -> list[tuple[NPC, RelationshipType]]
    def generate_family(self, family_name, settlement, size) -> list[NPC]
```

**Files to Create**:
- `src/cli_rpg/models/npc_network.py`

---

### Issue 12: World State Evolution
**Status**: PENDING
**Priority**: HIGH

Track persistent world changes from quest outcomes and player actions.

**WorldStateManager**:
```python
class WorldChangeType(Enum):
    NPC_DEATH, NPC_MOVED
    LOCATION_DESTROYED, LOCATION_CHANGED
    FACTION_CONTROL, SHOP_INVENTORY_CHANGE

@dataclass
class WorldStateChange:
    change_type: WorldChangeType
    affected_location: Optional[str]
    affected_npc: Optional[str]
    caused_by_quest: Optional[str]
    description: str

@dataclass
class WorldStateManager:
    changes: list[WorldStateChange]
    dead_npcs: set[str]
    faction_territories: dict[str, str]

    def apply_npc_death(self, npc, cause) -> list[str]:
        """Handle death with consequences."""

    def apply_quest_outcome(self, quest, outcome) -> list[WorldStateChange]
```

**Files to Create**:
- `src/cli_rpg/models/world_state.py`

**Files to Modify**:
- `src/cli_rpg/game_state.py` - Integrate WorldStateManager

---

### Issue 13: NPC Character Arcs
**Status**: PENDING
**Priority**: MEDIUM

Add character arc progression for NPCs based on player interactions.

**NPCArc**:
```python
class ArcType(Enum):
    REDEMPTION, CORRUPTION, GROWTH
    TRAGEDY, ROMANCE, VENGEANCE

@dataclass
class ArcStage:
    stage_id: str
    trigger: ArcTrigger
    new_dialogue: str
    trust_change: int
    unlocks: list[str]

@dataclass
class NPCArc:
    npc_id: str
    arc_type: ArcType
    current_stage: int
    stages: list[ArcStage]
```

**Files to Create**:
- `src/cli_rpg/models/npc_arc.py`

---

### Issue 14: Living Economy System
**Status**: PENDING
**Priority**: MEDIUM

Create dynamic economy with supply/demand and trade routes.

**Economy Models**:
```python
@dataclass
class MarketConditions:
    global_modifiers: dict[str, float]
    local_scarcity: dict[str, float]
    trade_routes: list[TradeRoute]

@dataclass
class TradeRoute:
    origin: str
    destination: str
    goods: list[str]
    status: str  # active, disrupted, destroyed

class EconomySimulator:
    def simulate_hour(self, game_state) -> list[str]:
        """Update supply/demand, process trade routes."""

    def apply_player_action(self, action, item, quantity):
        """Track player market impact."""
```

**Files to Create**:
- `src/cli_rpg/models/economy.py`

**Files to Modify**:
- `src/cli_rpg/models/shop.py` - Use economy modifiers

---

### Issue 15: Interconnected Quest Networks
**Status**: PENDING
**Priority**: MEDIUM

Create storyline system with branching quests and investigations.

**Quest Network Models**:
```python
@dataclass
class Storyline:
    storyline_id: str
    quest_ids: list[str]
    branches: dict[str, list[str]]  # Choice -> quest branches

@dataclass
class Investigation:
    clues_found: list[Clue]
    locations_involved: list[str]
    solution: str

@dataclass
class FactionConflict:
    faction_a: str
    faction_b: str
    current_phase: int
    player_involvement: Optional[str]
```

**Files to Create**:
- `src/cli_rpg/models/quest_network.py`

---

### AI Content Generation Implementation Phases

**Phase 1: Core Context Layers**
1. Expand WorldContext with lore/faction fields (Issue 1)
2. Expand RegionContext with economy/history fields (Issue 2)
3. Create GenerationContext aggregator (Issue 5)
4. Add `get_generation_context()` to GameState

**Phase 2: New Layer Models**
5. ✅ Create SettlementContext model - Layer 5 (Issue 3 COMPLETE)
6. ✅ Create LoreContext model - Layer 6 (Issue 4 COMPLETE)
7. Add generation methods to AIService
8. Integrate with existing generation flow

**Phase 3: Progress Feedback**
9. Add rich dependency (Issue 6)
10. Create progress.py with ProgressManager
11. Add streaming support to AIService (Issue 7)
12. Create background_gen.py with BackgroundGenerator (Issue 8)

**Phase 4: Settlement Scale**
13. Expand SUBGRID_BOUNDS for cities (Issue 9)
14. Create District and Settlement models
15. Create SettlementGenerator with batch AI calls
16. Integrate with expand_area()

**Phase 5: NPC Networks**
17. Create NPCRelationship model (Issue 10)
18. Extend NPC with relationship fields
19. Create NPCNetwork manager (Issue 11)
20. Update dialogue generation for cross-references

**Phase 6: World Evolution**
21. Create WorldStateManager (Issue 12)
22. Integrate with quest completion
23. Add NPC death consequences
24. Update location descriptions from state

**Phase 7: Economy & Quests**
25. Create MarketConditions, TradeRoute, EconomySimulator (Issue 14)
26. Create Storyline, Investigation, FactionConflict (Issue 15)
27. Integrate economy with shops
28. Create quest network generation

---

## Location & Dungeon System - Immersion Overhaul

**Status**: PLANNED
**Date Added**: 2025-12-27
**Priority**: HIGH

Transform the dungeon/interior experience from functional to immersive. The SubGrid architecture supports rich interiors, but AI generation doesn't populate them with meaningful content.

### Background Analysis

**Current Strengths:**
- SubGrid supports 3D multi-level dungeons (z-axis navigation)
- Coordinate-based navigation is robust
- Secret discovery mechanics exist in `secrets.py`
- Dread/atmosphere systems are well-integrated

**Critical Gaps:**
- AI-generated areas have no bosses, treasures, or secrets
- Dungeons are flat (z-axis unused by AI generation)
- Encounters are generic everywhere
- No puzzles or environmental hazards
- No exploration tracking or completion rewards

---

### Issue 16: AI-Generated Dungeon Bosses ✅ COMPLETE

**Labels:** `enhancement` `AI` `gameplay` `P0`

**Status:** ✅ COMPLETE (2025-12-27)

**Problem**: The `boss_enemy` field exists on Location but is only set in hardcoded `world.py`. AI-generated areas via `expand_area()` have no bosses, making dynamically generated dungeons feel empty and anticlimactic.

**Implementation:**
- Added `BOSS_CATEGORIES = frozenset({"dungeon", "cave", "ruins"})` constant
- Added `_find_furthest_room(placed_locations)` helper using Manhattan distance
- Wired boss placement into `expand_area()` after SubGrid population
- Boss is placed in the room furthest from entry point (0,0)
- Uses category-based boss assignment (e.g., "dungeon" → Lich Lord/Dark Champion/Demon Lord)
- Existing `spawn_boss()` in `combat.py` handles boss creation with category-appropriate templates

**Acceptance Criteria:**
- [x] Dungeon/cave/ruins areas generated via AI include a boss in the deepest room
- [ ] Boss stats scale with region danger level (from RegionContext) - future enhancement
- [x] Boss names/descriptions match area theme (via category-based templates)
- [x] Boss placement algorithm puts boss in room furthest from entry
- [ ] Defeating boss triggers "area cleared" state - future enhancement

**Tests:**
- 17 tests in `tests/test_ai_world_boss.py` covering boss categories, distance calculation, and placement integration

**Files Modified:**
- `src/cli_rpg/ai_world.py` - Added `BOSS_CATEGORIES`, `_find_furthest_room()`, boss placement in `expand_area()`

---

### Issue 17: AI-Generated Treasure Chests ✅ COMPLETE

**Labels:** `enhancement` `AI` `gameplay` `P0`

**Status:** ✅ COMPLETE (2025-12-27)

**Problem**: The `treasures` field on Location exists but AI never populates it. Only hardcoded examples in `world.py`. AI-generated dungeons have no treasure rewards, reducing exploration incentive.

**Implementation:**
- Added `TREASURE_LOOT_TABLES` constant with category-specific loot (weapons, armor, consumables, misc items per category)
- Added `TREASURE_CHEST_NAMES` constant with thematic chest names per category
- Added `TREASURE_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple", "forest"})`
- Added `_place_treasures()` function with scaling: 1 chest for 2-3 rooms, 2 for 4-5 rooms, 3 for 6+ rooms
- Added `_create_treasure_chest()` function creating treasure dicts with items, difficulty, and schema
- Lock difficulty scales with Manhattan distance from entry point + random(0,1)
- Treasure placement excludes entry rooms (is_exit_point) and boss rooms (boss_enemy)
- Distribution uses step-based selection to spread treasures across dungeon
- Integrated into both `generate_subgrid_for_location()` and `expand_area()`

**Acceptance Criteria:**
- [x] AI-generated areas include 1-3 treasure chests based on area size
- [x] Thematic items match dungeon type (ancient weapons in ruins, crystals in caves)
- [x] Treasure distribution spreads across dungeon, not clustered
- [ ] Loot tables scale with region danger level (future enhancement)
- [ ] Some chests are trap-protected (DEX check to open safely) (future enhancement)

**Tests:** 28 tests in `tests/test_ai_world_treasure.py`

**Files Modified:**
- `src/cli_rpg/ai_world.py` - Added treasure constants and placement functions

---

### Issue 18: AI-Generated Hidden Secrets

**Labels:** `enhancement` `AI` `exploration` `P0`

**Status:** ✅ COMPLETE (2025-12-27)

**Problem**: The `hidden_secrets` field is never populated by AI generation. Additionally, `check_passive_detection()` in `secrets.py` is defined but never called anywhere in the codebase. Players never automatically discover secrets and AI areas have no secrets to find.

**Implementation:**
- Added `SECRET_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple", "forest"})` constant
- Added `SECRET_TEMPLATES` dict with category-specific secrets (hidden_treasure, trap, hidden_door types)
- Added `_generate_secrets_for_location()` function that creates 1-2 secrets per qualifying location
- Secret thresholds scale with distance from entry point (deeper = harder to detect)
- Type-specific fields: `reward_gold` for treasure, `trap_damage` for traps, `exit_direction` for doors
- Wired secret generation into `generate_subgrid_for_location()`, `expand_area()`, and `expand_world()`
- Wired `check_passive_detection()` into `move()`, `_move_in_sub_grid()`, and `enter()` in game_state.py
- Added `_check_and_report_passive_secrets()` helper method

**Acceptance Criteria:**
- [x] AI-generated named locations include 1-2 hidden secrets
- [x] Passive detection called when entering a new location
- [x] Secret thresholds scale with distance (deeper = harder)
- [x] Secret descriptions match location theme via category-specific templates
- [x] Three secret types used: HIDDEN_TREASURE, TRAP, HIDDEN_DOOR (LORE_HINT available via active search)
- [x] Discovered secrets show "You notice: [description]" feedback message to player

**Tests:** 10 tests in `tests/test_ai_secrets.py`

**Files Modified:**
- `src/cli_rpg/ai_world.py` - Added SECRET_CATEGORIES, SECRET_TEMPLATES, _generate_secrets_for_location(), secret wiring
- `src/cli_rpg/game_state.py` - Added passive detection import, helper method, and calls in movement methods

---

### Issue 19: Multi-Level Dungeon Generation

**Labels:** `enhancement` `gameplay` `architecture` `P1`

**Problem**: SubGrid architecture supports z-axis navigation (dungeons defined as `z=-2 to 0`) but `expand_area()` only generates flat 2D areas. The multi-level infrastructure exists but is never exercised by AI generation.

**Current State:**
- `SUBGRID_BOUNDS["dungeon"] = (-3, 3, -3, 3, -2, 0)` supports 3 vertical levels
- `go up` / `go down` commands work in SubGrid
- `expand_area()` only uses (x, y) coordinates, ignoring z
- Hardcoded dungeons in `world.py` use z but AI doesn't

**Acceptance Criteria:**
- [ ] Dungeon areas generate across multiple z-levels (entry at z=0, descending)
- [ ] Stairs/ladders connect levels with appropriate descriptions
- [ ] Deeper levels have increased danger and better loot
- [ ] Boss placed at lowest level
- [ ] Vertical shortcuts possible via hidden passages
- [ ] Map command shows current level indicator

**Related Files:**
- `src/cli_rpg/ai_world.py` - Extend `expand_area()` for z-axis
- `src/cli_rpg/ai_service.py` - Multi-level layout generation
- `src/cli_rpg/map_renderer.py` - Level indicator in map display

---

### Issue 20: Procedural Dungeon Layouts

**Labels:** `enhancement` `AI` `gameplay` `P1`

**Problem**: `_generate_area_layout()` uses a simple branching pattern for all areas. No dungeon-specific layouts exist. All AI-generated interiors feel structurally identical regardless of category.

**Current State:**
- `_generate_area_layout()` in `ai_service.py` creates simple branching
- Fixed coordinates relative to entry point
- No category-specific layout algorithms
- No secret passages or alternative routes

**Acceptance Criteria:**
- [ ] **Linear** layout for caves/mines (progression-focused)
- [ ] **Branching** layout for forests/ruins (exploration-focused)
- [ ] **Circular/Hub** layout for temples (central hub with spokes)
- [ ] **Maze** layout for large dungeons (multiple paths, dead ends)
- [ ] Secret passages connecting non-adjacent rooms
- [ ] Layout type selected based on location category

**Related Files:**
- `src/cli_rpg/ai_service.py` - New layout algorithms
- `src/cli_rpg/ai_world.py` - Layout selection logic
- `src/cli_rpg/world_grid.py` - Secret passage support in SubGrid

---

### Issue 21: Location-Specific Random Encounters

**Labels:** `enhancement` `gameplay` `immersion` `P2`

**Problem**: Random encounters use the same tables everywhere. Dungeon encounters feel identical to forest encounters. No thematic connection between location and enemies/merchants encountered.

**Current State:**
- `random_encounters.py` uses generic encounter spawning
- `spawn_enemy()` only considers terrain, not location category
- Merchants have same inventory everywhere
- No dungeon-specific enemy types

**Acceptance Criteria:**
- [ ] **Dungeon**: undead, constructs, cultists
- [ ] **Cave**: beasts, spiders, giant bats
- [ ] **Ruins**: ghosts, treasure hunters, golems
- [ ] **Forest**: wolves, bandits, fey creatures
- [ ] **Temple**: dark priests, animated statues
- [ ] Category-specific merchant inventories (dungeon merchant sells torches/antidotes)
- [ ] Encounter rate varies by category (dungeons more dangerous)

**Related Files:**
- `src/cli_rpg/random_encounters.py` - Category-aware encounter tables
- `src/cli_rpg/combat.py` - Enemy template selection
- New `src/cli_rpg/encounter_tables.py` - Centralized encounter definitions

---

### Issue 22: Location-Themed Hallucinations

**Labels:** `enhancement` `immersion` `dread` `P2`

**Problem**: High-dread hallucinations use the same 3 templates everywhere regardless of location. A forest hallucination should differ from a dungeon hallucination for thematic coherence.

**Current State:**
- `hallucinations.py` has 3 hardcoded templates: Shadow Mimic, Phantom Shade, Nightmare Echo
- No location category consideration
- No AI generation for unique hallucination descriptions
- Same experience in every location type

**Acceptance Criteria:**
- [ ] **Dungeon**: ghostly prisoners, skeletal warriors, whispering chains
- [ ] **Forest**: twisted treants, shadow wolves, corrupted fey
- [ ] **Temple**: fallen priests, dark angels, corrupted statues
- [ ] **Cave**: eyeless horrors, dripping shadows, chittering swarms
- [ ] Hallucination descriptions reference location-specific elements
- [ ] Optional AI-generated unique hallucination for named locations

**Related Files:**
- `src/cli_rpg/hallucinations.py` - Category-based templates
- `src/cli_rpg/ai_service.py` - Optional AI hallucination generation

---

### Issue 23: Dungeon Puzzle Mechanics

**Labels:** `enhancement` `gameplay` `content` `P2`

**Problem**: No interactive puzzles exist in dungeons. Gameplay is combat-only with occasional loot. Adding puzzles provides non-combat gameplay depth and rewards different character builds (INT-focused).

**Current State:**
- No puzzle system exists
- Dungeons only have combat encounters and treasure
- No keys, levers, or interactive elements
- No INT-based challenges

**Acceptance Criteria:**
- [ ] **Locked doors** requiring keys found in other rooms
- [ ] **Pressure plates/levers** that open passages or disable traps
- [ ] **Riddle NPCs** guarding boss rooms or treasure
- [ ] **Sequence puzzles** (light torches in order, rotate statues)
- [ ] INT stat provides hints for puzzle solving
- [ ] Puzzles are optional (can be bypassed with combat or STR checks)
- [ ] 1-2 puzzles per dungeon area

**Related Files:**
- New `src/cli_rpg/puzzles.py` - Puzzle system
- `src/cli_rpg/models/location.py` - Puzzle state fields
- `src/cli_rpg/game_state.py` - Puzzle interaction commands

---

### Issue 24: Exploration Progress Tracking

**Labels:** `enhancement` `gameplay` `QoL` `P2`

**Problem**: No tracking of dungeon completion exists. Players have no way to know if they've fully explored an area and receive no reward for thorough exploration.

**Current State:**
- No visited/explored state per room
- No completion percentage
- No discovery milestones
- No bonus for 100% exploration
- Map command shows terrain but not exploration state

**Acceptance Criteria:**
- [ ] Track visited rooms in SubGrid (persisted in save)
- [ ] "Fully explored" bonus (XP + gold) when all rooms visited
- [ ] Discovery milestones: first secret, all treasures, boss defeated
- [ ] Exploration percentage visible in `map` command
- [ ] Dungeon completion recorded in player stats
- [ ] Visited rooms marked differently on map

**Related Files:**
- `src/cli_rpg/models/location.py` - Add `explored` state
- `src/cli_rpg/world_grid.py` - SubGrid exploration tracking
- `src/cli_rpg/game_state.py` - Milestone rewards
- `src/cli_rpg/map_renderer.py` - Exploration visualization

---

### Issue 25: Dynamic Interior Events

**Labels:** `enhancement` `gameplay` `world` `P3`

**Problem**: World events only affect the overworld. Dungeon interiors feel static and unchanging. Adding interior-specific events makes dungeons feel alive and time-pressured.

**Current State:**
- `world_events.py` has caravan, plague, invasion events
- Events only affect overworld locations
- Dungeon state is static once generated
- No time-pressure in dungeon exploration

**Acceptance Criteria:**
- [ ] **Cave-in**: Temporarily blocks passages (clears after time or with STR)
- [ ] **Monster migration**: Changes enemy spawn locations
- [ ] **Rival adventurers**: NPCs racing player to boss/treasure
- [ ] **Ritual in progress**: Time-limited boss fight with consequences
- [ ] **Spreading hazard**: Fire/flooding that expands through dungeon
- [ ] Events trigger on dungeon entry or after time spent inside

**Related Files:**
- `src/cli_rpg/world_events.py` - Interior event types
- `src/cli_rpg/game_state.py` - Interior event triggers
- `src/cli_rpg/world_grid.py` - Dynamic passage blocking

---

### Issue 26: Environmental Hazards

**Labels:** `enhancement` `gameplay` `challenge` `P3`

**Problem**: Movement in dungeons is always safe. No environmental challenges exist. Adding hazards creates tactical decisions and item/skill utility.

**Current State:**
- Movement never causes damage
- No terrain effects in interiors
- Light/darkness is purely descriptive
- Temperature/weather don't affect gameplay

**Acceptance Criteria:**
- [ ] **Poison gas**: Periodic damage, mitigated by antidotes or holding breath
- [ ] **Darkness**: Reduces perception checks, requires torch/light spell
- [ ] **Unstable ground**: Chance to fall (DEX check), minor damage
- [ ] **Extreme cold/heat**: Tiredness drain, mitigated by gear
- [ ] **Flooded rooms**: Slows movement, drowning risk if extended
- [ ] Hazards visible in room description
- [ ] Class/item mitigation (Ranger ignores natural hazards)

**Related Files:**
- New `src/cli_rpg/hazards.py` - Hazard system
- `src/cli_rpg/models/location.py` - Hazard fields
- `src/cli_rpg/game_state.py` - Hazard damage/effects on movement

---

### Issue 27: Dungeon Ambiance System

**Labels:** `enhancement` `immersion` `atmosphere` `P3`

**Problem**: Dungeons have limited atmospheric feedback beyond static descriptions. Enhanced ambiance makes exploration more immersive and psychologically engaging.

**Current State:**
- `whisper.py` provides ambient whispers but not location-aware
- No ambient sounds tied to location
- Dread buildup is global, not location-specific
- No environmental storytelling elements
- Day/night doesn't affect dungeon behavior

**Acceptance Criteria:**
- [ ] **Ambient sounds**: Dripping water, distant screams, echoing footsteps
- [ ] **Progressive dread**: Deeper dungeon levels increase dread faster
- [ ] **Environmental storytelling**: Corpses, bloodstains, journals, graffiti
- [ ] **Weather penetration**: Rain sounds near cave entrance, fades deeper
- [ ] **Day/night effects**: Undead more active at night, some creatures sleep
- [ ] **Location-specific whispers**: Dungeon whispers differ from forest
- [ ] Ambiance messages appear periodically during exploration

**Related Files:**
- `src/cli_rpg/whisper.py` - Location-aware whispers
- `src/cli_rpg/models/location.py` - Ambiance fields
- `src/cli_rpg/game_state.py` - Periodic ambiance triggers
- `src/cli_rpg/models/dread.py` - Location-specific dread modifiers

---

### Dungeon Immersion Implementation Phases

**Phase 1 - Core Content (P0)** - Issues 16-18 ✅ COMPLETE
- ✅ AI-generated bosses (Issue 16 COMPLETE)
- ✅ AI-generated treasures (Issue 17 COMPLETE)
- ✅ AI-generated secrets (Issue 18 COMPLETE)
- Filled the biggest content gap in AI-generated areas
- Wired passive secret detection into movement methods

**Phase 2 - Dungeon Structure (P1)** - Issues 19-20
- Multi-level dungeon generation using z-axis
- Category-specific procedural layouts
- Makes dungeons feel distinct and designed

**Phase 3 - Thematic Variety (P2)** - Issues 21-22
- Location-specific encounters
- Themed hallucinations
- Adds thematic coherence to exploration

**Phase 4 - Non-Combat Depth (P2)** - Issues 23-24
- Puzzle mechanics
- Exploration progress tracking
- Adds gameplay depth beyond combat

**Phase 5 - Dynamic Polish (P3)** - Issues 25-27
- Interior events
- Environmental hazards
- Ambiance system
- Adds atmosphere and challenge variety

---

### Architecture Notes

**Key Integration Points:**
- `expand_area()` in `ai_world.py` is the primary hook for AI content
- SubGrid in `world_grid.py` already supports 3D coordinates
- `game_state.py:move()` flow handles encounters, events, dread
- Layer 1-4 generation in `ai_service.py` can be extended for new content types

**Data Flow:**
```
AI Generation → Location Model → SubGrid → GameState → Player Experience
     ↓              ↓              ↓           ↓
  Bosses       Treasures      3D Layout    Events
  Secrets      Hazards        Progress     Ambiance
  Puzzles      NPCs           Navigation   Combat
```

**Backward Compatibility:**
- All new fields should have defaults (existing saves work)
- Feature flags can gate new systems during rollout
- Hardcoded content in `world.py` continues to work

