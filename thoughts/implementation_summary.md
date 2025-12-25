# Implementation Summary: Add `complete` command to parser

## What was implemented

Added `"complete"` to the `known_commands` set in the `parse_command()` function in `src/cli_rpg/game_state.py`.

## Files modified

- `src/cli_rpg/game_state.py` (line 67): Added `"complete"` to the known_commands set

## Problem solved

The `complete <quest>` command handler existed in `main.py` but the parser was returning `("unknown", [])` because `"complete"` was not in the `known_commands` set. This one-line fix enables the quest turn-in functionality.

## Test results

All 27 tests in `tests/test_quest_commands.py` pass, including the 6 tests specifically for the `complete` command:
- `test_complete_command_requires_npc`
- `test_complete_command_requires_quest_name`
- `test_complete_command_requires_ready_to_turn_in_status`
- `test_complete_command_requires_matching_quest_giver`
- `test_complete_command_grants_rewards_and_sets_completed`
- `test_complete_command_shows_reward_messages`

## E2E validation

To validate manually:
1. Start game, find an NPC with a quest
2. Use `talk <npc>` to see available quests
3. Use `accept <quest>` to accept a quest
4. Complete the quest objectives
5. Return to the quest giver NPC
6. Use `complete <quest>` to turn in the quest and receive rewards
