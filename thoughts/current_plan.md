# Implementation Plan: Improve Test Coverage for Low-Coverage Modules

## Summary
Add tests for uncovered lines in modules below 94% coverage to increase overall reliability. Coverage is already excellent (94%), so this focuses on specific untested edge cases.

## Priority Modules (lowest coverage first)

### 1. config.py (88% - lines 34-35)
**Missing:** `load_ai_config()` success path logging

```python
# tests/test_config.py - Add to TestLoadAIConfig class:
def test_load_ai_config_returns_config_when_api_key_set(self):
    """Test that load_ai_config returns AIConfig when OPENAI_API_KEY is set."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        config = load_ai_config()
        assert config is not None
        assert isinstance(config, AIConfig)
```

### 2. autosave.py (89% - lines 9, 73-74)
**Missing:** TYPE_CHECKING import (line 9 - not testable), corrupted file handling (lines 73-74)

```python
# tests/test_autosave.py - Add test:
def test_load_autosave_corrupted_json(self, tmp_path):
    """Should return None for corrupted JSON file."""
    filepath = tmp_path / "autosave_Hero.json"
    filepath.write_text("not valid json{{{")
    loaded = load_autosave("Hero", save_dir=str(tmp_path))
    assert loaded is None

def test_load_autosave_invalid_data_structure(self, tmp_path):
    """Should return None for valid JSON with invalid structure."""
    filepath = tmp_path / "autosave_Hero.json"
    filepath.write_text('{"invalid": "structure"}')
    loaded = load_autosave("Hero", save_dir=str(tmp_path))
    assert loaded is None
```

### 3. world.py (90% - lines 18-21, 142, 146, 150-151)
**Missing:** ImportError handling when AI unavailable, fallback path in non-strict mode

```python
# tests/test_world.py - Add tests:
def test_create_world_logs_warning_on_ai_failure_non_strict(self, mock_create_ai_world, caplog):
    """Test that warning is logged when AI fails in non-strict mode."""
    mock_create_ai_world.side_effect = Exception("AI failed")
    mock_ai_service = Mock()

    with caplog.at_level(logging.WARNING):
        world, _ = create_world(ai_service=mock_ai_service, strict=False)

    assert "AI world generation failed" in caplog.text
    assert "Town Square" in world  # Falls back to default
```

### 4. main.py (92% - multiple scattered lines)
**Key uncovered paths:**
- Lines 148-149, 157-159: Load character error paths in main menu
- Lines 404-415: Combat command when already in combat
- Lines 905-912: Combat commands outside combat
- Lines 953-968: Conversation mode handling

```python
# tests/test_main_coverage.py - Add tests for edge cases:

def test_handle_exploration_attack_when_not_in_combat(self):
    """Attack command should say 'Not in combat' when not in combat."""
    game_state = create_test_game_state()
    continue_game, message = handle_exploration_command(game_state, "attack", [])
    assert "Not in combat" in message

def test_handle_exploration_unknown_command(self):
    """Unknown command should show help hint."""
    game_state = create_test_game_state()
    continue_game, message = handle_exploration_command(game_state, "xyz", [])
    assert "Unknown command" in message
```

## Test Execution Order

1. Add tests to `tests/test_config.py` for `load_ai_config()` success path
2. Add tests to `tests/test_autosave.py` for corrupted/invalid file handling
3. Add tests to `tests/test_world.py` for logging in non-strict fallback
4. Add tests to `tests/test_main_coverage.py` for remaining edge cases

## Verification

```bash
pytest --cov=src/cli_rpg --cov-report=term-missing tests/test_config.py tests/test_autosave.py tests/test_world.py tests/test_main_coverage.py -v
```

Target: Increase coverage from 94% to 95%+ by covering these specific edge cases.
