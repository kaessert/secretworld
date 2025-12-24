# Implementation Plan: Quest Commands

## Spec

Expose the existing `models/quest.py` Quest model to users via command interface:
- `quests` (alias `q`) - View all active/completed quests with progress
- `quest <name>` - View details of a specific quest

**Scope**: Phase 1 only exposes viewing quests. Quest acquisition (via NPCs) and progress tracking (from combat/exploration) are future work.

## Tests First (`tests/test_quest_commands.py`)

### parse_command Tests
- `test_parse_quests_command` - "quests" recognized
- `test_parse_quests_shorthand` - "q" expands to "quests"
- `test_parse_quest_command` - "quest" recognized with args

### handle_exploration_command Tests
- `test_quests_shows_empty_when_no_quests` - "No active quests" message
- `test_quests_shows_active_quests` - Lists quests with progress (e.g., "Kill Goblins [2/5]")
- `test_quests_shows_completed_quests` - Shows completed quests separately
- `test_quest_detail_shows_quest_info` - Full quest details (name, description, type, progress)
- `test_quest_detail_not_found` - Error for unknown quest name
- `test_quest_blocked_during_combat` - Returns combat restriction message

## Implementation

### 1. Add quests list to Character (`models/character.py`)
- Add `quests: List[Quest] = field(default_factory=list)` attribute
- Update `to_dict()` to serialize quests
- Update `from_dict()` to deserialize quests

### 2. Add quest commands to parse_command (`game_state.py`)
- Add "quests", "quest" to `known_commands` set (line 56)
- Add "q": "quests" to aliases dict (line 48)

### 3. Add quest command handlers (`main.py`)
- Add `quests` handler in `handle_exploration_command()`:
  - List active quests with progress bars/counts
  - Separate section for completed quests
- Add `quest <name>` handler:
  - Find quest by name (case-insensitive partial match)
  - Display full details: name, description, objective type, target, progress

### 4. Block quest commands during combat (`main.py`)
- `handle_combat_command()` returns error for quest commands

### 5. Update help text (`main.py`)
- Add to `get_command_reference()`:
  - `quests (q)      - View your quest journal`
  - `quest <name>   - View details of a specific quest`

## File Changes Summary
1. `src/cli_rpg/models/character.py` - Add quests list field + serialization
2. `src/cli_rpg/game_state.py` - Add quests/quest to parse_command
3. `src/cli_rpg/main.py` - Add handlers + help text
4. `tests/test_quest_commands.py` - New test file
