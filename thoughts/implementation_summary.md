# Implementation Summary: NPC Arc Shop Price Modifiers

## Date: 2025-12-28

## What Was Implemented

This feature adds shop price modifiers based on NPC arc (relationship) stage. Merchants with arc relationships now offer better or worse prices based on how the player has treated them.

### Price Modifier Table (per spec)

| Arc Stage     | Buy Modifier | Sell Modifier | Effect                          |
|---------------|--------------|---------------|---------------------------------|
| ENEMY         | REFUSED      | REFUSED       | Trade blocked entirely          |
| HOSTILE       | +20%         | -20%          | Hostile NPCs charge more        |
| WARY          | +10%         | -10%          | Suspicious NPCs slightly worse  |
| STRANGER      | +0%          | +0%           | Default, neutral                |
| ACQUAINTANCE  | -5%          | +5%           | Building rapport, slight bonus  |
| TRUSTED       | -10%         | +10%          | Real trust, good prices         |
| DEVOTED       | -15%         | +15%          | Best prices for loyal customers |

These modifiers **stack** with existing modifiers (CHA, faction, economy, persuade, haggle).

## Files Created/Modified

### New File: `src/cli_rpg/npc_arc_shop.py`
- `ARC_PRICE_MODIFIERS`: Dict mapping NPCArcStage to (buy_mod, sell_mod) tuples
- `ARC_PRICE_MESSAGES`: Dict mapping NPCArcStage to display messages
- `get_arc_price_modifiers(arc)`: Returns (buy_mod, sell_mod, trade_refused) tuple
- `get_arc_price_message(stage)`: Returns display message for price effects

### New File: `tests/test_npc_arc_shop.py`
- 14 unit tests covering all arc stages and edge cases
- Tests verify modifier values, trade refusal for ENEMY, and message content

### Modified: `src/cli_rpg/main.py`
- **shop command** (~line 1498): Added arc modifier check, trade refusal for ENEMY stage, arc message display, and arc-adjusted displayed prices
- **buy command** (~line 1554): Added arc modifier check, trade refusal, and arc price modifier applied to final_price
- **sell command** (~line 1636): Added arc modifier check, trade refusal, and arc price modifier applied to sell_price

## Test Results

```
tests/test_npc_arc_shop.py: 14 passed
Full test suite: 5512 passed, 4 skipped, 1 warning
```

## Integration Points

The arc modifiers integrate naturally with the existing price calculation chain:
1. Base price (CHA modifier)
2. Economy modifier (supply/demand, location, world events)
3. Faction modifier (Merchant Guild reputation)
4. **NPC Arc modifier** (NEW - based on relationship with specific merchant)
5. Persuade discount (if NPC was persuaded)
6. Haggle bonus (if haggle was successful)

## E2E Test Suggestions

To validate end-to-end:
1. Start a game, find a merchant NPC, check shop prices at STRANGER stage
2. Improve relationship via dialogue/quests to TRUSTED, verify ~10% discount
3. Attack/antagonize merchant to ENEMY stage, verify trade is refused
4. Verify arc messages appear in shop display at non-STRANGER stages
