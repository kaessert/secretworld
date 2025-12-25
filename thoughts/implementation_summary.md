# Implementation Summary: --delay CLI Option

## What Was Implemented

Added `--delay <ms>` CLI option for controlling pacing between commands in non-interactive and JSON automation modes.

### Features:
- **CLI Argument**: `--delay MS` - accepts integer milliseconds (e.g., `--delay 500`)
- **Default**: 0 (no delay, preserves existing behavior)
- **Range Clamping**: Values are automatically clamped to 0-60000ms range
- **Applies to**: `--non-interactive` and `--json` modes only

### Files Modified:

1. **src/cli_rpg/main.py**:
   - Added `--delay` argument to argparse (lines 1480-1486)
   - Added delay clamping logic before mode dispatch (lines 1493-1494)
   - Updated `run_json_mode()` signature to accept `delay_ms` parameter
   - Updated `run_non_interactive()` signature to accept `delay_ms` parameter
   - Added `time.sleep()` calls after command processing in both modes

2. **tests/test_delay_option.py** (new file):
   - `test_delay_flag_accepted` - verifies flag is parsed without error
   - `test_delay_requires_integer` - verifies non-integer values are rejected
   - `test_delay_parsed_with_non_interactive` - verifies flag works with --non-interactive
   - `test_delay_slows_execution` - verifies measurable delay in execution time
   - `test_delay_works_with_json_mode` - verifies flag works with --json
   - `test_delay_zero_is_default` - verifies default behavior (no delay)
   - `test_delay_negative_value_handled` - verifies negative values are handled (clamped)

## Test Results

- **New tests**: 7 passed
- **Full test suite**: 1500 passed

## Usage Examples

```bash
# 500ms delay between commands in non-interactive mode
cli-rpg --non-interactive --delay 500 < commands.txt

# 200ms delay in JSON mode
cli-rpg --json --delay 200 < commands.txt

# Combine with other options
cli-rpg --non-interactive --seed 42 --delay 100 --log-file session.log < commands.txt
```

## Technical Notes

- Delay is applied AFTER each command's output is emitted, before reading the next command
- Delay does not apply after commands that exit the game (quit with death, etc.)
- Value is clamped to 0-60000ms to prevent unreasonably long delays
- Uses `time.sleep()` for the delay implementation

## E2E Validation

To validate end-to-end:
```bash
# Run with delay, observe pacing
echo -e "status\nlook\nstatus" | cli-rpg --non-interactive --delay 500

# Verify delay is measurable (should take ~1 second with 500ms delay x 2 commands)
time (echo -e "status\nlook" | cli-rpg --non-interactive --delay 500)
```
