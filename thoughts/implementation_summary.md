# Implementation Summary: Haggle Command for Shops

## What Was Implemented

The haggle command allows players to negotiate better buy/sell prices with merchants using CHA-based mechanics.

### Files Modified

1. **`src/cli_rpg/models/npc.py`** - Added NPC haggle attributes:
   - `haggleable: bool = True` - whether merchant allows haggling
   - `haggle_cooldown: int = 0` - turns remaining before haggling allowed again
   - Updated `to_dict()` and `from_dict()` with backward compatibility

2. **`src/cli_rpg/social_skills.py`** - Added haggle functions:
   - `calculate_haggle_chance(charisma, persuaded)` - 25% base + CHA×2% + 15% if persuaded, max 85%
   - `attempt_haggle(character, npc)` - returns (success, message, bonus, cooldown_to_set)

3. **`src/cli_rpg/game_state.py`** - GameState updates:
   - Added `self.haggle_bonus: float = 0.0` attribute
   - Added `"haggle"` to `KNOWN_COMMANDS`

4. **`src/cli_rpg/main.py`** - Command integration:
   - Added help text: `"  haggle             - Negotiate better prices (CHA-based, at shop)"`
   - Added cooldown decrement in exploration command handler
   - Added `haggle` command handler that calls `attempt_haggle()` and sets bonus/cooldown
   - Modified `buy` to apply and consume `haggle_bonus`
   - Modified `sell` to apply and consume `haggle_bonus`

5. **`tests/test_haggle.py`** - Comprehensive test suite (24 tests):
   - `TestCalculateHaggleChance` (5 tests) - formula verification
   - `TestAttemptHaggle` (6 tests) - success/failure/cooldown mechanics
   - `TestHaggleIntegration` (7 tests) - buy/sell bonus application
   - `TestNPCHaggleAttributes` (5 tests) - serialization/defaults
   - `TestGameStateHaggleBonus` (1 test) - GameState attribute

6. **`ISSUES.md`** - Marked "Haggling at shops" as RESOLVED

## Test Results

All 24 haggle tests pass:

```
tests/test_haggle.py::TestCalculateHaggleChance::test_calculate_haggle_chance_base PASSED
tests/test_haggle.py::TestCalculateHaggleChance::test_calculate_haggle_chance_low_cha PASSED
tests/test_haggle.py::TestCalculateHaggleChance::test_calculate_haggle_chance_high_cha PASSED
tests/test_haggle.py::TestCalculateHaggleChance::test_calculate_haggle_chance_max_cap PASSED
tests/test_haggle.py::TestCalculateHaggleChance::test_calculate_haggle_chance_with_persuaded_bonus PASSED
tests/test_haggle.py::TestAttemptHaggle::test_haggle_success_grants_discount PASSED
tests/test_haggle.py::TestAttemptHaggle::test_haggle_critical_success_grants_larger_discount PASSED
tests/test_haggle.py::TestAttemptHaggle::test_haggle_failure_no_effect PASSED
tests/test_haggle.py::TestAttemptHaggle::test_haggle_critical_failure_sets_cooldown PASSED
tests/test_haggle.py::TestAttemptHaggle::test_haggle_stubborn_merchant PASSED
tests/test_haggle.py::TestAttemptHaggle::test_haggle_cooldown_blocks_attempt PASSED
tests/test_haggle.py::TestHaggleIntegration::test_haggle_not_at_shop PASSED
tests/test_haggle.py::TestHaggleIntegration::test_buy_applies_haggle_bonus PASSED
tests/test_haggle.py::TestHaggleIntegration::test_sell_applies_haggle_bonus PASSED
tests/test_haggle.py::TestHaggleIntegration::test_haggle_bonus_consumed_after_buy PASSED
tests/test_haggle.py::TestHaggleIntegration::test_haggle_bonus_consumed_after_sell PASSED
tests/test_haggle.py::TestHaggleIntegration::test_haggle_cooldown_decrements PASSED
tests/test_haggle.py::TestNPCHaggleAttributes::test_npc_default_haggleable PASSED
tests/test_haggle.py::TestNPCHaggleAttributes::test_npc_default_haggle_cooldown PASSED
tests/test_haggle.py::TestNPCHaggleAttributes::test_npc_to_dict_includes_haggle_fields PASSED
tests/test_haggle.py::TestNPCHaggleAttributes::test_npc_from_dict_with_haggle_fields PASSED
tests/test_haggle.py::TestNPCHaggleAttributes::test_npc_from_dict_backwards_compat PASSED
tests/test_haggle.py::TestGameStateHaggleBonus::test_game_state_default_haggle_bonus PASSED
tests/test_haggle.py::TestGameStateHaggleBonus::test_haggle_in_known_commands PASSED
```

Related tests also pass (76 tests in test_game_state.py and test_npc.py).

## Technical Details

### Haggle Mechanics

1. **Success Chance**: 25% base + (CHA × 2%) + 15% if NPC is persuaded, capped at 85%
2. **Outcomes**:
   - **Success**: 15% bonus on next transaction
   - **Critical Success** (roll ≤ 10% of success chance): 25% bonus + rare item hint message
   - **Failure**: No effect, can retry
   - **Critical Failure** (roll ≥ 95): 3-turn cooldown on NPC

### Integration Points

- Bonus applied AFTER CHA modifier and persuade discount in buy/sell
- Bonus consumed (reset to 0.0) after ANY transaction (buy or sell)
- Cooldown decremented at start of each exploration command (when NPC is set)
- Command only works when `current_shop` is active

## E2E Test Suggestions

1. Start game, find merchant, use `talk <merchant>`, then `shop`
2. Use `haggle` command, verify success/failure messages
3. On success, use `buy <item>` and verify discounted price
4. On critical failure, verify cannot haggle for 3 turns
5. Use `look` or `go` commands to verify cooldown decrements
