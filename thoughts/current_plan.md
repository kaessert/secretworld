# Implementation Plan: Make WFC Default

## Spec

Replace `--wfc` flag with `--no-wfc` flag so WFC terrain generation is enabled by default. Wire WFC to non-interactive modes (`--json`, `--non-interactive`) which currently always use fallback world generation.

## Files to Modify

1. `src/cli_rpg/main.py` - Flip flag, wire WFC to all modes
2. `tests/test_wfc_integration.py` - Add test for `--no-wfc` flag behavior

## Tests

### New Test: `tests/test_wfc_integration.py`

Add to test file:

```python
class TestWFCDefaultBehavior:
    """Tests for WFC being default behavior."""

    def test_wfc_enabled_by_default_in_start_game(self, basic_character, basic_world):
        """Test: start_game uses WFC by default (use_wfc=True)."""
        # Verify start_game signature defaults use_wfc=True
        import inspect
        from cli_rpg.main import start_game
        sig = inspect.signature(start_game)
        assert sig.parameters['use_wfc'].default == True

    def test_no_wfc_flag_disables_wfc(self, basic_character, basic_world):
        """Test: --no-wfc flag sets use_wfc=False."""
        from cli_rpg.main import parse_args
        args = parse_args(['--no-wfc'])
        assert args.no_wfc == True  # Flag is set
```

## Implementation Steps

### Step 1: Change `--wfc` to `--no-wfc` in argument parser (line ~2852)

Change:
```python
parser.add_argument(
    "--wfc",
    action="store_true",
    help="Enable WFC terrain generation for infinite procedural world"
)
```

To:
```python
parser.add_argument(
    "--no-wfc",
    action="store_true",
    help="Disable WFC terrain generation (use fixed world instead)"
)
```

### Step 2: Invert the flag usage in interactive mode (line ~2891)

Change:
```python
use_wfc = parsed_args.wfc
```

To:
```python
use_wfc = not parsed_args.no_wfc
```

### Step 3: Change `start_game()` default parameter (line ~2336)

Change:
```python
def start_game(
    character: "Character",
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy",
    strict: bool = False,
    use_wfc: bool = False,
) -> None:
```

To:
```python
def start_game(
    character: "Character",
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy",
    strict: bool = False,
    use_wfc: bool = True,
) -> None:
```

### Step 4: Wire WFC to `run_json_mode()` (lines ~2502-2510)

Change:
```python
world, starting_location = create_world(ai_service=ai_service, theme="fantasy", strict=False)

game_state = GameState(
    character,
    world,
    starting_location=starting_location,
    ai_service=ai_service,
    theme="fantasy"
)
```

To:
```python
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY
import random

world, starting_location = create_world(ai_service=ai_service, theme="fantasy", strict=False)
chunk_manager = ChunkManager(
    tile_registry=DEFAULT_TILE_REGISTRY,
    world_seed=random.randint(0, 2**31 - 1),
)

game_state = GameState(
    character,
    world,
    starting_location=starting_location,
    ai_service=ai_service,
    theme="fantasy",
    chunk_manager=chunk_manager,
)
```

### Step 5: Wire WFC to `run_non_interactive()` (lines ~2707-2715)

Apply same change as Step 4.

### Step 6: Run tests

```bash
pytest tests/test_wfc_integration.py tests/test_wfc.py tests/test_wfc_chunks.py -v
```
