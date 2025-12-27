"""World events system for living world mechanics.

Provides timed world events (plagues, caravans, invasions) that progress
with in-game time, giving players urgency and making the world feel alive.
"""

import random
from typing import Optional, TYPE_CHECKING

from cli_rpg.models.world_event import WorldEvent
from cli_rpg import colors
from cli_rpg.frames import frame_announcement

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState
    from cli_rpg.models.shop import Shop


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
    consequences if expired. Also updates economy disruption based on
    active events.

    Args:
        game_state: Current game state

    Returns:
        List of progress/consequence messages
    """
    from cli_rpg.economy import update_economy_from_events

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

    # Update economy disruption based on active events
    update_economy_from_events(game_state.economy_state, game_state.world_events)

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

    # Build content
    content_lines = [
        event.description,
        "",
        f"Time remaining: {time_remaining} hours",
    ]

    if hint:
        content_lines.append("")
        content_lines.append(colors.location(f"[Hint]: {hint}"))  # cyan color

    content = "\n".join(content_lines)
    title = f"WORLD EVENT: {event.name}"

    return "\n" + frame_announcement(content, title=title)


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
        elif event.event_type == "festival":
            status = colors.gold(f"[FESTIVAL]")
        else:
            status = f"[{event.event_type.upper()}]"

        # Festivals affect all locations
        if event.event_type == "festival":
            location = "Everywhere"

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


def find_event_by_name(game_state: "GameState", event_name: str) -> Optional[WorldEvent]:
    """Find an active event by partial name match.

    Args:
        game_state: Current game state
        event_name: Partial or full event name (case-insensitive)

    Returns:
        Matching WorldEvent if found, None otherwise
    """
    event_name_lower = event_name.lower()
    for event in game_state.world_events:
        if event.is_active and event_name_lower in event.name.lower():
            return event
    return None


def get_resolution_requirements(event: WorldEvent) -> str:
    """Get human-readable requirements to resolve an event.

    Args:
        event: The event to get requirements for

    Returns:
        Description of what's needed to resolve the event
    """
    if event.event_type == "plague":
        return "Use a Cure or Antidote item at the affected location."
    elif event.event_type == "invasion":
        return "Defeat the invading creatures in combat."
    elif event.event_type == "caravan":
        return "Trade with the caravan by buying or selling items."
    else:
        return "Unknown event type."


def can_resolve_event(
    game_state: "GameState", event: WorldEvent
) -> tuple[bool, str]:
    """Check if the player can resolve an event.

    Args:
        game_state: Current game state
        event: The event to check

    Returns:
        Tuple of (can_resolve, reason_if_not)
    """
    # Check if player is at affected location
    if game_state.current_location not in event.affected_locations:
        return (
            False,
            f"You must be at {event.affected_locations[0]} to resolve this event."
        )

    # Check type-specific requirements
    if event.event_type == "plague":
        # Need a cure item in inventory
        inventory = game_state.current_character.inventory
        cure_items = [item for item in inventory.items if item.is_cure]
        if not cure_items:
            return (
                False,
                "You need a Cure or Antidote item to resolve the plague."
            )
        return (True, "")

    elif event.event_type == "invasion":
        # No special requirements - just need to fight
        return (True, "")

    elif event.event_type == "caravan":
        # Caravans are auto-resolved by trading, but player can still try
        return (True, "")

    return (False, "Cannot resolve this type of event.")


def try_resolve_event(
    game_state: "GameState", event: WorldEvent
) -> tuple[bool, str]:
    """Attempt to resolve an event.

    Args:
        game_state: Current game state
        event: The event to resolve

    Returns:
        Tuple of (success, message)
    """
    # Check if resolution is possible
    can_do, reason = can_resolve_event(game_state, event)
    if not can_do:
        return (False, reason)

    if event.event_type == "plague":
        return _resolve_plague(game_state, event)
    elif event.event_type == "invasion":
        return _resolve_invasion(game_state, event)
    elif event.event_type == "caravan":
        return _resolve_caravan(game_state, event)

    return (False, "Cannot resolve this type of event.")


def _resolve_plague(
    game_state: "GameState", event: WorldEvent
) -> tuple[bool, str]:
    """Resolve a plague event by using a cure item.

    Args:
        game_state: Current game state
        event: The plague event

    Returns:
        Tuple of (success, message)
    """
    inventory = game_state.current_character.inventory
    cure_items = [item for item in inventory.items if item.is_cure]

    if not cure_items:
        return (False, "You need a Cure or Antidote item to cure the plague.")

    # Consume the cure item
    cure = cure_items[0]
    inventory.remove_item(cure)

    # Mark event as resolved
    event.is_resolved = True
    event.is_active = False

    # Award rewards: XP and gold based on event difficulty
    xp_reward = 50
    gold_reward = 30
    game_state.current_character.gain_xp(xp_reward)
    game_state.current_character.add_gold(gold_reward)

    location = event.affected_locations[0]
    return (
        True,
        colors.heal(
            f"You use the {cure.name} to cure the plague in {location}!\n"
            f"The townspeople are grateful. (+{xp_reward} XP, +{gold_reward} gold)"
        )
    )


def _resolve_invasion(
    game_state: "GameState", event: WorldEvent
) -> tuple[bool, str]:
    """Start combat to resolve an invasion event.

    Note: The actual resolution happens when combat is won.
    This function spawns the enemies and starts combat.

    Args:
        game_state: Current game state
        event: The invasion event

    Returns:
        Tuple of (success, message)
    """
    from cli_rpg.combat import CombatEncounter, spawn_enemies

    # Spawn invasion enemies (2-3 enemies)
    enemies = spawn_enemies(
        location_name=event.affected_locations[0],
        level=game_state.current_character.level,
        count=random.randint(2, 3),
    )

    # Store event ID on combat so we can resolve on victory
    location = game_state.get_current_location()
    game_state.current_combat = CombatEncounter(
        game_state.current_character,
        enemies=enemies,
        weather=game_state.weather,
        companions=game_state.companions,
        location_category=location.category if location else None,
        game_state=game_state,
    )
    # Mark the invasion event ID for post-combat resolution
    game_state._pending_invasion_event = event.event_id

    combat_intro = game_state.current_combat.start()
    return (
        True,
        f"You charge into combat to repel the invasion!\n\n{combat_intro}"
    )


def _resolve_caravan(
    game_state: "GameState", event: WorldEvent
) -> tuple[bool, str]:
    """Resolve a caravan event by acknowledging trade.

    Caravans are usually auto-resolved when player buys something,
    but this allows explicit resolution.

    Args:
        game_state: Current game state
        event: The caravan event

    Returns:
        Tuple of (success, message)
    """
    event.is_resolved = True
    event.is_active = False

    return (
        True,
        colors.heal(
            f"You've traded with the {event.name}. The merchants thank you for your patronage!"
        )
    )


def check_and_resolve_caravan(game_state: "GameState") -> bool:
    """Check for and resolve a caravan event at current location.

    Called after successful purchase to auto-resolve caravan events.

    Args:
        game_state: Current game state

    Returns:
        True if a caravan was resolved, False otherwise
    """
    for event in game_state.world_events:
        if (
            event.is_active
            and event.event_type == "caravan"
            and game_state.current_location in event.affected_locations
        ):
            event.is_resolved = True
            event.is_active = False
            return True
    return False


def get_caravan_shop(game_state: "GameState") -> Optional["Shop"]:
    """Get a temporary shop from an active caravan event at current location.

    Args:
        game_state: Current game state

    Returns:
        Shop instance if caravan active at location, None otherwise
    """
    from cli_rpg.models.shop import Shop, ShopItem
    from cli_rpg.models.item import Item, ItemType

    # Find active caravan at current location
    for event in game_state.world_events:
        if (
            event.is_active
            and event.event_type == "caravan"
            and game_state.current_location in event.affected_locations
        ):
            # Create temporary caravan shop with exotic items
            return Shop(
                name=f"{event.name}",
                inventory=[
                    ShopItem(
                        item=Item(
                            name="Exotic Spices",
                            description="Rare spices from distant lands. Restores stamina.",
                            item_type=ItemType.CONSUMABLE,
                            stamina_restore=30,
                        ),
                        buy_price=50,
                    ),
                    ShopItem(
                        item=Item(
                            name="Traveler's Map",
                            description="A detailed map revealing hidden paths.",
                            item_type=ItemType.MISC,
                        ),
                        buy_price=75,
                    ),
                    ShopItem(
                        item=Item(
                            name="Foreign Elixir",
                            description="A potent healing elixir from far away.",
                            item_type=ItemType.CONSUMABLE,
                            heal_amount=75,
                        ),
                        buy_price=100,
                    ),
                    ShopItem(
                        item=Item(
                            name="Rare Gemstone",
                            description="A valuable gemstone sought by collectors.",
                            item_type=ItemType.MISC,
                        ),
                        buy_price=200,
                    ),
                    ShopItem(
                        item=Item(
                            name="Antidote",
                            description="Cures poison and plague afflictions.",
                            item_type=ItemType.CONSUMABLE,
                            is_cure=True,
                        ),
                        buy_price=40,
                    ),
                ],
            )
    return None


def resolve_invasion_on_victory(game_state: "GameState") -> Optional[str]:
    """Resolve pending invasion event after combat victory.

    Called when player wins combat to check if it was an invasion resolution.

    Args:
        game_state: Current game state

    Returns:
        Resolution message if invasion was resolved, None otherwise
    """
    pending_id = getattr(game_state, "_pending_invasion_event", None)
    if not pending_id:
        return None

    # Find and resolve the event
    for event in game_state.world_events:
        if event.event_id == pending_id:
            event.is_resolved = True
            event.is_active = False

            # Award rewards
            xp_reward = 75
            gold_reward = 50
            game_state.current_character.gain_xp(xp_reward)
            game_state.current_character.add_gold(gold_reward)

            # Clear pending event
            game_state._pending_invasion_event = None

            location = event.affected_locations[0]
            return colors.heal(
                f"\nYou have repelled the {event.name} at {location}!\n"
                f"The area is now safe. (+{xp_reward} XP, +{gold_reward} gold)"
            )

    game_state._pending_invasion_event = None
    return None
