# Implementation Summary: Multi-Layered Examination (Environmental Storytelling MVP)

## What Was Implemented

### Feature Overview
The multi-layered examination system allows players to reveal progressively more details about a location by using the `look` command multiple times:

1. **First look**: Standard surface description (existing behavior)
2. **Second look**: Reveals environmental details
3. **Third look**: Reveals hidden secrets or lore hints

Moving to a new location resets the look counter for the previous location, so returning to a location starts fresh.

### Files Modified

#### 1. `src/cli_rpg/models/character.py`
- Added `look_counts: Dict[str, int]` field to track looks per location
- Added three new methods:
  - `record_look(location_name) -> int`: Increment and return look count
  - `get_look_count(location_name) -> int`: Get current look count (0 if never looked)
  - `reset_look_count(location_name) -> None`: Clear look count for a location
- Updated `to_dict()` to include look_counts in serialization
- Updated `from_dict()` to restore look_counts (with backward compatibility)

#### 2. `src/cli_rpg/models/location.py`
- Added two new optional fields:
  - `details: Optional[str]` - Environmental details (shown on second look)
  - `secrets: Optional[str]` - Hidden secrets (shown on third look)
- Added `get_layered_description(look_count) -> str` method that builds the description with appropriate layers
- Updated `to_dict()` to include details/secrets in serialization
- Updated `from_dict()` to restore details/secrets (with backward compatibility)

#### 3. `src/cli_rpg/game_state.py`
- Modified `look()` method to:
  - Increment character's look count for current location
  - Return layered description based on look count
- Modified `move()` method to:
  - Track previous location before movement
  - Reset look count for previous location after successful movement

### Files Created

#### `tests/test_examination.py`
25 tests covering:
- Character look tracking (7 tests)
- Location layer fields (6 tests)
- Location layered description method (6 tests)
- GameState integration (6 tests)

## Test Results

```
tests/test_examination.py: 25 passed
Full test suite: 1852 passed
```

No regressions introduced.

## Display Format

When details/secrets are available:

```
Town Square
A bustling town square with a fountain in the center.
Exits: north, south

Upon closer inspection, you notice:
  - Worn grooves in the cobblestones from years of cart traffic
  - A faded notice board with curling papers
  - The fountain's basin has coins glinting at the bottom

Hidden secrets reveal themselves:
  - Behind the notice board, someone has scratched initials: "R.K. + M.T."
  - One cobblestone near the fountain is loose, as if frequently moved
```

## Design Decisions

1. **Backward Compatibility**: All new fields are optional with defaults that preserve existing behavior
2. **Look Counter Reset**: Counter resets when leaving a location, not when returning. This ensures fresh exploration each visit.
3. **Serialization**: Look counts are persisted in save files (useful for game continuity)
4. **Layer Content Format**: Details and secrets are stored as raw strings, allowing flexibility for formatting (e.g., bullet points with "  - " prefix)

## E2E Testing Notes

To manually verify:
1. Start a new game
2. Use `look` command 3 times in starting location
3. Move to another location
4. Return to starting location
5. Verify `look` shows only surface description (counter was reset)

**Note**: The feature requires locations to have `details` and `secrets` fields populated to see the effect. Currently, this can be added:
- By AI generation (when AI service is available)
- By manually adding to template locations in `world.py`
- In save files directly
