# Implementation Summary: Secret Discovery Rewards

## What Was Implemented

### New Features
1. **Secret Reward System** - Players now receive tangible rewards when discovering secrets via the `search` command:
   - **hidden_treasure**: Awards gold and/or items to the player's inventory
   - **trap**: Either deals damage (DEX < 12) or grants 10 XP for disarming (DEX >= 12)
   - **lore_hint**: Grants 5 XP for discovery
   - **hidden_door**: Reveals a new exit direction at the current location

2. **`apply_secret_rewards()` function** in `secrets.py` - Handles reward application based on secret type

3. **`temporary_exits` field** on Location model - Stores exits revealed by hidden_door secrets

### Files Modified
| File | Changes |
|------|---------|
| `src/cli_rpg/secrets.py` | Added `apply_secret_rewards()` function and helper functions (`_apply_treasure_reward`, `_apply_trap_effect`, `_apply_lore_reward`, `_apply_hidden_door`). Updated `perform_active_search()` to call reward logic. |
| `src/cli_rpg/models/location.py` | Added `temporary_exits: List[str]` field with serialization/deserialization support |
| `tests/test_secret_rewards.py` | NEW - 11 test cases covering all reward types |

### Key Design Decisions
- Rewards are marked as `reward_applied: True` in the secret dict to prevent re-granting on subsequent searches
- Item creation uses `_create_treasure_item()` which matches known item types (potions, weapons, etc.) or defaults to misc items
- Trap disarm threshold is DEX >= 12 (configurable via `TRAP_DEX_THRESHOLD` constant)
- XP rewards: 10 XP for trap disarm, 5 XP for lore discovery

## Test Results
- **11 new tests** in `test_secret_rewards.py` - all passing
- **22 existing tests** in `test_perception.py` - all still passing
- **Full test suite**: 4113 tests passing

## E2E Validation
To manually test:
1. Start game with `cli-rpg`
2. Navigate to a location with hidden secrets
3. Run `search` command
4. Verify:
   - For `hidden_treasure`: Gold/item added to inventory
   - For `lore_hint`: XP gained
   - For `trap`: Either damage or XP based on DEX
   - For `hidden_door`: New exit revealed
5. Run `search` again - should not re-grant rewards
