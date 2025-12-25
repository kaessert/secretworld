# Implementation Plan: Test Coverage Reporting and Improvement

## Overview

Current overall coverage: 89% (2831 statements, 308 missed).
Only one module is below 80%: `main.py` at 78% (148 uncovered lines).

---

## Step 1: Configure pytest-cov in pyproject.toml

**File:** `pyproject.toml`

Add coverage configuration:
```toml
[tool.coverage.run]
source = ["src/cli_rpg"]
omit = ["*/tests/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
]

[tool.coverage.html]
directory = "htmlcov"
```

Add pytest-cov to dev dependencies:
```toml
[project.optional-dependencies]
dev = [
    ...
    "pytest-cov>=4.0.0",
]
```

---

## Step 2: Add Tests for Uncovered main.py Lines

**File:** `tests/test_main_coverage.py`

Target the critical uncovered functionality:

### 2a. Character Save Prompt (lines 64-75)
- `test_offer_save_character_saves_on_yes` - User answers 'y', character is saved
- `test_offer_save_character_skips_on_no` - User answers 'n', character not saved
- `test_offer_save_character_handles_io_error` - IOError caught, error message shown

### 2b. Load Character Error Handling (lines 133-135, 143-158)
- `test_load_character_handles_game_state_exception` - Exception during game_state load
- `test_load_character_handles_invalid_input` - Non-numeric input returns None
- `test_load_character_handles_file_not_found` - FileNotFoundError returns None
- `test_load_character_handles_generic_exception` - Generic Exception caught

### 2c. Combat Death During Various Commands (lines 274-278, 302-305, 334-340, 362-365)
- `test_combat_defend_player_death` - Player dies after defend command
- `test_combat_flee_failed_player_death` - Player dies after failed flee
- `test_combat_cast_victory_with_quest_progress` - Cast kills enemy, triggers quest progress
- `test_combat_cast_player_death` - Player dies after failed cast
- `test_combat_use_item_player_death` - Player dies after using item

### 2d. AI Conversation Error Path (lines 208-210)
- `test_conversation_ai_error_fallback` - AI service exception triggers fallback response

### 2e. Combat Quit During Combat (lines 403-414)
Already partially tested but ensure quit confirmation path is covered.

### 2f. Game Loop Death/Recovery (lines 915-926, 936)
- `test_game_loop_death_return_to_menu` - Player dead, answers 'y' returns to menu
- `test_game_loop_death_continue` - Player dead, answers 'n' resurrects player
- `test_game_loop_empty_input_ignored` - Empty command input continues loop

### 2g. Start Game AI Error Recovery (lines 987-1014)
- `test_start_game_ai_error_retry` - AI fails, user retries
- `test_start_game_ai_error_use_default` - AI fails, user chooses default world
- `test_start_game_ai_error_return_to_menu` - AI fails, user returns to menu

---

## Step 3: Run Coverage and Verify

```bash
pytest --cov=src/cli_rpg --cov-report=html --cov-report=term-missing
```

Verify:
1. `main.py` reaches >= 80% coverage
2. Overall coverage stays >= 89%
3. HTML report generated in `htmlcov/`

---

## Implementation Order

1. Update `pyproject.toml` with coverage config
2. Create `tests/test_main_coverage.py` with tests for uncovered lines
3. Run tests to verify coverage improvement
