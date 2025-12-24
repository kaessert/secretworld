# Implementation Plan: Create CLAUDE.md

## Task Summary
Create a CLAUDE.md file to document project conventions and development workflow for AI-assisted development.

## Difficulty: SIMPLE
This is a documentation-only task with no code changes or testing requirements.

## Implementation Steps

1. **Create `/Users/tkaesser/up/secretworld/CLAUDE.md`** with the following sections:

   - **Quick Project Overview**: CLI RPG with AI-generated worlds, combat, inventory, shops, and save/load
   - **Testing Commands**:
     - `source venv/bin/activate && pytest` (full test suite)
     - `pytest tests/test_<module>.py -v` (specific tests)
     - `pytest --cov=src/cli_rpg` (with coverage)
   - **Key Architectural Patterns**:
     - Grid-based world (`world_grid.py`) with spatial consistency
     - Location model with coordinates, connections, and NPCs
     - GameState manages character, world, combat, and shop state
     - AI service integration is optional (graceful fallback)
   - **Project Structure**: Reference `src/cli_rpg/` layout
   - **Coding Standards**:
     - Python 3.9+
     - Line length 100 (black/ruff)
     - Type hints encouraged
     - Dataclasses for models

2. **Verify**: Confirm file exists and content is accurate

## Files to Create
- `CLAUDE.md` (project root)

## No Tests Required
This is a documentation task - no code functionality to test.
