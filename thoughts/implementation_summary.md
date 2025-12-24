# Implementation Summary: Fix test_main_load_character_no_saves

## What was Fixed

The failing test `test_main_load_character_no_saves` in `tests/test_main_menu.py` was fixed by adding proper test isolation.

### Root Cause
The test was failing with `StopIteration` because:
1. A save file (`autosave_abcdef.json`) existed in the `saves/` directory from previous test runs
2. The existing `conftest.py` only redirected autosave writes to temp, but `list_saves()` was reading from the actual saves directory
3. When saves existed, `select_and_load_character()` prompted for character selection, consuming an extra input
4. The mock provided only `["2", "3"]` which was insufficient when saves exist

### Solution
Added a mock for `list_saves()` to return an empty list, ensuring the test always simulates the "no saves exist" scenario:

```python
@patch('cli_rpg.main.list_saves', return_value=[])  # Ensure no saves exist for this test
@patch('builtins.input', side_effect=["2", "3"])
def test_main_load_character_no_saves(self, mock_input, mock_list_saves):
```

## Files Modified

- `tests/test_main_menu.py` (lines 32-37)

## Test Results

- **Target test**: `tests/test_main_menu.py::TestMainFunction::test_main_load_character_no_saves` - PASSED
- **Full test suite**: 444 passed, 1 skipped in 6.51s

## E2E Validation

This fix should validate:
1. When a user selects "Load Character" (option 2) and no saves exist, the game displays a message and returns to the main menu
2. The user can then select "Exit" (option 3) to quit with return code 0
