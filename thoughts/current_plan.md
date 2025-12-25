# Plan: Add ASCII Art to Bestiary

## Summary
Extend the existing bestiary feature to store and display enemy ASCII art on first encounter.

## Spec
- When an enemy is defeated, store its `ascii_art` along with existing enemy_data
- The `bestiary` command should display ASCII art for each discovered enemy
- ASCII art is captured on first encounter and reused for display
- Backward compatible with saves that don't have ascii_art in bestiary entries

## Implementation Steps

### 1. Update `Character.record_enemy_defeat()` to store ASCII art
**File:** `src/cli_rpg/models/character.py` (lines 639-664)

Add `ascii_art` to the `enemy_data` dict stored in bestiary:
```python
self.bestiary[key] = {
    "count": 1,
    "enemy_data": {
        "name": enemy.name,
        "level": enemy.level,
        "attack_power": enemy.attack_power,
        "defense": enemy.defense,
        "description": enemy.description,
        "is_boss": enemy.is_boss,
        "ascii_art": enemy.ascii_art,  # ADD THIS
    }
}
```

### 2. Update bestiary command to display ASCII art
**File:** `src/cli_rpg/main.py` (lines 1040-1062)

Modify the bestiary display loop to show ASCII art if available:
```python
for key in sorted(bestiary.keys()):
    entry = bestiary[key]
    data = entry["enemy_data"]

    lines.append(f"{data['name']} (x{entry['count']})")

    # Show ASCII art if available
    if data.get("ascii_art"):
        for art_line in data["ascii_art"].strip().split("\n"):
            lines.append(f"  {art_line}")

    lines.append(f"  Level {data['level']} | ATK: {data['attack_power']} | DEF: {data['defense']}")
    # ... rest unchanged
```

### 3. Add tests for ASCII art in bestiary

**File:** `tests/test_bestiary.py`

Add test cases:
1. `test_record_enemy_defeat_stores_ascii_art` - Verify ascii_art is stored on first defeat
2. `test_bestiary_command_shows_ascii_art` - Verify command displays art
3. `test_bestiary_backward_compat_no_ascii_art` - Old saves without ascii_art still work

## Test Commands
```bash
pytest tests/test_bestiary.py -v
```
