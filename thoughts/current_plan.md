# Implementation Plan: Issue 14 - Living Economy System

## Spec

Create a dynamic economy system with supply/demand and trade routes that modifies shop prices based on:
1. **Item scarcity** - Items recently bought become more expensive; items sold drop in price
2. **Location type** - Terrain/category affects item availability (weapons cheaper at smithies, potions cheaper at temples)
3. **Trade route disruption** - Caravan events and invasions affect regional prices
4. **Time-based recovery** - Prices drift back toward baseline over time

### Price Modifier Stacking Order
1. Base price (ShopItem.buy_price)
2. Economy modifier (supply/demand, trade routes) - NEW
3. CHA modifier (existing)
4. Faction modifier (existing)
5. Persuade/haggle bonuses (existing)

### Data Model: EconomyState
```python
@dataclass
class EconomyState:
    # Per-item supply modifier (1.0 = baseline, >1.0 = scarce/expensive, <1.0 = surplus/cheap)
    item_supply: dict[str, float]  # item_name -> modifier

    # Regional disruption (from world events like invasions)
    regional_disruption: float  # 1.0 = normal, >1.0 = prices inflated

    last_update_hour: int  # For time-based recovery
```

### Economy Rules
- **Buy transaction**: Increase item_supply[item] by 0.05 (max 1.5 = 50% price increase)
- **Sell transaction**: Decrease item_supply[item] by 0.03 (min 0.7 = 30% price decrease)
- **Time recovery**: Every 6 game hours, item_supply drifts 5% toward 1.0
- **Invasion event**: Sets regional_disruption = 1.2 (+20% all prices) while active
- **Caravan event**: Sets regional_disruption = 0.9 (-10% all prices) while active
- **Location bonuses** (permanent, defined as constants):
  - Temple: consumables -15%
  - Town/village: weapons -10%
  - Forest: resources -20%

---

## Tests (tests/test_economy.py)

### Unit Tests: EconomyState
1. `test_default_economy_state` - All modifiers start at 1.0
2. `test_record_buy_increases_supply_modifier` - Buy adds 0.05 to item supply
3. `test_record_buy_caps_at_max` - Supply modifier caps at 1.5
4. `test_record_sell_decreases_supply_modifier` - Sell reduces by 0.03
5. `test_record_sell_caps_at_min` - Supply modifier floors at 0.7
6. `test_time_recovery_drifts_toward_baseline` - Modifiers drift 5% toward 1.0 per 6 hours
7. `test_get_economy_modifier_combines_factors` - Combines supply, location, and disruption
8. `test_serialization_roundtrip` - to_dict/from_dict preserves state

### Unit Tests: Location Bonuses
9. `test_temple_consumable_discount` - Consumables 15% cheaper at temples
10. `test_town_weapon_discount` - Weapons 10% cheaper at towns
11. `test_forest_resource_discount` - Resources 20% cheaper in forests

### Unit Tests: World Event Integration
12. `test_invasion_increases_prices` - Active invasion sets disruption = 1.2
13. `test_caravan_decreases_prices` - Active caravan sets disruption = 0.9
14. `test_disruption_clears_when_event_ends` - Disruption returns to 1.0 after event

### Integration Tests: Buy/Sell Commands
15. `test_buy_applies_economy_modifier` - Final price includes economy factor
16. `test_sell_applies_economy_modifier` - Sell price includes economy factor
17. `test_shop_display_shows_economy_adjusted_prices` - Shop command shows final prices
18. `test_economy_modifier_stacks_with_faction` - Economy + faction modifiers stack correctly

---

## Implementation Steps

### Step 1: Create economy model
**File**: `src/cli_rpg/models/economy.py`

```python
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
```

### Step 2: Create economy helper module
**File**: `src/cli_rpg/economy.py`

```python
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
```

### Step 3: Integrate into GameState
**File**: `src/cli_rpg/game_state.py`

Add import:
```python
from cli_rpg.models.economy import EconomyState
```

Add field in `__init__`:
```python
self.economy_state: EconomyState = EconomyState()
```

Update `to_dict()`:
```python
data["economy_state"] = self.economy_state.to_dict()
```

Update `from_dict()`:
```python
game_state.economy_state = EconomyState.from_dict(data.get("economy_state"))
```

Call time update in `advance_time()` method:
```python
self.economy_state.update_time(self.game_time.hour)
```

### Step 4: Integrate into buy/sell/shop commands
**File**: `src/cli_rpg/main.py`

Add import:
```python
from cli_rpg.economy import get_economy_price_modifier
```

**Buy command** (after CHA modifier line ~1463):
```python
# Apply economy modifier
location = game_state.get_current_location()
economy_mod = get_economy_price_modifier(shop_item.item, game_state.economy_state, location.category)
final_price = int(final_price * economy_mod)
```
After successful purchase:
```python
game_state.economy_state.record_buy(shop_item.item.name)
```

**Sell command** (after CHA modifier line ~1533):
```python
# Apply economy modifier
location = game_state.get_current_location()
economy_mod = get_economy_price_modifier(item, game_state.economy_state, location.category)
sell_price = int(sell_price * economy_mod)
```
After successful sale:
```python
game_state.economy_state.record_sell(item.name)
```

**Shop command** (in price display loop ~1423):
```python
economy_mod = get_economy_price_modifier(si.item, game_state.economy_state, location.category)
display_price = int(display_price * economy_mod)
```

### Step 5: Integrate world event effects
**File**: `src/cli_rpg/world_events.py`

Add import:
```python
from cli_rpg.economy import update_economy_from_events
```

In `progress_events()` function, after processing events:
```python
update_economy_from_events(game_state.economy_state, game_state.world_events)
```

### Step 6: Write tests
**File**: `tests/test_economy.py`

Implement all 18 tests per spec above.

---

## Files Summary

**Create**:
- `src/cli_rpg/models/economy.py` - EconomyState dataclass with supply/demand logic
- `src/cli_rpg/economy.py` - Price calculation helpers and event integration
- `tests/test_economy.py` - All economy tests (18 tests)

**Modify**:
- `src/cli_rpg/game_state.py` - Add economy_state field and serialization
- `src/cli_rpg/main.py` - Apply economy modifiers in buy/sell/shop commands
- `src/cli_rpg/world_events.py` - Update economy disruption from active events
