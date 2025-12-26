# Implementation Plan: Fix Shop Price Display Inconsistency

## Bug Summary
Shop displays base prices (e.g., "Health Potion - 50 gold") but error/purchase messages show faction-adjusted prices (e.g., "You can't afford Health Potion (48 gold)"). This confuses players when displayed and charged prices don't match.

## Root Cause
In `src/cli_rpg/main.py`:
- **Line 1332**: `shop` command displays `si.buy_price` (base price)
- **Lines 1361-1373**: `buy` command calculates `final_price` with CHA modifier, faction modifier, persuade discount, and haggle bonus

The display and purchase logic use different price calculations.

## Solution
Update the `shop` command to display the same adjusted prices that the `buy` command uses. Apply all active modifiers to the displayed price.

## Implementation Steps

### 1. Add test for shop price display consistency
**File:** `tests/test_faction_shop_prices.py`

Add a new test to `TestShopCommandWithFactionReputation` that verifies displayed prices match the faction-adjusted prices:

```python
def test_shop_displays_faction_adjusted_prices(self, game_with_shop_and_factions):
    """Shop command shows faction-adjusted prices, not base prices."""
    game = game_with_shop_and_factions
    game.factions = create_factions_with_merchant_guild(90)  # HONORED (-20%)

    cont, msg = handle_exploration_command(game, "shop", [])
    assert cont is True
    # Base price is 100 for Health Potion, HONORED = 80
    assert "80 gold" in msg
    # Should NOT show base price
    assert "100 gold" not in msg
```

### 2. Update shop command to display adjusted prices
**File:** `src/cli_rpg/main.py`, lines 1331-1332

Replace:
```python
for si in shop.inventory:
    lines.append(f"  {si.item.name} - {si.buy_price} gold")
```

With:
```python
from cli_rpg.social_skills import get_cha_price_modifier
cha_modifier = get_cha_price_modifier(game_state.current_character.charisma)
for si in shop.inventory:
    # Calculate display price with all modifiers
    display_price = int(si.buy_price * cha_modifier)
    if faction_buy_mod is not None:
        display_price = int(display_price * faction_buy_mod)
    if game_state.current_npc and game_state.current_npc.persuaded:
        display_price = int(display_price * 0.8)
    if game_state.haggle_bonus > 0:
        display_price = int(display_price * (1 - game_state.haggle_bonus))
    lines.append(f"  {si.item.name} - {display_price} gold")
```

### 3. Run tests
```bash
pytest tests/test_faction_shop_prices.py -v
pytest tests/test_shop_commands.py tests/test_charisma.py tests/test_haggle.py -v
pytest -x
```

## Files to Modify
1. `tests/test_faction_shop_prices.py` - Add test for price display consistency
2. `src/cli_rpg/main.py` - Update shop display to show adjusted prices (lines 1331-1332)
