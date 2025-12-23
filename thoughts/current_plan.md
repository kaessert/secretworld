# Implementation Plan: Initialize Project Structure

## 1. SPECIFICATION

### Project Structure Requirements
- Modern Python package using `pyproject.toml` (PEP 621)
- Src-layout structure for better isolation and testing
- CLI entry point for the game
- Support for Python 3.10+
- Essential development tools configuration (pytest, black, etc.)

### Directory Structure
```
cli-rpg/
├── pyproject.toml
├── README.md (existing)
├── .gitignore
├── src/
│   └── cli_rpg/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
└── thoughts/
    └── current_plan.md
```

### pyproject.toml Specification
- Project metadata (name: cli-rpg, version, description, authors, license)
- Python version requirement: >=3.10
- Build system: hatchling
- CLI entry point: cli-rpg command pointing to cli_rpg.main:main
- Core dependencies: (to be added as needed)
- Dev dependencies: pytest, black, mypy, ruff

### Package Specification (src/cli_rpg/)
- `__init__.py`: Defines package version
- `main.py`: Contains main() function that serves as CLI entry point
  - Must be callable with no arguments
  - Should print welcome message confirming setup
  - Exit cleanly with status code 0

## 2. TESTS

### Test File: tests/test_main.py
**Purpose**: Verify the basic package structure and entry point work correctly

**Test Cases**:
1. `test_package_importable`: Import cli_rpg package succeeds
2. `test_package_has_version`: Package has __version__ attribute
3. `test_main_function_exists`: main() function exists in cli_rpg.main
4. `test_main_function_callable`: main() can be called without errors
5. `test_main_returns_zero`: main() returns 0 or None (success)

**Test Implementation Steps**:
1. Create `tests/__init__.py` (empty file)
2. Create `tests/test_main.py` with pytest test functions
3. Each test should be minimal and verify only the spec requirement
4. Tests should run with `pytest tests/`

## 3. IMPLEMENTATION

### Step 1: Create .gitignore
**File**: `.gitignore`
**Content**: Standard Python gitignore patterns
- `__pycache__/`, `*.py[cod]`, `*$py.class`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `*.egg-info/`, `dist/`, `build/`
- `.venv/`, `venv/`, `env/`
- `.env`, `.vscode/`, `.idea/`

### Step 2: Create pyproject.toml
**File**: `pyproject.toml`
**Sections**:
- `[build-system]`: Use hatchling as build backend
- `[project]`: 
  - name = "cli-rpg"
  - version = "0.1.0"
  - description = "A CLI-based AI-generated role-playing game"
  - requires-python = ">=3.10"
  - dependencies = [] (empty for now)
- `[project.scripts]`: cli-rpg = "cli_rpg.main:main"
- `[tool.pytest.ini_options]`: Basic pytest config (testpaths, python_files)
- `[tool.black]`: line-length = 100
- `[tool.ruff]`: line-length = 100

### Step 3: Create Package Directory Structure
**Action**: Create `src/cli_rpg/` directory

### Step 4: Create Package __init__.py
**File**: `src/cli_rpg/__init__.py`
**Content**:
```python
"""CLI RPG - An AI-generated role-playing game."""

__version__ = "0.1.0"
```

### Step 5: Create Main Entry Point
**File**: `src/cli_rpg/main.py`
**Content**:
```python
"""Main entry point for CLI RPG."""

def main() -> int:
    """Main function to start the CLI RPG game."""
    print("Welcome to CLI RPG!")
    print("Project structure initialized successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
```

### Step 6: Create Test Directory Structure
**Action**: Create `tests/` directory

### Step 7: Create Test Package Init
**File**: `tests/__init__.py`
**Content**: Empty file

### Step 8: Create Main Tests
**File**: `tests/test_main.py`
**Content**: Implement all 5 test cases listed in section 2
- Import statements: pytest, sys, cli_rpg, cli_rpg.main
- Each test function with descriptive name
- Use assertions to verify expected behavior

### Step 9: Run Tests
**Command**: `pytest tests/ -v`
**Expected**: All 5 tests pass

### Step 10: Verify Installation
**Commands**:
1. `pip install -e .` (editable install)
2. `cli-rpg` (run the CLI command)
3. Verify output shows welcome message

## VERIFICATION CHECKLIST

- [ ] All files created in correct locations
- [ ] Package is importable: `python -c "import cli_rpg; print(cli_rpg.__version__)"`
- [ ] All tests pass: `pytest tests/ -v`
- [ ] CLI command works: `cli-rpg` prints welcome message
- [ ] Editable install works: `pip install -e .` succeeds
- [ ] No import errors or syntax errors
