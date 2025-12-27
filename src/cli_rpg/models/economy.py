"""Economy model for dynamic supply/demand pricing."""
from dataclasses import dataclass, field
from typing import Optional


# Location category -> item_type.value -> modifier
LOCATION_BONUSES: dict[str, dict[str, float]] = {
    "temple": {"consumable": 0.85},
    "town": {"weapon": 0.90},
    "village": {"weapon": 0.90},
    "forest": {"resource": 0.80},
}


@dataclass
class EconomyState:
    """Tracks dynamic economy state for supply/demand pricing."""

    item_supply: dict[str, float] = field(default_factory=dict)
    regional_disruption: float = 1.0
    last_update_hour: int = 0

    SUPPLY_INCREASE: float = 0.05
    SUPPLY_DECREASE: float = 0.03
    MAX_SUPPLY_MOD: float = 1.5
    MIN_SUPPLY_MOD: float = 0.7
    RECOVERY_RATE: float = 0.05
    RECOVERY_INTERVAL: int = 6

    def record_buy(self, item_name: str) -> None:
        """Record a buy transaction, increasing item scarcity."""
        current = self.item_supply.get(item_name, 1.0)
        self.item_supply[item_name] = min(self.MAX_SUPPLY_MOD, current + self.SUPPLY_INCREASE)

    def record_sell(self, item_name: str) -> None:
        """Record a sell transaction, increasing item surplus."""
        current = self.item_supply.get(item_name, 1.0)
        self.item_supply[item_name] = max(self.MIN_SUPPLY_MOD, current - self.SUPPLY_DECREASE)

    def update_time(self, current_hour: int) -> None:
        """Apply time-based recovery toward baseline prices."""
        hours_elapsed = current_hour - self.last_update_hour
        if hours_elapsed < 0:
            hours_elapsed += 24  # Handle day wrap

        intervals = hours_elapsed // self.RECOVERY_INTERVAL
        if intervals > 0:
            self.last_update_hour = current_hour
            for item_name in list(self.item_supply.keys()):
                current = self.item_supply[item_name]
                # Drift toward 1.0
                for _ in range(intervals):
                    if current > 1.0:
                        current = max(1.0, current - self.RECOVERY_RATE)
                    elif current < 1.0:
                        current = min(1.0, current + self.RECOVERY_RATE)
                if current == 1.0:
                    del self.item_supply[item_name]  # Clean up baseline entries
                else:
                    self.item_supply[item_name] = current

    def get_modifier(
        self,
        item_name: str,
        item_type: str,
        location_category: Optional[str],
    ) -> float:
        """Calculate combined economy modifier for an item."""
        # Supply/demand modifier
        supply_mod = self.item_supply.get(item_name, 1.0)

        # Location bonus
        location_mod = 1.0
        if location_category and location_category in LOCATION_BONUSES:
            location_mod = LOCATION_BONUSES[location_category].get(item_type, 1.0)

        return supply_mod * location_mod * self.regional_disruption

    def to_dict(self) -> dict:
        return {
            "item_supply": self.item_supply.copy(),
            "regional_disruption": self.regional_disruption,
            "last_update_hour": self.last_update_hour,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "EconomyState":
        if not data:
            return cls()
        return cls(
            item_supply=data.get("item_supply", {}),
            regional_disruption=data.get("regional_disruption", 1.0),
            last_update_hour=data.get("last_update_hour", 0),
        )
