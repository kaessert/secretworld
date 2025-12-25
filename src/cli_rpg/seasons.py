"""Seasonal events and festivals system.

Provides a calendar system that tracks seasons and triggers festivals -
special world events that occur during specific times of year.
"""

from typing import Optional, TYPE_CHECKING

from cli_rpg.models.world_event import WorldEvent
from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


# Festival definitions with templates and effects
# Day ranges are relative to the season (1-30 within each season)
FESTIVAL_TEMPLATES = {
    "spring_festival": {
        "name": "Spring Festival",
        "description": "The town celebrates the return of warmth with music and feasting. "
                       "Merchants offer special discounts, and the air feels lighter.",
        "season": "spring",
        "day_start": 10,  # Relative to season (overall days 10-12)
        "day_end": 12,
        "duration_hours": 48,
        "effects": {
            "shop_discount": 0.20,  # 20% off shop prices
            "dread_reduction_multiplier": 2.0,  # Double dread reduction
        },
    },
    "midsummer_night": {
        "name": "Midsummer Night",
        "description": "On the longest night, the veil between worlds grows thin. "
                       "Strange whispers echo through the darkness, and mysterious encounters abound.",
        "season": "summer",
        "day_start": 15,  # Summer days 15-16 = overall days 45-46
        "day_end": 16,
        "duration_hours": 36,
        "effects": {
            "whisper_chance_multiplier": 1.5,  # 50% more whispers
        },
    },
    "harvest_moon": {
        "name": "Harvest Moon",
        "description": "Under the golden harvest moon, bounty flows freely. "
                       "Merchants grow wealthy and adventurers gain more from their exploits.",
        "season": "autumn",
        "day_start": 20,  # Autumn days 20-22 = overall days 80-82
        "day_end": 22,
        "duration_hours": 72,
        "effects": {
            "xp_multiplier": 1.25,  # 25% more XP
            "merchant_gold_multiplier": 1.5,  # Merchants have 50% more gold
        },
    },
    "winter_solstice": {
        "name": "Winter Solstice",
        "description": "The darkest night of winter brings communities together around warm hearths. "
                       "In towns, the dread cannot touch you, and rest restores more vitality.",
        "season": "winter",
        "day_start": 15,  # Winter days 15-17 = overall days 105-107
        "day_end": 17,
        "duration_hours": 72,
        "effects": {
            "town_dread_immunity": True,  # No dread increase in towns
            "rest_bonus": 25,  # +25 HP on rest in town
        },
    },
}


def _get_season_day(game_state: "GameState") -> tuple[str, int]:
    """Get current season and day within that season.

    Args:
        game_state: Current game state

    Returns:
        Tuple of (season_name, day_within_season) where day_within_season is 1-30
    """
    day = game_state.game_time.get_day()
    season = game_state.game_time.get_season()

    # Calculate day within season (1-30)
    if season == "spring":
        season_day = day  # Days 1-30
    elif season == "summer":
        season_day = day - 30  # Days 31-60 -> 1-30
    elif season == "autumn":
        season_day = day - 60  # Days 61-90 -> 1-30
    else:  # winter
        season_day = day - 90  # Days 91-120 -> 1-30

    return season, season_day


def _is_festival_day(template: dict, season: str, season_day: int) -> bool:
    """Check if a festival should be active based on current season/day.

    Args:
        template: Festival template dictionary
        season: Current season name
        season_day: Current day within the season (1-30)

    Returns:
        True if festival should be active, False otherwise
    """
    if template["season"] != season:
        return False
    return template["day_start"] <= season_day <= template["day_end"]


def _get_active_festival_id(game_state: "GameState") -> Optional[str]:
    """Get the ID of currently active festival, if any.

    Args:
        game_state: Current game state

    Returns:
        Festival ID string if a festival is active, None otherwise
    """
    for event in game_state.world_events:
        if event.is_active and event.event_type == "festival":
            return event.event_id
    return None


def check_for_festival(game_state: "GameState") -> Optional[str]:
    """Check if a festival should spawn based on current day/season.

    Called on movement. Spawns the appropriate festival if the day matches
    and no festival is already active.

    Args:
        game_state: Current game state

    Returns:
        Festival notification message if festival spawned, None otherwise
    """
    season, season_day = _get_season_day(game_state)

    # Check if any festival should be active
    for festival_id, template in FESTIVAL_TEMPLATES.items():
        if not _is_festival_day(template, season, season_day):
            continue

        # Check if this festival is already active
        active_id = _get_active_festival_id(game_state)
        if active_id is not None:
            # A festival is already active - don't spawn another
            return None

        # Spawn the festival
        event = WorldEvent(
            event_id=festival_id,
            name=template["name"],
            description=template["description"],
            event_type="festival",
            affected_locations=["all"],  # Festivals affect everywhere
            start_hour=game_state.game_time.hour,
            duration_hours=template["duration_hours"],
        )
        game_state.world_events.append(event)

        return _format_festival_notification(event)

    return None


def _format_festival_notification(event: WorldEvent) -> str:
    """Format a festival announcement.

    Args:
        event: The festival event

    Returns:
        Formatted festival notification string
    """
    width = 56
    border = "=" * width

    lines = [
        "",
        colors.gold(border),
        colors.gold(f"  🎉 FESTIVAL: {event.name} 🎉"),
        colors.gold(border),
        "",
        f"  {event.description}",
        "",
        colors.gold(f"  Duration: {event.duration_hours} hours"),
        "",
        colors.gold(border),
    ]

    return "\n".join(lines)


def get_active_festival(game_state: "GameState") -> Optional[WorldEvent]:
    """Get currently active festival event, if any.

    Args:
        game_state: Current game state

    Returns:
        Active festival WorldEvent, or None if no festival is active
    """
    for event in game_state.world_events:
        if event.is_active and event.event_type == "festival":
            return event
    return None


def _get_active_festival_effects(game_state: "GameState") -> dict:
    """Get effects dictionary from active festival, if any.

    Args:
        game_state: Current game state

    Returns:
        Effects dictionary from active festival template, or empty dict
    """
    festival = get_active_festival(game_state)
    if festival is None:
        return {}

    template = FESTIVAL_TEMPLATES.get(festival.event_id)
    if template is None:
        return {}

    return template.get("effects", {})


def get_festival_shop_discount(game_state: "GameState") -> float:
    """Get shop discount from active festival.

    Args:
        game_state: Current game state

    Returns:
        Discount as decimal (0.0 = no discount, 0.20 = 20% off)
    """
    effects = _get_active_festival_effects(game_state)
    return effects.get("shop_discount", 0.0)


def get_festival_xp_multiplier(game_state: "GameState") -> float:
    """Get XP multiplier from active festival.

    Args:
        game_state: Current game state

    Returns:
        XP multiplier (1.0 = normal, 1.25 = 25% bonus)
    """
    effects = _get_active_festival_effects(game_state)
    return effects.get("xp_multiplier", 1.0)


def get_festival_rest_bonus(game_state: "GameState") -> int:
    """Get rest HP bonus from active festival.

    Args:
        game_state: Current game state

    Returns:
        Extra HP restored on rest (0 = no bonus)
    """
    effects = _get_active_festival_effects(game_state)
    return effects.get("rest_bonus", 0)


def get_festival_whisper_multiplier(game_state: "GameState") -> float:
    """Get whisper chance multiplier from active festival.

    Args:
        game_state: Current game state

    Returns:
        Whisper chance multiplier (1.0 = normal, 1.5 = 50% more)
    """
    effects = _get_active_festival_effects(game_state)
    return effects.get("whisper_chance_multiplier", 1.0)


def get_festival_dread_reduction_multiplier(game_state: "GameState") -> float:
    """Get dread reduction multiplier from active festival.

    Args:
        game_state: Current game state

    Returns:
        Dread reduction multiplier (1.0 = normal, 2.0 = double reduction)
    """
    effects = _get_active_festival_effects(game_state)
    return effects.get("dread_reduction_multiplier", 1.0)


def has_town_dread_immunity(game_state: "GameState") -> bool:
    """Check if active festival grants dread immunity in towns.

    Args:
        game_state: Current game state

    Returns:
        True if dread is blocked in towns during festival
    """
    effects = _get_active_festival_effects(game_state)
    return effects.get("town_dread_immunity", False)
