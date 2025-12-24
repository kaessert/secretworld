# Implementation Plan: Fix Dead-End Issue in AI-Generated Locations

## Problem Statement
The `expand_world()` function in `ai_world.py` (lines 217-224) creates locations with only the back-connection to the source location. When AI suggests additional connections, they're only added if the target already exists, leaving players stuck in dead-end locations (e.g., "Chrome Canyon" with only north exit).

## Spec Update

**File:** `docs/ai_location_generation_spec.md`

Add to Section 3.3 `expand_world()` documentation:
- "Newly generated locations MUST include at least one dangling connection (beyond the back-connection) to enable future exploration"
- "If AI doesn't suggest additional connections, add a random unused direction as a dangling connection"

---

## Implementation Steps

### Step 1: Add Tests for Dangling Connection Guarantee

**File:** `tests/test_ai_world_generation.py`

Add tests:

```python
def test_expand_world_creates_dangling_connection(mock_ai_service, basic_world):
    """Test expand_world ensures new locations have at least one dangling exit.

    Spec: New locations must have at least one exit besides the back-connection.
    """
    # AI returns location with only back-connection
    mock_ai_service.generate_location.return_value = {
        "name": "Dead End Canyon",
        "description": "A remote canyon.",
        "connections": {"south": "Town Square"}  # Only back-connection
    }

    updated_world = expand_world(
        world=basic_world,
        ai_service=mock_ai_service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )

    # New location must have >= 2 exits (back + dangling)
    new_loc = updated_world["Dead End Canyon"]
    assert len(new_loc.connections) >= 2
    assert new_loc.has_connection("south")  # Back-connection exists

    # At least one non-south connection exists
    other_connections = [d for d in new_loc.connections if d != "south"]
    assert len(other_connections) >= 1


def test_expand_world_preserves_ai_suggested_dangling_connections(mock_ai_service, basic_world):
    """Test expand_world preserves AI-suggested dangling connections.

    Spec: AI-suggested exits to non-existent locations should be kept as dangling.
    """
    mock_ai_service.generate_location.return_value = {
        "name": "Crossroads",
        "description": "A busy crossroads.",
        "connections": {
            "south": "Town Square",  # Back-connection
            "east": "Mountain Path",  # Dangling
            "west": "Dark Forest"     # Dangling
        }
    }

    updated_world = expand_world(
        world=basic_world,
        ai_service=mock_ai_service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )

    new_loc = updated_world["Crossroads"]
    assert new_loc.has_connection("south")
    assert new_loc.has_connection("east")
    assert new_loc.has_connection("west")
    assert new_loc.get_connection("east") == "Mountain Path"
    assert new_loc.get_connection("west") == "Dark Forest"


def test_expand_world_adds_dangling_when_ai_suggests_none(mock_ai_service, basic_world):
    """Test expand_world adds dangling connection when AI suggests none.

    Spec: If AI returns empty connections, a dangling exit must be added.
    """
    mock_ai_service.generate_location.return_value = {
        "name": "Isolated Cave",
        "description": "An isolated cave.",
        "connections": {}  # No connections at all
    }

    updated_world = expand_world(
        world=basic_world,
        ai_service=mock_ai_service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )

    new_loc = updated_world["Isolated Cave"]
    # Must have back-connection + at least one dangling
    assert len(new_loc.connections) >= 2
    assert new_loc.has_connection("south")  # Back to Town Square


def test_expand_world_dangling_excludes_back_direction(mock_ai_service, basic_world):
    """Test added dangling connection is not in back direction.

    Spec: Auto-added dangling exit must be in a different direction than back.
    """
    mock_ai_service.generate_location.return_value = {
        "name": "Remote Place",
        "description": "A remote place.",
        "connections": {"south": "Town Square"}  # Only back
    }

    updated_world = expand_world(
        world=basic_world,
        ai_service=mock_ai_service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )

    new_loc = updated_world["Remote Place"]
    # Get non-back connections
    other_dirs = [d for d in new_loc.connections if d != "south"]
    assert len(other_dirs) >= 1
    # Dangling should not be "south" (the back direction)
    for d in other_dirs:
        assert d != "south"
```

### Step 2: Modify expand_world() Function

**File:** `src/cli_rpg/ai_world.py`

**Replace lines 217-224:**

```python
    # Add suggested dangling connections (keep them even if targets don't exist)
    for new_dir, target_name in location_data["connections"].items():
        if new_dir != opposite:  # Skip the back-connection we already added
            new_location.add_connection(new_dir, target_name)
            # Also add bidirectional connection if target exists
            if target_name in world:
                rev_dir = get_opposite_direction(new_dir)
                if not world[target_name].has_connection(rev_dir):
                    world[target_name].add_connection(rev_dir, new_location.name)

    # Ensure at least one dangling connection for future expansion
    non_back_connections = [d for d in new_location.connections if d != opposite]
    if not non_back_connections:
        import random
        available_dirs = [d for d in Location.VALID_DIRECTIONS
                         if d not in new_location.connections]
        if available_dirs:
            dangling_dir = random.choice(available_dirs)
            placeholder_name = f"Unexplored {dangling_dir.title()}"
            new_location.add_connection(dangling_dir, placeholder_name)
```

### Step 3: Add E2E Test

**File:** `tests/test_e2e_world_expansion.py`

Add test:

```python
def test_expanded_location_never_dead_end(basic_character, mock_ai_service_success):
    """Test: Expanded locations never become dead-ends.

    Spec: Newly expanded locations always have at least one exit besides
    the back-connection, preventing dead-end scenarios like Chrome Canyon.
    """
    # Override mock to return only back-connection
    def generate_dead_end(theme, context_locations, source_location, direction):
        opposites = {"north": "south", "south": "north", "east": "west",
                     "west": "east", "up": "down", "down": "up"}
        return {
            "name": "Chrome Canyon",
            "description": "A canyon with chrome walls.",
            "connections": {opposites[direction]: source_location}  # Only back
        }

    mock_ai_service_success.generate_location.side_effect = generate_dead_end

    town = Location(name="Town Square", description="A town square.")
    town.connections = {"south": "Chrome Canyon"}
    world = {"Town Square": town}

    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="cyberpunk"
    )

    # Trigger expansion
    success, _ = game_state.move("south")
    assert success is True

    # Verify Chrome Canyon has more than just the back exit
    chrome_canyon = game_state.world["Chrome Canyon"]
    assert len(chrome_canyon.connections) >= 2, \
        "Expanded location should have at least 2 exits (back + dangling)"

    # Verify at least one non-back exit exists
    non_back = [d for d in chrome_canyon.connections if d != "north"]
    assert len(non_back) >= 1, \
        "Expanded location must have at least one forward exit for exploration"
```

---

## Verification

1. Run new unit tests: `pytest tests/test_ai_world_generation.py::test_expand_world_creates_dangling_connection tests/test_ai_world_generation.py::test_expand_world_preserves_ai_suggested_dangling_connections tests/test_ai_world_generation.py::test_expand_world_adds_dangling_when_ai_suggests_none tests/test_ai_world_generation.py::test_expand_world_dangling_excludes_back_direction -v`
2. Run E2E test: `pytest tests/test_e2e_world_expansion.py::test_expanded_location_never_dead_end -v`
3. Run full test suite: `pytest`
