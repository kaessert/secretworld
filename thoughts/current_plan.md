# Issue 27: Dungeon Ambiance System - Location-Specific Whispers (Increment 1)

## Spec

Expand the existing whisper system to provide richer, location-specific atmospheric feedback in dungeons and other interior locations. This increment focuses on:

1. **Expanded category-specific whispers**: Add more whisper templates for dungeon, cave, ruins, temple, and forest categories (matching the pattern in `hallucinations.py` and `encounter_tables.py`)
2. **Depth-based whisper intensity**: Deeper dungeon levels (negative z-coordinates) select from more ominous whisper pools
3. **Progressive dread from depth**: Deeper exploration increases dread accumulation rate

## Tests First (tests/test_dungeon_ambiance.py)

### TestExpandedCategoryWhispers
1. `test_dungeon_whispers_expanded` - Verify dungeon category has 8+ whisper templates (up from 3)
2. `test_cave_whispers_expanded` - Verify cave category has 8+ whisper templates
3. `test_ruins_whispers_expanded` - Verify ruins category has 8+ whisper templates
4. `test_temple_whispers_expanded` - Verify temple category has 8+ whisper templates
5. `test_forest_whispers_expanded` - Verify forest category has 8+ whisper templates

### TestDepthWhispers
6. `test_depth_whisper_templates_exist` - Verify `DEPTH_WHISPERS` dict exists with z-level keys (0, -1, -2, -3)
7. `test_surface_whispers_mild` - z=0 uses standard category whispers
8. `test_shallow_depth_whispers` - z=-1 includes some ominous templates
9. `test_deep_whispers_ominous` - z=-2 and below uses increasingly dark templates
10. `test_get_whisper_accepts_depth` - `get_whisper()` accepts optional `depth` parameter

### TestDepthDread
11. `test_depth_dread_modifier_exists` - `get_depth_dread_modifier(z)` function exists
12. `test_surface_no_extra_dread` - z=0 returns modifier of 1.0
13. `test_shallow_depth_dread` - z=-1 returns 1.25x dread modifier
14. `test_deep_dread_modifier` - z=-2 returns 1.5x, z=-3 returns 2.0x
15. `test_dread_capped_at_depth` - z < -3 caps at 2.0x modifier

### TestWhisperIntegrationWithDepth
16. `test_subgrid_movement_passes_depth` - `_move_in_sub_grid` passes z-coordinate to whisper service
17. `test_subgrid_dread_uses_depth_modifier` - Dread gain in SubGrid uses depth modifier

## Implementation Steps

### 1. Expand whisper templates in `src/cli_rpg/whisper.py`

Add more category-specific whispers (8+ per category):
```python
CATEGORY_WHISPERS = {
    "dungeon": [
        # Existing 3 + add 5 more:
        "Rust-colored stains mark the walls...",
        "The scent of decay lingers here.",
        "Chains rattle somewhere in the dark.",
        "Faint scratching sounds from behind the stones.",
        "The torchlight seems dimmer here...",
    ],
    # Similar expansions for cave, ruins, temple, forest
}
```

### 2. Add depth-based whisper system in `src/cli_rpg/whisper.py`

```python
DEPTH_WHISPERS = {
    0: [],  # Use standard category whispers
    -1: [
        "The weight of stone presses down above you...",
        "Echoes seem to take longer to fade here.",
    ],
    -2: [
        "The air grows thick and stale...",
        "Something ancient stirs in the depths below.",
    ],
    -3: [  # And deeper
        "You sense you've gone where few return from...",
        "The darkness here feels alive, hungry.",
    ],
}

DEPTH_WHISPER_CHANCE = 0.40  # 40% chance to use depth whisper when underground
```

### 3. Update `WhisperService.get_whisper()` signature

Add optional `depth: int = 0` parameter:
```python
def get_whisper(
    self,
    location_category: Optional[str],
    character: Optional["Character"] = None,
    theme: str = "fantasy",
    is_night: bool = False,
    dread: int = 0,
    depth: int = 0  # NEW: z-coordinate for depth-based whispers
) -> Optional[str]:
```

### 4. Add depth selection logic in `_get_template_whisper()`

```python
def _get_template_whisper(
    self, category: Optional[str], is_night: bool = False, depth: int = 0
) -> str:
    # At night, chance to use night-specific whispers
    if is_night and random.random() < NIGHT_WHISPER_CHANCE:
        return random.choice(NIGHT_WHISPERS)

    # Underground, chance to use depth whispers
    if depth < 0 and random.random() < DEPTH_WHISPER_CHANCE:
        depth_key = max(depth, -3)  # Cap at -3
        if DEPTH_WHISPERS.get(depth_key):
            return random.choice(DEPTH_WHISPERS[depth_key])

    whispers = CATEGORY_WHISPERS.get(category or "default", CATEGORY_WHISPERS["default"])
    return random.choice(whispers)
```

### 5. Add depth dread modifier function in `src/cli_rpg/whisper.py`

```python
def get_depth_dread_modifier(z: int) -> float:
    """Get dread accumulation modifier based on depth.

    Args:
        z: Z-coordinate (0 = surface, negative = underground)

    Returns:
        Dread multiplier (1.0 at surface, up to 2.0 at depth -3+)
    """
    if z >= 0:
        return 1.0
    elif z == -1:
        return 1.25
    elif z == -2:
        return 1.5
    else:  # z <= -3
        return 2.0
```

### 6. Update `game_state.py` `_move_in_sub_grid()`

Pass depth to whisper service:
```python
# In _move_in_sub_grid(), after successful move:
whisper = self.whisper_service.get_whisper(
    location_category=location.category,
    character=self.current_character,
    theme=self.theme,
    is_night=self.game_time.is_night(),
    dread=self.current_character.dread_meter.dread,
    depth=self.sub_grid_position[2]  # z-coordinate
)
```

### 7. Update dread gain in `_move_in_sub_grid()` to use depth modifier

```python
from cli_rpg.whisper import get_depth_dread_modifier

# When adding dread during SubGrid movement:
base_dread = 2  # Base dread per move in dungeon
depth_modifier = get_depth_dread_modifier(self.sub_grid_position[2])
dread_gain = int(base_dread * depth_modifier)
milestone = self.current_character.dread_meter.add_dread(dread_gain)
```

## Files Modified

- `src/cli_rpg/whisper.py` - Expanded templates, depth whispers, depth dread modifier
- `src/cli_rpg/game_state.py` - Pass depth to whisper service, use depth dread modifier
- `tests/test_dungeon_ambiance.py` - New test file with 17 tests
