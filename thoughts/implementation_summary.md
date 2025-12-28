# Implementation Summary: Fix Maze Layout Tests

## Date: 2025-12-28

## Overview

Fixed two flaky tests in `tests/test_procedural_layouts.py` by modifying the `_generate_maze_layout()` method to properly respect size constraints while ensuring dead ends exist.

## Files Modified

### Core Implementation

1. **`src/cli_rpg/ai_service.py`** - Modified dead-end fix logic in `_generate_maze_layout()` (lines 3433-3461)

## Change Details

### The Problem
The original code would unconditionally add a dead-end coordinate when none existed, causing the returned list to exceed the requested size (e.g., returning 11 coords when 10 were requested).

### The Fix
Modified the dead-end fix logic to handle two cases:
1. **When under size limit** (`len(coords) < size`): Add a dead end as before (room to add)
2. **When at size limit** (`len(coords) >= size`): Replace the last coordinate with a dead end instead of adding one

Added a final `return coords[:size]` as a safety guarantee to never exceed the requested size.

## Root Cause

The random walk with backtracking algorithm could produce compact clusters where all nodes have 2+ neighbors. The original fix for this (adding a dead end) didn't account for the size constraint, causing `test_maze_layout_respects_size` to fail intermittently.

## Test Results

- **Specific tests**: Ran `test_maze_layout_has_dead_ends` and `test_maze_layout_respects_size` 30+ times consecutively - all passed (0 failures)
- **Full test file**: All 35 tests in `tests/test_procedural_layouts.py` pass

## E2E Validation

No E2E tests required - this is an internal algorithm fix that doesn't affect external behavior. The existing unit tests are sufficient to validate correctness.
