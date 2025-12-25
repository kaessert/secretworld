# Implementation Summary: Argument Parsing Fix

## What Was Implemented

Fixed the argument parsing conflict in `main.py` that caused 15 test failures when pytest ran tests calling `main()`.

### Root Cause
The `main()` function called `parser.parse_args()` without arguments, which defaults to `sys.argv[1:]`. When pytest runs tests, pytest's arguments (e.g., `tests/test_main.py -v --tb=short`) get parsed by argparse, causing errors like "unrecognized arguments".

### Solution
Modified `main()` to accept an optional `args` parameter:
- When `args=None` (default), argparse uses `sys.argv[1:]` (normal CLI behavior)
- When `args=[]`, argparse uses an empty list (no arguments to parse)
- Tests now pass `args=[]` to avoid pytest argument conflicts

## Files Modified

### 1. `src/cli_rpg/main.py` (line 1217)
- Changed function signature from `def main() -> int:` to `def main(args: Optional[list] = None) -> int:`
- Changed `args = parser.parse_args()` to `parsed_args = parser.parse_args(args)`
- Updated condition from `if args.non_interactive:` to `if parsed_args.non_interactive:`
- Added docstring documenting the `args` parameter

### 2. Test files updated to pass `args=[]`:
- `tests/test_main.py` (2 calls)
- `tests/test_main_menu.py` (5 calls)
- `tests/test_main_coverage.py` (2 calls)
- `tests/test_e2e_ai_integration.py` (4 calls)
- `tests/test_main_load_integration.py` (2 calls)

## Test Results

- **100 tests** in the affected test files: all PASSED
- **Full test suite**: 1457 passed, 1 failed (unrelated documentation test)

The 1 failing test (`test_resolved_issues_are_marked`) is unrelated to this fix - it checks documentation markers in `issues.md`.

## Technical Notes

- Used `Optional[list]` instead of `list[str] | None` for Python 3.9 compatibility
- The `Optional` import was already present in the file
