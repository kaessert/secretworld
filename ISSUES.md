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

**Remaining**:
- Riddles and puzzles
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
**Status**: PENDING
**Priority**: HIGH

Expand SubGrid bounds for larger cities and add district system.

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

**Files to Create**:
- `src/cli_rpg/models/npc_relationship.py`

**Files to Modify**:
- `src/cli_rpg/models/npc.py`

---

### Issue 11: NPC Network Manager
**Status**: PENDING
**Priority**: MEDIUM

Create manager for NPC networks and family generation.

**Files to Create**:
- `src/cli_rpg/models/npc_network.py`

---

### Issue 12: World State Evolution
**Status**: PENDING
**Priority**: HIGH

Track persistent world changes from quest outcomes and player actions.

**Files to Create**:
- `src/cli_rpg/models/world_state.py`

**Files to Modify**:
- `src/cli_rpg/game_state.py` - Integrate WorldStateManager

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
**Status**: PENDING
**Priority**: P2

**Problem**: Random encounters use the same tables everywhere. Dungeon encounters feel identical to forest encounters.

**Acceptance Criteria:**
- [ ] **Dungeon**: undead, constructs, cultists
- [ ] **Cave**: beasts, spiders, giant bats
- [ ] **Ruins**: ghosts, treasure hunters, golems
- [ ] **Forest**: wolves, bandits, fey creatures
- [ ] **Temple**: dark priests, animated statues
- [ ] Category-specific merchant inventories
- [ ] Encounter rate varies by category

**Related Files:**
- `src/cli_rpg/random_encounters.py`
- `src/cli_rpg/combat.py`
- New `src/cli_rpg/encounter_tables.py`

---

### Issue 22: Location-Themed Hallucinations
**Status**: PENDING
**Priority**: P2

**Problem**: High-dread hallucinations use the same 3 templates everywhere regardless of location.

**Acceptance Criteria:**
- [ ] **Dungeon**: ghostly prisoners, skeletal warriors
- [ ] **Forest**: twisted treants, shadow wolves
- [ ] **Temple**: fallen priests, dark angels
- [ ] **Cave**: eyeless horrors, dripping shadows
- [ ] Hallucination descriptions reference location-specific elements

**Related Files:**
- `src/cli_rpg/hallucinations.py`
- `src/cli_rpg/ai_service.py`

---

### Issue 23: Dungeon Puzzle Mechanics
**Status**: PENDING
**Priority**: P2

**Problem**: No interactive puzzles exist in dungeons. Gameplay is combat-only.

**Acceptance Criteria:**
- [ ] **Locked doors** requiring keys found in other rooms
- [ ] **Pressure plates/levers** that open passages
- [ ] **Riddle NPCs** guarding boss rooms
- [ ] **Sequence puzzles** (light torches in order)
- [ ] INT stat provides hints for puzzle solving
- [ ] 1-2 puzzles per dungeon area

**Related Files:**
- New `src/cli_rpg/puzzles.py`
- `src/cli_rpg/models/location.py`
- `src/cli_rpg/game_state.py`

---

### Issue 24: Exploration Progress Tracking
**Status**: PENDING
**Priority**: P2

**Problem**: No tracking of dungeon completion exists. No reward for thorough exploration.

**Acceptance Criteria:**
- [ ] Track visited rooms in SubGrid (persisted in save)
- [ ] "Fully explored" bonus (XP + gold) when all rooms visited
- [ ] Discovery milestones: first secret, all treasures, boss defeated
- [ ] Exploration percentage visible in `map` command
- [ ] Visited rooms marked differently on map

**Related Files:**
- `src/cli_rpg/models/location.py`
- `src/cli_rpg/world_grid.py`
- `src/cli_rpg/game_state.py`
- `src/cli_rpg/map_renderer.py`

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
- Location-specific encounters
- Themed hallucinations

**Phase 4 - Non-Combat Depth (P2)** - Issues 23-24
- Puzzle mechanics
- Exploration progress tracking

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
- Mega-settlements with districts

**Phase 5: NPC Networks** - Issues 10-11
- Relationship system
- NPC network manager

**Phase 6: World Evolution** - Issues 12-13
- World state tracking
- NPC character arcs

**Phase 7: Economy & Quests** - Issues 14-15
- Living economy
- Quest networks
