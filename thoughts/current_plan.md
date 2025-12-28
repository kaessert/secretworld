# Dungeon Ambient Sounds Implementation

## Spec
Add periodic text-based ambient sound descriptions during SubGrid exploration. Sounds trigger on movement within SubGrid locations (dungeons, caves, ruins, temples), with depth-based intensity and category-specific sound pools.

## Tests (TDD)
1. Create `tests/test_ambient_sounds.py`:
   - `test_get_ambient_sound_returns_string_or_none`: Returns Optional[str]
   - `test_ambient_sound_categories`: Dungeon/cave/ruins/temple have distinct sound pools
   - `test_ambient_sound_depth_scaling`: Deeper z-levels have higher trigger chance
   - `test_ambient_sound_trigger_chance`: ~15% base chance per move
   - `test_ambient_sound_cooldown`: Sounds don't repeat within cooldown period (3 moves)
   - `test_format_ambient_sound`: Format includes `[Sound]:` prefix with dim styling
   - `test_ambient_sound_in_subgrid_move`: Sounds trigger in `_move_in_sub_grid`

## Implementation

### 1. Create `src/cli_rpg/ambient_sounds.py`
```python
# Constants
AMBIENT_SOUND_CHANCE = 0.15  # 15% base chance per move
DEPTH_SOUND_CHANCE_BONUS = 0.05  # +5% per depth level
SOUND_COOLDOWN_MOVES = 3  # Minimum moves between sounds

# Sound pools by category (8-10 sounds each)
CATEGORY_SOUNDS = {
    "dungeon": ["Chains rattle...", "Dripping water echoes...", ...],
    "cave": ["Water drips steadily...", "Bats screech...", ...],
    "ruins": ["Stone groans...", "Wind howls...", ...],
    "temple": ["Distant chanting...", "Bell tolls...", ...],
}

# Depth-based sounds (increasingly ominous)
DEPTH_SOUNDS = {
    -1: ["Echoes take longer to fade...", ...],
    -2: ["Something scrapes against stone...", ...],
    -3: ["Inhuman sounds rise from below...", ...],
}

class AmbientSoundService:
    def __init__(self):
        self.moves_since_last_sound = 0

    def get_ambient_sound(self, category: str, depth: int = 0) -> Optional[str]
    def format_sound(self, text: str) -> str
```

### 2. Update `src/cli_rpg/game_state.py`
- Add `self.ambient_sound_service = AmbientSoundService()` in `__init__`
- In `_move_in_sub_grid` after whisper check (~line 1080), add:
```python
# Check for ambient sound (SubGrid only)
ambient = self.ambient_sound_service.get_ambient_sound(
    category=destination.category,
    depth=dest_z
)
if ambient:
    print(self.ambient_sound_service.format_sound(ambient))
```

### 3. Serialization (Optional but recommended)
Add `moves_since_last_sound` to GameState serialization to persist cooldown across saves.

## Verification
```bash
pytest tests/test_ambient_sounds.py -v
pytest tests/test_game_state.py -v  # Ensure no regressions
```
