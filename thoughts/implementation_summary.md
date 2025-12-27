# Implementation Summary: Fix Flaky Poison Test

## What Was Implemented

Fixed a flaky test `test_enemy_with_poison_can_apply_poison` in `tests/test_status_effects.py` by adding a mock to prevent random dodge behavior.

## Changes Made

**File**: `tests/test_status_effects.py`, lines 278-293

Added `unittest.mock.patch` to mock `cli_rpg.combat.random.random` with a fixed return value of `0.50`, which:
- Prevents the character from dodging the enemy attack (dodge requires random value < 0.10 for 10% dodge chance)
- Ensures the poison application code is reached every time

## Root Cause

The character fixture had `dexterity=10`, giving ~10% dodge chance. Without mocking, approximately 1 in 10 test runs would result in a dodge, skipping the poison application code entirely and failing the assertion.

## Test Results

- Target test passes consistently (verified 10 consecutive runs)
- All 75 tests in `tests/test_status_effects.py` pass

## Technical Details

The fix follows the established pattern used in other similar tests:
- `test_burn_applies_in_combat` (line 530)
- `test_stun_applies_in_combat` (line 682)
- `test_bleed_applies_in_combat` (line 1266)

All use the same mocking approach to prevent dodge from interfering with status effect application tests.
