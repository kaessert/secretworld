# Quest Faction Integration - Implementation Summary

## What Was Implemented

### 1. Quest Model Updates (`src/cli_rpg/models/quest.py`)
Added four new fields to the Quest dataclass:
- `faction_affiliation: Optional[str]` - The faction this quest is associated with (defaults to None)
- `faction_reward: int` - Reputation gained with affiliated faction on completion (defaults to 0)
- `faction_penalty: int` - Reputation lost with rival faction on completion (defaults to 0)
- `required_reputation: Optional[int]` - Minimum reputation with faction required to accept quest (defaults to None)

Added validation in `__post_init__`:
- `faction_reward` cannot be negative
- `faction_penalty` cannot be negative

Updated serialization:
- `to_dict()` includes all four faction fields
- `from_dict()` restores faction fields with backward compatibility for old save files

### 2. Character Model Updates (`src/cli_rpg/models/character.py`)
Updated `claim_quest_rewards()` method:
- Added optional `factions: Optional[List["Faction"]]` parameter
- On quest completion with faction affiliation:
  - Applies `faction_reward` to the affiliated faction
  - Applies `faction_penalty` to the rival faction (using `FACTION_RIVALRIES` mapping)
  - Returns appropriate reputation change messages
  - Includes level-up messages when reputation thresholds are crossed

### 3. Main Command Handler Updates (`src/cli_rpg/main.py`)

#### Complete Command (line ~1703)
- Passes `game_state.factions` to `claim_quest_rewards()` so faction reputation changes are applied

#### Accept Command (line ~1649-1681)
- Added reputation check before accepting quest:
  - If quest has `required_reputation` and `faction_affiliation`, checks if player's reputation meets the requirement
  - If reputation is too low, NPC refuses to give the quest with appropriate message
- Quest cloning now includes all four faction fields when creating the player's copy

### 4. Test Updates (`tests/test_quest.py`)
- Updated `test_to_dict` to include the four new faction fields in the expected output

## Test Results

All tests pass:
- `tests/test_quest_faction.py`: 22 new tests covering all aspects of the feature
- `tests/test_quest*.py` and `tests/test_faction*.py`: 308 tests pass
- Full test suite: 3785 tests pass

## New Test File: `tests/test_quest_faction.py`

Created comprehensive tests covering:
- Quest model tests (13 tests): field defaults, validation, serialization
- Claim rewards faction integration tests (6 tests): reputation changes, messages, level-ups
- Quest acceptance tests (3 tests): reputation requirements

## E2E Validation Scenarios

To validate the implementation end-to-end:

1. **Quest with faction reward**: Create/accept a quest with `faction_affiliation="Town Guard"` and `faction_reward=10`. Complete it and verify Town Guard reputation increases by 10.

2. **Quest with faction penalty**: Create a quest with `faction_penalty=5` for Town Guard. Complete it and verify Thieves Guild reputation decreases by 5.

3. **Reputation requirement**: Create a quest requiring 60 reputation with Town Guard. With player at 50 reputation, verify quest cannot be accepted. Increase reputation to 60+ and verify quest can be accepted.

4. **Save/Load**: Accept a faction quest, save game, load game, and verify all faction fields are preserved on the quest.
