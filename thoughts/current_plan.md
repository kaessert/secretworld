# Implementation Plan: Faction Reputation Effects on Shop Prices

## Spec

Make faction reputation meaningful for trading by applying price modifiers based on the player's standing with the **Merchant Guild** faction:

| Reputation Level | Buy Price | Sell Price | Trade Allowed |
|------------------|-----------|------------|---------------|
| HOSTILE (1-19)   | N/A       | N/A        | **REFUSED**   |
| UNFRIENDLY (20-39) | +15%    | -15%       | Yes           |
| NEUTRAL (40-59)  | +0%       | +0%        | Yes           |
| FRIENDLY (60-79) | -10%      | +10%       | Yes           |
| HONORED (80-100) | -20%      | +20%       | Yes           |

**Design Decisions:**
- Use **Merchant Guild** faction (already exists) as the sole faction affecting shop prices
- Price modifiers stack with existing CHA, persuade, and haggle modifiers (applied last)
- HOSTILE blocks all trading entirely (shops refuse service)
- Messages explain reputation effects when relevant

## Tests First (TDD)

### `tests/test_faction_shop_prices.py`

1. `TestGetFactionPriceModifiers`:
   - `test_hostile_buy_modifier_refuses`: HOSTILE returns (None, None, refused=True)
   - `test_unfriendly_buy_modifier`: UNFRIENDLY returns 1.15 buy, 0.85 sell
   - `test_neutral_no_modifier`: NEUTRAL returns 1.0, 1.0
   - `test_friendly_discount`: FRIENDLY returns 0.90 buy, 1.10 sell
   - `test_honored_discount`: HONORED returns 0.80 buy, 1.20 sell

2. `TestBuyCommandWithFactionReputation`:
   - `test_buy_hostile_faction_refuses_trade`: HOSTILE rep blocks buy command
   - `test_buy_unfriendly_pays_premium`: UNFRIENDLY pays 15% more
   - `test_buy_friendly_gets_discount`: FRIENDLY pays 10% less
   - `test_buy_honored_gets_best_discount`: HONORED pays 20% less
   - `test_buy_stacks_with_cha_modifier`: Faction + CHA modifiers stack correctly

3. `TestSellCommandWithFactionReputation`:
   - `test_sell_hostile_faction_refuses_trade`: HOSTILE rep blocks sell command
   - `test_sell_unfriendly_gets_less`: UNFRIENDLY receives 15% less gold
   - `test_sell_friendly_gets_bonus`: FRIENDLY receives 10% more gold
   - `test_sell_honored_gets_best_bonus`: HONORED receives 20% more gold

## Implementation Steps

### Step 1: Create faction shop module
**File:** `src/cli_rpg/faction_shop.py`

```python
"""Faction reputation effects on shop prices."""
from typing import Optional, Tuple
from cli_rpg.models.faction import Faction, ReputationLevel

# Price modifiers by reputation level (buy_modifier, sell_modifier)
# Buy: <1.0 is discount, >1.0 is premium
# Sell: <1.0 is penalty, >1.0 is bonus
FACTION_PRICE_MODIFIERS = {
    ReputationLevel.HOSTILE: (None, None),  # Trade refused
    ReputationLevel.UNFRIENDLY: (1.15, 0.85),
    ReputationLevel.NEUTRAL: (1.0, 1.0),
    ReputationLevel.FRIENDLY: (0.90, 1.10),
    ReputationLevel.HONORED: (0.80, 1.20),
}

def get_merchant_guild_faction(factions: list[Faction]) -> Optional[Faction]:
    """Find the Merchant Guild faction."""

def get_faction_price_modifiers(factions: list[Faction]) -> Tuple[Optional[float], Optional[float], bool]:
    """Get buy/sell modifiers and whether trade is refused."""

def get_faction_price_message(level: ReputationLevel) -> str:
    """Get a message describing the price effect (for display)."""
```

### Step 2: Integrate into buy command
**File:** `src/cli_rpg/main.py` (buy command, ~line 1324)

Before calculating final_price:
1. Call `get_faction_price_modifiers(game_state.factions)`
2. If trade_refused, return early with message: "The merchants refuse to trade with you due to your poor reputation."
3. Otherwise, multiply final_price by buy_modifier after other modifiers

### Step 3: Integrate into sell command
**File:** `src/cli_rpg/main.py` (sell command, ~line 1378)

Before calculating sell_price:
1. Call `get_faction_price_modifiers(game_state.factions)`
2. If trade_refused, return early with same refusal message
3. Otherwise, multiply sell_price by sell_modifier after other modifiers

### Step 4: Update shop display (optional enhancement)
**File:** `src/cli_rpg/main.py` (shop command, ~line 1306)

Add reputation status message if not NEUTRAL:
- HOSTILE: "The merchants eye you with hostility and refuse to serve you."
- UNFRIENDLY: "(Prices are 15% higher due to your reputation)"
- FRIENDLY: "(You receive a 10% discount for your good standing)"
- HONORED: "(You receive a 20% discount as an honored customer)"

### Step 5: Run tests
```bash
pytest tests/test_faction_shop_prices.py -v
pytest tests/test_shop_commands.py -v
pytest --cov=src/cli_rpg --cov-report=term-missing
```
