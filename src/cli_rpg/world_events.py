"""World events system for living world mechanics.

Provides timed world events (plagues, caravans, invasions) that progress
with in-game time, giving players urgency and making the world feel alive.
"""

import random
from typing import Optional, TYPE_CHECKING

from cli_rpg.models.world_event import WorldEvent
from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


# Spawn chance: 5% per move
EVENT_SPAWN_CHANCE = 0.05

# Event templates with default configurations
EVENT_TEMPLATES = {
    "caravan": {
        "name_templates": [
            "Merchant Caravan Arriving",
            "Traveling Traders",
            "Exotic Goods Caravan",
        ],
        "description_templates": [
            "A wealthy merchant caravan has arrived at {location}. They carry rare goods from distant lands.",
            "Traveling traders have set up camp at {location}. Their wares are said to be exceptional.",
            "A caravan bearing exotic goods has stopped at {location}. They won't stay long.",
        ],
        "duration_range": (8, 16),  # 8-16 hours
        "hint": "Visit to trade for rare goods!",
    },
    "plague": {
        "name_templates": [
            "The Crimson Plague",
            "Spreading Sickness",
            "Dark Affliction",
        ],
        "description_templates": [
            "A deadly plague spreads through {location}. Without a cure, many will perish.",
            "Sickness has taken hold of {location}. The afflicted cry out for help.",
            "A dark affliction plagues {location}. Time is running out.",
        ],
        "duration_range": (16, 32),  # 16-32 hours
        "hint": "Find a cure or healer to save the afflicted!",
    },
    "invasion": {
        "name_templates": [
            "Monster Incursion",
            "Creature Uprising",
            "Dark Forces Gathering",
        ],
        "description_templates": [
            "Monsters have overrun {location}! Clear them out before they spread further.",
            "Dangerous creatures are gathering at {location}. The threat grows by the hour.",
            "Dark forces are amassing at {location}. Heroes are needed!",
        ],
        "duration_range": (6, 12),  # 6-12 hours
        "hint": "Clear out the monsters before they overwhelm the area!",
    },
}


def spawn_random_event(game_state: "GameState") -> WorldEvent:
    """Create a new random world event.

    Args:
        game_state: Current game state

    Returns:
        New WorldEvent instance
    """
    # Choose random event type
    event_type = random.choice(list(EVENT_TEMPLATES.keys()))
    template = EVENT_TEMPLATES[event_type]

    # Choose affected location (current or nearby)
    affected_location = game_state.current_location

    # Generate event ID
    event_id = f"{event_type}_{affected_location.replace(' ', '_').lower()}_{random.randint(1000, 9999)}"

    # Choose random name and description
    name = random.choice(template["name_templates"])
    description = random.choice(template["description_templates"]).format(
        location=affected_location
    )

    # Random duration within range
    min_dur, max_dur = template["duration_range"]
    duration = random.randint(min_dur, max_dur)

    return WorldEvent(
        event_id=event_id,
        name=name,
        description=description,
        event_type=event_type,
        affected_locations=[affected_location],
        start_hour=game_state.game_time.hour,
        duration_hours=duration,
    )


def check_for_new_event(game_state: "GameState") -> Optional[str]:
    """Check if a new world event should spawn.

    Called on movement, with EVENT_SPAWN_CHANCE probability of spawning.

    Args:
        game_state: Current game state

    Returns:
        Event notification message if event spawned, None otherwise
    """
    # Don't spawn if too many active events
    active_events = [e for e in game_state.world_events if e.is_active]
    if len(active_events) >= 3:
        return None

    # Roll for event spawn
    if random.random() > EVENT_SPAWN_CHANCE:
        return None

    # Create and add event
    event = spawn_random_event(game_state)
    game_state.world_events.append(event)

    # Return formatted notification
    return format_event_notification(event, game_state.game_time.hour)


def progress_events(game_state: "GameState") -> list[str]:
    """Progress all active events and apply consequences for expired ones.

    Called when time advances. Checks each active event and applies
    consequences if expired.

    Args:
        game_state: Current game state

    Returns:
        List of progress/consequence messages
    """
    messages = []
    current_hour = game_state.game_time.hour

    for event in game_state.world_events:
        if not event.is_active:
            continue

        if event.is_resolved:
            continue

        # Check if event expired
        if event.is_expired(current_hour):
            # Apply consequence
            consequence_msg = apply_consequence(event, game_state)
            event.consequence_applied = True
            event.is_active = False
            messages.append(consequence_msg)

    return messages


def apply_consequence(event: WorldEvent, game_state: "GameState") -> str:
    """Apply the consequence of an expired event.

    Args:
        event: The expired event
        game_state: Current game state

    Returns:
        Message describing the consequence
    """
    if event.event_type == "caravan":
        return colors.warning(
            f"The {event.name} has departed from {event.affected_locations[0]}. "
            "You missed the chance to trade for rare goods."
        )
    elif event.event_type == "plague":
        return colors.damage(
            f"The {event.name} has claimed many lives in {event.affected_locations[0]}. "
            "The survivors are in despair."
        )
    elif event.event_type == "invasion":
        return colors.damage(
            f"The {event.name} has overrun {event.affected_locations[0]}! "
            "The area is now extremely dangerous."
        )
    else:
        return f"The {event.name} has ended."


def resolve_event(game_state: "GameState", event_id: str) -> str:
    """Mark an event as resolved by the player.

    Args:
        game_state: Current game state
        event_id: ID of the event to resolve

    Returns:
        Resolution message
    """
    for event in game_state.world_events:
        if event.event_id == event_id:
            event.is_resolved = True
            event.is_active = False
            return colors.heal(
                f"You have resolved the {event.name}! "
                f"The people of {event.affected_locations[0]} are grateful."
            )

    return "Event not found."


def format_event_notification(event: WorldEvent, current_hour: int) -> str:
    """Format an event announcement in a decorative box.

    Args:
        event: The event to format
        current_hour: Current game hour for time remaining calculation

    Returns:
        Formatted event notification string
    """
    time_remaining = event.get_time_remaining(current_hour)
    template = EVENT_TEMPLATES.get(event.event_type, {})
    hint = template.get("hint", "")

    # Build the box
    width = 56
    border = "=" * width

    lines = [
        "",
        colors.gold(border),
        colors.gold(f"  WORLD EVENT: {event.name}"),
        colors.gold(border),
        "",
        f"  {event.description}",
        "",
        f"  Time remaining: {time_remaining} hours",
        "",
    ]

    if hint:
        lines.append(colors.location(f"  [Hint]: {hint}"))  # cyan color

    lines.extend([
        "",
        colors.gold(border),
    ])

    return "\n".join(lines)


def get_location_event_warning(
    location_name: str, events: list[WorldEvent]
) -> Optional[str]:
    """Get warning message if location is affected by an event.

    Args:
        location_name: Name of the location being entered
        events: List of world events to check

    Returns:
        Warning message if location is affected, None otherwise
    """
    for event in events:
        if not event.is_active:
            continue

        if location_name in event.affected_locations:
            if event.event_type == "plague":
                return colors.warning(
                    f"Warning: {location_name} is afflicted by {event.name}!"
                )
            elif event.event_type == "invasion":
                return colors.damage(
                    f"Danger: {location_name} is under attack by monsters!"
                )
            elif event.event_type == "caravan":
                return colors.heal(
                    f"A merchant caravan is present in {location_name}!"
                )
            else:
                return f"Event active in {location_name}: {event.name}"

    return None


def get_active_events_display(game_state: "GameState") -> str:
    """Get formatted display of all active events.

    Args:
        game_state: Current game state

    Returns:
        Formatted string listing all active events
    """
    active_events = [e for e in game_state.world_events if e.is_active]

    if not active_events:
        return "\n=== World Events ===\nNo active world events."

    lines = ["\n=== World Events ==="]
    current_hour = game_state.game_time.hour

    for i, event in enumerate(active_events, 1):
        time_remaining = event.get_time_remaining(current_hour)
        location = event.affected_locations[0] if event.affected_locations else "Unknown"

        # Color based on event type
        if event.event_type == "plague":
            status = colors.damage(f"[PLAGUE]")
        elif event.event_type == "invasion":
            status = colors.warning(f"[INVASION]")
        elif event.event_type == "caravan":
            status = colors.heal(f"[CARAVAN]")
        else:
            status = f"[{event.event_type.upper()}]"

        lines.append(
            f"{i}. {event.name} {status} - {location} ({time_remaining} hours remaining)"
        )

    return "\n".join(lines)


def get_active_event_count(game_state: "GameState") -> int:
    """Get count of active events.

    Args:
        game_state: Current game state

    Returns:
        Number of active events
    """
    return sum(1 for e in game_state.world_events if e.is_active)
