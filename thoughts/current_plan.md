# Fix: Argument Parsing Conflict in main.py

## Problem
The `main()` function in `main.py` calls `parser.parse_args()` without arguments, which defaults to `sys.argv[1:]`. When pytest runs tests that call `main()`, pytest's arguments (e.g., `tests/test_main.py -v --tb=short`) are parsed by argparse, causing 15 test failures because argparse doesn't recognize them.

## Solution
Modify `main()` to accept an optional `args` parameter (default `None`). Pass this to `parser.parse_args(args)`. When `args=None`, argparse uses `sys.argv[1:]` (normal behavior). When `args=[]` or a specific list, it uses that instead.

## Implementation Steps

1. **Modify `main()` function signature** in `src/cli_rpg/main.py` (line 1217):
   - Change `def main() -> int:` to `def main(args: Optional[list[str]] = None) -> int:`
   - Change `args = parser.parse_args()` to `parsed_args = parser.parse_args(args)`
   - Rename internal variable from `args` to `parsed_args` to avoid shadowing parameter
   - Update references: `args.non_interactive` → `parsed_args.non_interactive`

2. **Update tests** that call `main()` to pass `args=[]`:
   - `tests/test_main.py` - `test_main_function_callable`, `test_main_returns_zero`
   - `tests/test_main_menu.py` - any direct `main()` calls
   - `tests/test_main_coverage.py` - any direct `main()` calls
   - `tests/test_e2e_ai_integration.py` - any direct `main()` calls
   - `tests/test_main_load_integration.py` - any direct `main()` calls

## Files to Modify
- `src/cli_rpg/main.py` (lines 1217-1234)
- `tests/test_main.py`
- `tests/test_main_menu.py`
- `tests/test_main_coverage.py`
- `tests/test_e2e_ai_integration.py`
- `tests/test_main_load_integration.py`

## Verification
Run: `pytest -v` to confirm all 15 previously failing tests now pass.
