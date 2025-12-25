# Plan: Add test for invalid category in area generation

## Task
Add a single test to cover lines 760-763 in `ai_service.py` — the warning branch when `_validate_area_location` receives an invalid category value.

## Implementation

### Step 1: Add test to `tests/test_ai_location_category.py`

Add test after `test_area_generation_missing_category_defaults_to_none` (around line 307):

```python
@patch('cli_rpg.ai_service.OpenAI')
def test_area_generation_invalid_category_defaults_to_none(mock_openai_class, basic_config):
    """Test area locations with invalid category default to None and log warning."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    area_response = [
        {
            "name": "Weird Location",
            "description": "A location with an invalid category.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"},
            "category": "invalid_dungeon"  # Invalid category
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="mysterious",
        entry_direction="north",
        context_locations=[],
        size=4
    )

    assert len(result) == 1
    assert result[0]["category"] is None
```

### Step 2: Verify

```bash
pytest tests/test_ai_location_category.py::test_area_generation_invalid_category_defaults_to_none -v
pytest --cov=src/cli_rpg/ai_service --cov-report=term-missing
```
