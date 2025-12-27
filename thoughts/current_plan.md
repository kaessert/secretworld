# Implementation Plan: Hidden Rooms via Secret Doors (SubGrid Integration)

## Summary
Make discovered hidden doors lead to actual hidden rooms within SubGrid locations, not just cosmetic temporary exits.

## Current State
- `search` command works (PER-based checks in `secrets.py`)
- Hidden doors add direction strings to `location.temporary_exits`
- `temporary_exits` are NOT used for actual navigation - they're cosmetic only
- SubGrid rooms are placed at 3D coordinates; navigation uses `_move_in_sub_grid()`

## Spec
When a `hidden_door` secret is discovered:
1. Create an actual hidden room Location in the SubGrid at an empty adjacent coordinate
2. Add the room to the SubGrid so navigation works via `go <direction>`
3. Hidden rooms should have thematic content (treasure, lore, sometimes traps)
4. The `temporary_exits` field can be removed since navigation will use real coordinates

## Implementation

### Step 1: Add hidden room generation function in secrets.py

**File**: `src/cli_rpg/secrets.py`

Add function to generate hidden rooms when hidden_door secrets are discovered:

```python
def generate_hidden_room(
    location: Location,
    sub_grid: "SubGrid",
    direction: str,
    parent_category: Optional[str] = None,
) -> Optional[Location]:
    """Generate a hidden room in the SubGrid at an empty adjacent coordinate.

    Args:
        location: Current location where door was found
        sub_grid: The SubGrid to add the room to
        direction: Direction the hidden door leads (north, south, east, west, up, down)
        parent_category: Category of parent location for theming

    Returns:
        The new Location if created, None if no valid position found
    """
```

Logic:
1. Get current location's 3D coordinates
2. Calculate target coordinates using `SUBGRID_DIRECTION_OFFSETS[direction]`
3. Check if target is within bounds AND empty
4. If valid, create a thematic hidden room Location
5. Add to SubGrid via `sub_grid.add_location()`
6. Return the new location

Hidden room templates by parent category:
- `dungeon`: "Hidden Chamber", "Secret Vault", "Forgotten Cell"
- `cave`: "Crystal Grotto", "Hidden Cavern", "Secret Pool"
- `forest`: "Hidden Glade", "Secret Hollow", "Fairy Circle"
- `temple`: "Hidden Shrine", "Secret Crypt", "Sacred Chamber"
- Default: "Hidden Room", "Secret Alcove", "Concealed Chamber"

### Step 2: Modify `_apply_hidden_door()` to create real rooms

**File**: `src/cli_rpg/secrets.py`

Update `_apply_hidden_door()` to:
1. Accept additional parameters: `sub_grid` and `parent_category`
2. Call `generate_hidden_room()` to create the actual room
3. Fall back to `temporary_exits` only if room creation fails

**Current**:
```python
def _apply_hidden_door(location: Location, secret: dict) -> str:
    exit_direction = secret.get("exit_direction", "secret passage")
    if exit_direction not in location.temporary_exits:
        location.temporary_exits.append(exit_direction)
    return f"A hidden passage to the {exit_direction} is revealed!"
```

**Updated**:
```python
def _apply_hidden_door(
    location: Location,
    secret: dict,
    sub_grid: Optional["SubGrid"] = None,
    parent_category: Optional[str] = None,
) -> str:
    exit_direction = secret.get("exit_direction", "north")

    # Try to generate actual hidden room in SubGrid
    if sub_grid is not None:
        hidden_room = generate_hidden_room(
            location, sub_grid, exit_direction, parent_category
        )
        if hidden_room is not None:
            return f"A hidden passage to the {exit_direction} reveals {hidden_room.name}!"

    # Fallback: just add temporary exit (cosmetic)
    if exit_direction not in location.temporary_exits:
        location.temporary_exits.append(exit_direction)
    return f"A hidden passage to the {exit_direction} is revealed!"
```

### Step 3: Update `apply_secret_rewards()` signature

**File**: `src/cli_rpg/secrets.py`

Update `apply_secret_rewards()` to accept and pass SubGrid context:

```python
def apply_secret_rewards(
    char: Character,
    location: Location,
    secret: dict,
    sub_grid: Optional["SubGrid"] = None,
) -> Tuple[bool, str]:
```

Update the `HIDDEN_DOOR` case:
```python
elif secret_type == SecretType.HIDDEN_DOOR.value:
    messages.append(_apply_hidden_door(
        location, secret, sub_grid, location.category
    ))
```

### Step 4: Update `perform_active_search()` to pass SubGrid

**File**: `src/cli_rpg/secrets.py`

Update signature and pass SubGrid:
```python
def perform_active_search(
    char: Character,
    location: Location,
    sub_grid: Optional["SubGrid"] = None,
) -> Tuple[bool, str]:
```

Pass `sub_grid` to `apply_secret_rewards()`.

### Step 5: Update search command in main.py

**File**: `src/cli_rpg/main.py`

Find the `search` command handler and pass the SubGrid:

```python
elif command == "search":
    found, message = perform_active_search(
        game_state.current_character,
        game_state.get_current_location(),
        sub_grid=game_state.current_sub_grid,  # Pass SubGrid context
    )
```

### Step 6: Add hidden room templates

**File**: `src/cli_rpg/secrets.py`

Add template dictionaries:
```python
HIDDEN_ROOM_TEMPLATES = {
    "dungeon": [
        ("Hidden Chamber", "A dusty chamber concealed behind the wall. Cobwebs drape ancient shelves."),
        ("Secret Vault", "A small vault with iron-banded chests. Someone hid their treasures here."),
        ("Forgotten Cell", "A cramped cell, long abandoned. Scratch marks cover the walls."),
    ],
    "cave": [
        ("Crystal Grotto", "A natural hollow where crystals glitter in the darkness."),
        ("Hidden Cavern", "A secluded cave with a still pool of water."),
        ("Secret Pool", "An underground spring hidden from view."),
    ],
    "forest": [
        ("Hidden Glade", "A peaceful clearing hidden by dense undergrowth."),
        ("Secret Hollow", "A concealed hollow within a massive ancient tree."),
        ("Fairy Circle", "A mystical circle of mushrooms in a hidden clearing."),
    ],
    "temple": [
        ("Hidden Shrine", "A secret shrine to a forgotten deity."),
        ("Secret Crypt", "An unmarked crypt beneath the floor."),
        ("Sacred Chamber", "A chamber of meditation hidden from worldly eyes."),
    ],
    "default": [
        ("Hidden Room", "A secret room concealed behind a false wall."),
        ("Secret Alcove", "A small alcove hidden from casual view."),
        ("Concealed Chamber", "A chamber that has been carefully hidden."),
    ],
}
```

### Step 7: Add hidden room contents

Hidden rooms should contain rewards. Add to `generate_hidden_room()`:
```python
# 50% chance of treasure
if random.random() < 0.5:
    hidden_room.hidden_secrets.append({
        "type": "hidden_treasure",
        "description": "A cache left by whoever built this secret room.",
        "threshold": 8,  # Easy to find once you're in
        "discovered": False,
        "reward_gold": random.randint(20, 50),
    })
```

## Tests

**File**: `tests/test_hidden_rooms.py` (new file)

```python
"""Tests for hidden rooms generated from secret doors."""
import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid
from cli_rpg.secrets import (
    generate_hidden_room,
    perform_active_search,
    apply_secret_rewards,
)


class TestHiddenRoomGeneration:
    """Test hidden room creation from secret doors."""

    def test_generate_hidden_room_creates_location(self):
        """generate_hidden_room creates a Location in the SubGrid."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        origin = Location(name="Entry Hall", description="A hall.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "north", "dungeon")

        assert hidden is not None
        assert hidden.coordinates == (0, 1, 0)
        assert sub_grid.get_by_coordinates(0, 1, 0) == hidden

    def test_generate_hidden_room_fails_when_occupied(self):
        """generate_hidden_room returns None if target cell is occupied."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        origin = Location(name="Entry Hall", description="A hall.")
        blocker = Location(name="Other Room", description="Another room.")
        sub_grid.add_location(origin, 0, 0)
        sub_grid.add_location(blocker, 0, 1)

        hidden = generate_hidden_room(origin, sub_grid, "north", "dungeon")

        assert hidden is None

    def test_generate_hidden_room_fails_out_of_bounds(self):
        """generate_hidden_room returns None if target is out of bounds."""
        sub_grid = SubGrid(bounds=(0, 0, 0, 0, 0, 0), parent_name="Tiny")
        origin = Location(name="Only Room", description="The only room.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "north", "dungeon")

        assert hidden is None

    def test_hidden_room_uses_category_templates(self):
        """Hidden rooms use templates matching parent category."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Cave")
        origin = Location(name="Cave Entry", description="A cave.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "east", "cave")

        assert hidden is not None
        # Cave templates have specific names
        assert any(word in hidden.name for word in ["Crystal", "Cavern", "Grotto", "Pool", "Hidden"])


class TestHiddenDoorCreatesRoom:
    """Test that discovering hidden_door creates real rooms."""

    def test_search_creates_hidden_room_in_subgrid(self):
        """Discovering hidden_door via search creates navigable room."""
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=18)
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        location = Location(
            name="Hall",
            description="A hall.",
            coordinates=(0, 0, 0),
            hidden_secrets=[{
                "type": "hidden_door",
                "description": "A hidden passage",
                "threshold": 12,
                "exit_direction": "north",
            }]
        )
        sub_grid.add_location(location, 0, 0)

        found, message = perform_active_search(char, location, sub_grid)

        assert found
        assert "north" in message.lower()
        # Verify room was actually created
        hidden = sub_grid.get_by_coordinates(0, 1, 0)
        assert hidden is not None

    def test_search_falls_back_to_temporary_exits_outside_subgrid(self):
        """Hidden door adds temporary_exit when not in SubGrid."""
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=18)
        location = Location(
            name="Overworld",
            description="Open area.",
            hidden_secrets=[{
                "type": "hidden_door",
                "description": "A hidden path",
                "threshold": 12,
                "exit_direction": "west",
            }]
        )

        found, message = perform_active_search(char, location, sub_grid=None)

        assert found
        assert "west" in location.temporary_exits


class TestHiddenRoomNavigation:
    """Test that hidden rooms are navigable after discovery."""

    def test_can_navigate_to_hidden_room(self):
        """Player can use go command to enter hidden room after discovery."""
        from cli_rpg.game_state import GameState

        # Setup
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=18)
        overworld = Location(name="Dungeon", description="A dungeon.", is_overworld=True)
        hall = Location(
            name="Entry Hall",
            description="A dark hall.",
            coordinates=(0, 0, 0),
            hidden_secrets=[{
                "type": "hidden_door",
                "description": "Hidden passage",
                "threshold": 10,
                "exit_direction": "north",
            }]
        )
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        sub_grid.add_location(hall, 0, 0)
        overworld.sub_grid = sub_grid
        overworld.entry_point = "Entry Hall"
        hall.is_exit_point = True

        world = {"Dungeon": overworld}
        game_state = GameState(char, world, "Dungeon")
        game_state.enter()  # Enter dungeon

        # Discover hidden door
        perform_active_search(char, hall, sub_grid)

        # Navigate to hidden room
        success, message = game_state.move("north")

        assert success
        assert "Hidden" in game_state.current_location or "Secret" in game_state.current_location
```

## Verification

```bash
# Run new tests
pytest tests/test_hidden_rooms.py -v

# Run existing secret tests to ensure no regression
pytest tests/test_secret_rewards.py -v
pytest tests/test_perception.py -v

# Full test suite
pytest
```

## Files Modified
1. `src/cli_rpg/secrets.py` - Add `generate_hidden_room()`, update `_apply_hidden_door()`, `apply_secret_rewards()`, `perform_active_search()`
2. `src/cli_rpg/main.py` - Pass `sub_grid` to `perform_active_search()` in search command
3. `tests/test_hidden_rooms.py` - New test file (7+ tests)
