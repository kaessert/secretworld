# Issue 23: Dungeon Puzzle Mechanics - AI Generation Integration

## Status
Commands complete. This plan covers the final remaining item: AI puzzle generation during SubGrid creation.

## Spec: Puzzle Generation Requirements

From ISSUES.md:
- 1-2 puzzles per dungeon area (dungeons, caves, ruins, temples)
- Puzzles should use existing PuzzleType: LOCKED_DOOR, LEVER, PRESSURE_PLATE, RIDDLE, SEQUENCE
- Puzzles block directions until solved (Location.blocked_directions)
- INT stat provides hints (hint_threshold, hint_text)

## Design

Follow the pattern established by `_generate_secrets_for_location()`:
1. Define `PUZZLE_CATEGORIES` constant (dungeon, cave, ruins, temple)
2. Define `PUZZLE_TEMPLATES` dict with category-specific puzzle templates
3. Create `_generate_puzzles_for_location()` function
4. Call it in `generate_subgrid_for_location()` for non-entry rooms

### Template Structure
```python
PUZZLE_TEMPLATES = {
    "dungeon": [
        (PuzzleType.LOCKED_DOOR, "Rusted Iron Door", "A heavy iron door...", "Iron Key", 14, "The key bears rusty marks."),
        (PuzzleType.LEVER, "Ancient Lever", "A stone lever...", None, 12, "Worn marks indicate the mechanism."),
        (PuzzleType.RIDDLE, "Stone Guardian", "A statue asks:", "What has keys but no locks?", "piano", 15, "Think of music."),
        # ...
    ],
    "cave": [...],
    # ...
}
```

### Key Placement for LOCKED_DOOR
- Key must be placed in a room that player visits BEFORE the locked door
- Use distance from entry: if puzzle is at distance D, key goes at distance 0 to D-1

## Tests

### File: `tests/test_ai_puzzle_generation.py`

```python
TestPuzzleConstants:
  - test_puzzle_categories_defined
  - test_puzzle_templates_for_each_category

TestGeneratePuzzlesForLocation:
  - test_generates_0_to_2_puzzles
  - test_puzzle_has_required_fields
  - test_locked_door_has_required_key
  - test_riddle_has_riddle_text_and_answer
  - test_lever_has_target_direction
  - test_distance_scales_hint_threshold
  - test_non_puzzle_category_returns_empty

TestSubGridPuzzleIntegration:
  - test_subgrid_rooms_have_puzzles
  - test_puzzles_block_directions
  - test_entry_room_has_no_puzzles
  - test_key_placed_before_locked_door
```

## Implementation Steps

### Step 1: Define puzzle generation constants in ai_world.py

After line ~381 (SECRET_CATEGORIES):
```python
# Categories that should have puzzles
PUZZLE_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple"})

# Puzzle templates: (type, name, description, type-specific-data, hint_threshold, hint_text)
PUZZLE_TEMPLATES: dict[str, list[tuple]] = {
    "dungeon": [
        # LOCKED_DOOR: (type, name, desc, required_key, threshold, hint)
        (PuzzleType.LOCKED_DOOR, "Rusted Iron Door", "A heavy iron door blocks the passage.", "Iron Key", 14, "The lock shows signs of rust."),
        (PuzzleType.LOCKED_DOOR, "Ancient Stone Door", "A massive stone door with intricate carvings.", "Stone Key", 15, "The keyhole matches ancient stonework."),
        # LEVER: (type, name, desc, None, threshold, hint)
        (PuzzleType.LEVER, "Wall Lever", "A rusted lever protrudes from the wall.", None, 12, "Scratch marks show it can be pulled."),
        (PuzzleType.LEVER, "Chain Mechanism", "Heavy chains hang from a pulley.", None, 13, "The chain is worn from use."),
        # PRESSURE_PLATE: (type, name, desc, None, threshold, hint)
        (PuzzleType.PRESSURE_PLATE, "Floor Plate", "A stone plate slightly raised from the floor.", None, 11, "It depresses slightly under weight."),
        # RIDDLE: (type, name, desc, riddle_text, riddle_answer, threshold, hint)
        (PuzzleType.RIDDLE, "Stone Guardian", "A statue with glowing eyes blocks the way.", "What has keys but no locks?", "piano", 15, "Think of music."),
        (PuzzleType.RIDDLE, "Whispering Face", "A carved face in the wall speaks in riddles.", "I have cities but no houses, forests but no trees. What am I?", "map", 14, "Think of representations."),
        # SEQUENCE: (type, name, desc, sequence_ids, threshold, hint)
        (PuzzleType.SEQUENCE, "Torch Row", "Four torches line the walls.", ["torch_1", "torch_2", "torch_3", "torch_4"], 16, "The murals show a lighting order."),
    ],
    "cave": [
        (PuzzleType.PRESSURE_PLATE, "Cracked Stone", "A cracked stone in the floor.", None, 10, "Pressure seems to shift it."),
        (PuzzleType.LEVER, "Crystal Lever", "A lever formed from cave crystal.", None, 11, "The crystal glows faintly."),
        (PuzzleType.LOCKED_DOOR, "Boulder Door", "A massive boulder blocks the tunnel.", "Cave Key", 13, "There's a keyhole in the rock."),
    ],
    "ruins": [
        (PuzzleType.LOCKED_DOOR, "Sealed Portal", "An ancient portal sealed by magic.", "Portal Key", 15, "Glyphs suggest a key exists."),
        (PuzzleType.RIDDLE, "Ancient Oracle", "A spectral figure poses a challenge.", "I am always in front of you but can never be seen. What am I?", "future", 14, "Think of time."),
        (PuzzleType.SEQUENCE, "Rune Stones", "Three rune stones glow dimly.", ["rune_sun", "rune_moon", "rune_star"], 15, "The ceiling mural shows the order."),
    ],
    "temple": [
        (PuzzleType.RIDDLE, "Sacred Guardian", "A divine statue guards the sanctum.", "What is given freely but cannot be bought?", "love", 13, "Think of the heart."),
        (PuzzleType.LEVER, "Altar Mechanism", "A hidden lever behind the altar.", None, 12, "The altar can be moved."),
        (PuzzleType.LOCKED_DOOR, "Blessed Gate", "A gate protected by divine wards.", "Holy Key", 14, "A blessed key would open it."),
    ],
}
```

### Step 2: Create _generate_puzzles_for_location() function

After `_generate_secrets_for_location()` (~line 461):
```python
def _generate_puzzles_for_location(
    category: str,
    distance: int = 0,
    z_level: int = 0,
    available_directions: list[str] = None,
) -> tuple[list[Puzzle], list[str], list[tuple[str, str]]]:
    """Generate 0-2 puzzles for a location.

    Args:
        category: Location category (dungeon, cave, etc.)
        distance: Distance from entry (affects chance and difficulty)
        z_level: Z-level of location (negative = deeper)
        available_directions: Directions that can be blocked

    Returns:
        Tuple of (puzzles, blocked_directions, keys_to_place):
        - puzzles: List of Puzzle objects
        - blocked_directions: List of directions blocked by puzzles
        - keys_to_place: List of (key_name, category) for locked doors
    """
    from cli_rpg.models.puzzle import Puzzle, PuzzleType

    if category not in PUZZLE_CATEGORIES:
        return ([], [], [])

    templates = PUZZLE_TEMPLATES.get(category, [])
    if not templates:
        return ([], [], [])

    # 50% chance of 1 puzzle, 25% chance of 2 puzzles, 25% chance of none
    # But only if distance > 0 (no puzzles at entry)
    if distance == 0:
        return ([], [], [])

    roll = random.random()
    if roll < 0.25:
        num_puzzles = 0
    elif roll < 0.75:
        num_puzzles = 1
    else:
        num_puzzles = 2

    if num_puzzles == 0:
        return ([], [], [])

    # Use available directions if provided, else default
    directions = available_directions or ["north", "south", "east", "west"]
    if not directions:
        return ([], [], [])

    selected = random.sample(templates, min(num_puzzles, len(templates)))
    puzzles = []
    blocked = []
    keys_to_place = []

    for template in selected:
        puzzle_type = template[0]
        # Pick a direction to block
        if not directions:
            break
        target_dir = random.choice(directions)
        directions.remove(target_dir)

        # Scale hint threshold with distance and depth
        base_threshold = template[-2]
        threshold = base_threshold + min(distance, 3) + abs(z_level)
        hint_text = template[-1]

        if puzzle_type == PuzzleType.LOCKED_DOOR:
            # (type, name, desc, required_key, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                required_key=template[3],
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
            keys_to_place.append((template[3], category))
        elif puzzle_type == PuzzleType.LEVER or puzzle_type == PuzzleType.PRESSURE_PLATE:
            # (type, name, desc, None, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
        elif puzzle_type == PuzzleType.RIDDLE:
            # (type, name, desc, riddle_text, riddle_answer, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                riddle_text=template[3],
                riddle_answer=template[4],
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
        elif puzzle_type == PuzzleType.SEQUENCE:
            # (type, name, desc, sequence_ids, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                sequence_ids=template[3].copy(),
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
        else:
            continue

        puzzles.append(puzzle)
        blocked.append(target_dir)

    return (puzzles, blocked, keys_to_place)
```

### Step 3: Create _place_keys_in_earlier_rooms() helper

```python
def _place_keys_in_earlier_rooms(
    placed_locations: dict,
    keys_to_place: list[tuple[str, str, int]],
) -> None:
    """Place keys in rooms before their corresponding locked doors.

    Args:
        placed_locations: Dict of {name: {location, relative_coords, is_entry}}
        keys_to_place: List of (key_name, category, door_distance) tuples
    """
    from cli_rpg.models.item import Item, ItemType

    for key_name, category, door_distance in keys_to_place:
        # Find valid rooms (distance < door_distance, not entry)
        candidates = []
        for name, data in placed_locations.items():
            if data.get("is_entry", False):
                continue
            loc = data.get("location")
            if loc is None:
                continue
            rel = data.get("relative_coords", (0, 0, 0))
            dist = abs(rel[0]) + abs(rel[1])
            if dist < door_distance:
                candidates.append((name, dist, loc))

        if not candidates:
            # Fall back to entry room
            for name, data in placed_locations.items():
                if data.get("is_entry", False):
                    candidates.append((name, 0, data.get("location")))
                    break

        if candidates:
            # Pick room closest to door distance (more interesting placement)
            candidates.sort(key=lambda x: -x[1])
            _, _, room = candidates[0]

            # Create key item and add to room treasures
            key_item = {
                "name": key_name,
                "description": f"A key that might open something in the {category}.",
                "item_type": "misc",
            }
            # Add as a findable item (not locked chest)
            room.treasures.append({
                "name": f"Hidden {key_name}",
                "description": f"A {key_name.lower()} lies on the ground.",
                "locked": False,
                "difficulty": 0,
                "opened": False,
                "items": [key_item],
                "requires_key": None,
            })
```

### Step 4: Integrate puzzle generation in generate_subgrid_for_location()

In `generate_subgrid_for_location()` after placing locations (~line 852), before boss placement:
```python
    # Track keys to place after all rooms are processed
    all_keys_to_place = []

    for loc_data in area_data:
        # ... existing code ...

        # Add puzzles to non-entry rooms
        if not first_location:
            distance = abs(rel_x) + abs(rel_y)
            # Get available directions for this room (approximate)
            avail_dirs = ["north", "south", "east", "west"]
            puzzles, blocked, keys = _generate_puzzles_for_location(
                loc_category or "dungeon", distance, rel_z, avail_dirs
            )
            new_loc.puzzles.extend(puzzles)
            new_loc.blocked_directions.extend(blocked)
            # Track keys with door distance
            for key_name, key_cat in keys:
                all_keys_to_place.append((key_name, key_cat, distance))

        # ... rest of existing code ...

    # Place keys in earlier rooms
    if all_keys_to_place:
        _place_keys_in_earlier_rooms(placed_locations, all_keys_to_place)
```

### Step 5: Also integrate in expand_area()

Similar integration in `expand_area()` function for consistency.

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/ai_world.py` | Add PUZZLE_CATEGORIES, PUZZLE_TEMPLATES, _generate_puzzles_for_location(), _place_keys_in_earlier_rooms(), integrate in generate_subgrid_for_location() and expand_area() |
| `tests/test_ai_puzzle_generation.py` | New test file for puzzle generation |

## Acceptance Criteria Verification

- [x] 1-2 puzzles per dungeon area - via _generate_puzzles_for_location()
- [x] Locked doors requiring keys - keys placed in earlier rooms
- [x] Pressure plates/levers opening passages - via templates
- [x] Riddle puzzles - via templates with riddle_text/answer
- [x] Sequence puzzles - via templates with sequence_ids
- [x] INT hints - hint_threshold scales with distance/depth
