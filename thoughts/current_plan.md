# Implementation Plan: Load Character Screen UX Improvements

## Spec
Improve the load character screen to handle many saves gracefully:
1. Limit display to 20 most recent saves (manual saves first)
2. Group autosaves separately with collapse option
3. Fix "(saved: unknown)" timestamp parsing issue by using file mtime
4. Add pagination hint when more saves exist

## Files to Modify
- `src/cli_rpg/persistence.py` - Add `is_autosave` detection, improve timestamp parsing
- `src/cli_rpg/main.py` - Update `select_and_load_character()` display logic

## Tests First

### `tests/test_persistence.py` - Add tests:
```python
class TestListSavesEnhancements:
    def test_list_saves_identifies_autosaves(self, tmp_path):
        """Autosave files should be marked with is_autosave=True."""

    def test_list_saves_parses_timestamp_from_file_mtime(self, tmp_path):
        """When filename timestamp is 'unknown', use file mtime."""

    def test_list_saves_formats_display_time(self, tmp_path):
        """Saves should include human-readable display_time field."""
```

### `tests/test_main_load_integration.py` - Add tests:
```python
class TestLoadScreenDisplay:
    def test_display_groups_autosaves_separately(self, tmp_path):
        """Autosaves shown in collapsed section after manual saves."""

    def test_display_limits_manual_saves(self, tmp_path):
        """Only 15 most recent manual saves shown with 'more available' hint."""

    def test_display_shows_readable_timestamps(self, tmp_path):
        """Timestamps displayed as 'Dec 25, 2024 3:45 PM' not '20241225_154500'."""
```

## Implementation Steps

### Step 1: Enhance `list_saves()` in `persistence.py`

Add helper function and update return format:

```python
def _format_timestamp(ts: str) -> str:
    """Convert YYYYMMDD_HHMMSS to human-readable format."""
    try:
        dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
        return dt.strftime("%b %d, %Y %I:%M %p")
    except ValueError:
        return ts

def list_saves(save_dir: str = "saves") -> list[dict[str, str]]:
    # ... existing file discovery ...

    for json_file in json_files:
        filename = json_file.stem

        # Detect autosave
        is_autosave = filename.startswith("autosave_")

        # Parse filename for timestamp (existing logic)
        parts = filename.rsplit('_', 2)
        if len(parts) >= 3:
            character_name = '_'.join(parts[:-2])
            timestamp = f"{parts[-2]}_{parts[-1]}"
        else:
            character_name = filename
            timestamp = "unknown"

        # Fallback timestamp from file mtime if unknown
        if timestamp == "unknown":
            mtime = json_file.stat().st_mtime
            timestamp = datetime.fromtimestamp(mtime).strftime("%Y%m%d_%H%M%S")

        saves.append({
            'name': character_name,
            'filepath': str(json_file),
            'timestamp': timestamp,
            'display_time': _format_timestamp(timestamp),
            'is_autosave': is_autosave
        })

    # Sort by timestamp (most recent first)
    saves.sort(key=lambda x: x['timestamp'], reverse=True)
    return saves
```

### Step 2: Update `select_and_load_character()` in `main.py`

Refactor display logic:

```python
def select_and_load_character() -> tuple[Optional[Character], Optional[GameState]]:
    all_saves = list_saves()

    if not all_saves:
        print("\n⚠ No saved characters found.")
        print("  Create a new character first!")
        return (None, None)

    # Separate manual saves and autosaves
    manual_saves = [s for s in all_saves if not s.get('is_autosave')]
    autosaves = [s for s in all_saves if s.get('is_autosave')]

    # Limit display
    MANUAL_LIMIT = 15
    displayed_manual = manual_saves[:MANUAL_LIMIT]
    hidden_manual = len(manual_saves) - len(displayed_manual)

    print("\n" + "=" * 50)
    print("LOAD CHARACTER")
    print("=" * 50)

    # Build selection list
    selectable = []
    idx = 1

    # Display manual saves
    if displayed_manual:
        print("\nSaved Games:")
        for save in displayed_manual:
            print(f"  {idx}. {save['name']} ({save['display_time']})")
            selectable.append(save)
            idx += 1
        if hidden_manual > 0:
            print(f"      ... and {hidden_manual} older saves")

    # Display autosave summary + option
    if autosaves:
        latest = autosaves[0]
        print(f"\n  {idx}. [Autosave] {latest['name']} ({latest['display_time']})")
        if len(autosaves) > 1:
            print(f"      ({len(autosaves) - 1} older autosaves available)")
        selectable.append(latest)
        idx += 1

    print(f"\n  {idx}. Cancel")
    print("=" * 50)

    # ... rest of selection logic using selectable list ...
```

### Step 3: Run tests
```bash
pytest tests/test_persistence.py tests/test_main_load_integration.py -v
```

## Success Criteria
- [ ] Manual saves displayed first with human-readable timestamps
- [ ] At most 15 manual saves shown, with "(X older saves)" hint
- [ ] Autosaves collapsed to single entry with count
- [ ] No more "(saved: unknown)" - all saves show readable timestamps
- [ ] All existing tests pass
