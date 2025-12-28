## Active Issues

---

### Interior Navigation Bug - Rooms Not Connected
**Status**: FIXED
**Priority**: CRITICAL
**Date Added**: 2025-12-28
**Date Fixed**: 2025-12-28

#### Problem
Interiors (dungeons, sanctuaries, etc.) were generated with rooms but players couldn't navigate between them. The map showed "Exits: None" even though multiple rooms existed.

**Symptom:**
```
=== INTERIOR MAP === (Inside: Neon Heights Sanctuary, Level 1)
Explored: 1/16 rooms (6%)
┌────────────────────────────────────────┐
│      -1   0   1   2   3   4   5   6   7│
│  4    █   █   █   █   █   █   █        │
│  0    █   █   █   █   @   █   █        │
│ -3    █   █   █   █   I   █   █        │
└────────────────────────────────────────┘
Exits: None  <-- BUG: Should show exits
```

#### Root Cause
1. **BSP Generator creates rooms at non-adjacent coordinates**: The BSP algorithm places rooms at partition centers (e.g., (4,0) and (4,-3)), which aren't at adjacent grid positions.

2. **Navigation relied on coordinate adjacency**: `Location.get_available_directions()` checked for Location objects at adjacent coordinates `(x±1, y±1)`. Since BSP rooms aren't adjacent, no exits were found.

3. **RoomTemplate connections were ignored**: Procedural generators created `RoomTemplate` objects with explicit `connections` (like `["east", "south"]`), but these were never transferred to the actual `Location` objects.

#### Fix Applied
1. **Added `allowed_exits` field to Location** (`models/location.py:65`):
   - New field stores explicit exit directions from procedural generation
   - Overrides coordinate-based lookup when set

2. **Transfer connections in ContentLayer** (`content_layer.py:188`):
   - `template.connections` are now copied to `location.allowed_exits`

3. **Updated `get_available_directions()`** (`models/location.py:126-133`):
   - Checks `allowed_exits` first for SubGrid navigation
   - Falls back to coordinate-based lookup for backward compatibility

4. **Updated `_move_in_sub_grid()`** (`game_state.py:1056-1101`):
   - Finds destination rooms via `allowed_exits` matching
   - Uses relative position + opposite direction to find connected room
   - Picks closest candidate when multiple matches exist

#### Files Changed
- `src/cli_rpg/models/location.py` - Added `allowed_exits` field, updated serialization
- `src/cli_rpg/content_layer.py` - Transfer `template.connections` to `location.allowed_exits`
- `src/cli_rpg/game_state.py` - Updated `_move_in_sub_grid()` to use `allowed_exits`

---

### Increase Named Location Density and Enterability
**Status**: COMPLETE
**Priority**: HIGH
**Date Added**: 2025-12-28
**Date Completed**: 2025-12-28

#### Problem
The world feels empty and exploration is unrewarding. Players walk too many tiles without encountering cities, dungeons, or other interesting named locations. When they do find named locations, many cannot be entered.

#### Goals
1. **More Cities/Towns**: Increase spawn rate of settlements (cities, towns, villages, outposts)
2. **More Dungeons/Caves**: Increase spawn rate of adventure locations (dungeons, caves, ruins, temples, tombs)
3. **All Named Locations Enterable**: Every named location (`is_named=True`) should be enterable with a SubGrid interior

#### Completed Work (2025-12-28)

**✅ All Named Locations Now Enterable**

Added 5 new wilderness POI categories to `ENTERABLE_CATEGORIES`:
- `grove` - Forest clearing with druid/hermit
- `waystation` - Mountain/road rest stop
- `campsite` - Wilderness camp
- `hollow` - Hidden forest area
- `overlook` - Scenic viewpoint with structure

Created `WILDERNESS_ENTERABLE_FALLBACK` mapping for non-enterable → enterable conversion:
- forest → grove
- wilderness → campsite
- mountain → waystation
- desert → campsite
- swamp → hollow
- beach → campsite
- plains → waystation
- hills → overlook
- foothills → waystation

Added `get_enterable_category()` helper function that converts any category to an enterable one.

All new categories use 3x3 single-level bounds and SingleRoomGenerator.

**Files Changed:**
- `src/cli_rpg/world_tiles.py` - New categories, fallback mapping, helper function
- `src/cli_rpg/world_grid.py` - SubGrid bounds for new categories
- `src/cli_rpg/procedural_interiors.py` - Generator mappings
- `src/cli_rpg/fallback_content.py` - Room and treasure templates
- `tests/test_named_locations_enterable.py` - 20 new tests

#### Implementation Summary

**1. Reduce Tiles Between Enterables:**
```python
# world_tiles.py
MAX_TILES_WITHOUT_ENTERABLE = 15  # Reduced from 25 for more density
```

**2. Increase Base Spawn Rates:**
```python
# location_noise.py
BASE_SPAWN_PROBABILITY = 0.20  # Was 0.15, ~33% more named locations
```

#### Acceptance Criteria
- [ ] Named locations appear every 10-15 tiles on average (was ~25)
- [ ] Cities/towns appear at least once per 50 tiles explored
- [ ] Dungeons/caves appear at least once per 30 tiles explored
- [x] ALL named locations can be entered (no "You cannot enter here" for named places)
- [x] Wilderness named locations have small but interesting interiors

#### Related Files
- `src/cli_rpg/world_tiles.py` - `MAX_TILES_WITHOUT_ENTERABLE`, `ENTERABLE_CATEGORIES`
- `src/cli_rpg/location_noise.py` - Spawn density thresholds
- `src/cli_rpg/ai_world.py` - `generate_subgrid_for_location()`
- `src/cli_rpg/game_state.py` - `enter()` command, `tiles_since_enterable`
- `src/cli_rpg/world_grid.py` - `SUBGRID_BOUNDS` for new categories

---

### Scripted Playthrough for Feature Validation
**Status**: ACTIVE
**Priority**: HIGH
**Date Added**: 2025-12-28

#### Problem
Game features are validated manually, which is time-consuming and error-prone. Need automated scripted playthroughs that exercise each major feature systematically to catch regressions and verify functionality.

#### Goal
Create scripted test sessions that walk through each game feature, issuing commands and validating expected outcomes.

#### Features to Cover
- [ ] Character creation (all 5 classes)
- [ ] Movement and navigation (overworld, SubGrid entry/exit, vertical z-levels)
- [ ] Combat (attack, abilities, flee, stealth kills, companion combat)
- [ ] NPC interaction (talk, dialogue choices, arc progression, shop, quest acceptance)
- [ ] Inventory management (equip, unequip, use, drop, armor restrictions, holy symbols)
- [ ] Quests (accept, track, complete, world effects, quest chains)
- [ ] Crafting and gathering (gather, craft, skill progression, rare recipes)
- [ ] Exploration (map, secrets, puzzles, treasures, exploration bonus)
- [ ] Rest and camping (rest, camp, forage, hunt, dreams)
- [ ] Economy (buy, sell, price modifiers, supply/demand)
- [ ] Environmental hazards (poison gas, darkness, flooding, temperature)
- [ ] Interior events (cave-ins, monster migration, rivals, rituals, spreading hazards)
- [ ] Ranger companion (tame, summon, dismiss, feed, combat integration)
- [ ] Social skills (persuade, intimidate, bribe)
- [ ] Save/load (persistence, backward compatibility)

#### Critical Requirement: Real AI Content Generation
**The scripted playthroughs MUST use real AI content generation, not mocks or fallbacks.**

- ✅ Load `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) from `.env` file - **IMPLEMENTED**: `run_simulation.py` uses `python-dotenv` to load `.env` files
- ✅ Use `--with-ai` flag to enable real AI generation: `python -m scripts.run_simulation --with-ai --max-commands=100`
- AI-generated content is crucial for validating:
  - **Locations**: Names, descriptions, categories, theme consistency
  - **NPCs**: Names, dialogue, personas, greetings, shop flavor text
  - **Quests**: Narrative wrapping, objectives, completion text, world effects
  - **Enemies**: Names, descriptions, stats, abilities, flavor text
  - **Items**: Weapons, armor, consumables with themed names/stats
  - **Lore**: World history, legends, prophecies, creation myths
  - **Context layers**: WorldContext → RegionContext → SettlementContext propagation
  - **ASCII art**: Location art, NPC art, quality and theme matching
  - **Dreams**: Rest dream sequences matching world theme
  - **Whispers**: Atmospheric whispers matching location/depth
  - **Companion banter**: Context-aware travel comments
  - **Environmental storytelling**: Corpses, journals, bloodstains
  - **Shop inventories**: Themed merchant stock
  - **Secret descriptions**: Hidden treasure, traps, lore hints
  - **Puzzle riddles**: AI-generated riddle text for RIDDLE puzzles
  - **Region landmarks**: AI-generated landmark names for EXPLORE quests
  - **NPC relationships**: Family/network generation coherence

#### Implementation Options
1. **Extend existing simulation**: Build on `scripts/ai_agent.py` and `scripts/run_simulation.py`
2. **Pytest-based scenarios**: Integration tests that run command sequences
3. **Replay system**: Use `--replay` with pre-recorded sessions and `--validate` assertions

#### Acceptance Criteria
- [ ] Scripted playthrough covers all major features listed above
- [x] **Loads API key from .env and uses real AI generation** (via `--with-ai` flag in `run_simulation.py`)
- [ ] Runs deterministically with fixed seed (structure deterministic, AI content cached)
- [ ] Outputs pass/fail for each feature area
- [ ] Can be run in CI/CD pipeline (with API key as secret)
- [ ] Documents expected behavior for each test scenario
- [ ] Logs AI-generated content for review (uses existing `log_ai_content()`)

#### Related Files
- `scripts/ai_agent.py` - Existing heuristic AI agent
- `scripts/run_simulation.py` - Simulation runner
- `src/cli_rpg/session_replay.py` - Replay system
- `tests/e2e/` - Existing E2E test infrastructure

---

### Automated Playtesting Infrastructure Improvements
**Status**: OPEN
**Priority**: HIGH
**Date Added**: 2025-12-28

#### Problem
The current AI agent in `scripts/ai_agent.py` lacks save/restore capabilities, behaves deterministically (not human-like), and has no comprehensive validation framework. Playtesting sessions cannot be resumed after interruption, and there's no systematic way to detect feature regressions.

#### Goals
1. **Save/Restore**: Checkpoint agent progress, recover crashed sessions, branch exploration
2. **Human-Like Behavior**: Personality profiles, memory, class-specific behaviors, environmental awareness
3. **Validation Framework**: Assertions, coverage tracking, failure classification, regression detection

---

#### Part 1: Save/Load System

**Architecture:**
```
simulation_saves/
├── sessions/{seed}_{timestamp}/
│   ├── session_meta.json         # Session metadata
│   ├── checkpoints/              # Agent + game snapshots
│   │   ├── auto_0001.json
│   │   ├── quest_accept_0002.json
│   │   └── boss_0003.json
│   ├── game_saves/               # Corresponding game saves
│   ├── crash_recovery.json       # Latest state for recovery
│   └── command_log.jsonl         # Full command history
├── branches/{branch_name}/       # Alternate exploration paths
└── latest_session.txt            # Pointer to most recent
```

**Checkpoint Triggers:**
- `QUEST_ACCEPT` / `QUEST_COMPLETE` - Quest milestones
- `DUNGEON_ENTRY` / `DUNGEON_EXIT` - Sub-location transitions
- `BOSS_ENCOUNTER` / `BOSS_DEFEAT` - Boss fights
- `DEATH` / `LEVEL_UP` - Character events
- `INTERVAL` - Every 50 commands
- `CRASH_RECOVERY` - Continuous background save

**New Files:**
- `scripts/agent_checkpoint.py` - AgentCheckpoint dataclass
- `scripts/agent_persistence.py` - SessionManager class
- `scripts/checkpoint_triggers.py` - Trigger detection

**CLI Extensions:**
```bash
python -m scripts.run_simulation --recover                    # Resume crashed session
python -m scripts.run_simulation --from-checkpoint=boss_0003  # Resume from point
python -m scripts.run_simulation --branch=alternate --from-checkpoint=quest_0002
```

---

#### Part 2: Human-Like Agent Behavior

**New Package: `scripts/agent/`**
```
scripts/agent/
├── personality.py         # PersonalityType enum, PersonalityTraits dataclass
├── memory.py              # AgentMemory with failure tracking, NPC memory
├── class_behaviors.py     # Class-specific combat/exploration strategies
├── environmental.py       # Time/weather/hazard awareness
├── social_intelligence.py # NPC interaction, dialogue choices
├── decision_timing.py     # Variable response timing, hesitation
├── strategic_planning.py  # Multi-step quest/dungeon planning
└── resource_manager.py    # Potion/camping/crafting decisions
```

**Personality Presets:**
| Type | Risk | Exploration | Social | Combat | Conservation |
|------|------|-------------|--------|--------|--------------|
| CAUTIOUS_EXPLORER | 0.2 | 0.9 | 0.7 | 0.3 | 0.7 |
| AGGRESSIVE_FIGHTER | 0.9 | 0.4 | 0.3 | 0.9 | 0.2 |
| COMPLETIONIST | 0.5 | 1.0 | 1.0 | 0.5 | 0.4 |
| SPEEDRUNNER | 0.7 | 0.1 | 0.1 | 0.4 | 0.3 |
| ROLEPLAYER | 0.5 | 0.7 | 0.9 | 0.5 | 0.5 |

**Memory System:**
- `failures: list[FailureRecord]` - Learn from deaths/damage
- `npc_memories: dict[str, NPCMemory]` - Relationship history
- `location_memories: dict[str, LocationMemory]` - Danger/secret tracking
- `dangerous_enemies: set[str]` - Enemy types that killed us

**Class-Specific Behaviors:**
| Class | Combat | Exploration |
|-------|--------|-------------|
| Warrior | Bash, aggressive/berserker stance | Direct approach |
| Mage | Fireball/ice_bolt, self-heal | Conserve mana |
| Rogue | Sneak attacks, hide | Search for secrets |
| Ranger | Summon companion, track | Wilderness comfort |
| Cleric | Smite undead, bless, heal | Holy symbol equipped |

**Environmental Awareness:**
- Day/night cycle (undead +50% at night)
- Weather effects (storms, fog)
- Dread level (hesitation, paralysis)
- Tiredness (rest decisions)

**Decision Timing Variability:**
- Base: 0.5s, Danger hesitation: +1.5s
- Combat adrenaline: 0.5x delay
- Dread paralysis: proportional to dread
- 10% reconsideration chance

**CLI Extensions:**
```bash
python -m scripts.run_simulation --personality=cautious --class=ranger
python -m scripts.run_simulation --human-timing
```

---

#### Part 3: Validation Framework

**New Package: `scripts/validation/`**
```
scripts/validation/
├── assertions.py         # Assertion types and checking
├── coverage.py           # FeatureCoverage tracker
├── failures.py           # FailureCategory classification
├── reporting.py          # JSON/Markdown/HTML reports
├── scenarios.py          # YAML scenario runner
├── regression.py         # Baseline comparison
└── ai_quality.py         # AI content validators
```

**Assertion Types:**
- `STATE_EQUALS` / `STATE_CONTAINS` / `STATE_RANGE` - State validation
- `NARRATIVE_MATCH` - Regex pattern matching
- `COMMAND_VALID` / `COMMAND_EFFECT` - Command validation
- `CONTENT_PRESENT` / `CONTENT_QUALITY` - AI content validation

**Feature Coverage Tracking:**
- Character creation (all 5 classes)
- Movement (overworld, subgrid, vertical)
- Combat (attacks, abilities, flee, stealth, companions)
- NPC (dialogue, shops, quests)
- Inventory (equip, use, restrictions)
- Crafting (gather, craft, skill progression)
- Exploration (secrets, puzzles, treasures)
- Environmental (hazards, events)
- Persistence (save/load)

**Failure Categories:**
- **Critical**: CRASH, INFINITE_LOOP, SAVE_CORRUPTION
- **Logic**: STATE_DESYNC, COMMAND_REJECTED, COMMAND_WRONG_EFFECT
- **Content**: CONTENT_EMPTY, CONTENT_MALFORMED, FALLBACK_USED
- **Quality**: CONTENT_QUALITY, BALANCE_ISSUE

**YAML Scenario Scripts:**
```yaml
scenario:
  name: "Basic Combat Validation"
  steps:
    - command: "attack"
      wait_for: "in_combat"
      assertions:
        - type: STATE_EQUALS
          field: "in_combat"
          value: true
```

**Regression Detection:**
- Store baselines in `scripts/baselines/`
- Compare pass rate, coverage, failures
- Flag new failures and resolved issues

**CLI Interface:**
```bash
python -m scripts.run_validation --seed=42 --scenario=combat/basic.yaml
python -m scripts.run_validation --validate-ai-content --ai-quality-threshold=0.7
python -m scripts.run_validation --baseline=v1.0.json --detect-regression
python -m scripts.run_validation --report-format=html --output=report.html
```

---

#### Implementation Phases

**Phase 1: Save/Load Infrastructure (HIGH)** ✅ COMPLETE
1. ✅ Create `scripts/agent_checkpoint.py` with AgentCheckpoint dataclass
2. ✅ Create `scripts/agent_persistence.py` with SessionManager
3. ✅ Create `scripts/checkpoint_triggers.py` with trigger detection
4. ✅ Add checkpoint methods to Agent class (`to_checkpoint_dict()`, `restore_from_checkpoint()`)
5. ✅ Integrate into GameSession (`_check_triggers()`, `_create_checkpoint()`, `from_checkpoint()`)
6. ✅ Add CLI flags to run_simulation.py (`--recover`, `--from-checkpoint`, `--no-checkpoints`, `--checkpoints-dir`)

**Phase 2: Human-Like Agent Core (HIGH)** ✅ COMPLETE
1. ✅ Create `scripts/agent/` package
2. ✅ Implement personality.py with 5 presets (PersonalityType enum, PersonalityTraits dataclass, serialization)
3. ✅ Implement memory.py with failure tracking (FailureRecord, NPCMemory, LocationMemory, AgentMemory)
4. ✅ Implement class_behaviors.py for all 5 classes (CharacterClassName enum, ClassBehaviorConfig, ClassBehavior Protocol, 5 behavior classes with combat/exploration strategies, 47 tests)
5. ✅ Extend AgentState with environmental fields (`time_of_day`, `hour`, `season`, `weather`, `tiredness`) and helper methods (`is_night()`, `is_tired()`, `is_exhausted()`, `is_bad_weather()`, `should_rest()`)
6. ✅ Create HumanLikeAgent class (`scripts/human_like_agent.py`) integrating personality, class behaviors, and memory with observable behavioral differences (21 tests)

**Phase 3: Validation Framework (MEDIUM)** ✅ COMPLETE
1. ✅ Create `scripts/validation/` package
2. ✅ Implement assertion types and checking (8 assertion types: STATE_EQUALS, STATE_CONTAINS, STATE_RANGE, NARRATIVE_MATCH, COMMAND_VALID, COMMAND_EFFECT, CONTENT_PRESENT, CONTENT_QUALITY placeholder)
3. ✅ Implement FeatureCoverage tracker (14 categories, 50 features, FeatureEvent/CoverageStats dataclasses, record/get_coverage_by_category/get_uncovered_features/get_coverage_percentage methods, full serialization)
4. ✅ Create YAML scenario format and runner (ScenarioRunner with run/run_scenario methods, Scenario/ScenarioStep/StepResult/ScenarioResult dataclasses, wait_for support, 17 tests)
5. ✅ Create initial scenarios for core features (11 YAML scenarios in scripts/scenarios/: movement (basic_navigation, subgrid_entry_exit, vertical_navigation), combat, inventory, NPC, exploration, rest; seeds 42001-42011; validated by tests/test_scenario_files.py)

**Phase 4: Advanced Features (LOW)** - IN PROGRESS
1. Decision timing variability
2. Social intelligence and dialogue choices
3. Strategic planning for dungeons/quests
4. ✅ Regression detection (`scripts/validation/regression.py` with `RegressionDetector`, `RegressionBaseline`, `RegressionReport`, baseline comparison)
5. ✅ AI content quality validation (`scripts/validation/ai_quality.py` with `ContentQualityChecker`, `ContentType`, `QualityResult` - validates location/NPC/quest/item content for length bounds, placeholder detection, valid values)

---

#### Acceptance Criteria
- [x] Can interrupt simulation, resume from checkpoint, get identical results (Phase 1 - COMPLETE)
- [x] Observable behavioral differences between personalities and classes (Phase 2 - COMPLETE)
- [x] Track which features are exercised, identify coverage gaps (Phase 3 - FeatureCoverage tracker COMPLETE)
- [x] Initial YAML scenarios for core features created and validated (Phase 3 Step 5 - 11 scenarios COMPLETE)
- [x] Detect feature regressions automatically with clear reports (Phase 4 - `RegressionDetector` COMPLETE)
- [x] Validate AI-generated content meets quality standards (Phase 4 - `ContentQualityChecker` COMPLETE with 12 tests)

#### Related Files
- `scripts/ai_agent.py` - Core agent to extend
- `scripts/state_parser.py` - AgentState to extend
- `scripts/run_simulation.py` - CLI to extend
- `scripts/scenarios/` - YAML validation scenarios (11 files organized by feature, including vertical_navigation.yaml)
- `scripts/validation/regression.py` - Regression detection (RegressionDetector, baselines, comparison)
- `scripts/validation/ai_quality.py` - AI content quality validation (ContentQualityChecker, ContentType, QualityResult)
- `scripts/baselines/` - Directory for storing baseline files
- `tests/test_scenario_files.py` - Scenario validation tests
- `tests/test_validation_regression.py` - Regression detection tests (16 tests)
- `tests/test_ai_quality.py` - AI quality validation tests (12 tests)
- `tests/test_validation_assertions.py` - Assertion checker tests including CONTENT_QUALITY type
- `src/cli_rpg/persistence.py` - Game save/load to integrate

#### Full Plan
See: `/Users/tkaesser/.claude/plans/rippling-percolating-biscuit.md`

---

### Confusing `enter` Command Error Message at Named Locations
**Status**: FIXED
**Priority**: MEDIUM
**Date Added**: 2025-12-28
**Date Fixed**: 2025-12-28

#### Problem
When a user is at a named location (e.g., "Dark Cave") that has an enterable SubGrid, the `look` command shows:
```
Dark Cave
A gaping cave mouth opens in the hillside. Cold air flows from within.
Exits: west
Enter: Cave Entrance
```

The natural user behavior is to type `enter Dark Cave` (the location name they see), but this failed with a confusing error message listing internal SubGrid room names.

#### Fix Applied
When `enter <name>` fails to match a SubGrid room, the code now checks if `<name>` matches the current overworld location's name (exact or partial match). If so, it automatically redirects to the entry_point.

**Behavior after fix:**
- `enter Dark Cave` at Dark Cave → enters through Cave Entrance ✓
- `enter dark` at Dark Cave → enters through Cave Entrance (partial match) ✓
- Invalid names still show helpful error message with available rooms ✓

#### Files Changed
- `src/cli_rpg/game_state.py` (~lines 1435-1444) - Added logic to detect parent location name and redirect to entry_point
- `tests/test_game_state.py` (~lines 1216-1305) - Added tests for exact and partial match redirection

#### Related Files
- `src/cli_rpg/game_state.py` - `enter()` command implementation
- `src/cli_rpg/models/location.py` - Location model and SubGrid relationships
