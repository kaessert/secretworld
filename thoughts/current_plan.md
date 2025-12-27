# RNG Seeds in Logs for Reproducibility

## Summary
Include the RNG seed used for each session in logs and JSON output, enabling session replay for debugging.

## Spec
- When `--seed N` is provided, log that seed in `session_start`
- When no seed is provided, generate a random seed, apply it, and log it
- Add `seed` field to `session_start` log entry type
- Add `emit_session_info()` to JSON output for session metadata including seed

## Files to Modify

### 1. `src/cli_rpg/logging_service.py`
Update `log_session_start()` to accept optional `seed` parameter:
```python
def log_session_start(self, character_name: str, location: str, theme: str, seed: Optional[int] = None) -> None:
```
Add `seed` to the entry data when provided.

### 2. `src/cli_rpg/json_output.py`
Add new function for session info in JSON mode:
```python
def emit_session_info(seed: int, theme: str) -> None:
    """Emit session metadata including RNG seed."""
    print(json.dumps({"type": "session_info", "seed": seed, "theme": theme}))
```

### 3. `src/cli_rpg/main.py`
- In `run_json_mode()` (~line 2596-2630):
  - Generate seed if not provided: `seed = parsed_args.seed if parsed_args.seed is not None else rnd.randint(0, 2**31 - 1)`
  - Apply seed before world creation: `random.seed(seed)`
  - Pass seed to `ChunkManager` instead of generating new one
  - Call `emit_session_info(seed, theme)` after state emit
  - Pass seed to `logger.log_session_start()`

- In `run_non_interactive()` (~line 2817-2850):
  - Same seed generation/application pattern
  - Pass seed to `logger.log_session_start()`

- In `main()` (~line 2994-2996):
  - Generate seed if not provided before `random.seed()` call
  - Store seed for later use (pass to game modes)

## Tests

### `tests/test_rng_seed_logging.py` (new file)
1. `test_seed_logged_in_session_start`: Verify `session_start` includes `seed` field
2. `test_auto_generated_seed_logged`: When no `--seed`, verify a seed is still logged
3. `test_json_mode_emits_session_info`: Verify `session_info` message with seed in JSON output
4. `test_same_seed_same_session_log`: Same seed produces identical seeds in log

## Implementation Order
1. Update `log_session_start()` signature in `logging_service.py`
2. Add `emit_session_info()` to `json_output.py`
3. Update `run_json_mode()` to generate/track seed and emit session info
4. Update `run_non_interactive()` to generate/track seed and log it
5. Update `main()` to generate seed early if needed
6. Add tests in `tests/test_rng_seed_logging.py`
7. Run `pytest` to verify
