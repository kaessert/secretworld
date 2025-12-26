# Implementation Plan: Haggle Command for Shops

## Spec

**Command**: `haggle` - Negotiate better buy/sell prices with merchants

**Mechanics**:
- **Success formula**: 25% base + (CHA × 2%) + (relationship bonus)
  - If `npc.persuaded`: +15% bonus to success chance
- **Effects**:
  - Success: 15% discount on next buy OR 15% bonus on next sell
  - Critical success (roll ≤ 10% of success chance): 25% discount + merchant offers a rare item hint
  - Failure: No effect, can try again
  - Critical failure (roll ≥ 95): Merchant refuses to trade for 3 turns (cooldown)
- **NPC attributes**:
  - `haggleable: bool = True` - whether merchant allows haggling
  - `haggle_cooldown: int = 0` - turns remaining before haggling allowed again
- **GameState tracking**: `haggle_bonus: float = 0.0` - active bonus (reset after one transaction)

**Constraints**:
- Only works when `current_shop` is active
- Cooldown decrements on each exploration command

## Tests (TDD)

**File**: `tests/test_haggle.py`

1. `test_calculate_haggle_chance_base` - 25% + CHA×2% formula
2. `test_calculate_haggle_chance_with_persuaded_bonus` - +15% when persuaded
3. `test_haggle_success_grants_discount` - success sets `game_state.haggle_bonus = 0.15`
4. `test_haggle_critical_success_grants_larger_discount` - 25% bonus on crit
5. `test_haggle_failure_no_effect` - failed haggle keeps `haggle_bonus = 0`
6. `test_haggle_critical_failure_sets_cooldown` - roll ≥ 95 sets cooldown = 3
7. `test_haggle_not_at_shop` - error when `current_shop` is None
8. `test_haggle_stubborn_merchant` - NPC with `haggleable=False` refuses
9. `test_haggle_cooldown_blocks_attempt` - can't haggle when cooldown > 0
10. `test_haggle_cooldown_decrements` - cooldown reduced each command
11. `test_buy_applies_haggle_bonus` - buy price reduced by haggle_bonus
12. `test_sell_applies_haggle_bonus` - sell price increased by haggle_bonus
13. `test_haggle_bonus_consumed_after_buy` - bonus reset to 0 after purchase
14. `test_haggle_bonus_consumed_after_sell` - bonus reset to 0 after sale

## Implementation Steps

### 1. Update NPC model (`src/cli_rpg/models/npc.py`)
- Add `haggleable: bool = True` field (line ~45)
- Add `haggle_cooldown: int = 0` field (line ~46)
- Update `to_dict()`: add both fields
- Update `from_dict()`: parse with defaults for backward compat

### 2. Add haggle functions (`src/cli_rpg/social_skills.py`)
```python
def calculate_haggle_chance(charisma: int, persuaded: bool = False) -> int:
    """25% base + CHA×2% + 15% if persuaded, max 85%."""
    chance = 25 + charisma * 2
    if persuaded:
        chance += 15
    return min(chance, 85)

def attempt_haggle(character, npc) -> Tuple[bool, str, float, int]:
    """Returns (success, message, bonus, cooldown_to_set)."""
```

### 3. Update GameState (`src/cli_rpg/game_state.py`)
- Add `self.haggle_bonus: float = 0.0` to `__init__` (line ~90)
- Add `"haggle"` to `KNOWN_COMMANDS` (line ~54)

### 4. Add haggle command handler (`src/cli_rpg/main.py`)
- Add handler after `elif command == "bribe":` block (~line 960)
- Check: `current_shop` exists, NPC is `haggleable`, cooldown == 0
- Call `attempt_haggle()`, set `game_state.haggle_bonus`

### 5. Modify buy to apply bonus (`src/cli_rpg/main.py`, ~line 843)
- After CHA/persuade modifiers: `final_price = int(final_price * (1 - game_state.haggle_bonus))`
- After purchase: `game_state.haggle_bonus = 0.0`

### 6. Modify sell to apply bonus (`src/cli_rpg/main.py`, ~line 898)
- Apply: `sell_price = int(sell_price * (1 + game_state.haggle_bonus))`
- After sale: `game_state.haggle_bonus = 0.0`

### 7. Add cooldown decrement (`src/cli_rpg/main.py`)
- At start of `handle_exploration_command()`: if `game_state.current_npc` and `haggle_cooldown > 0`, decrement it

### 8. Update help text (`src/cli_rpg/main.py`, ~line 47)
- Add to shop commands: `"  haggle             - Negotiate better prices (CHA-based)"`

### 9. Update ISSUES.md
- Mark "Haggling at shops" as RESOLVED
