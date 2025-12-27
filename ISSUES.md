## Active Issues

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
**Status**: ACTIVE (Partial)

**Implemented**:
- Secret discovery via `search` command (PER-based checks)
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
   - [x] Ensure terrain transitions feel natural (forest → plains → desert, not forest → desert)
     - ✅ Implemented via `TerrainTransitions` in `world_tiles.py` with `get_transition_weights()`
     - ✅ Comprehensive test suite in `tests/test_terrain_transitions.py`
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

