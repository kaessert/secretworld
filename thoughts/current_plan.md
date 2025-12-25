# Implementation Plan: Configurable Delays/Timeouts for Automation

## Feature Spec

Add `--delay <ms>` CLI option to control pacing between commands in automated (non-interactive/JSON) runs. This is the final item under "Additional automation features" in ISSUES.md.

**Behavior**:
- `--delay 500` - Wait 500ms after each command response before processing the next command
- Only applies to `--non-interactive` and `--json` modes
- Default: 0 (no delay, current behavior)
- Valid range: 0-60000ms (0 to 60 seconds)

## Tests First (TDD)

Create `tests/test_delay_option.py`:

1. `test_delay_flag_accepted` - `--delay 100` is accepted without error
2. `test_delay_requires_integer` - `--delay notanumber` fails with argparse error
3. `test_delay_requires_non_interactive` - `--delay` only meaningful with `--non-interactive` or `--json` (should warn if used alone in interactive mode, but not fail)
4. `test_delay_slows_execution` - Run with `--delay 200` on 2 commands takes ~400ms longer than without
5. `test_delay_works_with_json_mode` - `--json --delay 100` works correctly
6. `test_delay_zero_is_default` - No delay when not specified

## Implementation Steps

### 1. Add CLI argument in `main.py`

Location: `main()` function, after `--seed` argument (~line 1479)

```python
parser.add_argument(
    "--delay",
    type=int,
    default=0,
    metavar="MS",
    help="Delay in milliseconds between commands (non-interactive/JSON modes)"
)
```

### 2. Add delay logic to `run_non_interactive()`

Location: `run_non_interactive()` (~line 1332)

- Add `delay_ms: int = 0` parameter
- After processing each command (after `print(message)`), add:
  ```python
  if delay_ms > 0:
      import time
      time.sleep(delay_ms / 1000.0)
  ```

### 3. Add delay logic to `run_json_mode()`

Location: `run_json_mode()` (~line 1158)

- Add `delay_ms: int = 0` parameter
- After emitting response JSON, add same delay logic

### 4. Pass delay from `main()` to mode functions

Update calls to `run_non_interactive()` and `run_json_mode()` to pass `parsed_args.delay`.

## Files to Modify

1. `src/cli_rpg/main.py` - Add argument and delay logic
2. `tests/test_delay_option.py` - New test file

## Verification

Run: `pytest tests/test_delay_option.py -v`
