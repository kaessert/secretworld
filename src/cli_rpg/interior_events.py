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

# Monster migration constants
# Spawn chance: 3% per move (lower than cave-in's 5% since less disruptive)
MONSTER_MIGRATION_SPAWN_CHANCE = 0.03

# Duration range in hours (shorter than cave-ins since less impactful)
MONSTER_MIGRATION_DURATION_RANGE = (2, 6)

# Location categories where migrations can occur (same as cave-ins)
MONSTER_MIGRATION_CATEGORIES = CAVE_IN_CATEGORIES

# Encounter modifier range (0.5x to 2.0x)
MONSTER_MIGRATION_MODIFIER_RANGE = (0.5, 2.0)

# Rival adventurer constants
# Spawn chance: 15% on SubGrid entry (higher than per-move events since checked once)
RIVAL_SPAWN_CHANCE = 0.15

# Party size: 1-3 rival adventurers
RIVAL_PARTY_SIZE_RANGE = (1, 3)

# Location categories where rivals can spawn (same as cave-ins)
RIVAL_CATEGORIES = CAVE_IN_CATEGORIES

# Rival party names for flavor
RIVAL_PARTY_NAMES = [
    "The Iron Seekers",
    "Shadow Company",
    "Fortune's Edge",
    "The Blade Collective",
    "Crimson Oath",
    "The Wanderers",
]

# Rival adventurer combat templates
RIVAL_ADVENTURER_TEMPLATES = [
    {"name": "Rival Warrior", "hp": 30, "attack": 8, "defense": 4},
    {"name": "Rival Mage", "hp": 20, "attack": 10, "defense": 2},
    {"name": "Rival Rogue", "hp": 25, "attack": 9, "defense": 3},
]

# Warning messages at different progress percentages
RIVAL_WARNING_MESSAGES = {
    25: "You hear distant voices echoing through the corridors...",
    50: "The sound of hurried footsteps reaches your ears from ahead!",
    75: "You hear combat sounds in the distance - someone else is fighting!",
}

# Ritual event constants
# Spawn chance: 15% on SubGrid entry (same as rivals)
RITUAL_SPAWN_CHANCE = 0.15

# Countdown range in turns
RITUAL_COUNTDOWN_RANGE = (8, 12)

# Location categories where rituals can occur (same as cave-ins)
RITUAL_CATEGORIES = CAVE_IN_CATEGORIES

# Warning messages at different progress percentages (inverted - based on time remaining)
# Progress percentage = (initial - countdown) / initial * 100
RITUAL_WARNING_MESSAGES = {
    25: "An ominous chanting echoes through the corridors...",
    50: "Dark energy pulses through the walls! The ritual grows stronger!",
    75: "Reality flickers - the ritual nears completion!",
}

# Message when ritual completes
RITUAL_COMPLETE_MESSAGE = "The ritual is complete! An empowered being has been summoned!"

# Message when ritual is interrupted
RITUAL_INTERRUPTED_MESSAGE = "You interrupt the ritual! The summoning is incomplete!"


@dataclass
class InteriorEvent:
    """A dynamic event occurring within a SubGrid location.

    Attributes:
        event_id: Unique identifier for this event
        event_type: Type of event (e.g., "cave_in", "monster_migration", "rival_adventurers")
        location_coords: 3-tuple (x, y, z) where the event occurred
        blocked_direction: Direction that is blocked by this event (for cave_in)
        start_hour: Game hour when the event started
        duration_hours: How long the event lasts (in game hours)
        is_active: Whether the event is still in effect
        affected_rooms: Dict of {(x,y,z): modifier} for monster_migration events
        rival_party: List of rival NPC dicts for rival_adventurers events
        target_room: Name of boss/treasure room rivals are racing to
        rival_progress: Current progress toward target (in turns)
        arrival_turns: Turns until rivals arrive at target
        rival_at_target: True if rivals have arrived at target room
    """

    event_id: str
    event_type: str
    location_coords: tuple
    blocked_direction: str
    start_hour: int
    duration_hours: int
    is_active: bool = True
    affected_rooms: Optional[dict] = None
    # Rival adventurer fields
    rival_party: Optional[List[dict]] = None
    target_room: Optional[str] = None
    rival_progress: int = 0
    arrival_turns: int = 0
    rival_at_target: bool = False
    # Ritual event fields
    ritual_room: Optional[str] = None
    ritual_countdown: int = 0
    ritual_initial_countdown: int = 0  # Track initial for percentage calculations
    ritual_completed: bool = False

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

    def is_rival_arrived(self) -> bool:
        """Check if rival party has arrived at target.

        For rival_adventurers events, returns True when progress >= arrival_turns.

        Returns:
            True if rivals have arrived at target, False otherwise
        """
        if self.event_type != "rival_adventurers":
            return False
        return self.rival_progress >= self.arrival_turns

    def to_dict(self) -> dict:
        """Serialize the event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "location_coords": list(self.location_coords),
            "blocked_direction": self.blocked_direction,
            "start_hour": self.start_hour,
            "duration_hours": self.duration_hours,
            "is_active": self.is_active,
        }
        # Serialize affected_rooms: dict with tuple keys -> list of [coords, modifier]
        if self.affected_rooms is not None:
            result["affected_rooms"] = [
                [list(coords), modifier]
                for coords, modifier in self.affected_rooms.items()
            ]
        # Serialize rival adventurer fields
        if self.rival_party is not None:
            result["rival_party"] = self.rival_party
        if self.target_room is not None:
            result["target_room"] = self.target_room
        if self.rival_progress != 0:
            result["rival_progress"] = self.rival_progress
        if self.arrival_turns != 0:
            result["arrival_turns"] = self.arrival_turns
        if self.rival_at_target:
            result["rival_at_target"] = self.rival_at_target
        # Serialize ritual event fields
        if self.ritual_room is not None:
            result["ritual_room"] = self.ritual_room
        if self.ritual_countdown != 0:
            result["ritual_countdown"] = self.ritual_countdown
        if self.ritual_initial_countdown != 0:
            result["ritual_initial_countdown"] = self.ritual_initial_countdown
        if self.ritual_completed:
            result["ritual_completed"] = self.ritual_completed
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "InteriorEvent":
        """Create an InteriorEvent from a dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            InteriorEvent instance
        """
        # Deserialize affected_rooms: list of [coords, modifier] -> dict with tuple keys
        affected_rooms = None
        if "affected_rooms" in data and data["affected_rooms"] is not None:
            affected_rooms = {
                tuple(coords): modifier
                for coords, modifier in data["affected_rooms"]
            }

        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            location_coords=tuple(data["location_coords"]),
            blocked_direction=data["blocked_direction"],
            start_hour=data["start_hour"],
            duration_hours=data["duration_hours"],
            is_active=data.get("is_active", True),
            affected_rooms=affected_rooms,
            # Rival adventurer fields (with backward-compatible defaults)
            rival_party=data.get("rival_party"),
            target_room=data.get("target_room"),
            rival_progress=data.get("rival_progress", 0),
            arrival_turns=data.get("arrival_turns", 0),
            rival_at_target=data.get("rival_at_target", False),
            # Ritual event fields (with backward-compatible defaults)
            ritual_room=data.get("ritual_room"),
            ritual_countdown=data.get("ritual_countdown", 0),
            ritual_initial_countdown=data.get("ritual_initial_countdown", 0),
            ritual_completed=data.get("ritual_completed", False),
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
    removes blockages when they expire, or clears migrations.

    Args:
        game_state: Current game state
        sub_grid: The SubGrid to progress events for
        hours: Number of hours that passed (default 1)

    Returns:
        List of messages about cleared events
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

        elif event.event_type == "monster_migration" and event.is_expired(current_hour):
            # Clear the migration
            event.is_active = False
            messages.append(
                colors.heal(
                    "The monster migration has subsided. "
                    "Creature activity returns to normal."
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


def check_for_monster_migration(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Check if a monster migration should spawn after movement in a SubGrid.

    Spawns a migration with MONSTER_MIGRATION_SPAWN_CHANCE probability, modifying
    encounter rates for rooms in the SubGrid. Only spawns in appropriate location
    categories (dungeon, cave, ruins, temple).

    Args:
        game_state: Current game state
        sub_grid: The SubGrid the player is moving in

    Returns:
        Message describing the migration if one occurred, None otherwise
    """
    # Get current location
    current = game_state.get_current_location()
    if current is None or current.coordinates is None:
        return None

    # Check if parent location category allows migrations
    parent_location = game_state.world.get(sub_grid.parent_name)
    if parent_location is None:
        return None

    parent_category = (parent_location.category or "").lower()
    if parent_category not in MONSTER_MIGRATION_CATEGORIES:
        return None

    # Roll for migration spawn
    if random.random() > MONSTER_MIGRATION_SPAWN_CHANCE:
        return None

    # Get all room coordinates in the SubGrid
    room_coords = []
    for loc in sub_grid._grid.values():
        if loc.coordinates:
            # Normalize to 3-tuple
            coords = loc.coordinates
            if len(coords) == 2:
                coords = (coords[0], coords[1], 0)
            room_coords.append(coords)

    if len(room_coords) < 2:
        return None  # Need at least 2 rooms for migration to matter

    # Select 1-3 rooms to be affected (or all if fewer)
    num_affected = min(random.randint(1, 3), len(room_coords))
    affected = random.sample(room_coords, num_affected)

    # Assign modifiers to affected rooms
    min_mod, max_mod = MONSTER_MIGRATION_MODIFIER_RANGE
    affected_rooms = {}
    for coords in affected:
        modifier = random.uniform(min_mod, max_mod)
        affected_rooms[coords] = round(modifier, 2)

    # Create the migration event
    coords = current.coordinates
    x, y = coords[:2]
    z = coords[2] if len(coords) > 2 else 0

    event_id = f"migration_{x}_{y}_{z}_{random.randint(1000, 9999)}"
    min_dur, max_dur = MONSTER_MIGRATION_DURATION_RANGE
    duration = random.randint(min_dur, max_dur)

    event = InteriorEvent(
        event_id=event_id,
        event_type="monster_migration",
        location_coords=(x, y, z),
        blocked_direction="",  # Not applicable for migrations
        start_hour=game_state.game_time.total_hours,
        duration_hours=duration,
        affected_rooms=affected_rooms,
    )

    # Add to sub_grid's interior events list
    sub_grid.interior_events.append(event)

    # Return message
    return colors.warning(
        "You hear creatures stirring in the distance... "
        "A monster migration is underway!"
    )


def get_encounter_modifier_at_location(
    sub_grid: "SubGrid",
    coords: tuple,
) -> float:
    """Get cumulative encounter rate modifier from active migrations.

    Multiple migrations stack multiplicatively.

    Args:
        sub_grid: The SubGrid to check
        coords: (x, y, z) coordinates of the location

    Returns:
        Cumulative encounter rate modifier (1.0 = no change)
    """
    # Normalize coords to 3-tuple
    if len(coords) == 2:
        coords = (coords[0], coords[1], 0)

    modifier = 1.0

    for event in sub_grid.interior_events:
        if (
            event.is_active
            and event.event_type == "monster_migration"
            and event.affected_rooms is not None
        ):
            if coords in event.affected_rooms:
                modifier *= event.affected_rooms[coords]

    return modifier


def get_active_migrations(sub_grid: "SubGrid") -> List[InteriorEvent]:
    """Get all active monster migration events in a SubGrid.

    Args:
        sub_grid: The SubGrid to check

    Returns:
        List of active monster migration events
    """
    return [
        event
        for event in sub_grid.interior_events
        if event.is_active and event.event_type == "monster_migration"
    ]


# -----------------------------------------------------------------------------
# Rival Adventurer Functions
# -----------------------------------------------------------------------------


def _find_target_rooms(sub_grid: "SubGrid") -> tuple[Optional[str], Optional[str]]:
    """Find boss room and treasure room in SubGrid.

    Args:
        sub_grid: The SubGrid to search

    Returns:
        Tuple of (boss_room_name, treasure_room_name), either may be None
    """
    boss_room = None
    treasure_room = None

    for location in sub_grid._by_name.values():
        # Check for boss room (undefeated boss)
        if location.boss_enemy and not location.boss_defeated:
            boss_room = location.name
        # Check for treasure room (unopened treasure)
        if location.treasures:
            for treasure in location.treasures:
                if not treasure.get("opened", False):
                    treasure_room = location.name
                    break

    return boss_room, treasure_room


def _calculate_distance_to_target(sub_grid: "SubGrid", target_name: str) -> int:
    """Calculate Manhattan distance from entry to target room.

    Args:
        sub_grid: The SubGrid containing the rooms
        target_name: Name of the target room

    Returns:
        Manhattan distance (minimum 3 to ensure some race time)
    """
    entry_coords = None
    target_coords = None

    for location in sub_grid._by_name.values():
        if location.is_exit_point:
            entry_coords = location.coordinates
        if location.name == target_name:
            target_coords = location.coordinates

    if entry_coords is None or target_coords is None:
        return 5  # Default if can't calculate

    # Calculate Manhattan distance in 3D
    e_x, e_y = entry_coords[:2]
    e_z = entry_coords[2] if len(entry_coords) > 2 else 0
    t_x, t_y = target_coords[:2]
    t_z = target_coords[2] if len(target_coords) > 2 else 0

    distance = abs(t_x - e_x) + abs(t_y - e_y) + abs(t_z - e_z)
    return max(3, distance)  # Minimum 3 turns


def _create_rival_party(party_size: int) -> List[dict]:
    """Create a party of rival adventurers.

    Args:
        party_size: Number of rivals (1-3)

    Returns:
        List of rival adventurer dicts with combat stats
    """
    party = []
    templates = RIVAL_ADVENTURER_TEMPLATES.copy()
    random.shuffle(templates)

    for i in range(party_size):
        template = templates[i % len(templates)]
        party.append(template.copy())

    return party


def check_for_rival_spawn(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Check if rival adventurers should spawn on SubGrid entry.

    Called once when player first enters a SubGrid. Spawns rivals
    with RIVAL_SPAWN_CHANCE probability if a valid target exists.
    Selects target (boss room preferred, then treasure room).
    Calculates arrival_turns based on distance from entry.

    Args:
        game_state: Current game state
        sub_grid: The SubGrid the player is entering

    Returns:
        Message describing the rival spawn if one occurred, None otherwise
    """
    # Check if parent location category allows rivals
    parent_location = game_state.world.get(sub_grid.parent_name)
    if parent_location is None:
        return None

    parent_category = (parent_location.category or "").lower()
    if parent_category not in RIVAL_CATEGORIES:
        return None

    # Check if rival event already exists (don't spawn twice)
    if get_active_rival_event(sub_grid) is not None:
        return None

    # Roll for rival spawn
    if random.random() > RIVAL_SPAWN_CHANCE:
        return None

    # Find target rooms
    boss_room, treasure_room = _find_target_rooms(sub_grid)

    # Prefer boss room over treasure room
    target_room = boss_room or treasure_room
    if target_room is None:
        return None  # No valid targets

    # Calculate arrival time based on distance
    arrival_turns = _calculate_distance_to_target(sub_grid, target_room)

    # Create rival party (1-3 members)
    min_size, max_size = RIVAL_PARTY_SIZE_RANGE
    party_size = random.randint(min_size, max_size)
    rival_party = _create_rival_party(party_size)

    # Choose party name
    party_name = random.choice(RIVAL_PARTY_NAMES)

    # Create the rival event
    event_id = f"rival_{random.randint(1000, 9999)}"
    event = InteriorEvent(
        event_id=event_id,
        event_type="rival_adventurers",
        location_coords=(0, 0, 0),  # Entry point
        blocked_direction="",
        start_hour=game_state.game_time.total_hours,
        duration_hours=0,  # Not time-based
        rival_party=rival_party,
        target_room=target_room,
        rival_progress=0,
        arrival_turns=arrival_turns,
    )

    sub_grid.interior_events.append(event)

    # Return spawn message
    return colors.warning(
        f"You sense you're not alone... {party_name} has entered ahead of you, "
        f"racing toward the depths!"
    )


def progress_rival_party(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Advance rival party progress by 1 turn.

    Called after each player move in SubGrid. Returns warning message
    based on progress percentage. If rivals arrive, updates target room
    (defeats boss/opens treasure) and marks rivals at location.

    Args:
        game_state: Current game state
        sub_grid: The SubGrid containing the rival event

    Returns:
        Warning or arrival message if applicable, None otherwise
    """
    rival_event = get_active_rival_event(sub_grid)
    if rival_event is None:
        return None

    # Already arrived, no more progress needed
    if rival_event.rival_at_target:
        return None

    # Increment progress
    rival_event.rival_progress += 1

    # Check for arrival
    if rival_event.is_rival_arrived():
        return _handle_rival_arrival(sub_grid, rival_event)

    # Check for warning message based on progress percentage
    if rival_event.arrival_turns > 0:
        progress_pct = (rival_event.rival_progress / rival_event.arrival_turns) * 100

        for threshold in sorted(RIVAL_WARNING_MESSAGES.keys()):
            # Trigger message when just crossing threshold
            prev_progress = rival_event.rival_progress - 1
            prev_pct = (prev_progress / rival_event.arrival_turns) * 100

            if prev_pct < threshold <= progress_pct:
                return colors.warning(RIVAL_WARNING_MESSAGES[threshold])

    return None


def _handle_rival_arrival(
    sub_grid: "SubGrid",
    rival_event: InteriorEvent,
) -> str:
    """Handle rivals arriving at their target room.

    Updates the target location (defeats boss or opens treasure)
    and positions rivals at that location.

    Args:
        sub_grid: The SubGrid containing the target
        rival_event: The rival event that just arrived

    Returns:
        Message describing what happened
    """
    rival_event.rival_at_target = True

    target = sub_grid.get_by_name(rival_event.target_room)
    if target is None:
        return colors.error("The rival party has reached their destination!")

    # Update rival event location to target room
    if target.coordinates:
        rival_event.location_coords = target.coordinates

    # Check if it's a boss room
    if target.boss_enemy and not target.boss_defeated:
        target.boss_defeated = True
        return colors.damage(
            f"You hear a triumphant shout echo through the corridors - "
            f"rival adventurers have defeated the boss in {target.name}!"
        )

    # Check if it's a treasure room
    if target.treasures:
        for treasure in target.treasures:
            treasure["opened"] = True
        return colors.damage(
            f"You hear excited voices and the clinking of coins - "
            f"rival adventurers have claimed the treasure in {target.name}!"
        )

    return colors.damage("The rival party has reached their destination!")


def get_active_rival_event(sub_grid: "SubGrid") -> Optional[InteriorEvent]:
    """Get the active rival adventurer event, if any.

    Args:
        sub_grid: The SubGrid to check

    Returns:
        The active rival event if one exists, None otherwise
    """
    for event in sub_grid.interior_events:
        if event.is_active and event.event_type == "rival_adventurers":
            return event
    return None


def get_rival_encounter_at_location(
    sub_grid: "SubGrid",
    location: "Location",
) -> Optional[InteriorEvent]:
    """Check if rival adventurers are at the specified location.

    Used to trigger combat when player enters a room with rivals.

    Args:
        sub_grid: The SubGrid to check
        location: The location to check for rivals

    Returns:
        The rival event if rivals are at this location, None otherwise
    """
    from cli_rpg.models.location import Location

    rival_event = get_active_rival_event(sub_grid)
    if rival_event is None:
        return None

    # Check if rivals have arrived at target
    if not rival_event.rival_at_target:
        return None

    # Check if this is the target room
    if rival_event.target_room == location.name:
        return rival_event

    # Also check by coordinates
    if location.coordinates and rival_event.location_coords:
        loc_coords = location.coordinates
        if len(loc_coords) == 2:
            loc_coords = (loc_coords[0], loc_coords[1], 0)
        event_coords = rival_event.location_coords
        if len(event_coords) == 2:
            event_coords = (event_coords[0], event_coords[1], 0)
        if loc_coords == event_coords:
            return rival_event

    return None


# -----------------------------------------------------------------------------
# Ritual Event Functions
# -----------------------------------------------------------------------------


def _find_ritual_room(sub_grid: "SubGrid") -> Optional["Location"]:
    """Find a suitable room for the ritual (not entry, not boss, not treasure).

    Args:
        sub_grid: The SubGrid to search

    Returns:
        Location for ritual, or None if no suitable room found
    """
    from cli_rpg.models.location import Location

    candidates = []
    for location in sub_grid._by_name.values():
        # Skip entry points
        if location.is_exit_point:
            continue
        # Skip boss rooms
        if location.boss_enemy:
            continue
        # Skip treasure rooms
        if location.treasures:
            continue
        candidates.append(location)

    if not candidates:
        # Fallback: use any non-entry room
        for location in sub_grid._by_name.values():
            if not location.is_exit_point:
                candidates.append(location)

    if not candidates:
        return None

    return random.choice(candidates)


def check_for_ritual_spawn(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Check if a ritual should spawn on SubGrid entry.

    Spawns a ritual event at a room distant from entry.
    Called once when player first enters a SubGrid.

    Args:
        game_state: Current game state
        sub_grid: The SubGrid the player is entering

    Returns:
        Message describing the ritual spawn if one occurred, None otherwise
    """
    # Check if parent location category allows rituals
    parent_location = game_state.world.get(sub_grid.parent_name)
    if parent_location is None:
        return None

    parent_category = (parent_location.category or "").lower()
    if parent_category not in RITUAL_CATEGORIES:
        return None

    # Check if ritual event already exists (don't spawn twice)
    if get_active_ritual_event(sub_grid) is not None:
        return None

    # Roll for ritual spawn
    if random.random() > RITUAL_SPAWN_CHANCE:
        return None

    # Find a suitable ritual room
    ritual_room = _find_ritual_room(sub_grid)
    if ritual_room is None:
        return None

    # Calculate countdown
    min_countdown, max_countdown = RITUAL_COUNTDOWN_RANGE
    countdown = random.randint(min_countdown, max_countdown)

    # Get ritual room coordinates
    ritual_coords = ritual_room.coordinates
    if ritual_coords is None:
        ritual_coords = (0, 0, 0)
    elif len(ritual_coords) == 2:
        ritual_coords = (ritual_coords[0], ritual_coords[1], 0)

    # Create the ritual event
    event_id = f"ritual_{random.randint(1000, 9999)}"
    event = InteriorEvent(
        event_id=event_id,
        event_type="ritual",
        location_coords=ritual_coords,
        blocked_direction="",
        start_hour=game_state.game_time.total_hours,
        duration_hours=0,  # Not time-based
        ritual_room=ritual_room.name,
        ritual_countdown=countdown,
        ritual_initial_countdown=countdown,
        ritual_completed=False,
    )

    sub_grid.interior_events.append(event)

    # Return spawn message
    return colors.warning(
        "You sense dark energy gathering in the depths... "
        "A ritual is being performed somewhere within!"
    )


def progress_ritual(
    game_state: "GameState",
    sub_grid: "SubGrid",
) -> Optional[str]:
    """Advance ritual countdown by 1 turn.

    Called after each player move in SubGrid. Returns warning message
    based on progress percentage. If countdown reaches 0, marks ritual
    as completed.

    Args:
        game_state: Current game state
        sub_grid: The SubGrid containing the ritual event

    Returns:
        Warning or completion message if applicable, None otherwise
    """
    ritual_event = get_active_ritual_event(sub_grid)
    if ritual_event is None:
        return None

    # Already completed, no more progress
    if ritual_event.ritual_completed:
        return None

    # Decrement countdown
    ritual_event.ritual_countdown -= 1

    # Check for completion
    if ritual_event.ritual_countdown <= 0:
        ritual_event.ritual_countdown = 0
        ritual_event.ritual_completed = True
        return colors.damage(RITUAL_COMPLETE_MESSAGE)

    # Check for warning message based on progress percentage
    if ritual_event.ritual_initial_countdown > 0:
        # Progress = how much countdown has decreased (inverted from countdown)
        progress_pct = (
            (ritual_event.ritual_initial_countdown - ritual_event.ritual_countdown)
            / ritual_event.ritual_initial_countdown
        ) * 100

        # Previous progress (before this decrement)
        prev_progress_pct = (
            (ritual_event.ritual_initial_countdown - (ritual_event.ritual_countdown + 1))
            / ritual_event.ritual_initial_countdown
        ) * 100

        for threshold in sorted(RITUAL_WARNING_MESSAGES.keys()):
            # Trigger message when just crossing threshold
            if prev_progress_pct < threshold <= progress_pct:
                return colors.warning(RITUAL_WARNING_MESSAGES[threshold])

    return None


def get_active_ritual_event(sub_grid: "SubGrid") -> Optional[InteriorEvent]:
    """Get the active ritual event, if any.

    Args:
        sub_grid: The SubGrid to check

    Returns:
        The active ritual event if one exists, None otherwise
    """
    for event in sub_grid.interior_events:
        if event.is_active and event.event_type == "ritual":
            return event
    return None


def get_ritual_encounter_at_location(
    sub_grid: "SubGrid",
    location: "Location",
) -> Optional[tuple[InteriorEvent, bool]]:
    """Check if player entered the ritual room.

    Used to trigger combat when player enters the ritual room.
    Returns the event and whether the boss should be empowered
    (True if ritual completed, False if interrupted).

    Args:
        sub_grid: The SubGrid to check
        location: The location to check for ritual

    Returns:
        Tuple of (event, is_empowered) if ritual room, None otherwise
    """
    ritual_event = get_active_ritual_event(sub_grid)
    if ritual_event is None:
        return None

    # Check if this is the ritual room by name
    if ritual_event.ritual_room == location.name:
        is_empowered = ritual_event.ritual_completed
        return (ritual_event, is_empowered)

    # Also check by coordinates
    if location.coordinates and ritual_event.location_coords:
        loc_coords = location.coordinates
        if len(loc_coords) == 2:
            loc_coords = (loc_coords[0], loc_coords[1], 0)
        event_coords = ritual_event.location_coords
        if len(event_coords) == 2:
            event_coords = (event_coords[0], event_coords[1], 0)
        if tuple(loc_coords) == tuple(event_coords):
            is_empowered = ritual_event.ritual_completed
            return (ritual_event, is_empowered)

    return None
