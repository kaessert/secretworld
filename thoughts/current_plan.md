# Plan: Register Custom Pytest Marks

## Task
Register the `slow` custom mark in pytest configuration to eliminate warnings about unknown marks.

## Implementation

**File:** `pyproject.toml`

Add `markers` to the existing `[tool.pytest.ini_options]` section (after line 37):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

## Verification

Run: `pytest --co -q 2>&1 | grep -i "unknown\|PytestUnknownMarkWarning"` - should produce no output.
