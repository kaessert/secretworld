# Quest Completion Rewards Implementation Plan

## Feature Spec

When a quest's objectives are met (e.g., kill X enemies), the system should:
1. Automatically mark the quest as COMPLETED (already implemented)
2. Grant defined rewards to the player: gold, XP, and optionally items
3. Display reward notification messages to the player

## Implementation Steps

### 1. Extend Quest Model with Rewards

**File:** `src/cli_rpg/models/quest.py`

Add optional reward fields to the Quest dataclass:
```python
gold_reward: int = field(default=0)
xp_reward: int = field(default=0)
item_rewards: List[str] = field(default_factory=list)  # Item names
```

Update:
- `__post_init__`: Validate rewards are non-negative
- `to_dict()`: Include reward fields
- `from_dict()`: Deserialize reward fields

### 2. Create Reward Granting Method on Character

**File:** `src/cli_rpg/models/character.py`

Add method `claim_quest_rewards(quest: Quest) -> List[str]`:
- Validates quest status is COMPLETED
- Grants gold via `add_gold()`
- Grants XP via `gain_xp()`
- Grants items by name lookup (requires item generation utility)
- Returns list of reward messages

### 3. Integrate Rewards into record_kill

**File:** `src/cli_rpg/models/character.py`

Modify `record_kill()` to call `claim_quest_rewards()` when a quest completes:
```python
if completed:
    quest.status = QuestStatus.COMPLETED
    messages.append(f"Quest Complete: {quest.name}!")
    reward_messages = self.claim_quest_rewards(quest)
    messages.extend(reward_messages)
```

### 4. Update NPC Quest Generation with Rewards

**File:** `src/cli_rpg/ai_world.py` (or wherever NPC quests are created)

Ensure generated quests include reward values. For AI-generated quests, add reward fields to the generation template. For static quests, set sensible defaults based on difficulty/target_count.

### 5. Write Tests

**File:** `tests/test_quest_rewards.py`

Tests to write:
- `test_quest_with_rewards_serialization` - to_dict/from_dict with rewards
- `test_quest_reward_validation` - negative rewards rejected
- `test_claim_quest_rewards_grants_gold`
- `test_claim_quest_rewards_grants_xp`
- `test_claim_quest_rewards_grants_items`
- `test_claim_quest_rewards_requires_completed_status`
- `test_record_kill_grants_rewards_on_completion`
- `test_quest_rewards_display_messages`

**File:** `tests/test_quest_progress.py`

Add integration test:
- `test_record_kill_with_rewards_integration`

## Test-First Order

1. Write Quest model reward field tests
2. Implement Quest model changes
3. Write claim_quest_rewards tests
4. Implement claim_quest_rewards method
5. Write record_kill reward integration tests
6. Integrate into record_kill
7. Update quest generation to include rewards
