# Plan: Shop Price Modifiers Based on NPC Arc Stage

## Spec

Merchant NPCs with arc relationships should offer better/worse prices based on their arc stage with the player:

| Arc Stage     | Buy Price | Sell Price | Notes                           |
|---------------|-----------|------------|---------------------------------|
| ENEMY         | REFUSED   | REFUSED    | No trading allowed              |
| HOSTILE       | +20%      | -20%       | Active hostility                |
| WARY          | +10%      | -10%       | Suspicious of player            |
| STRANGER      | +0%       | +0%        | Default, no modifier            |
| ACQUAINTANCE  | -5%       | +5%        | Building trust                  |
| TRUSTED       | -10%      | +10%       | Real trust established          |
| DEVOTED       | -15%      | +15%       | Unbreakable bond, best prices   |

This stacks with existing modifiers (CHA, faction, economy, persuade, haggle).

## Implementation

### 1. Create `src/cli_rpg/npc_arc_shop.py`

```python
"""NPC arc effects on shop prices."""
from typing import Optional, Tuple
from cli_rpg.models.npc_arc import NPCArc, NPCArcStage

# Price modifiers by arc stage (buy_modifier, sell_modifier)
ARC_PRICE_MODIFIERS: dict[NPCArcStage, Tuple[Optional[float], Optional[float]]] = {
    NPCArcStage.ENEMY: (None, None),  # Trade refused
    NPCArcStage.HOSTILE: (1.20, 0.80),
    NPCArcStage.WARY: (1.10, 0.90),
    NPCArcStage.STRANGER: (1.0, 1.0),
    NPCArcStage.ACQUAINTANCE: (0.95, 1.05),
    NPCArcStage.TRUSTED: (0.90, 1.10),
    NPCArcStage.DEVOTED: (0.85, 1.15),
}

def get_arc_price_modifiers(arc: Optional[NPCArc]) -> Tuple[Optional[float], Optional[float], bool]:
    """Get buy/sell price modifiers based on NPC arc stage."""
    if arc is None:
        return (1.0, 1.0, False)
    stage = arc.get_stage()
    buy_mod, sell_mod = ARC_PRICE_MODIFIERS[stage]
    if stage == NPCArcStage.ENEMY:
        return (None, None, True)
    return (buy_mod, sell_mod, False)

def get_arc_price_message(stage: NPCArcStage) -> str:
    """Get display message for arc-based price effects."""
    # Return appropriate messages for each stage
```

### 2. Update `src/cli_rpg/main.py`

In the `buy` command (around line 1571-1573):
- After faction modifier, add arc modifier:
```python
from cli_rpg.npc_arc_shop import get_arc_price_modifiers
if game_state.current_npc and game_state.current_npc.arc:
    arc_buy_mod, arc_sell_mod, arc_refused = get_arc_price_modifiers(
        game_state.current_npc.arc
    )
    if arc_refused:
        return (True, "\nThis merchant refuses to trade with you due to your past actions.")
    if arc_buy_mod is not None:
        final_price = int(final_price * arc_buy_mod)
```

In the `sell` command (around line 1651-1652):
- Add similar arc modifier after faction modifier

In the `shop` command (around line 1519-1532):
- Add arc price message display and adjust displayed prices

### 3. Create `tests/test_npc_arc_shop.py`

Test cases:
1. `test_arc_price_modifiers_enemy_refuses_trade`
2. `test_arc_price_modifiers_hostile_premium`
3. `test_arc_price_modifiers_stranger_neutral`
4. `test_arc_price_modifiers_trusted_discount`
5. `test_arc_price_modifiers_devoted_best_discount`
6. `test_arc_price_modifiers_none_arc_neutral`
7. `test_buy_command_arc_modifier_applied`
8. `test_sell_command_arc_modifier_applied`
9. `test_shop_display_arc_adjusted_prices`
10. `test_arc_modifier_stacks_with_faction`

## Steps

1. Create `src/cli_rpg/npc_arc_shop.py` with modifier logic
2. Write tests in `tests/test_npc_arc_shop.py`
3. Run tests (expect failures)
4. Update `main.py` buy command to apply arc modifier
5. Update `main.py` sell command to apply arc modifier
6. Update `main.py` shop command to display arc-adjusted prices
7. Run tests until passing
8. Run full test suite: `pytest`
