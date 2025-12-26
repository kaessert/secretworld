# Implementation Plan: Strip Markdown Code Fences from ASCII Art

## Summary
Fix `_parse_location_ascii_art_response`, `_parse_ascii_art_response`, and `_parse_npc_ascii_art_response` methods in `ai_service.py` to strip markdown code fences from AI-generated ASCII art, matching how `_extract_json_from_code_block` handles JSON responses.

## The Bug
AI may return ASCII art wrapped in markdown code fences like:
```
```
   /\
  /  \
 /____\
```
```
This renders incorrectly in the game, breaking immersion.

## Implementation Steps

### Step 1: Add tests for code fence stripping

**File: `tests/test_ascii_art.py`**

Add to `TestAsciiArtFirstLineAlignment` class (around line 434):

```python
def test_parse_location_ascii_art_strips_code_fences(self):
    """Verify location art parsing strips markdown code fences."""
    from cli_rpg.ai_service import AIService
    from cli_rpg.ai_config import AIConfig

    config = AIConfig(api_key="test-key", provider="openai", enable_caching=False)
    service = AIService(config)

    # Response wrapped in code fences
    response = """```
     /\\
    /  \\
   /    \\
  /______\\
```"""

    art = service._parse_location_ascii_art_response(response)

    # Should not contain backticks
    assert "```" not in art
    # First line should be the art
    first_line = art.splitlines()[0]
    assert first_line == "     /\\"

def test_parse_enemy_ascii_art_strips_code_fences(self):
    """Verify enemy art parsing strips markdown code fences."""
    from cli_rpg.ai_service import AIService
    from cli_rpg.ai_config import AIConfig

    config = AIConfig(api_key="test-key", provider="openai", enable_caching=False)
    service = AIService(config)

    response = """```ascii
   /\\ /\\
  (  V  )
  /|   |\\
```"""

    art = service._parse_ascii_art_response(response)

    assert "```" not in art
    first_line = art.splitlines()[0]
    assert first_line == "   /\\ /\\"

def test_parse_npc_ascii_art_strips_code_fences(self):
    """Verify NPC art parsing strips markdown code fences."""
    from cli_rpg.ai_service import AIService
    from cli_rpg.ai_config import AIConfig

    config = AIConfig(api_key="test-key", provider="openai", enable_caching=False)
    service = AIService(config)

    response = """```
    O
   /|\\
   / \\
```"""

    art = service._parse_npc_ascii_art_response(response)

    assert "```" not in art
    first_line = art.splitlines()[0]
    assert first_line == "    O"
```

### Step 2: Add helper method for code fence extraction

**File: `src/cli_rpg/ai_service.py`**

Add new helper method (after `_extract_json_from_code_block` at line 364):

```python
def _extract_ascii_art_from_code_block(self, response_text: str) -> str:
    """Extract ASCII art from markdown code fence if present.

    Args:
        response_text: Raw response text that may contain code fences

    Returns:
        Extracted content without code fences, or original text if no fence found
    """
    import re
    # Match ```<optional-lang> ... ``` (handles ascii, text, or no language tag)
    pattern = r'```(?:\w*)?\s*\n?([\s\S]*?)\n?```'
    match = re.search(pattern, response_text)
    if match:
        return match.group(1)
    return response_text
```

### Step 3: Update `_parse_ascii_art_response` (enemy art)

**File: `src/cli_rpg/ai_service.py` (line 1294-1295)**

Change:
```python
# Strip only trailing whitespace, preserve first line's leading spaces
art = response_text.rstrip()
```

To:
```python
# Extract from code fence if present
art = self._extract_ascii_art_from_code_block(response_text)
# Strip only trailing whitespace, preserve first line's leading spaces
art = art.rstrip()
```

### Step 4: Update `_parse_location_ascii_art_response`

**File: `src/cli_rpg/ai_service.py` (line 1391-1392)**

Change:
```python
# Strip only trailing whitespace, preserve first line's leading spaces
art = response_text.rstrip()
```

To:
```python
# Extract from code fence if present
art = self._extract_ascii_art_from_code_block(response_text)
# Strip only trailing whitespace, preserve first line's leading spaces
art = art.rstrip()
```

### Step 5: Update `_parse_npc_ascii_art_response`

**File: `src/cli_rpg/ai_service.py` (line 1995-1996)**

Change:
```python
# Strip only trailing whitespace, preserve first line's leading spaces
art = response_text.rstrip()
```

To:
```python
# Extract from code fence if present
art = self._extract_ascii_art_from_code_block(response_text)
# Strip only trailing whitespace, preserve first line's leading spaces
art = art.rstrip()
```

## Code Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/ai_service.py` | Add `_extract_ascii_art_from_code_block` helper method |
| `src/cli_rpg/ai_service.py` | Update `_parse_ascii_art_response` to use helper (line 1294) |
| `src/cli_rpg/ai_service.py` | Update `_parse_location_ascii_art_response` to use helper (line 1391) |
| `src/cli_rpg/ai_service.py` | Update `_parse_npc_ascii_art_response` to use helper (line 1995) |
| `tests/test_ascii_art.py` | Add 3 tests for code fence stripping |

## Verification

1. Run ASCII art tests: `pytest tests/test_ascii_art.py -v`
2. Run full AI service tests: `pytest tests/test_ai_service.py -v`
3. Run full suite: `pytest`
