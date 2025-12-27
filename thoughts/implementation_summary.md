# Implementation Summary: RNG Seeds in Logs for Reproducibility

## What Was Implemented

Added RNG seed tracking and logging to enable session replay for debugging.

### Files Modified

1. **`src/cli_rpg/logging_service.py`**
   - Updated `log_session_start()` to accept optional `seed` parameter
   - When seed is provided, it's included in the session_start log entry

2. **`src/cli_rpg/json_output.py`**
   - Added new function `emit_session_info(seed: int, theme: str)`
   - Emits `{"type": "session_info", "seed": ..., "theme": ...}` message

3. **`src/cli_rpg/main.py`**
   - Updated `main()` to generate seed early if not provided via `--seed`
   - Seeds the global RNG with the generated/provided seed
   - Passes seed to `run_json_mode()` and `run_non_interactive()`
   - Updated `run_json_mode()`:
     - Added `seed` parameter
     - Uses provided seed for ChunkManager instead of generating new one
     - Emits `session_info` message with seed
     - Passes seed to `logger.log_session_start()`
   - Updated `run_non_interactive()`:
     - Added `seed` parameter
     - Uses provided seed for ChunkManager
     - Passes seed to `logger.log_session_start()`

### New Test File

**`tests/test_rng_seed_logging.py`**
- `test_seed_logged_in_session_start`: Verifies seed field in session_start log entry
- `test_no_seed_when_not_provided`: Verifies no seed field when not provided
- `test_emit_session_info`: Verifies session_info JSON output with seed
- `test_auto_generated_seed_is_positive_integer`: Validates auto-generated seeds
- `test_same_seed_produces_reproducible_results`: Confirms same seed produces identical results

## Test Results

All 5 new tests pass. Full test suite: 3678 passed, 1 pre-existing flaky test failed (unrelated combat test).

## Verification

- JSON mode emits `{"type": "session_info", "seed": N, "theme": "fantasy"}` on startup
- Log files include `"seed": N` in session_start entries
- Seed is passed through correctly from `--seed` argument
- Auto-generated seeds are in valid range (0 to 2^31-1)

## E2E Validation

To validate:
1. Run `cli-rpg --json --skip-character-creation --seed 12345` and verify first line contains seed
2. Run `cli-rpg --non-interactive --log-file test.log --seed 12345` and verify log contains seed in session_start
3. Run twice with same seed to verify reproducible terrain generation
