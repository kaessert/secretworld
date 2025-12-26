# Fix Non-Interactive Character Creation Tests for Charisma Stat

## Problem
6 tests failing because stdin inputs provide 3 stats (str, dex, int) but character creation now requires 4 stats (str, dex, int, **charisma**).

## File to Update
`tests/test_non_interactive_character_creation.py`

## Changes Required

### 1. Update docstrings (lines 10, 72, 240)
Change spec comments from:
```
- If manual: Lines 4-6: strength, dexterity, intelligence (integers 1-20)
```
To:
```
- If manual: Lines 4-7: strength, dexterity, intelligence, charisma (integers 1-20)
```

### 2. Update stdin inputs for manual stat tests

**Line 76** (`test_non_interactive_character_creation_manual_stats`):
```python
# Old: stdin_input = "TestHero\n1\n1\n15\n12\n10\nyes\nstatus\n"
# New: stdin_input = "TestHero\n1\n1\n15\n12\n10\n8\nyes\nstatus\n"
```

**Line 241** (`test_json_mode_character_creation_manual`):
```python
# Old: stdin_input = "TestHero\n1\n1\n15\n12\n10\nyes\n"
# New: stdin_input = "TestHero\n1\n1\n15\n12\n10\n8\nyes\n"
```

**Line 296** (`test_non_interactive_character_creation_no_confirmation_exits`):
```python
# Old: stdin_input = "TestHero\n1\n1\n15\n12\n10\nno\n"
# New: stdin_input = "TestHero\n1\n1\n15\n12\n10\n8\nno\n"
```

## Verification
Run: `pytest tests/test_non_interactive_character_creation.py -v`
