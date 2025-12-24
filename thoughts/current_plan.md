# Implementation Plan: Fix Failing Test `test_main_load_character_no_saves`

## Spec

The test `test_main_load_character_no_saves` expects that when a user selects "Load Character" (option 2) and no saves exist, the game displays a message and returns to the main menu. The user then selects "Exit" (option 3) to quit.

**Current Problem:** The test fails with `StopIteration` because:
1. A save file (`autosave_abcdef.json`) exists in the `saves/` directory from previous test runs
2. The existing `conftest.py` only redirects autosave writes to temp, not `list_saves()` reads
3. When saves exist, `select_and_load_character()` prompts for character selection, consuming an extra input
4. The mock provides only `["2", "3"]` which is insufficient when saves exist

**Fix Options:**
1. **Option A (Recommended):** Add test isolation by mocking `list_saves()` to return empty list
2. **Option B:** Extend conftest.py fixture to also mock `list_saves()` to use temp directory

---

## Tests

**File:** `tests/test_main_menu.py`

The existing test is correct in its intent. We need to add proper test isolation:

```python
@patch('cli_rpg.main.list_saves', return_value=[])  # Ensure no saves exist for this test
@patch('builtins.input', side_effect=["2", "3"])
def test_main_load_character_no_saves(self, mock_input, mock_list_saves):
    """Test: Load character shows message when no saves exist"""
    result = main()
    assert result == 0
```

---

## Implementation Steps

### Step 1: Update test to mock `list_saves()`
**File:** `tests/test_main_menu.py`
**Location:** Lines 32-36

Change:
```python
@patch('builtins.input', side_effect=["2", "3"])
def test_main_load_character_no_saves(self, mock_input):
```

To:
```python
@patch('cli_rpg.main.list_saves', return_value=[])
@patch('builtins.input', side_effect=["2", "3"])
def test_main_load_character_no_saves(self, mock_input, mock_list_saves):
```

### Step 2: Run test to verify fix
```bash
pytest tests/test_main_menu.py::TestMainFunction::test_main_load_character_no_saves -v
```

### Step 3: Run all tests to ensure no regressions
```bash
pytest tests/ -v
```
