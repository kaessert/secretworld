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
├── config.py            # General configuration
├── colors.py            # ANSI color output utilities
├── json_output.py       # JSON Lines output for --json mode
├── logging_service.py   # Gameplay logging for --log-file option
├── input_handler.py     # Readline-based input with command history
└── models/
    ├── character.py     # Player character model
    ├── enemy.py         # Enemy/monster model
    ├── item.py          # Item definitions
    ├── inventory.py     # Inventory management
    ├── location.py      # Location with coordinates, connections, NPCs
    ├── npc.py           # Non-player character model
    ├── quest.py         # Quest system with objectives and progress tracking
    └── shop.py          # Shop system
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
