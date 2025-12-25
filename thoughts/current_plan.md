# Implementation Plan: Add `complete` command to parser

## Problem
The `complete <quest>` command handler exists in `main.py` (lines 623-663), but the command is missing from the `known_commands` set in `parse_command()` in `game_state.py`. This causes the parser to return `("unknown", [])` before the handler is ever reached.

## Solution
Add `"complete"` to the `known_commands` set in `game_state.py`.

## Implementation Steps

1. **Edit `src/cli_rpg/game_state.py` line 65-67**
   - Add `"complete"` to the `known_commands` set
   - Current: `{"look", "go", "save", "quit", "attack", "defend", "flee", "status", "cast", "inventory", "equip", "unequip", "use", "talk", "buy", "sell", "shop", "map", "help", "quests", "quest", "accept"}`
   - New: Add `"complete"` to the set

2. **Verify tests pass**
   - Run: `pytest tests/test_quest_commands.py -v`
   - Existing tests for `complete` command should now pass (they test the handler which is already implemented)

3. **Manual verification**
   - Run game, talk to NPC with quest, complete quest objectives, use `complete <quest>` command
