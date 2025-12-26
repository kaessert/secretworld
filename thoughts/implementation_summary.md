# Implementation Summary: Fix Flaky Fighting Stance Test

## What Was Fixed

Fixed the flaky test `test_aggressive_stance_increases_attack_damage` in `tests/test_fighting_stances.py`.

## Root Cause

The test was seeding `random` only before the aggressive stance attack (line 247), allowing the balanced stance attack to potentially get a random critical hit while aggressive got a deterministic non-crit. When balanced critted (1.5x damage) and aggressive didn't, the assertion `aggressive_damage >= balanced_damage` could fail.

## Changes Made

**File: `tests/test_fighting_stances.py`**

1. Moved `import random` to the top of the test function
2. Added `random.seed(42)` before the balanced stance attack to make it deterministic
3. Added `random.seed(42)` again before the aggressive stance attack to reset RNG to the same state
4. Changed assertion from `>=` to `>` since with identical crit behavior, aggressive stance is always strictly greater (20% damage bonus)

## Test Results

- Ran the specific test 10 times consecutively - all passed
- Ran full `test_fighting_stances.py` test suite (29 tests) - all passed

## Key Technical Detail

By seeding `random` with the same value before both attacks, both get identical crit rolls (either both crit or neither crits), ensuring the 20% damage bonus from aggressive stance always results in strictly greater damage.
