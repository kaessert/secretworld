# Implementation Plan: Increase main.py Test Coverage (94% -> 98%+)

## Objective
Improve test coverage for `src/cli_rpg/main.py` from 94% to 98%+ by adding targeted tests for the 38 uncovered lines.

## Uncovered Lines Analysis

| Lines | Function | Description | Test Strategy |
|-------|----------|-------------|---------------|
| 157-159 | `select_and_load_character()` | Generic Exception catch-all handler | Raise Exception from unexpected source after save type detection |
| 189 | `handle_conversation_input()` | NPC role = "quest_giver" | Test with is_quest_giver=True, is_merchant=False |
| 245 | `handle_combat_command()` | Quest progress messages after attack | Attack victory with active KILL quest |
| 250-251 | `handle_combat_command()` | IOError during autosave after attack | Mock autosave to raise IOError |
| 294-295 | `handle_combat_command()` | IOError during autosave after flee | Mock autosave to raise IOError on successful flee |
| 327-328 | `handle_combat_command()` | IOError during autosave after cast | Mock autosave to raise IOError |
| 490-491 | `handle_exploration_command()` | AI dialogue exception fallback | Mock generate_npc_dialogue to raise |
| 498 | `handle_exploration_command()` | Talk shows quest progress | Character with TALK quest for NPC |
| 593 | `handle_exploration_command()` | Buy with full inventory | Fill inventory before buy |
| 610 | `handle_exploration_command()` | Buy triggers collect quest | Buy with active COLLECT quest |
| 617 | `handle_exploration_command()` | Sell without args | Call sell command with no args |
| 683 | `handle_exploration_command()` | Accept from non-quest-giver | NPC with is_quest_giver=False |
| 805 | `handle_exploration_command()` | Quests in AVAILABLE/FAILED state | Character with AVAILABLE status quest |
| 857-858 | `handle_exploration_command()` | Quit save success prints | Mock save_game_state to succeed |
| 909 | `handle_exploration_command()` | "unknown" command literal | Pass "unknown" as command |
| 953-961 | `run_game_loop()` | Combat status display | Full loop test with combat |
| 964-968 | `run_game_loop()` | Conversation mode routing | Full loop test in conversation |
| 1028 | `start_game()` | Empty world validation | Mock create_world to return empty dict |
| 1032 | `start_game()` | Invalid starting location | Mock create_world with bad start location |
| 1097-1100 | `main()` | AI fallback mode + init exception | Test with non-strict mode and AI init failure |

---

## Implementation Steps

### Step 1: Add tests to `tests/test_main_coverage.py`

Add the following test classes/methods:

```python
class TestGenericLoadException:
    def test_load_handles_unexpected_exception():
        """Lines 157-159: Generic Exception after save detection."""

class TestQuestGiverConversation:
    def test_conversation_with_quest_giver_role():
        """Line 189: NPC role is 'quest_giver'."""

class TestAttackVictoryQuestProgress:
    def test_attack_victory_quest_messages():
        """Line 245: Quest progress messages on attack victory."""

    def test_attack_victory_autosave_io_error():
        """Lines 250-251: IOError silently caught."""

class TestFleeAutosaveIOError:
    def test_flee_success_autosave_io_error():
        """Lines 294-295: IOError silently caught."""

class TestCastVictoryAutosave:
    def test_cast_victory_autosave_io_error():
        """Lines 327-328: IOError silently caught."""

class TestTalkAIDialogueFallback:
    def test_talk_ai_dialogue_exception():
        """Lines 490-491: AI failure uses existing greetings."""

class TestTalkQuestProgress:
    def test_talk_triggers_quest_progress():
        """Line 498: TALK quest progress on NPC conversation."""

class TestBuyEdgeCases:
    def test_buy_inventory_full():
        """Line 593: Inventory full error."""

    def test_buy_collect_quest_progress():
        """Line 610: COLLECT quest progress."""

class TestAcceptNonQuestGiver:
    def test_accept_from_non_quest_giver():
        """Line 683: Accept from NPC without quests."""

class TestQuestsEdgeCase:
    def test_quests_available_status():
        """Line 805: Quests in AVAILABLE state."""

class TestQuitSaveSuccess:
    def test_quit_save_success_output():
        """Lines 857-858: Save success message."""

class TestUnknownCommandLiteral:
    def test_unknown_command_literal():
        """Line 909: Explicit 'unknown' command."""

class TestGameLoopCombat:
    def test_game_loop_shows_combat_status():
        """Lines 953-961: Combat status after action."""

class TestGameLoopConversation:
    def test_game_loop_conversation_routing():
        """Lines 964-968: Conversation mode routing."""

class TestStartGameValidation:
    def test_start_game_empty_world():
        """Line 1028: Empty world raises ValueError."""

    def test_start_game_invalid_starting_location():
        """Line 1032: Bad starting location raises ValueError."""

class TestMainAIInit:
    def test_main_fallback_mode_message():
        """Line 1097: Fallback mode message."""

    def test_main_ai_init_exception():
        """Lines 1098-1100: AI init exception handling."""
```

### Step 2: Run tests to verify

```bash
source venv/bin/activate && pytest tests/test_main_coverage.py -v
source venv/bin/activate && pytest --cov=src/cli_rpg/main --cov-report=term-missing
```

---

## Expected Coverage Improvement

- **Before**: 94% (38 missing lines)
- **Target**: 98%+ (< 10 missing lines)
- **Lines to cover**: 20 distinct code paths
