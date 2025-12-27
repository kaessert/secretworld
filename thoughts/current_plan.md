# Implementation Plan: Fast Travel Between Discovered Overworld Locations

## Feature Summary
Add a `travel` command that allows players to teleport to any previously-visited named overworld location (towns, cities, dungeons, etc.). Travel consumes time proportional to distance and has a chance for random encounters during the journey.

## Specification

### Command Syntax
```
travel                    # List available fast travel destinations
travel <location>         # Travel to the specified named location
```

### Eligibility Rules
1. **Destination must exist** in `game_state.world` with coordinates
2. **Destination must be `is_named=True`** (only named POIs, not terrain filler)
3. **Destination must be on the overworld** (`parent_location is None`)
4. **Cannot travel while inside a SubGrid** - must `exit` first
5. **Cannot travel during combat** - block with helpful message
6. **Cannot travel during conversation** - block with helpful message

### Travel Mechanics
1. **Time cost**: Manhattan distance / 4 hours (minimum 1 hour, maximum 8 hours)
2. **Random encounter chance**: 15% per hour traveled (uses existing `check_for_random_encounter`)
3. **Tiredness increase**: 3 per hour traveled (same as normal movement)
4. **Dread**: Average wilderness dread (5) per hour
5. **Weather**: Transitions after travel

---

## Implementation Steps

### Step 1: Add `travel` to KNOWN_COMMANDS
**File**: `src/cli_rpg/game_state.py` (line ~77)

Add `"travel"` to the `KNOWN_COMMANDS` set.

### Step 2: Implement `get_fast_travel_destinations()` method
**File**: `src/cli_rpg/game_state.py`

```python
def get_fast_travel_destinations(self) -> list[str]:
    """Get list of valid fast travel destinations.

    Returns named overworld locations (excluding current location).
    """
    destinations = []
    for loc in self.world.values():
        # Must be named POI, have coordinates, be overworld (no parent)
        if (loc.is_named and
            loc.coordinates is not None and
            loc.parent_location is None and
            loc.name != self.current_location):
            destinations.append(loc.name)
    return sorted(destinations)
```

### Step 3: Implement `fast_travel()` method
**File**: `src/cli_rpg/game_state.py`

```python
def fast_travel(self, destination: str) -> tuple[bool, str]:
    """Travel instantly to a previously-visited named location.

    Args:
        destination: Name of destination (case-insensitive partial match)

    Returns:
        Tuple of (success, message)
    """
    # Block conditions
    if self.is_in_combat():
        return (False, "You cannot travel while in combat!")
    if self.is_in_conversation:
        return (False, "You're in a conversation. Say 'bye' to leave first.")
    if self.in_sub_location:
        return (False, "You must exit this location before fast traveling. Use 'exit' first.")

    # Find destination (case-insensitive partial match)
    dest_lower = destination.lower()
    matched = None
    for name in self.get_fast_travel_destinations():
        if name.lower().startswith(dest_lower) or dest_lower in name.lower():
            matched = name
            break

    if matched is None:
        return (False, f"Unknown destination: {destination}. Use 'travel' to see available locations.")

    dest_location = self.world[matched]
    current = self.get_current_location()

    # Calculate Manhattan distance and travel time
    dx = abs(dest_location.coordinates[0] - current.coordinates[0])
    dy = abs(dest_location.coordinates[1] - current.coordinates[1])
    distance = dx + dy
    travel_hours = max(1, min(8, distance // 4))

    messages = [f"You begin your journey to {colors.location(matched)}..."]

    # Simulate travel hour by hour
    for hour in range(travel_hours):
        # Advance time
        self.game_time.advance(1)

        # Weather transition
        self.weather.transition()

        # Tiredness increase (3 per move)
        tiredness_msg = self.current_character.tiredness.increase(3)
        if tiredness_msg:
            messages.append(tiredness_msg)

        # Dread increase (wilderness average = 5)
        dread_msg = self.current_character.dread_meter.add_dread(5)
        if dread_msg:
            messages.append(dread_msg)

        # Random encounter check (15% per hour)
        if random.random() < 0.15 and not self.get_current_location().is_safe_zone:
            # Hostile encounter interrupts travel
            enemy = spawn_enemy(
                location_name=self.current_location,
                level=self.current_character.level,
                location_category="wilderness",
            )
            self.current_combat = CombatEncounter(
                self.current_character,
                enemies=[enemy],
                companions=self.companions,
                location_category="wilderness",
                game_state=self,
            )
            combat_start = self.current_combat.start()
            messages.append(f"\n{colors.warning('[Ambush!]')} Your journey is interrupted!")
            messages.append(combat_start)
            return (True, "\n".join(messages))

    # Arrive at destination
    self.current_location = matched
    messages.append(f"\nAfter {travel_hours} hour{'s' if travel_hours > 1 else ''}, you arrive at {colors.location(matched)}.")

    # Look at new location
    messages.append(f"\n{self.look()}")

    # Autosave
    try:
        autosave(self)
    except IOError:
        pass

    return (True, "\n".join(messages))
```

### Step 4: Add command handler in main.py
**File**: `src/cli_rpg/main.py`

1. Update help text (~line 52):
   ```python
   "  travel <location>  - Fast travel to a discovered named location",
   ```

2. Add handler in game loop:
   ```python
   elif command == "travel":
       if not args:
           # List destinations with distances
           destinations = game_state.get_fast_travel_destinations()
           if not destinations:
               print("\nNo fast travel destinations available yet.")
               print("Explore named locations (towns, cities, dungeons) to unlock them.")
           else:
               current = game_state.get_current_location()
               print("\n" + colors.location("Fast Travel Destinations:"))
               for dest in destinations:
                   loc = game_state.world[dest]
                   dx = abs(loc.coordinates[0] - current.coordinates[0])
                   dy = abs(loc.coordinates[1] - current.coordinates[1])
                   distance = dx + dy
                   hours = max(1, min(8, distance // 4))
                   print(f"  {dest} ({hours}h travel)")
               print("\nUsage: travel <location name>")
       else:
           dest = " ".join(args)
           success, message = game_state.fast_travel(dest)
           print(message)
   ```

### Step 5: Add tab completion
**File**: `src/cli_rpg/completer.py`

1. Add case in `_complete_argument()` (~line 150):
   ```python
   elif command == "travel":
       return self._complete_travel(text_lower)
   ```

2. Add method:
   ```python
   def _complete_travel(self, text: str) -> List[str]:
       """Complete location name for 'travel' command."""
       if self._game_state is None:
           return []
       destinations = self._game_state.get_fast_travel_destinations()
       return [name for name in destinations if name.lower().startswith(text)]
   ```

### Step 6: Write tests
**File**: `tests/test_fast_travel.py` (NEW)

```python
"""Tests for fast travel functionality."""
import pytest
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.combat import CombatEncounter

class TestGetFastTravelDestinations:
    """Tests for get_fast_travel_destinations() method."""

    def test_returns_only_named_locations(self):
        """Unnamed terrain filler locations should not appear."""

    def test_returns_only_overworld_locations(self):
        """Sub-locations (with parent_location) should not appear."""

    def test_excludes_current_location(self):
        """Current location should not be in destinations."""

    def test_excludes_locations_without_coordinates(self):
        """Locations missing coordinates are filtered out."""

    def test_returns_sorted_list(self):
        """Destinations should be alphabetically sorted."""

    def test_empty_when_no_valid_destinations(self):
        """Returns empty list when no named locations exist."""

class TestFastTravelBlocks:
    """Tests for conditions that block fast travel."""

    def test_blocked_during_combat(self):
        """Cannot travel while in active combat."""

    def test_blocked_during_conversation(self):
        """Cannot travel while talking to NPC."""

    def test_blocked_inside_subgrid(self):
        """Cannot travel from inside a sub-location."""

    def test_error_for_unknown_destination(self):
        """Clear error for destination not in list."""

class TestFastTravelMechanics:
    """Tests for travel time and effects."""

    def test_travel_time_proportional_to_distance(self):
        """Travel time = distance // 4, clamped 1-8 hours."""

    def test_tiredness_increases_per_hour(self):
        """Tiredness increases by 3 per hour traveled."""

    def test_time_advances_correctly(self):
        """Game time advances by travel hours."""

    def test_player_arrives_at_destination(self):
        """current_location updated on success."""

    def test_partial_name_matching(self):
        """Case-insensitive partial matching works."""

class TestFastTravelEncounters:
    """Tests for random encounters during travel."""

    def test_encounter_can_interrupt_travel(self, mocker):
        """Combat encounter stops travel partway."""

    def test_no_encounter_when_safe(self, mocker):
        """15% base chance with random check."""

class TestFastTravelCompletion:
    """Tests for tab completion."""

    def test_complete_travel_returns_destinations(self):
        """Completion returns valid destinations."""

    def test_partial_match_filters_destinations(self):
        """Only matching prefixes returned."""
```

---

## Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/game_state.py` | Add `travel` to KNOWN_COMMANDS, add `get_fast_travel_destinations()` and `fast_travel()` methods |
| `src/cli_rpg/main.py` | Add `travel` command handler, update help text |
| `src/cli_rpg/completer.py` | Add `_complete_travel()` method and travel case |
| `tests/test_fast_travel.py` | NEW - ~15 tests for fast travel functionality |
