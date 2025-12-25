# Implementation Plan: Multi-Layered Examination (Environmental Storytelling MVP)

## Spec

When players use the `look` command multiple times in the same location, reveal progressively more details:

**Examination Layers**:
1. **Surface (first look)**: Standard location description (current behavior)
2. **Details (second look)**: Additional environmental details (new field on Location)
3. **Secrets (third look)**: Hidden secrets or lore hints (new field on Location)

**Core Behavior**:
- Track look count per location on the player character
- Each look in the same location advances to the next layer
- Moving to a new location resets the look count for the previous location
- Details/secrets are only shown if the location has that content (optional fields)
- AI can generate layer content when service is available

**Display Format**:
```
Town Square
[existing description]
Exits: north, south

Upon closer inspection, you notice:
  - Worn grooves in the cobblestones from years of cart traffic
  - A faded notice board with curling papers
  - The fountain's basin has coins glinting at the bottom

[On third look]
Hidden secrets reveal themselves:
  - Behind the notice board, someone has scratched initials: "R.K. + M.T."
  - One cobblestone near the fountain is loose, as if frequently moved
```

## Tests (TDD)

Create `tests/test_examination.py`:

### 1. Look count tracking tests
- `test_first_look_returns_surface_only`: First look shows standard description
- `test_second_look_reveals_details`: Second look includes details layer
- `test_third_look_reveals_secrets`: Third look includes secrets layer
- `test_fourth_look_repeats_full_description`: Additional looks repeat full content
- `test_moving_resets_look_count`: Moving to new location resets counter

### 2. Location model tests
- `test_location_details_field_optional`: Location works without details
- `test_location_secrets_field_optional`: Location works without secrets
- `test_location_serialization_with_layers`: to_dict/from_dict preserves layers
- `test_location_str_with_layers`: __str__ method includes all layers

### 3. Character look tracking tests
- `test_character_look_counts_init_empty`: New character has no look counts
- `test_character_record_look_increments`: record_look increments counter
- `test_character_get_look_count_returns_zero_for_new`: Unknown location returns 0
- `test_character_look_counts_serialization`: Save/load preserves look counts

### 4. GameState integration tests
- `test_gamestate_look_increments_counter`: look() method updates character
- `test_gamestate_move_resets_previous_look_count`: Move clears old counter

## Implementation Steps

### Step 1: Add look tracking to Character model
**File**: `src/cli_rpg/models/character.py`

Add `look_counts: dict[str, int]` field to track looks per location:

```python
# In Character dataclass
look_counts: dict[str, int] = field(default_factory=dict)

def record_look(self, location_name: str) -> int:
    """Record a look at a location and return the new count."""
    self.look_counts[location_name] = self.look_counts.get(location_name, 0) + 1
    return self.look_counts[location_name]

def get_look_count(self, location_name: str) -> int:
    """Get the number of times player has looked at a location."""
    return self.look_counts.get(location_name, 0)

def reset_look_count(self, location_name: str) -> None:
    """Reset the look count for a location."""
    self.look_counts.pop(location_name, None)
```

Update `to_dict()` and `from_dict()` for serialization.

### Step 2: Add layer fields to Location model
**File**: `src/cli_rpg/models/location.py`

Add optional fields for environmental details and secrets:

```python
# In Location dataclass (after existing fields)
details: Optional[str] = None  # Second-look environmental details
secrets: Optional[str] = None  # Third-look hidden secrets
```

Update `__str__()` to accept a look_level parameter (or create new method):

```python
def get_layered_description(self, look_count: int = 1) -> str:
    """Get description with appropriate layers based on look count."""
    result = f"{colors.location(self.name)}\n"

    if self.ascii_art:
        result += self.ascii_art.strip() + "\n"

    result += f"{self.description}\n"

    if self.npcs:
        npc_names = [colors.npc(npc.name) for npc in self.npcs]
        result += f"NPCs: {', '.join(npc_names)}\n"

    if self.connections:
        directions = self.get_available_directions()
        result += f"Exits: {', '.join(directions)}"
    else:
        result += "Exits: None"

    # Add details layer (look_count >= 2)
    if look_count >= 2 and self.details:
        result += f"\n\nUpon closer inspection, you notice:\n{self.details}"

    # Add secrets layer (look_count >= 3)
    if look_count >= 3 and self.secrets:
        result += f"\n\nHidden secrets reveal themselves:\n{self.secrets}"

    return result
```

Update `to_dict()` and `from_dict()` for serialization (with backward compatibility).

### Step 3: Update GameState.look() method
**File**: `src/cli_rpg/game_state.py`

Modify `look()` to track looks and return layered description:

```python
def look(self) -> str:
    """Get a formatted description of the current location with progressive detail.

    Returns:
        String description with appropriate detail layers based on look count
    """
    location = self.get_current_location()
    # Increment and get look count
    look_count = self.current_character.record_look(self.current_location)
    return location.get_layered_description(look_count)
```

### Step 4: Update GameState.move() to reset look count
**File**: `src/cli_rpg/game_state.py`

In `move()`, reset the look count for the previous location:

```python
# At start of move(), before movement logic:
previous_location = self.current_location

# After successful movement, reset previous location's look count:
self.current_character.reset_look_count(previous_location)
```

### Step 5: Add AI generation for layers (optional)
**File**: `src/cli_rpg/ai_world.py`

Update location generation prompts to include details and secrets fields. This is optional and can be added later - the base system works without AI.

### Step 6: Update world generation to include sample layers
**File**: `src/cli_rpg/world.py`

Add example details/secrets to template locations so the feature is visible without AI:

```python
# In create_default_world() or template generation
town_square = Location(
    name="Town Square",
    description="A bustling town square with a fountain in the center.",
    connections={"north": "Market", "south": "Gate"},
    details="  - Worn grooves in the cobblestones from years of cart traffic\n  - A faded notice board with curling papers\n  - The fountain's basin has coins glinting at the bottom",
    secrets="  - Behind the notice board, someone has scratched initials: 'R.K. + M.T.'\n  - One cobblestone near the fountain is loose, as if frequently moved"
)
```

## Verification

```bash
# Run examination tests
pytest tests/test_examination.py -v

# Run full test suite to check for regressions
pytest

# Manual verification
cli-rpg
> look        # See surface description
> look        # See surface + details
> look        # See surface + details + secrets
> go north    # Move to new location
> go south    # Return to Town Square
> look        # Should show surface only (counter reset)
```
