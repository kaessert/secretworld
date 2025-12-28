# CLAUDE.md - Project Guide for AI-Assisted Development

## Quick Project Overview

CLI RPG is a command-line role-playing game with AI-generated worlds, combat, inventory management, shops, and save/load functionality. Built with Python 3.9+.

## Testing Commands

```bash
# Full test suite (from project root)
source venv/bin/activate && pytest

# Specific module tests
pytest tests/test_<module>.py -v

# With coverage
pytest --cov=src/cli_rpg

# E2E tests (requires API key in environment)
pytest tests/e2e/ -v --e2e
```

## Project Structure

```
scripts/
├── __init__.py          # Package initialization
├── state_parser.py      # JSON output parsing for agent state
├── ai_agent.py          # Heuristic-based AI agent for playtesting
├── run_simulation.py    # CLI entry point for running simulations
├── generate_test_world.py # Regenerate test world fixture if models change
└── agent/
    ├── __init__.py      # Package exports for personality system
    └── personality.py   # PersonalityType enum, PersonalityTraits dataclass with 5 presets

tests/e2e/
├── __init__.py          # E2E test package
├── conftest.py          # E2E pytest configuration and fixtures
└── test_enterable_locations.py # E2E tests for enterable location generation

src/cli_rpg/
├── main.py              # Entry point
├── game_state.py        # Core game state management
├── world.py             # World generation and navigation
├── world_grid.py        # Grid-based spatial world system
├── world_tiles.py       # Terrain tile definitions, adjacency rules, region planning, visibility radius, enterable categories, forced enterable spawn after 15 tiles
├── wfc.py               # Wave Function Collapse terrain generation
├── wfc_chunks.py        # ChunkManager for infinite terrain via cached WFC chunks
├── map_renderer.py      # ASCII map display with visibility radius support
├── combat.py            # Combat mechanics
├── elements.py          # Elemental damage type system (fire, ice, poison)
├── character_creation.py # Player character setup
├── persistence.py       # Save/load game state
├── autosave.py          # Automatic save functionality
├── ai_service.py        # AI integration for content generation
├── ai_world.py          # AI-powered world content, on-demand SubGrid generation
├── ai_config.py         # AI service configuration
├── location_art.py      # Fallback ASCII art templates for locations
├── npc_art.py           # Fallback ASCII art templates for NPCs
├── location_noise.py    # Simplex noise for location spawn density and clustering
├── progress.py          # Progress indicators for AI generation (spinner, thematic messages)
├── background_gen.py    # Background generation queue for pre-generating adjacent locations
├── config.py            # General configuration
├── colors.py            # ANSI color output utilities
├── text_effects.py      # Typewriter text reveal and dramatic pause effects
├── frames.py            # Stylized borders and frames for UI elements
├── json_output.py       # JSON Lines output for --json mode
├── logging_service.py   # Gameplay logging for --log-file option
├── session_replay.py    # Session replay from log files (--replay, --validate, --continue-at)
├── input_handler.py     # Readline-based input with command history
├── completer.py         # Tab auto-completion for commands and arguments
├── whisper.py           # Ambient whisper system for atmosphere
├── dreams.py            # Dream sequences triggered on rest
├── companion_banter.py  # Context-aware companion travel comments
├── companion_reactions.py # Companion reactions to player combat choices
├── companion_quests.py  # Companion personal quest system
├── dialogue_choices.py  # Dialogue tone selection affecting NPC arc progression
├── random_encounters.py # Random travel encounters (merchants, wanderers, hostiles)
├── encounter_tables.py  # Location-specific encounter rates, enemy pools, merchant items
├── world_events.py      # Living world events (plagues, caravans, invasions)
├── seasons.py           # Seasonal events and festivals system
├── shadow_creature.py   # Shadow creature attack at 100% dread
├── hallucinations.py    # Dread hallucinations at 75-99% dread
├── brave_rewards.py     # Dread treasure rewards for high-dread exploration
├── sound_effects.py     # Terminal bell sound effects for game events
├── social_skills.py     # CHA-based persuade, intimidate, and bribe mechanics
├── secrets.py           # PER-based secret discovery and search mechanics
├── camping.py           # Wilderness camping, foraging, and hunting system
├── crafting.py          # Resource gathering and crafting recipes (gather, craft, recipes commands)
├── economy.py           # Economy helper functions (price modifiers, event integration)
├── ranger.py            # Ranger class abilities (track command, wilderness bonus)
├── ranger_companion.py  # Ranger animal companion commands (tame, summon, feed, companion status)
├── cleric.py            # Cleric class abilities (bless, smite commands)
├── faction_combat.py    # Faction reputation changes from combat outcomes
├── faction_shop.py      # Faction-based shop price modifiers
├── faction_content.py   # Faction-gated NPC/location access based on reputation
├── npc_arc_shop.py      # NPC arc-based shop price modifiers (relationship pricing)
├── npc_arc_quests.py    # NPC arc-based quest prerequisites (relationship gating)
├── settlement_generator.py # District generation for mega-settlements (cities, metropolises, capitals)
├── puzzles.py           # Dungeon puzzle interaction logic (unlock, pull, step, answer, activate)
├── interior_events.py   # Dynamic interior events (cave-ins, monster migrations, rival adventurers) for SubGrid locations
├── hazards.py           # Environmental hazards system (poison gas, darkness, unstable ground, temperature, flooding)
├── environmental_storytelling.py # Environmental details (corpses, bloodstains, journals) for dungeon atmosphere
├── ambient_sounds.py    # Ambient sounds during SubGrid exploration (dripping water, distant screams, etc.)
├── procedural_interiors.py # RoomType enum, RoomTemplate dataclass, BSPNode/BSPGenerator for dungeon layouts, GeneratorProtocol, CATEGORY_GENERATORS for procedural interior layout
├── procedural_quests.py # QuestTemplateType enum, QuestTemplate dataclass, QUEST_TEMPLATES, QUEST_CHAINS, select_quest_template(), scale_quest_difficulty(), generate_quest_chain()
├── content_layer.py     # ContentLayer mediator: bridges procedural RoomTemplates with AI/fallback content to produce populated SubGrids
├── content_cache.py     # Deterministic content cache using world seed + coordinates for reproducible world generation
├── fallback_content.py  # FallbackContentProvider: centralized deterministic fallback templates for rooms, NPCs, items, quests
├── test_world.py        # Demo mode fixture loading (load_test_world, create_demo_game_state)
└── models/
    ├── content_request.py # Typed request/response schemas for content generation (RoomContentRequest, NPCContentRequest, etc.)
    ├── character.py     # Player character model, CLASS_ARMOR_RESTRICTIONS, unlocked_recipes
    ├── district.py      # District model for mega-settlements (DistrictType enum, bounds, atmosphere)
    ├── dread.py         # Dread meter for psychological horror
    ├── economy.py       # Economy state (supply/demand, location bonuses, event disruption)
    ├── tiredness.py     # Tiredness meter for fatigue and sleep mechanics
    ├── enemy.py         # Enemy/monster model with perception stat for stealth detection
    ├── game_time.py     # Day/night cycle and time tracking
    ├── item.py          # Item definitions, ArmorWeight enum (LIGHT, MEDIUM, HEAVY), ItemType.HOLY_SYMBOL with divine_power stat
    ├── inventory.py     # Inventory management, equipped_holy_symbol slot for Cleric
    ├── location.py      # Location with coordinates and NPCs (movement via coordinate adjacency), puzzles, blocked_directions, hazards
    ├── npc.py           # Non-player character model with relationship support
    ├── puzzle.py        # Puzzle model with types (LOCKED_DOOR, LEVER, PRESSURE_PLATE, RIDDLE, SEQUENCE)
    ├── npc_relationship.py # NPC relationship types and trust levels
    ├── npc_network.py   # NPC network manager for family generation and network queries
    ├── npc_arc.py       # NPC character arc progression (stages, interactions, serialization)
    ├── quest.py         # Quest system with objectives, progress tracking, and world effects (WorldEffect dataclass for permanent world changes on completion)
    ├── quest_network.py # QuestNetworkManager for interconnected quest storylines
    ├── quest_outcome.py # Quest completion outcomes for NPC memory/reactions
    ├── shop.py          # Shop system
    ├── status_effect.py # Status effects (poison, buffs, debuffs)
    ├── random_encounter.py # Random encounter model for travel events
    ├── world_event.py   # World event model for timed events
    ├── weather.py       # Weather system (clear, rain, storm, fog)
    ├── companion.py     # Companion model with bond levels
    ├── animal_companion.py # Ranger animal companion model (AnimalType enum, AnimalCompanion dataclass)
    ├── weapon_proficiency.py # Weapon proficiency progression system
    ├── crafting_proficiency.py # Crafting skill progression system (NOVICE → MASTER levels)
    ├── faction.py       # Faction reputation system
    ├── world_context.py # Cached world theme context for layered AI generation
    ├── region_context.py # Region-level context for layered AI generation (Layer 2)
    ├── settlement_context.py # Settlement-level context for layered AI generation (Layer 5)
    ├── lore_context.py  # Lore context for historical events, legends (Layer 6)
    ├── generation_context.py # Unified context aggregator for AI prompt generation
    └── world_state.py   # World state tracking for permanent changes (boss defeats, NPC deaths, quest world effects, area cleared, etc.)
```

## Key Architectural Patterns

- **Grid-based world** (`world_grid.py`): Spatial consistency with coordinate-based navigation
- **SubGrid architecture**: Interior locations use bounded SubGrid instances (not the main world dict). Entry points marked with `is_exit_point=True` allow exiting back to overworld. SubGrid bounds vary by location category via `SUBGRID_BOUNDS` config and `get_subgrid_bounds(category)` helper (e.g., caves are 3x3, dungeons 7x7, cities 17x17, metropolises 25x25, capitals 33x33). **On-demand generation**: Named overworld locations with enterable categories (dungeons, caves, towns, etc. defined in `ENTERABLE_CATEGORIES`) generate SubGrids when the player first enters via `generate_subgrid_for_location()`. **Multi-level support**: SubGrids use 6-tuple bounds `(min_x, max_x, min_y, max_y, min_z, max_z)` for vertical navigation - dungeons extend downward (z<0), towers extend upward (z>0). Use `go up`/`go down` for vertical movement. **District system**: Mega-settlements (cities, metropolises, capitals with bounds ≥17) have districts with distinct types (MARKET, TEMPLE, RESIDENTIAL, etc.), atmosphere, and prosperity levels. Districts are generated via `settlement_generator.generate_districts()` and stored in `SubGrid.districts`.
- **Location model**: Each location has coordinates and NPCs; movement is determined by coordinate adjacency (going north from (0,0) leads to (0,1)). Hierarchical navigation via `enter`/`exit` commands supports overworld/sub-location relationships. Locations have `is_named` flag: unnamed locations (generic terrain) skip NPC generation; named locations (towns, dungeons) get full AI-generated NPCs.
- **GameState**: Central manager for character, world, combat, and shop state. Tracks `seen_tiles` (set of coordinates within visibility radius) separately from visited locations for map rendering.
- **AI service**: Optional integration with graceful fallback when unavailable
- **Dataclasses**: Used extensively for models (Character, Item, Location, etc.)

## Coding Standards

- **Python**: 3.9+
- **Line length**: 100 (enforced by black/ruff)
- **Type hints**: Encouraged throughout
- **Models**: Use dataclasses
- **Formatting**: black
- **Linting**: ruff

## Running the Game

```bash
source venv/bin/activate
cli-rpg

# Demo mode (pre-generated world, no AI required)
cli-rpg --demo
```
