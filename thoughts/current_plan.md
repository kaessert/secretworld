# Fix Failing Tests for Charisma Stat

## Problem
3 tests fail with `StopIteration` because mock input sequences don't include the charisma value added in commit 7b19ffb.

## Files to Fix

### 1. tests/test_main_menu.py (line 25)
**Current:** `["1", "Hero", "1", "1", "10", "12", "8", "yes", "quit", "n", "3"]`
**Fixed:** `["1", "Hero", "1", "1", "10", "12", "8", "10", "yes", "quit", "n", "3"]`
- Add "10" (charisma) after "8" (intelligence)

### 2. tests/test_integration_character.py (line 74)
**Current:** `["Hero", "1", "manual", "15", "12", "10", "yes"]`
**Fixed:** `["Hero", "1", "manual", "15", "12", "10", "10", "yes"]`
- Add "10" (charisma) after "10" (intelligence)

### 3. tests/test_e2e_ai_integration.py (lines 272-286)
**Current:** Stats are "12", "10", "14" (str, dex, int)
**Fixed:** Add "10" (charisma) after "14" (intelligence)

## Verification
Run: `pytest tests/test_main_menu.py tests/test_integration_character.py tests/test_e2e_ai_integration.py -v`
