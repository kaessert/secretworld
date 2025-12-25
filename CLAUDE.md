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
```

## Project Structure

```
src/cli_rpg/
├── main.py              # Entry point
├── game_state.py        # Core game state management
├── world.py             # World generation and navigation
├── world_grid.py        # Grid-based spatial world system
├── map_renderer.py      # ASCII map display for explored locations
├── combat.py            # Combat mechanics
├── character_creation.py # Player character setup
├── persistence.py       # Save/load game state
├── autosave.py          # Automatic save functionality
├── ai_service.py        # AI integration for content generation
├── ai_world.py          # AI-powered world content
├── ai_config.py         # AI service configuration
├── location_art.py      # Fallback ASCII art templates for locations
├── npc_art.py           # Fallback ASCII art templates for NPCs
├── config.py            # General configuration
├── colors.py            # ANSI color output utilities
├── json_output.py       # JSON Lines output for --json mode
├── logging_service.py   # Gameplay logging for --log-file option
├── input_handler.py     # Readline-based input with command history
├── completer.py         # Tab auto-completion for commands and arguments
├── whisper.py           # Ambient whisper system for atmosphere
├── dreams.py            # Dream sequences triggered on rest
├── random_encounters.py # Random travel encounters (merchants, wanderers, hostiles)
├── world_events.py      # Living world events (plagues, caravans, invasions)
└── models/
    ├── character.py     # Player character model
    ├── dread.py         # Dread meter for psychological horror
    ├── enemy.py         # Enemy/monster model
    ├── game_time.py     # Day/night cycle and time tracking
    ├── item.py          # Item definitions
    ├── inventory.py     # Inventory management
    ├── location.py      # Location with coordinates, connections, NPCs
    ├── npc.py           # Non-player character model
    ├── quest.py         # Quest system with objectives and progress tracking
    ├── shop.py          # Shop system
    ├── status_effect.py # Status effects (poison, buffs, debuffs)
    ├── random_encounter.py # Random encounter model for travel events
    ├── world_event.py   # World event model for timed events
    └── weather.py       # Weather system (clear, rain, storm, fog)
```

## Key Architectural Patterns

- **Grid-based world** (`world_grid.py`): Spatial consistency with coordinate-based navigation
- **Location model**: Each location has coordinates, connections to adjacent locations, and NPCs
- **GameState**: Central manager for character, world, combat, and shop state
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
```
