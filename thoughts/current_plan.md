# Fix E2E Test Failures After Character Class System Addition

## Problem
Two E2E tests in `test_e2e_ai_integration.py` are failing because they're missing the class selection input that was added to the character creation flow in commit ba1b3bc.

The character creation flow now requires an additional input for class selection (after name, before stat allocation method).

## Failing Tests
1. `test_theme_selection_flow_with_ai` - runs out of inputs (StopIteration on mock)
2. `test_complete_e2e_flow_with_mocked_ai` - runs out of inputs (StopIteration on mock)

## Fix

### 1. Update `test_theme_selection_flow_with_ai` (lines 118-127)

**Current inputs:**
```python
inputs = [
    "1",           # Create new character
    "TestHero",    # Character name
    "2",           # Random stats  <- WRONG: this is now class selection
    "yes",         # Confirm character
    "2",           # Select sci-fi theme
    "quit",        # Quit game
    "n",           # Don't save
    "3"            # Exit main menu
]
```

**Fixed inputs:**
```python
inputs = [
    "1",           # Create new character
    "TestHero",    # Character name
    "1",           # Select Warrior class (NEW)
    "2",           # Random stats
    "yes",         # Confirm character
    "2",           # Select sci-fi theme
    "quit",        # Quit game
    "n",           # Don't save
    "3"            # Exit main menu
]
```

### 2. Update `test_complete_e2e_flow_with_mocked_ai` (lines 271-284)

**Current inputs:**
```python
inputs = [
    "1",           # Create new character
    "Hero",        # Character name
    "1",           # Manual stats  <- WRONG: this is now class selection
    "12",          # Strength
    "10",          # Dexterity
    "14",          # Intelligence
    "yes",         # Confirm character
    "3",           # Select cyberpunk theme
    "look",        # Look around
    "quit",        # Quit game
    "n",           # Don't save
    "3"            # Exit main menu
]
```

**Fixed inputs:**
```python
inputs = [
    "1",           # Create new character
    "Hero",        # Character name
    "1",           # Select Warrior class (NEW)
    "1",           # Manual stats
    "12",          # Strength
    "10",          # Dexterity
    "14",          # Intelligence
    "yes",         # Confirm character
    "3",           # Select cyberpunk theme
    "look",        # Look around
    "quit",        # Quit game
    "n",           # Don't save
    "3"            # Exit main menu
]
```

## Verification
Run: `pytest tests/test_e2e_ai_integration.py -v`

All tests should pass after adding the class selection input to both test cases.
