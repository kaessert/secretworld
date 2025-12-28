## Active Issues

---

### Procedural World Generation with AI Content Layer
**Status**: COMPLETED ✓
**Priority**: -
**Date Added**: 2025-12-28

#### Problem
Current architecture mixes procedural and AI generation in ways that limit reproducibility and offline play. AI generates both structure (room layouts, location placement) and content (names, descriptions, NPCs), making worlds non-deterministic and requiring constant AI calls.

#### Goal
Refactor to use **procedural generation for world structure** while keeping **AI for content** (names, descriptions, NPC personas, quest narratives, ASCII art).

#### Key Decisions
- **Interiors**: Hybrid approach - different algorithms per category (BSP for dungeons, cellular automata for caves, grid for towns, vertical for towers)
- **Location Spawning**: Noise-based density with natural clustering (simplex noise layers)
- **AI Content**: Names, descriptions, full NPC personas, quest narratives, ASCII art, context layers
- **Determinism**: Fully seeded for reproducibility (same seed = identical structure)

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PROCEDURAL LAYER                         │
│  (Deterministic with world seed)                            │
├─────────────────────────────────────────────────────────────┤
│  Terrain (WFC)  │  Location Noise  │  Interior Generators   │
│  wfc.py         │  location_noise  │  procedural_interiors  │
│  wfc_chunks.py  │  .py             │  .py                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CONTENT LAYER                            │
│  (AI-generated, cached for determinism)                     │
├─────────────────────────────────────────────────────────────┤
│  ContentLayer   │  AIService      │  FallbackContent        │
│  (mediator)     │  (LLM calls)    │  (templates)            │
└─────────────────────────────────────────────────────────────┘
```

#### New Files Required
- ✓ `src/cli_rpg/procedural_interiors.py` - RoomType, RoomTemplate, GeneratorProtocol, CATEGORY_GENERATORS (CREATED 2025-12-28)
- ✓ `src/cli_rpg/location_noise.py` - Simplex noise for location density (CREATED 2025-12-28)
- ✓ `src/cli_rpg/content_layer.py` - Mediator between procedural and AI (CREATED 2025-12-28)
- ✓ `src/cli_rpg/content_cache.py` - Deterministic content caching (CREATED 2025-12-28)
- ✓ `src/cli_rpg/fallback_content.py` - Centralized FallbackContentProvider with deterministic templates (CREATED 2025-12-28)
- ✓ `src/cli_rpg/models/content_request.py` - Request/response schemas (CREATED 2025-12-28)

#### Files to Modify
- `src/cli_rpg/ai_world.py` - Use procedural layout + content layer
- `src/cli_rpg/ai_service.py` - Add content-focused generation methods
- `src/cli_rpg/ai_config.py` - Add content prompts
- ✓ `src/cli_rpg/game_state.py` - Use LocationNoiseManager (COMPLETED 2025-12-28)

#### Implementation Phases

**Phase 1: Core Infrastructure** ✓ COMPLETE
1. ✓ Create `procedural_interiors.py` with RoomType enum and RoomTemplate dataclass (COMPLETED 2025-12-28)
2. ✓ Create `location_noise.py` with pure-Python simplex noise (COMPLETED 2025-12-28)
3. ✓ Create content request/response models (COMPLETED 2025-12-28)

**Phase 2: Procedural Generators**
4. ✓ Implement BSPGenerator (dungeons, temples, ruins, tombs, crypts, monasteries, shrines) (COMPLETED 2025-12-28)
5. ✓ Implement CellularAutomataGenerator (caves, mines) (COMPLETED 2025-12-28)
6. ✓ Implement GridSettlementGenerator (towns, cities, villages, settlements, outposts, camps) (COMPLETED 2025-12-28)
7. ✓ Implement TowerGenerator (towers) (COMPLETED 2025-12-28)

**Phase 3: Location Noise System**
8. ✓ Implement LocationNoiseManager with noise layers (COMPLETED 2025-12-28)
9. ✓ Integrate with GameState.move() (COMPLETED 2025-12-28)
10. ✓ Maintain terrain constraint validation (COMPLETED 2025-12-28)

**Phase 4: Content Layer** ✓ COMPLETE
11. ✓ Create ContentLayer mediator class (COMPLETED 2025-12-28)
12. ✓ Create ContentCache with deterministic keying (COMPLETED 2025-12-28)
13. ✓ Create FallbackContentProvider with expanded templates (COMPLETED 2025-12-28)
14. ✓ Add new AIService methods for content generation (COMPLETED 2025-12-28: `generate_room_content()` method added)

**Phase 5: Integration**
15. ✓ Modify `generate_subgrid_for_location()` to use procedural + ContentLayer (COMPLETED 2025-12-28)
16. ✓ Add NPC and quest generation flows to ContentLayer (COMPLETED 2025-12-28: `generate_npc_content()` and `generate_quest_content()` methods added)
17. ✓ Update fallback paths (COMPLETED 2025-12-28: `_generate_fallback_interior()` and `_create_treasure_chest()` now use centralized `FallbackContentProvider`)

**Phase 6: Testing** ✓ COMPLETE
18. ✓ Unit tests for each generator algorithm (COMPLETED 2025-12-28: 41 tests in test_procedural_interiors.py)
19. ✓ Tests for noise determinism (COMPLETED 2025-12-28: 12 tests in test_location_noise.py)
20. ✓ Integration tests for full pipeline (COMPLETED 2025-12-28: 8 tests in test_content_layer.py, 11 tests in test_content_cache.py)

#### Detailed Plan
Full implementation plan available at: `/Users/tkaesser/.claude/plans/rippling-percolating-biscuit.md`

---

### Enterable Location Spawn Guarantees & E2E Tests
**Status**: COMPLETED ✓
**Priority**: CRITICAL
**Date Added**: 2025-12-28
**Completed**: 2025-12-28

#### Problem (Resolved)
AI-generated worlds were not producing enterable locations (dungeons, caves, cities, temples) reliably. Players could walk 50+ tiles without finding any enterable location.

#### Solution

1. **Forced Enterable Spawn**: Added threshold-based forcing in `world_tiles.py`:
   - `MAX_TILES_WITHOUT_ENTERABLE = 25` - After 25 tiles, forces enterable spawn
   - `FORCED_ENTERABLE_BY_TERRAIN` - Terrain-specific enterable category pools
   - `should_force_enterable_category()` and `get_forced_enterable_category()` helper functions

2. **AI Prompt Updates**: Updated `ai_config.py` prompts to request enterable categories ~30% of the time

3. **GameState Integration**: Added `tiles_since_enterable` counter to `game_state.py` with serialization

4. **E2E Test Infrastructure**: Created automated tests for AI → SubGrid → Content pipeline

#### Files Created
- `tests/e2e/__init__.py` - Package initialization
- `tests/e2e/conftest.py` - E2E pytest configuration with fixtures
- `tests/e2e/test_enterable_locations.py` - 4 E2E tests for enterable location generation
- `tests/test_enterable_spawn.py` - 11 unit tests for spawn logic

#### Files Modified
- `tests/conftest.py` - Added `--e2e` pytest command-line option
- `src/cli_rpg/world_tiles.py` - Forced enterable spawn logic
- `src/cli_rpg/ai_config.py` - Updated prompts for enterable categories
- `src/cli_rpg/game_state.py` - `tiles_since_enterable` tracking

#### Running E2E Tests

```bash
# Requires OPENAI_API_KEY or ANTHROPIC_API_KEY in environment
pytest tests/e2e/ -v --e2e
```

E2E tests are skipped by default (use `--e2e` flag to run)

---

### Game Crashes When Moving Inside SubGrid (colors.success AttributeError)
**Status**: COMPLETED ✓
**Priority**: CRITICAL
**Date Added**: 2025-12-27
**Completed**: 2025-12-27

#### Description
The game crashed with `AttributeError: module 'cli_rpg.colors' has no attribute 'success'` when the player moved within a SubGrid location.

#### Resolution
Added `success()` function to `src/cli_rpg/colors.py` that colors text green (matching the semantic pattern of `heal()` for positive messages).

**Changes**:
- `src/cli_rpg/colors.py`: Added `success()` function (lines 181-190)
- `tests/test_colors.py`: Added `test_success_uses_green()` test

All 24 color module tests pass.

---

### Rest Command Tiredness Threshold Mismatch
**Status**: COMPLETED ✓
**Priority**: LOW
**Date Added**: 2025-12-27
**Completed**: 2025-12-27

#### Description
The README documentation states "Sleep is only available when tiredness reaches 30+" but the actual implementation allowed rest at any tiredness level above 0%.

#### Resolution
**Option B - Fix Implementation**: Updated `main.py` to use `Tiredness.can_sleep()` method which enforces the 30% threshold.

**Changes**:
- `src/cli_rpg/main.py`: Changed `no_tiredness = char.tiredness.current == 0` to `can_sleep_for_tiredness = char.tiredness.can_sleep()` and updated condition logic
- `tests/test_rest_command.py`: Added `TestRestTirednessThreshold` test class to verify threshold enforcement

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
**Status**: COMPLETED ✓

**Implemented**:
- AI-generated secrets for dungeon, cave, ruins, temple, and forest locations (1-2 secrets per location)
- Passive secret detection when entering new areas (PER-based, "You notice: [description]" messages)
- Active secret discovery via `search` command (PER-based checks with +5 bonus)
- Secret thresholds scale with distance from entry (deeper locations = harder secrets)
- Reward system for discovered secrets
- Hidden rooms in SubGrid locations
- Dungeon puzzles (Issue 23 - Complete)
- Environmental storytelling (corpses, bloodstains, journals in dungeon/cave/ruins/temple SubGrids)

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
**Status**: COMPLETED ✓
**Date Added**: 2025-12-27
**Completed**: 2025-12-27

Created a pre-generated world with AI content (locations, NPCs, quests, items) that can be loaded for testing without requiring live AI service.

#### Benefits

- **Automated testing**: Run test suites without AI costs
- **Reproducible bugs**: Same world state for debugging
- **Rapid iteration**: No waiting for AI generation
- **Demo mode**: Showcase game without API keys
- **CI/CD**: Run full integration tests in pipelines

#### Implementation

**Files Created**:
- `scripts/generate_test_world.py` - Programmatic generation script
- `tests/fixtures/test_world.json` - Pre-generated world fixture (~12KB)
- `src/cli_rpg/test_world.py` - Fixture loading utility (`load_test_world()`, `create_demo_game_state()`)
- `tests/test_test_world.py` - 25 tests for fixture validation
- `tests/test_demo_mode.py` - 15 tests for demo mode CLI

**Files Modified**:
- `src/cli_rpg/main.py` - Added `--demo` flag and `run_demo_mode()` function
- `tests/conftest.py` - Added `pregenerated_game_state` pytest fixture

#### Usage

```bash
# Start game in demo mode (no AI, pre-generated world)
cli-rpg --demo

# Regenerate fixture if models change
python scripts/generate_test_world.py

# Run demo mode tests
pytest tests/test_test_world.py tests/test_demo_mode.py -v
```

---

### Issue 6: Progress Feedback System
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Completed**: 2025-12-27

Added thematic loading messages and ASCII spinners during AI generation.

**Implementation**:
- `src/cli_rpg/progress.py` - New module with:
  - `ProgressIndicator` class: Non-blocking ASCII spinner using threading
  - `progress_indicator()` context manager for clean AI call wrapping
  - Thematic messages for 10 generation types (location, npc, enemy, lore, area, item, quest, dream, atmosphere, art)
  - Thread-safe start/stop with proper lock handling
  - Respects `effects_enabled()` setting (disabled when `--no-color` or `--json`)
- `src/cli_rpg/ai_service.py` - Integrated progress indicator in `_call_llm()` method
- 23 tests in `tests/test_progress.py`

---

### Issue 7: LLM Streaming Support
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Completed**: 2025-12-27

Add streaming support to AIService for live text display during generation.

**Implementation**:
- `src/cli_rpg/ai_config.py` - Added `enable_streaming: bool` field and `AI_ENABLE_STREAMING` env var
- `src/cli_rpg/ai_service.py` - Streaming methods:
  - `_call_llm_streaming()`: Main streaming dispatcher
  - `_call_openai_streaming()`: OpenAI/Ollama streaming with `stream=True`
  - `_call_anthropic_streaming()`: Anthropic streaming via `client.messages.stream()`
  - `_call_llm_streamable()`: Smart wrapper checking config and effects
- Text-only methods use streaming when enabled: `generate_npc_dialogue()`, `generate_lore()`, `generate_dream()`, `generate_whisper()`, `generate_ascii_art()`, `generate_location_ascii_art()`, `generate_npc_ascii_art()`
- JSON methods remain non-streaming (need complete responses for parsing)
- 22 tests in `tests/test_ai_streaming.py`

**Usage**: Set `AI_ENABLE_STREAMING=true` environment variable to enable

---

### Issue 8: Background Generation Queue
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Completed**: 2025-12-27

Pre-generate adjacent regions in background to eliminate blocking during movement.

**Implementation**:
- `src/cli_rpg/background_gen.py` - New module with:
  - `GenerationTask` dataclass: Holds task data (coords, terrain, world_context, region_context)
  - `BackgroundGenerationQueue` class: Thread-based queue for pre-generating locations
  - Worker loop processes tasks asynchronously using AI service
  - Single worker thread (default) to avoid overwhelming AI service
  - Cache-first approach: checks cache before triggering new AI generation
- `src/cli_rpg/game_state.py` - Added:
  - `background_gen_queue` attribute
  - `start_background_generation()` / `stop_background_generation()` methods
  - `_queue_adjacent_locations()` for submitting unexplored tiles
  - Integration with `move()` to use cached locations
- 13 tests in `tests/test_background_gen.py`

**Note**: Requires `start_background_generation()` call in main.py to activate

---

### Issue 9: Mega-Settlements with Districts
**Status**: COMPLETED ✓
**Priority**: HIGH
**Completed**: 2025-12-27

Expanded SubGrid bounds for larger cities and added district system.

**Implementation**:
- `src/cli_rpg/models/district.py` - DistrictType enum (MARKET, TEMPLE, RESIDENTIAL, NOBLE, SLUMS, CRAFTSMEN, DOCKS, ENTERTAINMENT, MILITARY) and District dataclass with bounds, atmosphere, prosperity, and notable features
- `src/cli_rpg/settlement_generator.py` - District generation with quadrant-based partitioning, deterministic RNG seeds, and themed content
- `src/cli_rpg/world_grid.py` - Added metropolis (25x25) and capital (33x33) bounds; SubGrid now stores districts list with full serialization and backward compatibility

---

### Issue 10: NPC Relationship Networks
**Status**: COMPLETED ✓
**Priority**: HIGH
**Completed**: 2025-12-27

Created relationship system for interconnected NPCs.

**Implementation**:
- `src/cli_rpg/models/npc_relationship.py` - RelationshipType enum (FAMILY, FRIEND, RIVAL, MENTOR, EMPLOYER, ACQUAINTANCE) and NPCRelationship dataclass with trust levels (1-100)
- `src/cli_rpg/models/npc.py` - Added relationships list with add_relationship(), get_relationship(), get_relationships_by_type() methods; updated serialization with backward compatibility

---

### Issue 11: NPC Network Manager
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Completed**: 2025-12-27

Created manager for NPC networks and family generation.

**Implementation**:
- `src/cli_rpg/models/npc_network.py` - FamilyRole enum (SPOUSE, PARENT, CHILD, SIBLING) and NPCNetworkManager dataclass with NPC registration (add_npc, get_npc, get_all_npcs), bidirectional relationship management (add_relationship), family generation (generate_spouse, generate_child, generate_sibling, generate_family_unit), network queries (get_npcs_with_relationship, get_family_members, get_connections with BFS traversal, find_path for shortest paths), and full serialization (to_dict, from_dict)

---

### Issue 12: World State Evolution
**Status**: COMPLETED ✓
**Priority**: HIGH
**Completed**: 2025-12-27

Created world state tracking system for persistent world changes.

**Implementation**:
- `src/cli_rpg/models/world_state.py` - WorldStateChangeType enum (LOCATION_DESTROYED, LOCATION_TRANSFORMED, NPC_KILLED, NPC_MOVED, FACTION_ELIMINATED, BOSS_DEFEATED, AREA_CLEARED, QUEST_WORLD_EFFECT) and WorldStateChange dataclass with full serialization; WorldStateManager class with recording methods (record_change, record_location_transformed, record_npc_killed, record_boss_defeated, record_area_cleared) and query methods (get_changes_for_location, get_changes_by_type, is_location_destroyed, is_npc_killed, is_boss_defeated, is_area_cleared)
- `src/cli_rpg/game_state.py` - Integrated WorldStateManager; mark_boss_defeated() now records to world state; full serialization with backward compatibility for old saves

---

### Issue 13: NPC Character Arcs
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Completed**: 2025-12-27

Created NPC character arc system for tracking relationship progression based on player interactions.

**Implementation**:
- `src/cli_rpg/models/npc_arc.py` - New module with:
  - `NPCArcStage` enum: 7 stages (STRANGER → ACQUAINTANCE → TRUSTED → DEVOTED for positive; WARY → HOSTILE → ENEMY for negative)
  - `InteractionType` enum: 8 interaction types (TALKED, HELPED_QUEST, FAILED_QUEST, INTIMIDATED, BRIBED, DEFENDED, ATTACKED, GIFTED)
  - `NPCInteraction` dataclass: Records individual interactions with timestamps
  - `NPCArc` dataclass: Tracks arc_points (-100 to 100), interaction history (capped at 20), with `get_stage()` and `record_interaction()` methods
- `src/cli_rpg/models/npc.py` - Added optional `arc` field with full serialization and backward compatibility
- 37 tests in `tests/test_npc_arc.py`

**Integrated with Talk Command (2025-12-28)**:
- Talking to NPCs records a TALKED interaction and adds 1-3 arc points per conversation
- NPCs without arcs get one initialized on first talk
- Stage change messages displayed when arc crosses thresholds
- Arc-based warm greetings for ACQUAINTANCE, TRUSTED, and DEVOTED NPCs

**Future Integration Points (Not Yet Implemented)**:
- Dialogue selection based on arc stage
- Shop price modifiers based on arc
- Quest prerequisites based on arc stage

---

### Issue 14: Living Economy System
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Completed**: 2025-12-27

Created dynamic economy with supply/demand and trade routes.

**Implementation**:
- `src/cli_rpg/models/economy.py` - EconomyState dataclass with:
  - `item_supply` dict for per-item supply/demand modifiers
  - `regional_disruption` for world event effects
  - `record_buy()` / `record_sell()` to track transactions
  - `update_time()` for time-based price recovery toward baseline
  - `get_modifier()` combining supply, location, and disruption
  - Full serialization with `to_dict()` / `from_dict()`
- `src/cli_rpg/economy.py` - Helper functions:
  - `get_economy_price_modifier()` for calculating item prices
  - `update_economy_from_events()` for invasion/caravan effects
- `src/cli_rpg/game_state.py` - Integrated `economy_state` field with time-based recovery in `move()` and `fast_travel()`
- `src/cli_rpg/main.py` - Buy/sell/shop commands use economy modifiers
- `src/cli_rpg/world_events.py` - Calls `update_economy_from_events()` in `progress_events()`
- 34 tests in `tests/test_economy.py`

**Economy Behavior**:
- Supply/Demand: Buy increases price (+5% per purchase, max +50%), Sell decreases (-3% per sale, min -30%)
- Time Recovery: Every 6 game hours, prices drift 5% toward baseline
- Location Bonuses: Temple -15% consumables, Town/Village -10% weapons, Forest -20% resources
- World Events: Invasion +20% all prices, Caravan -10% all prices

---

### Issue 15: Interconnected Quest Networks
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Completed**: 2025-12-27

Created QuestNetworkManager for managing interconnected quest storylines.

**Implementation**:
- `src/cli_rpg/models/quest_network.py` - QuestNetworkManager dataclass with:
  - Quest registration: `add_quest()`, `get_quest()`, `get_all_quests()` (case-insensitive lookup)
  - Chain management: `get_chain_quests()`, `get_chain_progression()`, `get_next_in_chain()`
  - Dependency queries: `get_available_quests()`, `get_unlocked_quests()`
  - Storyline queries: `get_prerequisites_of()`, `get_unlocks_of()`, `find_path()` (BFS pathfinding)
  - Full serialization: `to_dict()`, `from_dict()`
- 19 tests in `tests/test_quest_network.py`

**Note**: GameState integration deferred - standalone manager ready for future integration

---

## Location & Dungeon System - Remaining Issues

### Issue 21: Location-Specific Random Encounters
**Status**: COMPLETED ✓
**Priority**: P2
**Completed**: 2025-12-27

**Implementation**:
- `src/cli_rpg/encounter_tables.py` - New module with category-specific encounter configuration:
  - `CATEGORY_ENEMIES`: Enemy pools by location type (dungeon, cave, ruins, forest, temple)
  - `CATEGORY_ENCOUNTER_RATES`: Variable encounter rates (dungeon 25%, cave/ruins/temple 20%, forest 15%, town/village/city 5%)
  - `CATEGORY_MERCHANT_ITEMS`: Location-appropriate merchant inventories
  - Helper functions: `get_enemies_for_category()`, `get_encounter_rate()`, `get_merchant_items()`
- `src/cli_rpg/random_encounters.py` - Updated to use category-specific encounter rates via `get_encounter_rate()`
- 18 new tests in `tests/test_encounter_tables.py` + 4 integration tests in `tests/test_random_encounters.py`

**Acceptance Criteria:**
- [x] **Dungeon**: undead, constructs, cultists (Skeleton Warrior, Zombie, Stone Construct, Cultist, Bone Golem, Dark Acolyte)
- [x] **Cave**: beasts, spiders, giant bats (Giant Spider, Cave Bear, Giant Bat, Goblin, Troll, Cave Beetle)
- [x] **Ruins**: ghosts, treasure hunters, golems (Restless Ghost, Stone Golem, Treasure Hunter, Phantom, Ancient Guardian, Ruin Lurker)
- [x] **Forest**: wolves, bandits, fey creatures (Wolf, Bandit, Wild Boar, Dryad, Forest Spirit, Giant Spider)
- [x] **Temple**: dark priests, animated statues (Dark Priest, Animated Statue, Temple Guardian, Cultist Zealot, Stone Sentinel, Shadow Monk)
- [x] Category-specific merchant inventories
- [x] Encounter rate varies by category

---

### Issue 22: Location-Themed Hallucinations
**Status**: COMPLETED ✓
**Priority**: P2
**Completed**: 2025-12-27

**Implementation**:
- `src/cli_rpg/hallucinations.py` - Added category-specific hallucination templates:
  - `CATEGORY_HALLUCINATION_TEMPLATES`: Location-themed enemy templates for dungeon, forest, temple, cave
  - `get_hallucination_templates(category)`: Helper function to retrieve templates by category (falls back to defaults)
  - `spawn_hallucination(level, category)`: Updated to accept optional category parameter
  - `check_for_hallucination()`: Now passes location category to spawn themed hallucinations
- 10 new tests in `tests/test_hallucinations.py` (`TestCategoryHallucinations` class)

**Acceptance Criteria:**
- [x] **Dungeon**: ghostly prisoners, skeletal warriors (Ghostly Prisoner, Skeletal Warrior)
- [x] **Forest**: twisted treants, shadow wolves (Twisted Treant, Shadow Wolf)
- [x] **Temple**: fallen priests, dark angels (Fallen Priest, Dark Angel)
- [x] **Cave**: eyeless horrors, dripping shadows (Eyeless Horror, Dripping Shadow)
- [x] Hallucination descriptions reference location-specific elements

**Related Files:**
- `src/cli_rpg/hallucinations.py`

---

### Issue 23: Dungeon Puzzle Mechanics
**Status**: COMPLETED ✓
**Priority**: P2
**Completed**: 2025-12-27

**Implementation:**
- `src/cli_rpg/models/puzzle.py` - Puzzle model with 5 types (LOCKED_DOOR, LEVER, PRESSURE_PLATE, RIDDLE, SEQUENCE)
- `src/cli_rpg/puzzles.py` - Puzzle interaction logic (unlock, pull, step, answer, activate)
- `src/cli_rpg/models/location.py` - Added `puzzles` and `blocked_directions` fields with serialization
- `src/cli_rpg/main.py` - Puzzle commands (unlock, pull, step, answer, activate)
- `src/cli_rpg/completer.py` - Tab completion for puzzle commands
- `src/cli_rpg/game_state.py` - KNOWN_COMMANDS and blocked_directions movement check
- `src/cli_rpg/ai_world.py` - AI puzzle generation during SubGrid creation:
  - `PUZZLE_CATEGORIES`: dungeon, cave, ruins, temple get puzzles
  - `PUZZLE_TEMPLATES`: Category-specific puzzle templates for all 5 types
  - `_generate_puzzles_for_location()`: 0-2 puzzles per room based on distance from entry
  - `_place_keys_in_earlier_rooms()`: Keys for LOCKED_DOOR puzzles placed in accessible rooms
  - Hint threshold scales with distance and z-level (deeper = higher INT required)
- 62 tests total: 30 in `test_puzzles.py`, 16 in `test_puzzle_commands.py`, 16 in `test_ai_puzzle_generation.py`

**Acceptance Criteria:**
- [x] **Locked doors** requiring keys found in other rooms
- [x] **Pressure plates/levers** that open passages
- [x] **Riddle NPCs** guarding boss rooms
- [x] **Sequence puzzles** (light torches in order)
- [x] INT stat provides hints for puzzle solving
- [x] 1-2 puzzles per dungeon area (AI integration complete)

---

### Issue 24: Exploration Progress Tracking
**Status**: COMPLETED ✓
**Priority**: P2
**Completed**: 2025-12-27

**Implementation:**
- `src/cli_rpg/world_grid.py` - Added to SubGrid class:
  - `visited_rooms: set` - Stores (x, y, z) coordinate tuples of visited rooms
  - `exploration_bonus_awarded: bool` - Prevents bonus from being awarded multiple times
  - `mark_visited(x, y, z)` method - Adds a room coordinate to the visited set
  - `get_exploration_stats()` method - Returns (visited_count, total_rooms, percentage)
  - `is_fully_explored()` method - Returns True when all rooms have been visited
  - Full serialization with backward compatibility
- `src/cli_rpg/game_state.py` - Movement tracking:
  - `enter()` marks entry room as visited when entering SubGrid
  - `_move_in_sub_grid()` marks destination room as visited after each move
  - Awards XP (50 × rooms) and gold (25 × rooms) bonus on full exploration
  - Displays "★ FULLY EXPLORED! ★" message with rewards
- `src/cli_rpg/map_renderer.py` - Displays "Explored: X/Y rooms (Z%)" in SubGrid map header
- 15 new tests in `tests/test_exploration_tracking.py`

**Acceptance Criteria:**
- [x] Track visited rooms in SubGrid (persisted in save)
- [x] "Fully explored" bonus (XP + gold) when all rooms visited
- [ ] Discovery milestones: first secret, all treasures, boss defeated (deferred to future enhancement)
- [x] Exploration percentage visible in `map` command
- [ ] Visited rooms marked differently on map (deferred - current map already shows visited vs seen tiles)

---

### Issue 25: Dynamic Interior Events
**Status**: COMPLETED ✓
**Priority**: P3
**Completed**: 2025-12-28

**Problem**: World events only affect the overworld. Dungeon interiors feel static.

**Implementation (Cave-ins):**
- `src/cli_rpg/interior_events.py` - New module with:
  - `InteriorEvent` dataclass with event_id, event_type, location_coords, blocked_direction, duration, serialization
  - `check_for_cave_in()`: 5% spawn chance per move in dungeon/cave/ruins/temple
  - `progress_interior_events()`: Clears expired cave-ins on time advance
  - `clear_cave_in()`: Manual clearing function for future digging tools
- `src/cli_rpg/world_grid.py` - Added `interior_events` field to SubGrid with serialization
- `src/cli_rpg/game_state.py` - Integrated cave-in checks and blocking into SubGrid movement
- 20 new tests in `tests/test_interior_events.py`

**Implementation (Monster Migration):**
- `src/cli_rpg/interior_events.py` - Extended with:
  - `InteriorEvent.affected_rooms`: Optional dict mapping coordinates to encounter rate modifiers
  - `check_for_monster_migration()`: 3% spawn chance per SubGrid move
  - `get_encounter_modifier_at_location()`: Returns cumulative encounter modifier for a coordinate
  - `get_active_migrations()`: Returns list of active migration events
  - Migration duration: 2-6 hours, modifiers range 0.5x-2.0x
- `src/cli_rpg/random_encounters.py` - Integrates migration modifiers into encounter rate calculation
- 10 new tests in `tests/test_interior_events.py` (`TestMonsterMigration` class)

**Implementation (Rival Adventurers):**
- `src/cli_rpg/interior_events.py` - Extended with:
  - `RIVAL_SPAWN_CHANCE = 0.15`: 15% spawn chance on SubGrid entry
  - `RIVAL_PARTY_SIZE_RANGE = (1, 3)`: 1-3 rival NPCs per party
  - `RIVAL_CATEGORIES`: dungeon, cave, ruins, temple
  - `RIVAL_PARTY_NAMES`: Flavor names for rival parties
  - `RIVAL_ADVENTURER_TEMPLATES`: Combat stats (Warrior, Mage, Rogue)
  - `RIVAL_WARNING_MESSAGES`: Messages at 25%, 50%, 75% progress
  - `InteriorEvent` extended: `rival_party`, `target_room`, `rival_progress`, `arrival_turns`, `rival_at_target`
  - `check_for_rival_spawn()`: Spawns rivals targeting boss/treasure rooms
  - `progress_rival_party()`: Advances rival progress, returns warning messages
  - `get_rival_encounter_at_location()`: Triggers combat when player reaches rivals
  - `_handle_rival_arrival()`: Handles boss defeat/treasure opening when rivals arrive first
- `src/cli_rpg/game_state.py` - Integrated rival spawning on `enter()` and progress/combat in `_move_in_sub_grid()`
- 20 new tests in `tests/test_rival_adventurers.py`

**Implementation (Ritual in Progress):**
- `src/cli_rpg/interior_events.py` - Extended with:
  - `RITUAL_SPAWN_CHANCE = 0.15`: 15% spawn chance on SubGrid entry
  - `RITUAL_COUNTDOWN_RANGE = (8, 12)`: 8-12 turns until ritual completion
  - `RITUAL_CATEGORIES`: dungeon, cave, ruins, temple
  - `RITUAL_WARNING_MESSAGES`: Messages at 25%, 50%, 75% progress
  - `InteriorEvent` extended: `ritual_room`, `ritual_countdown`, `ritual_initial_countdown`, `ritual_completed`
  - `check_for_ritual_spawn()`: Spawns ritual at non-entry/boss/treasure room
  - `progress_ritual()`: Decrements countdown, returns warning/completion messages
  - `get_ritual_encounter_at_location()`: Returns (event, is_empowered) at ritual room
- `src/cli_rpg/combat.py` - Added `ritual_summoned` boss type with `empowered` parameter (1.5x stats)
- `src/cli_rpg/game_state.py` - Integrated ritual spawning on `enter()` and progress/combat in `_move_in_sub_grid()`
- 21 new tests in `tests/test_ritual_events.py`

**Implementation (Spreading Hazards):**
- `src/cli_rpg/interior_events.py` - Extended with:
  - `SPREADING_HAZARD_SPAWN_CHANCE = 0.05`: 5% spawn chance on SubGrid entry
  - `SPREADING_HAZARD_DURATION_RANGE = (8, 16)`: 8-16 hours before dissipating
  - `FIRE_DAMAGE_RANGE = (4, 8)`: Fire deals 4-8 damage per turn
  - `FLOODING_TIREDNESS = 3`: Flooding adds +3 tiredness per turn
  - `MAX_SPREAD_RADIUS = 3`: Maximum spread from origin room
  - `InteriorEvent` extended: `hazard_type`, `spread_rooms`, `max_spread_radius`
  - `check_for_spreading_hazard()`: Spawns fire or flooding at random room
  - `spread_hazard()`: Spreads to adjacent rooms each hour
  - `get_active_spreading_hazard_event()`: Get active hazard event
  - `clear_spreading_hazard()`: Remove hazard on expiry
- `src/cli_rpg/hazards.py` - Added hazard types:
  - `spreading_fire`: Deals 4-8 damage when entering affected room
  - `spreading_flood`: 50% movement failure + 3 tiredness
  - `apply_spreading_fire()` and `apply_spreading_flood()` effect handlers
- `src/cli_rpg/game_state.py` - Integrated spreading hazard spawn check in `enter()` method
- 21 new tests in `tests/test_spreading_hazard.py`

**Acceptance Criteria:**
- [x] **Cave-in**: Temporarily blocks passages (4-12 hours, auto-clears)
- [x] **Monster migration**: Changes enemy spawn rates via room-specific modifiers (2-6 hours)
- [x] **Rival adventurers**: NPCs racing player to boss/treasure (15% spawn, combat encounter)
- [x] **Ritual in progress**: Time-limited boss fight (15% spawn, 8-12 turn countdown, empowered boss if completed)
- [x] **Spreading hazard**: Fire/flooding through dungeon (5% spawn, 4-8 fire damage, 50% flood movement fail + 3 tiredness, max 3-room spread, 8-16 hour duration)

**Related Files:**
- `src/cli_rpg/interior_events.py`
- `src/cli_rpg/hazards.py`
- `src/cli_rpg/world_grid.py`
- `src/cli_rpg/game_state.py`
- `src/cli_rpg/combat.py`
- `src/cli_rpg/random_encounters.py`
- `tests/test_rival_adventurers.py`
- `tests/test_ritual_events.py`
- `tests/test_spreading_hazard.py`

---

### Issue 26: Environmental Hazards
**Status**: COMPLETED ✓
**Priority**: P3
**Completed**: 2025-12-27

**Implementation:**
- `src/cli_rpg/hazards.py` - New module with environmental hazard system:
  - `HAZARD_TYPES`: poison_gas, darkness, unstable_ground, extreme_cold, extreme_heat, flooded
  - `CATEGORY_HAZARDS`: Location-specific hazard pools (dungeon, cave, ruins, temple)
  - `RANGER_MITIGATED_HAZARDS`: Rangers ignore unstable_ground, extreme_cold, extreme_heat
  - Hazard functions: `apply_poison_gas()` (3-6 damage), `check_darkness_penalty()` (50% perception reduction), `check_unstable_ground()` (DEX check vs DC 12 or 5-15 fall damage), `apply_temperature_effect()` (+5 tiredness), `check_flooded_movement()` (50% movement failure)
  - `can_mitigate_hazard()`: Class/equipment mitigation checks
  - `get_hazards_for_category()`: Distance-based hazard generation (10-40% chance, 1-2 hazards)
  - `check_hazards_on_entry()`: Main entry point for processing hazards on room entry
- `src/cli_rpg/models/location.py` - Added `hazards: List[str]` field with serialization and backward compatibility
- `src/cli_rpg/ai_world.py` - Integrated hazard generation in `generate_subgrid_for_location()`
- `src/cli_rpg/game_state.py` - Calls `check_hazards_on_entry()` during SubGrid movement
- 27 new tests in `tests/test_hazards.py`

**Acceptance Criteria:**
- [x] **Poison gas**: Periodic damage (3-6 per move), no class mitigation
- [x] **Darkness**: Reduces perception by 50%, negated by light source
- [x] **Unstable ground**: DEX check (d20 + DEX mod vs DC 12) or 5-15 fall damage
- [x] **Extreme cold/heat**: +5 tiredness per move
- [x] **Flooded rooms**: 50% movement failure chance
- [x] Class/item mitigation (Ranger ignores natural hazards, light negates darkness)

---

### Issue 27: Dungeon Ambiance System
**Status**: COMPLETED ✓
**Priority**: P3
**Completed**: 2025-12-28

**Problem**: Dungeons have limited atmospheric feedback beyond static descriptions.

**Implementation (Increment 3 - Ambient Sounds):**
- `src/cli_rpg/ambient_sounds.py` - New module with ambient sound system:
  - `AmbientSoundService` class: Manages ambient sound triggers with cooldown tracking
  - `CATEGORY_SOUNDS`: Category-specific sound pools (8-10 sounds each for dungeon, cave, ruins, temple)
  - `DEPTH_SOUNDS`: Increasingly ominous sounds for deeper z-levels (-1, -2, -3+)
  - `AMBIENT_SOUND_CHANCE = 0.15`: 15% base chance per move
  - `DEPTH_SOUND_CHANCE_BONUS = 0.05`: +5% per depth level
  - `SOUND_COOLDOWN_MOVES = 3`: Minimum moves between sounds
  - `format_ambient_sound()`: Formats sounds with `[Sound]:` prefix and blue ANSI color
- `src/cli_rpg/game_state.py` - Integrated `ambient_sound_service` with sound checks in `_move_in_sub_grid()`
- 18 new tests in `tests/test_ambient_sounds.py`

**Implementation (Increment 1 - Depth-Based Whispers):**
- `src/cli_rpg/whisper.py` - Expanded whisper system:
  - `CATEGORY_WHISPERS`: Expanded to 8+ templates per category (dungeon, cave, ruins, temple, forest, town, wilderness)
  - `DEPTH_WHISPERS`: New dictionary with depth-specific whispers for z-levels -1, -2, -3+
  - `DEPTH_WHISPER_CHANCE = 0.40`: 40% chance to use depth whispers when underground
  - `get_depth_dread_modifier(z)`: Returns dread multiplier based on depth (1.0 surface, 1.25 at z=-1, 1.5 at z=-2, 2.0 at z≤-3)
  - `get_whisper(depth)`: Updated signature with depth parameter for location-aware whispers
- `src/cli_rpg/game_state.py` - Integrated depth whispers and dread modifiers into SubGrid movement

**Implementation (Increment 2 - Undead Night Effects):**
- `src/cli_rpg/encounter_tables.py` - Undead night modifiers:
  - `UNDEAD_NIGHT_ENCOUNTER_MODIFIER = 1.5`: +50% encounter rate at night
  - `UNDEAD_CATEGORIES = {"dungeon", "ruins", "cave"}`: Categories affected by night bonus
  - `get_undead_night_modifier()`: Returns modifier based on category and time of day
- `src/cli_rpg/combat.py` - Undead stat boosts at night:
  - `spawn_enemy()` accepts `is_night` parameter
  - Undead enemies at night: +20% attack, +10% health
  - Uses existing `is_undead()` function from `cli_rpg.cleric`
- `src/cli_rpg/random_encounters.py` - Integrated night modifiers into encounter rate calculation
- 9 tests in `tests/test_undead_night_effects.py`

**Acceptance Criteria:**
- [x] **Ambient sounds**: Category-specific sounds (dripping water, rattling chains, distant screams) with depth-based ominous sounds
- [x] **Progressive dread**: Deeper levels increase dread faster (up to 2x at z≤-3)
- [x] **Environmental storytelling**: Corpses, bloodstains, journals (completed - see environmental_storytelling.py)
- [ ] **Weather penetration**: Rain sounds near cave entrance (deferred - future enhancement)
- [x] **Day/night effects**: Undead more active at night (+50% encounter rate, +20% attack, +10% health during 18:00-5:59)
- [x] **Location-specific whispers**: Dungeon whispers differ from forest (8+ templates per category, new temple category)

**Related Files:**
- `src/cli_rpg/ambient_sounds.py`
- `src/cli_rpg/whisper.py`
- `src/cli_rpg/models/location.py`
- `src/cli_rpg/game_state.py`
- `src/cli_rpg/models/dread.py`
- `tests/test_ambient_sounds.py`

---

## Implementation Phases

### Dungeon Immersion (Remaining)

**Phase 3 - Thematic Variety (P2)** - Issues 21-22
- ✓ Location-specific encounters (Issue 21 complete)
- ✓ Themed hallucinations (Issue 22 complete)

**Phase 4 - Non-Combat Depth (P2)** - Issues 23-24
- ✓ Puzzle mechanics (Issue 23 complete)
- ✓ Exploration progress tracking (Issue 24 complete)

**Phase 5 - Dynamic Polish (P3)** - Issues 25-27
- ✓ Interior events - cave-ins, monster migrations, rival adventurers, rituals, spreading hazards (Issue 25 complete)
- ✓ Environmental hazards (Issue 26 complete)
- ✓ Ambiance system - depth whispers, progressive dread, ambient sounds (Issue 27 complete)

### AI Content Generation (Remaining)

**Phase 3: Progress Feedback** - Issues 6-8
- ✓ Progress feedback (Issue 6 complete - ASCII spinner with thematic messages)
- ✓ LLM streaming (Issue 7 complete - streaming for text-only generation methods)
- ✓ Background generation (Issue 8 complete - thread-based queue for adjacent location pre-generation)

**Phase 4: Settlement Scale** - Issue 9
- ✓ Mega-settlements with districts (Issue 9 complete)

**Phase 5: NPC Networks** - Issues 10-11
- ✓ Relationship system (Issue 10 complete)
- ✓ NPC network manager (Issue 11 complete)

**Phase 6: World Evolution** - Issues 12-13
- ✓ World state tracking (Issue 12 complete)
- ✓ NPC character arcs (Issue 13 complete)

**Phase 7: Economy & Quests** - Issues 14-15
- ✓ Living economy (Issue 14 complete)
- ✓ Quest networks (Issue 15 complete)

---

## UX Issues

### SubGrid Exit Points Not Visually Indicated
**Status**: COMPLETED ✓
**Priority**: MEDIUM
**Date Added**: 2025-12-27
**Completed**: 2025-12-28

#### Description
When inside a SubGrid interior (dungeon, cave, mine, etc.), exit points were not visually indicated in the location description.

#### Resolution
Added "Exit to: <parent_location>" display in location descriptions when viewing an exit point inside a SubGrid.

**Changes**:
- `src/cli_rpg/models/location.py`: Added 3 lines to `get_layered_description()` method to show "Exit to: {parent_name}" with cyan coloring
- `tests/test_exit_points.py`: Added `TestExitPointDisplay` test class with 3 test methods

The indicator appears after the "Exits:" line (cardinal directions) but before the "Enter:" line, maintaining logical grouping of navigation information.
