## Active Issues

---

### Rest Command Tiredness Threshold Mismatch
**Status**: ACTIVE - Documentation/Implementation Discrepancy
**Priority**: LOW
**Date Added**: 2025-12-27

#### Description
The README documentation states "Sleep is only available when tiredness reaches 30+" but the actual implementation allows rest at any tiredness level above 0%.

#### Resolution Options
**Option A - Fix Documentation**: Update README.md to accurately describe rest behavior:
- "Rest is available when health/stamina need recovery, dread needs reducing, or tiredness is above 0%"

**Option B - Fix Implementation**: Enforce the documented 30% threshold in `game_state.py`:
- Only allow rest when tiredness >= 30 (or other conditions like low HP/stamina/dread)

#### Related Files
- `README.md` - Line 109: Claims "Sleep is only available when tiredness reaches 30+"
- `src/cli_rpg/game_state.py` - Contains `rest()` method implementation

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
**Status**: ACTIVE (Core Complete)

**Implemented**:
- AI-generated secrets for dungeon, cave, ruins, temple, and forest locations (1-2 secrets per location)
- Passive secret detection when entering new areas (PER-based, "You notice: [description]" messages)
- Active secret discovery via `search` command (PER-based checks with +5 bonus)
- Secret thresholds scale with distance from entry (deeper locations = harder secrets)
- Reward system for discovered secrets
- Hidden rooms in SubGrid locations
- Dungeon puzzles (Issue 23 - Complete)

**Remaining**:
- Environmental storytelling

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

### Issue 6: Progress Feedback System
**Status**: PENDING
**Priority**: MEDIUM

Add visual progress bars and thematic loading messages during AI generation.

**Files to Create**:
- `src/cli_rpg/progress.py`

**Files to Modify**:
- `pyproject.toml` - Add rich dependency

---

### Issue 7: LLM Streaming Support
**Status**: PENDING
**Priority**: MEDIUM

Add streaming support to AIService for live text display during generation.

**Files to Modify**:
- `src/cli_rpg/ai_service.py`

---

### Issue 8: Background Generation Queue
**Status**: PENDING
**Priority**: MEDIUM

Pre-generate adjacent regions in background to eliminate blocking during movement.

**Files to Create**:
- `src/cli_rpg/background_gen.py`

**Files to Modify**:
- `src/cli_rpg/game_state.py`
- `src/cli_rpg/main.py` - Initialize background system

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
**Status**: PENDING
**Priority**: MEDIUM

Add character arc progression for NPCs based on player interactions.

**Files to Create**:
- `src/cli_rpg/models/npc_arc.py`

---

### Issue 14: Living Economy System
**Status**: PENDING
**Priority**: MEDIUM

Create dynamic economy with supply/demand and trade routes.

**Files to Create**:
- `src/cli_rpg/models/economy.py`

**Files to Modify**:
- `src/cli_rpg/models/shop.py` - Use economy modifiers

---

### Issue 15: Interconnected Quest Networks
**Status**: PENDING
**Priority**: MEDIUM

Create storyline system with branching quests and investigations.

**Files to Create**:
- `src/cli_rpg/models/quest_network.py`

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
**Status**: PENDING
**Priority**: P3

**Problem**: World events only affect the overworld. Dungeon interiors feel static.

**Acceptance Criteria:**
- [ ] **Cave-in**: Temporarily blocks passages
- [ ] **Monster migration**: Changes enemy spawn locations
- [ ] **Rival adventurers**: NPCs racing player to boss/treasure
- [ ] **Ritual in progress**: Time-limited boss fight
- [ ] **Spreading hazard**: Fire/flooding through dungeon

**Related Files:**
- `src/cli_rpg/world_events.py`
- `src/cli_rpg/game_state.py`
- `src/cli_rpg/world_grid.py`

---

### Issue 26: Environmental Hazards
**Status**: PENDING
**Priority**: P3

**Problem**: Movement in dungeons is always safe. No environmental challenges.

**Acceptance Criteria:**
- [ ] **Poison gas**: Periodic damage, mitigated by antidotes
- [ ] **Darkness**: Reduces perception, requires torch
- [ ] **Unstable ground**: Chance to fall (DEX check)
- [ ] **Extreme cold/heat**: Tiredness drain
- [ ] **Flooded rooms**: Slows movement
- [ ] Class/item mitigation (Ranger ignores natural hazards)

**Related Files:**
- New `src/cli_rpg/hazards.py`
- `src/cli_rpg/models/location.py`
- `src/cli_rpg/game_state.py`

---

### Issue 27: Dungeon Ambiance System
**Status**: PENDING
**Priority**: P3

**Problem**: Dungeons have limited atmospheric feedback beyond static descriptions.

**Acceptance Criteria:**
- [ ] **Ambient sounds**: Dripping water, distant screams
- [ ] **Progressive dread**: Deeper levels increase dread faster
- [ ] **Environmental storytelling**: Corpses, bloodstains, journals
- [ ] **Weather penetration**: Rain sounds near cave entrance
- [ ] **Day/night effects**: Undead more active at night
- [ ] **Location-specific whispers**: Dungeon whispers differ from forest

**Related Files:**
- `src/cli_rpg/whisper.py`
- `src/cli_rpg/models/location.py`
- `src/cli_rpg/game_state.py`
- `src/cli_rpg/models/dread.py`

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
- Interior events
- Environmental hazards
- Ambiance system

### AI Content Generation (Remaining)

**Phase 3: Progress Feedback** - Issues 6-8
- Progress bars
- LLM streaming
- Background generation

**Phase 4: Settlement Scale** - Issue 9
- ✓ Mega-settlements with districts (Issue 9 complete)

**Phase 5: NPC Networks** - Issues 10-11
- ✓ Relationship system (Issue 10 complete)
- ✓ NPC network manager (Issue 11 complete)

**Phase 6: World Evolution** - Issues 12-13
- ✓ World state tracking (Issue 12 complete)
- NPC character arcs

**Phase 7: Economy & Quests** - Issues 14-15
- Living economy
- Quest networks
