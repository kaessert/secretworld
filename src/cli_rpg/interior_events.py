"""Interior events system for SubGrid locations.

Provides dynamic events that occur within interior locations (dungeons, caves,
temples, ruins). Cave-ins temporarily block passages with time-based expiry.
"""

import random
from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING

from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState
    from cli_rpg.world_grid import SubGrid


# Spawn chance: 5% per move (matches world event spawn rate)
CAVE_IN_SPAWN_CHANCE = 0.05

# Duration range in hours for cave-ins
CAVE_IN_DURATION_RANGE = (4, 12)

# Location categories where cave-ins can occur
CAVE_IN_CATEGORIES = {"dungeon", "cave", "ruins", "temple"}

# Directions that can be blocked (horizontal only, not up/down for now)
BLOCKABLE_DIRECTIONS = {"north", "south", "east", "west"}


@dataclass
class InteriorEvent:
    """A dynamic event occurring within a SubGrid location.

    Attributes:
        event_id: Unique identifier for this event
        event_type: Type of event (e.g., "cave_in")
        location_coords: 3-tuple (x, y, z) where the event occurred
        blocked_direction: Direction that is blocked by this event
        start_hour: Game hour when the event started
        duration_hours: How long the event lasts (in game hours)
        is_active: Whether the event is still in effect
    """

    event_id: str
    event_type: str
    location_coords: tuple
    blocked_direction: str
    start_hour: int
    duration_hours: int
    is_active: bool = True

    def is_expired(self, current_hour: int) -> bool:
        """Check if the event has expired based on current game time.

        Args:
            current_hour: Current game hour (total hours)

        Returns:
            True if event has expired, False otherwise
        """
        return current_hour >= self.start_hour + self.duration_hours

    def get_time_remaining(self, current_hour: int) -> int:
        """Get hours remaining until event expires.

        Args:
            current_hour: Current game hour (total hours)

        Returns:
            Hours remaining (minimum 0)
        """
        remaining = (self.start_hour + self.duration_hours) - current_hour
        return max(0, remaining)

    def to_dict(self) -> dict:
        """Serialize the event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "location_coords": list(self.location_coords),
            "blocked_direction": self.blocked_direction,
            "start_hour": self.start_hour,
            "duration_hours": self.duration_hours,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InteriorEvent":
        """Create an InteriorEvent from a dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            InteriorEvent instance
        """
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            location_coords=tuple(data["location_coords"]),
            blocked_direction=data["blocked_direction"],
            start_hour=data["start_hour"],
            duration_hours=data["duration_hours"],
            is_active=data.get("is_active", True),
        )


def check_for_cave_in(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Check if a cave-in should spawn after movement in a SubGrid.

    Spawns a cave-in with CAVE_IN_SPAWN_CHANCE probability, blocking
    a random available direction from the current location. Only spawns
    in appropriate location categories (dungeon, cave, ruins, temple).

    Args:
        game_state: Current game state
        sub_grid: The SubGrid the player is moving in

    Returns:
        Message describing the cave-in if one occurred, None otherwise
    """
    # Get current location
    current = game_state.get_current_location()
    if current is None or current.coordinates is None:
        return None

    # Check if parent location category allows cave-ins
    parent_location = game_state.world.get(sub_grid.parent_name)
    if parent_location is None:
        return None

    parent_category = (parent_location.category or "").lower()
    if parent_category not in CAVE_IN_CATEGORIES:
        return None

    # Roll for cave-in spawn
    if random.random() > CAVE_IN_SPAWN_CHANCE:
        return None

    # Get available directions that can be blocked
    # Check which directions have adjacent rooms in the sub_grid
    available_dirs = []
    coords = current.coordinates
    x, y = coords[:2]
    z = coords[2] if len(coords) > 2 else 0

    direction_offsets = {
        "north": (0, 1, 0),
        "south": (0, -1, 0),
        "east": (1, 0, 0),
        "west": (-1, 0, 0),
    }

    for direction, (dx, dy, dz) in direction_offsets.items():
        target = (x + dx, y + dy, z + dz)
        # Only consider directions with adjacent rooms that aren't already blocked
        if (
            sub_grid.is_within_bounds(*target)
            and sub_grid.get_by_coordinates(*target) is not None
            and direction not in current.blocked_directions
        ):
            available_dirs.append(direction)

    if not available_dirs:
        return None

    # Pick a random direction to block
    blocked_direction = random.choice(available_dirs)

    # Create the cave-in event
    event_id = f"cave_in_{x}_{y}_{z}_{random.randint(1000, 9999)}"
    min_dur, max_dur = CAVE_IN_DURATION_RANGE
    duration = random.randint(min_dur, max_dur)

    event = InteriorEvent(
        event_id=event_id,
        event_type="cave_in",
        location_coords=(x, y, z),
        blocked_direction=blocked_direction,
        start_hour=game_state.game_time.total_hours,
        duration_hours=duration,
    )

    # Add to sub_grid's interior events list
    sub_grid.interior_events.append(event)

    # Block the direction on the current location
    if blocked_direction not in current.blocked_directions:
        current.blocked_directions.append(blocked_direction)

    # Return message
    return colors.warning(
        f"The passage {blocked_direction} collapses in a cave-in! "
        f"The way is blocked for now."
    )


def progress_interior_events(
    game_state: "GameState",
    sub_grid: "SubGrid",
    hours: int = 1,
) -> List[str]:
    """Progress interior events and clear expired ones.

    Called when time advances. Checks each active interior event and
    removes blockages when they expire.

    Args:
        game_state: Current game state
        sub_grid: The SubGrid to progress events for
        hours: Number of hours that passed (default 1)

    Returns:
        List of messages about cleared cave-ins
    """
    messages = []
    current_hour = game_state.game_time.total_hours

    for event in sub_grid.interior_events:
        if not event.is_active:
            continue

        if event.event_type == "cave_in" and event.is_expired(current_hour):
            # Clear the cave-in
            cleared = clear_cave_in(sub_grid, event.location_coords, event.blocked_direction)
            if cleared:
                event.is_active = False
                messages.append(
                    colors.heal(
                        f"The cave-in at {event.blocked_direction} has cleared! "
                        f"The passage is open again."
                    )
                )

    return messages


def clear_cave_in(
    sub_grid: "SubGrid",
    coords: tuple,
    direction: str,
) -> bool:
    """Manually clear a cave-in, removing the blocked direction.

    Args:
        sub_grid: The SubGrid containing the blocked location
        coords: (x, y, z) coordinates of the blocked location
        direction: The direction that was blocked

    Returns:
        True if the cave-in was cleared, False if location not found
    """
    # Normalize coords to 3-tuple
    if len(coords) == 2:
        x, y = coords
        z = 0
    else:
        x, y, z = coords

    location = sub_grid.get_by_coordinates(x, y, z)
    if location is None:
        return False

    if direction in location.blocked_directions:
        location.blocked_directions.remove(direction)
        return True

    return False


def get_active_cave_ins(sub_grid: "SubGrid") -> List[InteriorEvent]:
    """Get all active cave-in events in a SubGrid.

    Args:
        sub_grid: The SubGrid to check

    Returns:
        List of active cave-in events
    """
    return [
        event
        for event in sub_grid.interior_events
        if event.is_active and event.event_type == "cave_in"
    ]


def get_cave_in_at_location(
    sub_grid: "SubGrid",
    coords: tuple,
    direction: str,
) -> Optional[InteriorEvent]:
    """Find an active cave-in at a specific location and direction.

    Args:
        sub_grid: The SubGrid to search
        coords: (x, y, z) coordinates of the location
        direction: Direction to check

    Returns:
        The cave-in event if found, None otherwise
    """
    # Normalize coords
    if len(coords) == 2:
        coords = (coords[0], coords[1], 0)

    for event in sub_grid.interior_events:
        if (
            event.is_active
            and event.event_type == "cave_in"
            and tuple(event.location_coords) == coords
            and event.blocked_direction == direction
        ):
            return event

    return None
