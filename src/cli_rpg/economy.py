"""Economy system helpers for price modification."""
from typing import Optional, TYPE_CHECKING

from cli_rpg.models.economy import EconomyState

if TYPE_CHECKING:
    from cli_rpg.models.item import Item
    from cli_rpg.models.world_event import WorldEvent


def get_economy_price_modifier(
    item: "Item",
    economy_state: EconomyState,
    location_category: Optional[str],
) -> float:
    """Get combined economy modifier for item price."""
    return economy_state.get_modifier(
        item.name,
        item.item_type.value,
        location_category,
    )


def update_economy_from_events(
    economy_state: EconomyState,
    events: list["WorldEvent"],
) -> None:
    """Update economy disruption based on active world events."""
    disruption = 1.0
    for event in events:
        if not event.is_active:
            continue
        if event.event_type == "invasion":
            disruption = max(disruption, 1.2)  # +20% prices
        elif event.event_type == "caravan":
            disruption = min(disruption, 0.9)  # -10% prices
    economy_state.regional_disruption = disruption
