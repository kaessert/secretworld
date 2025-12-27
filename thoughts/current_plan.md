# Plan: Default Character Class for --skip-character-creation

## Spec
When `--skip-character-creation` is used, the default "Agent" character should have `character_class=CharacterClass.WARRIOR` instead of `None`. This enables class-specific abilities (bash, sneak, fireball, etc.) for automated testing and AI agent playtesting.

## Test (TDD)
Add test in `tests/test_non_interactive_character_creation.py`:

```python
def test_skip_character_creation_assigns_warrior_class(self):
    """--skip-character-creation default character should have Warrior class.

    Spec: Default "Agent" character has character_class="warrior" so class
    abilities (bash) work in automated testing and AI agent playtesting.
    """
    result = subprocess.run(
        [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation"],
        input="status\n",
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0
    assert "Warrior" in result.stdout
```

## Implementation
Update two locations in `src/cli_rpg/main.py`:

1. **Line ~2740** (run_json_mode): Change:
   ```python
   character = Character(name="Agent", strength=10, dexterity=10, intelligence=10)
   ```
   to:
   ```python
   character = Character(name="Agent", strength=10, dexterity=10, intelligence=10, character_class=CharacterClass.WARRIOR)
   ```

2. **Line ~2971** (run_non_interactive): Same change.

Note: `CharacterClass` is already available via `from cli_rpg.models.character import Character, CharacterClass` - verify import exists or add it.

## Verification
Run: `pytest tests/test_non_interactive_character_creation.py -v -k skip_character_creation`
